# activity_score_router.py
from fastapi import APIRouter, HTTPException, Query
from app.Services.clearity_score.clearity_score import get_clearity_score_service
from app.Services.match_gig.match_gig import MatchGig
import asyncio

router = APIRouter()

@router.get("/clearity-score/{user_id}")
async def get_clearity_score(user_id: str):
     """
     Returns current and previous month activity scores.
     - Served from DB if < 24hrs old
     - Recalculated via AI if stale or missing
     """
     try:
          score_result, match_result = await asyncio.gather(
               get_clearity_score_service().get_clearity_score(user_id),
               MatchGig().get_user_this_month_match_gig(user_id),
          )
          return {**score_result, **match_result}   # merge both dicts
     except HTTPException:
          raise
     except Exception as e:
          raise HTTPException(status_code=500, detail=str(e))

@router.get("/debug/clearity-logs/{user_id}")
async def debug_clearity_logs(user_id: str):
     from app.DB.mongodb.mongodb import MongoDB
     from datetime import datetime, timezone, timedelta
     from calendar import monthrange
     from bson import ObjectId

     mongodb = MongoDB()
     now     = datetime.now(timezone.utc)

     # This month
     last_day   = monthrange(now.year, now.month)[1]
     curr_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
     curr_end   = datetime(now.year, now.month, last_day, 23, 59, 59, tzinfo=timezone.utc)

     logs = await mongodb.activityLog_collection.find(
          {"userId": ObjectId(user_id), "createdAt": {"$gte": curr_start, "$lte": curr_end}},
          {"action": 1, "createdAt": 1}
     ).to_list(length=100)

     return {
          "user_id":    user_id,
          "month":      now.strftime("%B %Y"),
          "log_count":  len(logs),
          "logs":       [{"action": l.get("action"), "createdAt": str(l.get("createdAt"))} for l in logs],
     }