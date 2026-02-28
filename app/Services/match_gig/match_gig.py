# match_gig.py
import asyncio
from datetime import datetime, timezone , timedelta
from fastapi import HTTPException
from bson import ObjectId
from sentence_transformers import SentenceTransformer
from app.DB.vectorDB.vectordb import search_similar_gigs, search_similar_resumes
from app.DB.mongodb.mongodb import MongoDB

_instance = None  # module-level singleton

def get_match_gig() -> "MatchGig":
     global _instance
     if _instance is None:
          _instance = MatchGig()
     return _instance


class MatchGig:
     def __init__(self):
          self.model   = SentenceTransformer('all-MiniLM-L6-v2')
          self.mongodb = MongoDB()
     async def get_embedding(self, text: str):
          try:
               loop = asyncio.get_event_loop()
               embedding = await loop.run_in_executor(None, self.model.encode, text)
               return embedding.tolist()
          except Exception as e:
               raise HTTPException(status_code=500, detail=str(e))

     async def get_similar_gigs(self, user_id: str, page: int = 1, page_size: int = 10) -> dict:
          # Run MongoDB lookup and nothing else here — fast path first
          existing_doc = await self.mongodb.matches_collection.find_one(
               {"userId": ObjectId(user_id)},
               {"gigIds": 1, "scoreMap": 1}   # ← projection — don't fetch whole doc
          )

          if existing_doc and existing_doc.get("gigIds"):
               return await self.get_matches_from_db(user_id, existing_doc, page, page_size)
          else:
               return await self.run_vector_search_and_save(user_id, page, page_size)

     async def get_matches_from_db(self, user_id: str, existing_doc: dict, page: int, page_size: int) -> dict:
          saved_gig_ids = existing_doc.get("gigIds", [])
          total         = len(saved_gig_ids)

          start    = (page - 1) * page_size
          end      = start + page_size
          page_ids = saved_gig_ids[start:end]

          object_ids = [ObjectId(gid) for gid in page_ids]

          # Projection — only fetch fields the UI card needs, skip heavy fields
          projection = {
               "gigTitle": 1, "industryName": 1, "description": 1,
               "location": 1, "duration": 1, "gigType": 1,
               "exparienceLevel": 1, "validUntil": 1, "createdAt": 1,
               "tech_stack": 1, "gigStatus": 1,
          }
          cursor = self.mongodb.job_collection.find(
               {"_id": {"$in": object_ids}},
               projection
          )
          gigs = await cursor.to_list(length=page_size)

          score_map = existing_doc.get("scoreMap", {})
          filtered  = self.filter_gigs(gigs, score_map)

          return {
               "user_id":     user_id,
               "page":        page,
               "page_size":   page_size,
               "total":       total,
               "total_pages": -(-total // page_size),
               "gigs":        filtered,
               "source":      "cache",
          }

     async def run_vector_search_and_save(self, user_id: str, page: int, page_size: int) -> dict:
          # Only fetch embedding field — skip rest of resume doc
          resume_doc = await self.mongodb.resume_collection.find_one(
               {"userId": ObjectId(user_id)},
               {"embedding": 1}              # ← projection
          )
          if not resume_doc:
               raise HTTPException(status_code=404, detail=f"Resume not found for userId: {user_id}")

          embedding = resume_doc.get("embedding")
          if not embedding:
               raise HTTPException(status_code=400, detail="Resume has no embedding yet")

          qdrant_results = await search_similar_gigs(embedding, limit=100)

          if not qdrant_results:
               return {
                    "user_id": user_id, "page": page, "page_size": page_size,
                    "total": 0, "total_pages": 0, "gigs": [], "source": "vector_search",
               }

          gig_id_list = [r["gig_id"] for r in qdrant_results]
          score_map   = {r["gig_id"]: r["score"] for r in qdrant_results}

          def safe_object_id(gid: str):
               try:
                    return ObjectId(gid)
               except Exception:
                    return None

          object_ids = [oid for gid in gig_id_list if (oid := safe_object_id(gid))]

          # Projection on gig fetch too
          projection = {
               "gigTitle": 1, "industryName": 1, "description": 1,
               "location": 1, "duration": 1, "gigType": 1,
               "exparienceLevel": 1, "validUntil": 1, "createdAt": 1,
               "tech_stack": 1, "gigStatus": 1,
          }
          cursor = self.mongodb.job_collection.find(
               {"_id": {"$in": object_ids}},
               projection
          )

          # ── Run MongoDB fetch and save_new_matches concurrently ──────────────
          gigs, _ = await asyncio.gather(
               cursor.to_list(length=100),
               self._background_save(user_id, gig_id_list, score_map),  # ← don't block on save
          )

          filtered = self.filter_gigs(gigs, score_map)

          total = len(filtered)
          start = (page - 1) * page_size
          end   = start + page_size

          return {
               "user_id":     user_id,
               "page":        page,
               "page_size":   page_size,
               "total":       total,
               "total_pages": -(-total // page_size),
               "gigs":        filtered[start:end],
               "source":      "vector_search",
          }

     async def _background_save(self, user_id: str, gig_ids: list, score_map: dict):
          """Fire-and-forget save — doesn't block the response."""
          try:
               await self.save_new_matches(user_id, gig_ids, score_map)
          except Exception as e:
               print(f"[Matches] Background save failed for {user_id}: {e}")

     def format_gig(self, gig: dict, score: float) -> dict:
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

     def filter_gigs(self, gigs: list, score_map: dict) -> list:
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
               filtered.append(self.format_gig(gig, score_map.get(gig_id_str, 0.0)))

          filtered.sort(key=lambda g: g["similarityScore"], reverse=True)
          return filtered

     async def save_new_matches(self, user_id: str, gig_ids: list[str], score_map: dict):
          existing_doc = await self.mongodb.matches_collection.find_one(
               {"userId": ObjectId(user_id)},
               {"gigIds": 1, "scoreMap": 1}   # projection
          )
          existing_ids    = set(existing_doc.get("gigIds", [])) if existing_doc else set()
          new_ids         = [gid for gid in gig_ids if gid not in existing_ids]

          if not new_ids:
               return

          existing_scores = existing_doc.get("scoreMap", {}) if existing_doc else {}
          merged_scores   = {**existing_scores, **score_map}

          await self.mongodb.matches_collection.update_one(
               {"userId": ObjectId(user_id)},
               {
                    "$addToSet": {"gigIds": {"$each": new_ids}},
                    "$set": {
                         "scoreMap":  merged_scores,
                         "updatedAt": datetime.now(timezone.utc),
                    },
                    "$setOnInsert": {
                         "userId":    ObjectId(user_id),
                         "createdAt": datetime.now(timezone.utc),
                    },
               },
               upsert=True,
          )
          print(f"[Matches] {len(new_ids)} new gigs saved for {user_id}")

     async def notify_matched_users_for_gig(self, embedding: list):
          try:
               results = await search_similar_resumes(embedding, limit=100)
               
               for result in results:
                    await self.mongodb.activityLog_collection.insert_one({
                         "userId":    ObjectId(result["userId"]),
                         "action":    "MATCHED_GIG",
                         "createdAt": datetime.now(timezone.utc),
                    })
               return results
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