from fastapi import APIRouter, HTTPException, Depends, Form,Query
from .match_gig import MatchGig


router = APIRouter()


@router.post("/get-embedding")
async def match_gig(
     text: str,
):
     try:
          result = await MatchGig().get_embedding(text)
          return result

     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
import traceback

# router — use singleton, not MatchGig() every request
from app.Services.match_gig.match_gig import get_match_gig

@router.get("/gigs/similar/{user_id}")
async def get_similar_gigs(
     user_id: str,
     page: int = Query(default=1, ge=1),
     page_size: int = Query(default=10, ge=1, le=50),
):
     try:
          result = await get_match_gig().get_similar_gigs(user_id, page=page, page_size=page_size)
          return result
     except HTTPException:
          raise
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))
@router.get("/debug/similar/{user_id}")
async def debug_similar_gigs(user_id: str):
     from bson import ObjectId
     from datetime import datetime, timezone

     mongodb = MatchGig().mongodb

     # Step 1 — check resume embedding exists
     resume_doc = await mongodb.resume_collection.find_one({"userId": ObjectId(user_id)})
     if not resume_doc:
          return {"step": "FAILED", "reason": "No resume found"}

     embedding = resume_doc.get("embedding")
     if not embedding:
          return {"step": "FAILED", "reason": "Resume has no embedding"}

     # Step 2 — check Qdrant results
     from app.DB.vectorDB.vectordb import search_similar_gigs
     qdrant_results = await search_similar_gigs(embedding, limit=100)

     if not qdrant_results:
          return {"step": "FAILED", "reason": "Qdrant returned 0 results — no gigs in vector DB or score threshold too high"}

     # Step 3 — check MongoDB fetch
     gig_id_list = [r["gig_id"] for r in qdrant_results]

     def safe_object_id(gid):
          try:
               return ObjectId(gid)
          except:
               return None

     object_ids = [oid for gid in gig_id_list if (oid := safe_object_id(gid))]
     cursor = mongodb.job_collection.find({"_id": {"$in": object_ids}})
     gigs   = await cursor.to_list(length=100)

     # Step 4 — check why each gig is filtered out
     now = datetime.now(timezone.utc)
     gig_report = []
     for gig in gigs:
          valid_until = gig.get("validUntil")
          if valid_until and valid_until.tzinfo is None:
               valid_until = valid_until.replace(tzinfo=timezone.utc)

               gig_report.append({
                    "_id":            str(gig["_id"]),
                    "gigTitle":       gig.get("gigTitle"),
                    "gigStatus":      gig.get("gigStatus"),
                    "validUntil":     str(valid_until),
                    "is_expired":     valid_until < now if valid_until else False,
                    "status_is_active": gig.get("gigStatus") == "ACTIVE",
                    "score":          next((r["score"] for r in qdrant_results if r["gig_id"] == str(gig["_id"])), None),
               })

     return {
               "resume_has_embedding":  True,
               "qdrant_results_count":  len(qdrant_results),
               "qdrant_gig_ids":        gig_id_list[:5],          # first 5
               "mongodb_fetched_count": len(gigs),
               "object_ids_converted":  len(object_ids),
               "gig_report":            gig_report,
     }


# one-time migration endpoint — run once then remove
@router.post("/admin/reindex-gigs")
async def reindex_all_gigs():
     from app.DB.mongodb.mongodb import MongoDB
     from app.DB.vectorDB.vectordb import upsert_gig_embedding

     mongodb = MongoDB()
     
     # Fetch all gigs that have an embedding
     cursor = mongodb.job_collection.find({"embedding": {"$exists": True}})
     gigs   = await cursor.to_list(length=1000)

     if not gigs:
          return {"error": "No gigs with embeddings found in MongoDB"}

     success = 0
     failed  = []

     for gig in gigs:
          gig_id    = str(gig["_id"])         # real MongoDB ObjectId string
          embedding = gig.get("embedding")

          if not embedding:
               failed.append(gig_id)
               continue

          try:
               await upsert_gig_embedding(gig_id, embedding)
               success += 1
          except Exception as e:
               failed.append({"gig_id": gig_id, "error": str(e)})

     return {
          "total_gigs":    len(gigs),
          "success":       success,
          "failed":        failed,
     }

@router.delete("/admin/qdrant-delete/{gig_id}")
async def delete_qdrant_point(gig_id: str):
     from app.DB.vectorDB.vectordb import client, GIG_COLLECTION, _id_to_int
     await client.delete(
          collection_name=GIG_COLLECTION,
          points_selector=[_id_to_int(gig_id)]
     )
     return {"message": f"Deleted {gig_id} from Qdrant"}