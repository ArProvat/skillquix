# cron.py
import asyncio
from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.DB.mongodb.mongodb import MongoDB
from app.Services.match_gig.match_gig import MatchGig


async def refresh_all_user_matches():
     print(f"[CRON] Starting match refresh at {datetime.now(timezone.utc)}")
     mongodb  = MongoDB()
     match_gig = MatchGig()

     # Get all users who have a resume with embedding
     cursor = mongodb.resume_collection.find(
          {"embedding": {"$exists": True}},
          {"userId": 1}          # only fetch userId, skip large embedding field
     )
     resumes = await cursor.to_list(length=10000)

     success = 0
     failed  = []

     for resume in resumes:
          user_id = str(resume.get("userId", ""))
          if not user_id:
               continue
          try:
               # run_vector_search_and_save handles saving new gig IDs to DB
               await match_gig.run_vector_search_and_save(
                    user_id=user_id,
                    page=1,
                    page_size=10     # we only care about saving, not paginating
               )
               success += 1
          except Exception as e:
               failed.append({"user_id": user_id, "error": str(e)})

     print(f"[CRON] Done — {success} users refreshed, {len(failed)} failed")
     if failed:
          print(f"[CRON] Failed users: {failed}")

from app.Services.clearity_score.clearity_score import get_clearity_score_service 


async def refresh_all_activity_scores():
     print(f"[CRON] Activity score refresh started at {datetime.now(datetime.timezone.utc)}")
     mongodb = MongoDB()
     service = get_clearity_score_service()

     # Get all users who have activity logs
     pipeline = [
          {"$group": {"_id": "$userId"}},   # distinct userIds from ActivityLog
          {"$limit": 10000}
     ]
     cursor  = mongodb.activityLog_collection.aggregate(pipeline)
     users   = await cursor.to_list(length=10000)

     success, failed = 0, []

     for u in users:
          user_id = str(u["_id"])
          try:
               await service._calculate_and_save(user_id)   # force recalculate
               success += 1
               await asyncio.sleep(0.2)   # avoid hammering AI API
          except Exception as e:
               failed.append({"user_id": user_id, "error": str(e)})

     print(f"[CRON] Activity scores done — {success} updated, {len(failed)} failed")


def start_scheduler():
     from apscheduler.schedulers.asyncio import AsyncIOScheduler

     scheduler = AsyncIOScheduler()

     # Gig matches — every 12 hours
     scheduler.add_job(
          refresh_all_user_matches,
          trigger="interval", hours=12,
          id="refresh_matches",
          next_run_time=datetime.now(timezone.utc),
     )

     # Activity scores — every 24 hours
     scheduler.add_job(
          refresh_all_activity_scores,
          trigger="interval", hours=24,
          id="refresh_activity_scores",
          next_run_time=datetime.now(timezone.utc),
     )

     scheduler.start()
     print("✅ Schedulers started — gig matches: 12hr, activity scores: 24hr")
     return scheduler
