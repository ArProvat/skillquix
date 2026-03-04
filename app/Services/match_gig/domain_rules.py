
HARD_BLOCK_RULES: dict[str, list[str]] = {
     "healthcare":        ["it_software", "devops", "data_science", "design", "marketing"],
     "clinical_research": ["it_software", "devops", "design", "marketing", "finance"],
     "it_software":       ["healthcare", "clinical_research", "legal"],
     "data_science":      ["healthcare", "clinical_research", "legal", "design"],
     "finance":           ["healthcare", "clinical_research", "devops", "design"],
     "devops":            ["healthcare", "clinical_research", "finance", "legal", "design"],
     "marketing":         ["healthcare", "clinical_research", "devops", "legal"],
     "design":            ["healthcare", "clinical_research", "devops", "finance", "legal"],
     "legal":             ["it_software", "devops", "design", "data_science"],
     "operations":        [],   # broad domain — allow most
}

DOMAIN_GIG_KEYWORDS: dict[str, list[str]] = {
     "healthcare":        ["clinical", "medical", "health", "pharma", "hospital", "patient", "nursing"],
     "clinical_research": ["clinical trial", "gcp", "cra", "crc", "protocol", "fda", "irb", "edc", "pharmacovigilance"],
     "it_software":       ["software", "developer", "frontend", "backend", "fullstack", "programming", "react", "node"],
     "data_science":      ["machine learning", "data science", "analytics", "nlp", "python", "tensorflow", "model"],
     "finance":           ["finance", "accounting", "audit", "investment", "banking", "cpa", "cfa"],
     "operations":        ["operations", "supply chain", "logistics", "procurement", "erp", "six sigma"],
     "marketing":         ["marketing", "seo", "brand", "campaign", "social media", "content", "growth"],
     "legal":             ["legal", "compliance", "law", "contract", "regulatory", "attorney"],
     "design":            ["design", "ux", "ui", "figma", "wireframe", "prototype", "graphic"],
     "devops":            ["devops", "aws", "kubernetes", "docker", "ci/cd", "cloud", "infrastructure", "terraform"],
}


def classify_gig_domain(gig: dict) -> str | None:
     """Keyword-based gig classification — no AI needed, fast."""
     gig_text = " ".join(filter(None, [
          (gig.get("category") or "").lower(),
          (gig.get("gigTitle") or "").lower(),
          (gig.get("description") or "").lower(),
          (gig.get("jobDescription") or "").lower(),
          " ".join(gig.get("tech_stack") or []).lower(),
          " ".join(gig.get("responsibilities") or []).lower(),
     ]))

     best_domain = None
     best_score  = 0

     for domain, keywords in DOMAIN_GIG_KEYWORDS.items():
          score = sum(1 for kw in keywords if kw in gig_text)
          if score > best_score:
               best_score  = score
               best_domain = domain

     return best_domain if best_score >= 1 else None


def is_hard_blocked(resume_domain: str, gig_domain: str) -> bool:
     if not resume_domain or not gig_domain:
          return False
     return gig_domain in HARD_BLOCK_RULES.get(resume_domain, [])