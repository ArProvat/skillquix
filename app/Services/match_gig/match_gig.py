# match_gig.py

import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from bson import ObjectId
from sentence_transformers import SentenceTransformer
from app.DB.vectorDB.vectordb import search_similar_gigs, search_similar_resumes
from app.DB.mongodb.mongodb import MongoDB
from app.Services.match_gig.ai_domain_match import ai_match_gigs_for_user, ai_match_users_for_gig

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
     # PUBLIC API — get similar gigs for user
     # ─────────────────────────────────────────────────────────────────────────

     async def get_similar_gigs(self, user_id: str, page: int = 1, page_size: int = 10) -> dict:
          """
          1. Check recommendations collection → serve from DB if exists
          2. Otherwise → vector search → AI domain match → save → return
          """
          rec_doc = await self.mongodb.recommended_skill_collection.find_one(
               {"userId": ObjectId(user_id)},
               {"gigIds": 1, "scoreMap": 1, "resumeDomain": 1, "resumeSubdomain": 1}
          )

          if rec_doc and rec_doc.get("gigIds"):
               return await self._serve_from_recommendations(user_id, rec_doc, page, page_size)

          return await self._run_search_and_save(user_id, page, page_size)

     # ─────────────────────────────────────────────────────────────────────────
     # SERVE FROM DB
     # ─────────────────────────────────────────────────────────────────────────

     async def _serve_from_recommendations(
          self, user_id: str, rec_doc: dict, page: int, page_size: int
     ) -> dict:
          saved_ids = rec_doc.get("gigIds", [])

          # Fetch user's applied gig IDs to exclude
          applied_ids = await self._get_applied_gig_ids(user_id)

          # Filter out already-applied before pagination
          eligible_ids = [gid for gid in saved_ids if gid not in applied_ids]
          total        = len(eligible_ids)
          start        = (page - 1) * page_size
          page_ids     = eligible_ids[start: start + page_size]

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
          formatted     = self._format_and_filter_active(gigs, score_map)

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
     # VECTOR SEARCH + AI DOMAIN MATCH + SAVE
     # ─────────────────────────────────────────────────────────────────────────

     async def _run_search_and_save(self, user_id: str, page: int, page_size: int) -> dict:
          # 1. Fetch resume with domain info
          resume_doc = await self.mongodb.resume_collection.find_one(
               {"userId": ObjectId(user_id)},
               {"embedding": 1, "domain": 1, "subDomain": 1}
          )
          if not resume_doc:
               return []

          embedding = resume_doc.get("embedding")
          if not embedding:
               raise HTTPException(status_code=400, detail="Resume has no embedding yet")

          resume_domain    = resume_doc.get("domain") or "unknown"
          resume_subdomain = resume_doc.get("subDomain") or "general"

          # 2. Vector search — get candidate gig IDs
          qdrant_results = await search_similar_gigs(embedding, limit=200)
          if not qdrant_results:
               return self._empty_response(user_id, page, page_size, resume_domain)

          gig_id_list = [r["gig_id"] for r in qdrant_results]
          score_map   = {r["gig_id"]: r["score"] for r in qdrant_results}

          # 3. Fetch gig docs with domain info
          object_ids = [oid for gid in gig_id_list if (oid := self._safe_oid(gid))]
          projection = {
               "gigTitle": 1, "industryName": 1, "description": 1, "location": 1,
               "duration": 1, "gigType": 1, "exparienceLevel": 1, "validUntil": 1,
               "createdAt": 1, "tech_stack": 1, "gigStatus": 1,
               "domain": 1, "subDomain": 1, "category": 1,   # ← domain fields
          }
          cursor = self.mongodb.job_collection.find({"_id": {"$in": object_ids}}, projection)
          gigs   = await cursor.to_list(length=200)
          print('gigs', gigs)
          # 4. Build candidates for AI — only ACTIVE + not expired
          now = datetime.now(timezone.utc)
          ai_candidates = []
          gig_lookup    = {}   # gig_id → full gig doc

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
               gig_lookup[gig_id_str] = gig
               ai_candidates.append({
                    "gig_id":    gig_id_str,
                    "domain":    gig.get("domain") or gig.get("category") or "unknown",
                    "subdomain": gig.get("gigTitle"),
                    "score":     round(score_map.get(gig_id_str, 0.0), 4),
               })
          print("resume_domain", resume_domain)
          print("resume_subdomain", resume_subdomain)
          print("ai_candidates", ai_candidates)
          # 5. AI domain match
          matched_gig_ids = await ai_match_gigs_for_user(
               resume_domain, resume_subdomain, ai_candidates
          )
          print("matched_gig_ids", matched_gig_ids)
          # 6. Build final list preserving score order
          matched_scores = {gid: score_map.get(gid, 0.0) for gid in matched_gig_ids}

          # 7. Save in background
          asyncio.create_task(
               self._save_recommendations(user_id, matched_gig_ids, matched_scores)
          )

          # 8. Format and paginate
          matched_gigs = [gig_lookup[gid] for gid in matched_gig_ids if gid in gig_lookup]
          formatted    = self._format_gigs(matched_gigs, matched_scores)
          total        = len(formatted)
          start        = (page - 1) * page_size

          return {
               "user_id":      user_id,
               "page":         page,
               "page_size":    page_size,
               "total":        total,
               "total_pages":  -(-total // page_size),
               "resumeDomain": resume_domain,
               "gigs":         formatted[start: start + page_size],
               "source":       "vector_search",
               "matchNote":    "Matches are based on skill similarity and will continue to improve as we refine industry-specific intelligence.",
          }

     # ─────────────────────────────────────────────────────────────────────────
     # NEW GIG UPLOADED — notify matching users
     # ─────────────────────────────────────────────────────────────────────────

     async def notify_matched_users_for_gig(self, gig_id: str, embedding: list):
          try:
               gig = await self.mongodb.job_collection.find_one(
                    {"_id": ObjectId(gig_id)},
                    {"gigTitle": 1, "category": 1, "gigStatus": 1}
               )
               if not gig or gig.get("gigStatus") != "ACTIVE":
                    return

               gig_domain    = gig.get("category")
               gig_subdomain = gig.get("gigTitle")

               matched_users = await search_similar_resumes(embedding, limit=100)

               if matched_users and isinstance(matched_users[0], str):
                    raise ValueError("search_similar_resumes returned strings not dicts.")

               ai_candidates = []
               score_by_user = {}

               for match in matched_users:
                    user_id     = match.get("user_id")
                    match_score = match.get("score", 0.0)

                    if not user_id or match_score < 0.60:
                         continue

                    resume_doc = await self.mongodb.resume_collection.find_one(
                         {"userId": ObjectId(user_id)},
                         {"domain": 1, "subDomain": 1}
                    )
                    if not resume_doc:
                         continue

                    score_by_user[user_id] = {
                         "score":     match_score,
                         "domain":    resume_doc.get("domain") or "unknown",
                         "subdomain": resume_doc.get("subDomain") or "general",
                    }

                    ai_candidates.append({
                         "user_id":   user_id,
                         "domain":    resume_doc.get("domain") or "unknown",
                         "subdomain": resume_doc.get("subDomain") or "general",
                         "score":     round(match_score, 4),
                    })

               if not ai_candidates:
                    return

               matched_user_ids = await ai_match_users_for_gig(
                    gig_domain, gig_subdomain, ai_candidates
               )

               if not matched_user_ids:
                    return

               # ── Build matched users list with score ───────────────────────────
               matched_users_with_score = [
                    {
                         "userId": ObjectId(uid),
                         "score":  score_by_user.get(uid, {}).get("score", 0.0),
                    }
                    for uid in matched_user_ids
               ]

               # ── Save to gigMatches collection ─────────────────────────────────
               await self.mongodb.notify_gig_match.update_one(
                    {"gigId": ObjectId(gig_id)},
                    {
                         "$set": {
                              "gigId":        ObjectId(gig_id),
                              "matchedUsers": matched_users_with_score,
                              "status":       False,          
                              "updatedAt":    datetime.now(timezone.utc),
                         },
                         "$setOnInsert": {
                              "createdAt": datetime.now(timezone.utc),
                         },
                    },
                    upsert=True,
               )

               # ── Save to recommendations + log activity ────────────────────────
               tasks = []
               for uid in matched_user_ids:
                    match_score = score_by_user.get(uid, {}).get("score", 0.0)
                    tasks.append(self._save_recommendations(
                         uid, [gig_id], {gig_id: match_score}
                    ))
                    tasks.append(self.mongodb.activityLog_collection.insert_one({
                         "userId":    ObjectId(uid),
                         "action":    "MATCHED_GIG",
                         "createdAt": datetime.now(timezone.utc),
                    }))

               if tasks:
                    await asyncio.gather(*tasks)

               print(f"[Notify] Gig {gig_id} → {len(matched_user_ids)} users saved (domain: {gig_domain})")

          except Exception as e:
               print(f"[Notify] Error for gig {gig_id}: {e}")
     # ─────────────────────────────────────────────────────────────────────────
     # SAVE RECOMMENDATIONS
     # ─────────────────────────────────────────────────────────────────────────

     async def _save_recommendations(
          self,
          user_id: str,
          gig_ids: list[str],
          score_map: dict,
     ):
          try:
               existing     = await self.mongodb.recommended_skill_collection.find_one(
                    {"userId": ObjectId(user_id)},
                    {"gigIds": 1, "scoreMap": 1}
               )
               existing_ids  = set(existing.get("gigIds", [])) if existing else set()
               new_ids       = [gid for gid in gig_ids if gid not in existing_ids]
               merged_scores = {**(existing.get("scoreMap", {}) if existing else {}), **score_map}

               update = {
                    "$addToSet": {"gigIds": {"$each": new_ids}},
                    "$set": {
                         "scoreMap":        merged_scores,
                         "updatedAt":       datetime.now(timezone.utc),
                    },
                    "$setOnInsert": {
                         "userId":    ObjectId(user_id),
                         "createdAt": datetime.now(timezone.utc),
                    },
               }

               await self.mongodb.recommended_skill_collection.update_one(
                    {"userId": ObjectId(user_id)}, update, upsert=True
               )
               if new_ids:
                    print(f"[Recommendations] {len(new_ids)} new gigs for {user_id}")
          except Exception as e:
               print(f"[Recommendations] Save failed for {user_id}: {e}")

     # ─────────────────────────────────────────────────────────────────────────
     # HELPERS
     # ─────────────────────────────────────────────────────────────────────────

     async def _get_applied_gig_ids(self, user_id: str) -> set[str]:
          """Get gig IDs the user has already applied to — exclude from results."""
          cursor = self.mongodb.applied_gigs_collection.find(
               {"userId": ObjectId(user_id)},
               {"gigId": 1}
          )
          logs = await cursor.to_list(length=1000)
          return {str(log["gigId"]) for log in logs if log.get("gigId")}

     def _format_and_filter_active(self, gigs: list, score_map: dict) -> list:
          now    = datetime.now(timezone.utc)
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
               score = score_map.get(str(gig["_id"]), 0.0)
               result.append(self._format_gig(gig, score))
          result.sort(key=lambda g: g["similarityScore"], reverse=True)
          return result

     def _format_gigs(self, gigs: list, score_map: dict) -> list:
          result = [self._format_gig(gig, score_map.get(str(gig["_id"]), 0.0)) for gig in gigs]
          result.sort(key=lambda g: g["similarityScore"], reverse=True)
          return result

     def _format_gig(self, gig: dict, score: float) -> dict:
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