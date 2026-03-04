# match_gig.py

import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from bson import ObjectId
from sentence_transformers import SentenceTransformer
from app.DB.vectorDB.vectordb import search_similar_gigs, search_similar_resumes
from app.DB.mongodb.mongodb import MongoDB
from app.Services.match_gig.domain_rules import classify_gig_domain, is_hard_blocked

_instance = None

def get_match_gig() -> "MatchGig":
    global _instance
    if _instance is None:
        _instance = MatchGig()
    return _instance


class MatchGig:
    def __init__(self):
        self.model   = SentenceTransformer('BAAI/bge-base-en-v1.5')
        self.mongodb = MongoDB()

    async def get_embedding(self, text: str):
        try:
            loop      = asyncio.get_event_loop()
            prefixed  = f"Represent this sentence for searching relevant passages: {text}"
            embedding = await loop.run_in_executor(None, self.model.encode, prefixed)
            return embedding.tolist()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC — API calls this
    # ─────────────────────────────────────────────────────────────────────────

    async def get_similar_gigs(self, user_id: str, page: int = 1, page_size: int = 10) -> dict:
        """
        1. Check recommendations collection
        2. If exists → serve from DB (fast path)
        3. If not → run full vector search + domain filter + save
        """
        rec_doc = await self.mongodb.recommendations_collection.find_one(
            {"userId": ObjectId(user_id)},
            {"gigIds": 1, "scoreMap": 1, "resumeDomain": 1}
        )

        if rec_doc and rec_doc.get("gigIds"):
            return await self._serve_from_recommendations(user_id, rec_doc, page, page_size)

        return await self._run_search_and_save(user_id, page, page_size)

    # ─────────────────────────────────────────────────────────────────────────
    # SERVE FROM DB — recommendations already exist
    # ─────────────────────────────────────────────────────────────────────────

    async def _serve_from_recommendations(
        self, user_id: str, rec_doc: dict, page: int, page_size: int
    ) -> dict:
        saved_ids = rec_doc.get("gigIds", [])
        total     = len(saved_ids)
        start     = (page - 1) * page_size
        page_ids  = saved_ids[start: start + page_size]

        object_ids = [ObjectId(gid) for gid in page_ids]
        projection = {
            "gigTitle": 1, "industryName": 1, "description": 1, "location": 1,
            "duration": 1, "gigType": 1, "exparienceLevel": 1, "validUntil": 1,
            "createdAt": 1, "tech_stack": 1, "gigStatus": 1, "category": 1,
        }
        cursor = self.mongodb.job_collection.find({"_id": {"$in": object_ids}}, projection)
        gigs   = await cursor.to_list(length=page_size)

        score_map     = rec_doc.get("scoreMap", {})
        resume_domain = rec_doc.get("resumeDomain")
        formatted     = self._format_gig_list(gigs, score_map, resume_domain)

        return {
            "user_id":      user_id,
            "page":         page,
            "page_size":    page_size,
            "total":        total,
            "total_pages":  -(-total // page_size),
            "resumeDomain": resume_domain,
            "gigs":         formatted,
            "source":       "recommendations",
            "matchNote":    "Matches are based on skill similarity and will continue to improve as we refine industry-specific intelligence.",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # FULL VECTOR SEARCH — first time or cron refresh
    # ─────────────────────────────────────────────────────────────────────────

    async def _run_search_and_save(self, user_id: str, page: int, page_size: int) -> dict:
        # 1. Fetch resume — domain already classified during parsing
        resume_doc = await self.mongodb.resume_collection.find_one(
            {"userId": ObjectId(user_id)},
            {"embedding": 1, "domain": 1}
        )
        if not resume_doc:
            raise HTTPException(status_code=404, detail=f"Resume not found for userId: {user_id}")

        embedding = resume_doc.get("embedding")
        if not embedding:
            raise HTTPException(status_code=400, detail="Resume has no embedding yet")

        resume_domain = resume_doc.get("domain")  # set during resume parse — no AI call here

        # 2. Vector search
        qdrant_results = await search_similar_gigs(embedding, limit=200)
        if not qdrant_results:
            return self._empty_response(user_id, page, page_size, resume_domain)

        gig_id_list = [r["gig_id"] for r in qdrant_results]
        score_map   = {r["gig_id"]: r["score"] for r in qdrant_results}

        # 3. Fetch gig docs
        object_ids = [oid for gid in gig_id_list if (oid := self._safe_oid(gid))]
        projection = {
            "gigTitle": 1, "industryName": 1, "description": 1, "location": 1,
            "duration": 1, "gigType": 1, "exparienceLevel": 1, "validUntil": 1,
            "createdAt": 1, "tech_stack": 1, "gigStatus": 1, "category": 1,
            "jobDescription": 1, "responsibilities": 1,
        }
        cursor = self.mongodb.job_collection.find({"_id": {"$in": object_ids}}, projection)
        gigs   = await cursor.to_list(length=200)

        # 4. Apply hard domain filter + score filtering
        filtered    = self._apply_domain_filter(gigs, score_map, resume_domain)
        filtered_ids = [g["_id"] for g in filtered]
        filtered_scores = {g["_id"]: g["similarityScore"] for g in filtered}

        # 5. Save to recommendations (background — don't block response)
        asyncio.create_task(
            self._save_recommendations(user_id, filtered_ids, filtered_scores, resume_domain)
        )

        total = len(filtered)
        start = (page - 1) * page_size

        return {
            "user_id":      user_id,
            "page":         page,
            "page_size":    page_size,
            "total":        total,
            "total_pages":  -(-total // page_size),
            "resumeDomain": resume_domain,
            "gigs":         filtered[start: start + page_size],
            "source":       "vector_search",
            "matchNote":    "Matches are based on skill similarity and will continue to improve as we refine industry-specific intelligence.",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # DOMAIN FILTER — hard block + score threshold
    # ─────────────────────────────────────────────────────────────────────────

    def _apply_domain_filter(
        self,
        gigs: list,
        score_map: dict,
        resume_domain: str = None,
    ) -> list:
        now      = datetime.now(timezone.utc)
        filtered = []

        for gig in gigs:
            if gig.get("gigStatus") != "ACTIVE":
                continue

            valid_until = gig.get("validUntil")
            if valid_until:
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                if valid_until < now:
                    continue

            gig_id_str = str(gig["_id"])
            raw_score  = score_map.get(gig_id_str, 0.0)

            # ── Hard domain block ─────────────────────────────────────────
            gig_domain = classify_gig_domain(gig)
            if resume_domain and is_hard_blocked(resume_domain, gig_domain):
                continue  # blocked — never show regardless of score

            # ── Soft score threshold ──────────────────────────────────────
            if raw_score < 0.45:
                continue

            formatted = self._format_gig(gig, raw_score, resume_domain, gig_domain)
            filtered.append(formatted)

        filtered.sort(key=lambda g: g["similarityScore"], reverse=True)
        return filtered

    # ─────────────────────────────────────────────────────────────────────────
    # SAVE RECOMMENDATIONS
    # ─────────────────────────────────────────────────────────────────────────

    async def _save_recommendations(
        self,
        user_id: str,
        gig_ids: list[str],
        score_map: dict,
        resume_domain: str = None,
    ):
        """Upsert recommendation doc — $addToSet ensures no duplicates."""
        try:
            existing = await self.mongodb.recommendations_collection.find_one(
                {"userId": ObjectId(user_id)},
                {"gigIds": 1, "scoreMap": 1}
            )
            existing_ids    = set(existing.get("gigIds", [])) if existing else set()
            new_ids         = [gid for gid in gig_ids if gid not in existing_ids]
            merged_scores   = {**(existing.get("scoreMap", {}) if existing else {}), **score_map}

            await self.mongodb.recommendations_collection.update_one(
                {"userId": ObjectId(user_id)},
                {
                    "$addToSet": {"gigIds": {"$each": new_ids}},
                    "$set": {
                        "scoreMap":     merged_scores,
                        "resumeDomain": resume_domain,
                        "updatedAt":    datetime.now(timezone.utc),
                    },
                    "$setOnInsert": {
                        "userId":    ObjectId(user_id),
                        "createdAt": datetime.now(timezone.utc),
                    },
                },
                upsert=True,
            )
            if new_ids:
                print(f"[Recommendations] {len(new_ids)} new gigs saved for {user_id}")
        except Exception as e:
            print(f"[Recommendations] Save failed for {user_id}: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # NOTIFY ON NEW GIG — called when a new gig is added to the platform
    # ─────────────────────────────────────────────────────────────────────────

    async def notify_matched_users_for_gig(self, gig_id: str, embedding: list):
        """
        1. Find matching resumes via Qdrant
        2. For each user — apply hard domain block
        3. If passes → add gig to their recommendations
        4. Log MATCHED_GIG activity
        """
        try:
            # Fetch full gig doc for domain classification
            gig = await self.mongodb.job_collection.find_one({"_id": ObjectId(gig_id)})
            if not gig:
                return

            gig_domain = classify_gig_domain(gig)

            # Find matching users from Qdrant
            matched_users = await search_similar_resumes(embedding, limit=100)
            # matched_users = [{"user_id": "...", "score": 0.87}, ...]

            notified = 0
            for match in matched_users:
                user_id   = match.get("user_id")
                match_score = match.get("score", 0.0)

                if not user_id or match_score < 0.45:
                    continue

                # Get user's resume domain from DB
                resume_doc = await self.mongodb.resume_collection.find_one(
                    {"userId": ObjectId(user_id)},
                    {"domain": 1}
                )
                if not resume_doc:
                    continue

                resume_domain = resume_doc.get("domain")

                # ── Hard domain block ─────────────────────────────────────
                if is_hard_blocked(resume_domain, gig_domain):
                    continue  # skip — wrong domain for this user

                # ── Add to user's recommendations ─────────────────────────
                await self._save_recommendations(
                    user_id,
                    [gig_id],
                    {gig_id: match_score},
                    resume_domain,
                )

                # ── Log activity ──────────────────────────────────────────
                await self.mongodb.activityLog_collection.insert_one({
                    "userId":    ObjectId(user_id),
                    "action":    "MATCHED_GIG",
                    "createdAt": datetime.now(timezone.utc),
                })
                notified += 1

            print(f"[Notify] Gig {gig_id} → {notified} users notified (domain: {gig_domain})")
            return {"notified": notified, "gig_domain": gig_domain}

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def get_user_this_month_match_gig(self, user_id: str):
        try:
            count = await self.mongodb.activityLog_collection.count_documents({
                "userId":    ObjectId(user_id),
                "action":    "MATCHED_GIG",
                "createdAt": {"$gte": datetime.now(timezone.utc) - timedelta(days=30)},
            })
            return {"user_id": user_id, "matched_gigs_this_month": count}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ─────────────────────────────────────────────────────────────────────────

    def _format_gig_list(self, gigs, score_map, resume_domain) -> list:
        now = datetime.now(timezone.utc)
        result = []
        for gig in gigs:
            if gig.get("gigStatus") != "ACTIVE":
                continue
            valid_until = gig.get("validUntil")
            if valid_until:
                if valid_until.tzinfo is None:
                    valid_until = valid_until.replace(tzinfo=timezone.utc)
                if valid_until < now:
                    continue
            gig_domain = classify_gig_domain(gig)
            score      = score_map.get(str(gig["_id"]), 0.0)
            result.append(self._format_gig(gig, score, resume_domain, gig_domain))
        result.sort(key=lambda g: g["similarityScore"], reverse=True)
        return result

    def _format_gig(self, gig, score, resume_domain=None, gig_domain=None) -> dict:
        return {
            "_id":             str(gig["_id"]),
            "gigTitle":        gig.get("gigTitle"),
            "industryName":    gig.get("industryName"),
            "description":     gig.get("description"),
            "location":        gig.get("location"),
            "duration":        gig.get("duration"),
            "gigType":         gig.get("gigType"),
            "exparienceLevel": gig.get("exparienceLevel"),
            "validUntil":      gig.get("validUntil"),
            "createdAt":       gig.get("createdAt"),
            "tech_stack":      gig.get("tech_stack", []),
            "similarityScore": round(score, 4),
            "matchPercent":    f"{round(score * 100)}%",
            "gigDomain":       gig_domain,
            "domainMatch":     resume_domain == gig_domain,
        }

    def _safe_oid(self, gid):
        try:
            return ObjectId(gid)
        except Exception:
            return None

    def _empty_response(self, user_id, page, page_size, resume_domain=None) -> dict:
        return {
               "user_id": user_id, "page": page, "page_size": page_size,
               "total": 0, "total_pages": 0, "gigs": [],
               "resumeDomain": resume_domain, "source": "vector_search",
               "matchNote": "Matches are based on skill similarity and will continue to improve as we refine industry-specific intelligence.",
        }