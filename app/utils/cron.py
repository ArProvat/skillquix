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


def start_scheduler():
     scheduler = AsyncIOScheduler()
     scheduler.add_job(
          refresh_all_user_matches,
          trigger="interval",
          hours=12,
          id="refresh_matches",
          next_run_time=datetime.now(timezone.utc),  # run immediately on startup too
     )
     scheduler.start()
     print("✅ Match refresh scheduler started — runs every 12 hours")
     return scheduler