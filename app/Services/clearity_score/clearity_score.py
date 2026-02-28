import json
import asyncio
from collections import Counter
from datetime import datetime, timezone, timedelta
from calendar import monthrange
from fastapi import HTTPException
from bson import ObjectId
from app.DB.mongodb.mongodb import MongoDB
from openai import AsyncOpenAI
from app.config.settings import settings

SCORE_TTL_HOURS = 24


class ClearityScoreService:
    def __init__(self):
        self.mongodb = MongoDB()
        self.openai  = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # ── Public ────────────────────────────────────────────────────────────────

    async def get_clearity_score(self, user_id: str) -> dict:
        existing = await self.mongodb.clearityScore_collection.find_one(
            {"userId": ObjectId(user_id)},
            {"currentMonth": 1, "previousMonth": 1, "updatedAt": 1}
        )
        if existing and self._is_fresh(existing.get("updatedAt")):
            return self._format_response(existing, source="cache")
        return await self._calculate_and_save(user_id)

    # ── Private ───────────────────────────────────────────────────────────────

    def _is_fresh(self, updated_at: datetime) -> bool:
        if not updated_at:
            return False
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - updated_at).total_seconds() < SCORE_TTL_HOURS * 3600

    def _month_range(self, year: int, month: int):
        last_day = monthrange(year, month)[1]
        start    = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        end      = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        return start, end

    def _fallback_score(self, logs: list) -> dict:
        count = len(logs)
        score = min(100, count * 2)
        quarter = score // 4
        return {
            "score":     score,
            "breakdown": {
                "engagement":  quarter,
                "variety":     quarter,
                "consistency": quarter,
                "volume":      quarter,
            },
            "summary": f"User had {count} activity events this period.",
        }

    def _format_response(self, doc: dict, source: str) -> dict:
        updated_at = doc.get("updatedAt")
        if updated_at and updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)

        next_refresh = (
            (updated_at + timedelta(hours=SCORE_TTL_HOURS)).isoformat()
            if updated_at else None
        )
        return {
            "currentMonth":  doc.get("currentMonth"),
            "previousMonth": doc.get("previousMonth"),
            "updatedAt":     updated_at.isoformat() if updated_at else None,
            "nextRefreshAt": next_refresh,
            "source":        source,
        }

    async def _get_logs(self, user_id: str, start: datetime, end: datetime) -> list:
        cursor = self.mongodb.activityLog_collection.find(
            {
                "userId":    ObjectId(user_id),
                "createdAt": {"$gte": start, "$lte": end},
            },
            {"action": 1, "createdAt": 1}
        )
        return await cursor.to_list(length=1000)

    async def _calculate_and_save(self, user_id: str) -> dict:
        now                      = datetime.now(timezone.utc)
        curr_start, curr_end     = self._month_range(now.year, now.month)
        prev_dt                  = now.replace(day=1) - timedelta(days=1)
        prev_start, prev_end     = self._month_range(prev_dt.year, prev_dt.month)

        curr_logs, prev_logs = await asyncio.gather(
            self._get_logs(user_id, curr_start, curr_end),
            self._get_logs(user_id, prev_start, prev_end),
        )

        curr_score, prev_score = await asyncio.gather(
            self._get_ai_score(user_id, curr_logs, "current"),
            self._get_ai_score(user_id, prev_logs, "previous"),
        )

        doc = {
            "userId": user_id,
            "currentMonth": {
                "month":       now.strftime("%B %Y"),
                "score":       curr_score["score"],
                "breakdown":   curr_score["breakdown"],
                "summary":     curr_score["summary"],
                "totalEvents": len(curr_logs),
            },
            "previousMonth": {
                "month":       prev_dt.strftime("%B %Y"),
                "score":       prev_score["score"],
                "breakdown":   prev_score["breakdown"],
                "summary":     prev_score["summary"],
                "totalEvents": len(prev_logs),
            },
            "updatedAt": datetime.now(timezone.utc),
        }

        await self.mongodb.clearityScore_collection.update_one(
            {"userId": ObjectId(user_id)},
            {
                "$set":         doc,
                "$setOnInsert": {"createdAt": datetime.now(timezone.utc)},
            },
            upsert=True,
        )
        return self._format_response(doc, source="ai")

    async def _get_ai_score(self, user_id: str, logs: list, period: str) -> dict:
        if not logs:
            return {"score": 0, "breakdown": {}, "summary": "No activity found for this period."}

        serialized = [
            {
                "action":    log.get("action", "").strip(","),
                "createdAt": log["createdAt"].isoformat() if log.get("createdAt") else None,
            }
            for log in logs
        ]

        action_counts = Counter(e["action"] for e in serialized)

        prompt = f"""
You are an activity scoring engine for a freelance gig platform.
Analyze this user's activity for the {period} month period.

Total events: {len(logs)}
Action breakdown: {dict(action_counts)}
Sample events (latest 10): {serialized[:10]}

Score 0-100 based on:
- Engagement: how often user is active (0-25)
- Variety: different types of actions taken (0-25)
- Consistency: regular vs sporadic usage (0-25)
- Volume: total meaningful interactions (0-25)

Possible actions: APPLIED_GIG, VIEWED_GIG, SAVED_GIG, UPDATED_PROFILE, UPLOADED_RESUME, MATCHED_GIG

Respond ONLY with valid JSON, no markdown:
{{
    "score": <integer 0-100>,
    "breakdown": {{
        "engagement":  <0-25>,
        "variety":     <0-25>,
        "consistency": <0-25>,
        "volume":      <0-25>
    }},
    "summary": "<one sentence about this user activity>"
}}
"""
        try:
            response = await self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            # ✅ response is already parsed — no .json() needed
            text = response.choices[0].message.content.strip()
            return json.loads(text)

        except Exception as e:
            print(f"[ClearityScore] AI failed for {user_id}: {e}")
            return self._fallback_score(logs)

    async def log_activity(self, user_id: str, action: str):
        """Helper — call this anywhere to log user activity."""
        await self.mongodb.activityLog_collection.insert_one({
            "userId":    ObjectId(user_id),
            "action":    action,
            "createdAt": datetime.now(timezone.utc),
        })


# ── Singleton ─────────────────────────────────────────────────────────────────
_instance = None

def get_clearity_score_service() -> ClearityScoreService:
    global _instance
    if _instance is None:
        _instance = ClearityScoreService()
    return _instance