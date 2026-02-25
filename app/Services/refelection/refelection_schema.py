


from pydantic import BaseModel


class refelectionResponse(BaseModel):
     skills: list[str],
     impact_bullets: list[str],
     summary: str
