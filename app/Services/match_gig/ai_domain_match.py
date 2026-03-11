
import json
from openai import AsyncOpenAI
from app.config.settings import settings

openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def ai_match_gigs_for_user(
     resume_domain: str,
     resume_subdomain: str,
     gig_candidates: list[dict],   # [{"gig_id": "...", "domain": "...", "subdomain": "...", "score": 0.87}]
) -> list[str]:
     """
     Feed resume domain + gig domain/subdomain into AI.
     AI returns only the gig_ids that are a genuine domain match.
     """
     if not gig_candidates:
          return []

     prompt = f"""
     You are a professional domain-matching engine for a freelance gig platform.

     Candidate's Profile:
     - Domain: {resume_domain}
     - Subdomain: {resume_subdomain}

     Below are gig candidates with their domains and subdomains.
     Return ONLY the gig_ids that are a genuine domain match for this candidate.

     Rules:
     - A match means the gig domain/subdomain aligns with the candidate's field
     - Do NOT match across unrelated domains (e.g. clinical research ↔ software development)
     - Subdomains within the same parent domain CAN match (e.g. clinical_research ↔ healthcare)
     - If domain is unclear or missing for a gig, use your best judgment
     - Be strict — it is better to return fewer high-quality matches

     Gig candidates:
     {json.dumps(gig_candidates, indent=2)}

     Respond ONLY with valid JSON, no markdown:
     {{
     "matched_gig_ids": ["gig_id_1", "gig_id_2", ...]
     }}
     """
     try:
          response = await openai_client.chat.completions.create(
               model="gpt-4o-mini",
               messages=[{"role": "user", "content": prompt}],
               max_tokens=500,
               temperature=0.1,
               response_format={"type": "json_object"},
          )
          result = json.loads(response.choices[0].message.content)
          return result.get("matched_gig_ids", [])
     except Exception as e:
          print(f"[AI Domain Matcher] Failed: {e}")
          # Fallback — return all candidates if AI fails
          return [g["gig_id"] for g in gig_candidates]


async def ai_match_users_for_gig(
     gig_domain: str,
     gig_subdomain: str,
     user_candidates: list[dict],  # [{"user_id": "...", "domain": "...", "subdomain": "...", "score": 0.87}]
) -> list[str]:
     """
     When a new gig is uploaded — AI decides which user IDs are a genuine domain match.
     """
     if not user_candidates:
          return []

     prompt = f"""
          You are a professional domain-matching engine for a freelance gig platform.

          New Gig Profile:
          - Domain: {gig_domain}
          - Subdomain: {gig_subdomain}

          Below are candidate users with their resume domain and subdomain.
          Return ONLY the user_ids whose background genuinely matches this gig.

          Rules:
          - Match means the user's domain/subdomain aligns with the gig's field
          - Do NOT match across unrelated domains
          - Subdomains within the same parent domain CAN match
          - Be strict — fewer high-quality matches is better

          User candidates:
          {json.dumps(user_candidates, indent=2)}

          Respond ONLY with valid JSON, no markdown:
          {{
          "matched_user_ids": ["user_id_1", "user_id_2", ...]
          }}
          """
     try:
          response = await openai_client.chat.completions.create(
               model="gpt-4o-mini",
               messages=[{"role": "user", "content": prompt}],
               temperature=0.1,
               response_format={"type": "json_object"},
          )
          result = json.loads(response.choices[0].message.content)
          return result.get("matched_user_ids", [])
     except Exception as e:
          print(f"[AI User Matcher] Failed: {e}")
          return [u["user_id"] for u in user_candidates]