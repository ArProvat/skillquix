from fastapi import FastAPI,HTTPException
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.DB.vectorDB.vectordb import create_collections
from fastapi.middleware.cors import CORSMiddleware
from app.Services.resume_parse.resume_parse_router import router as resume_parse_router
from app.Services.refelection.refelection_router import router as refelection_router
from app.Services.recommend_skill.recommend_skill_router import router as recommend_skill_router
from app.Services.skill_impact.skill_impact_router import router as skill_impact_router
from app.Services.match_gig.match_gig_router import router as match_gig_router
from app.DB.vectorDB.router import router as vectorDB_router
from app.utils.cron import start_scheduler
from app.Services.match_gig.match_gig import get_match_gig

@asynccontextmanager
async def lifespan(app: FastAPI):
     await create_collections()     # Qdrant collections
     start_scheduler()  
     get_match_gig()            # 12hr cron job
     yield

app = FastAPI(
     title="SkillQuix",
     description="SkillQuix AI API",
     version="1.0.0",
     docs_url="/docs",
     redoc_url="/redoc",
     lifespan=lifespan
)

app.add_middleware(
     CORSMiddleware,
     allow_origins=["*"],
     allow_credentials=True,
     allow_methods=["*"],
     allow_headers=["*"],
)

app.include_router(resume_parse_router,prefix="/v1",tags=["Resume Parse"])
app.include_router(refelection_router,prefix="/v1",tags=["Refelection"])
app.include_router(recommend_skill_router,prefix="/v1",tags=["Recommend Skill"])
app.include_router(skill_impact_router,prefix="/v1",tags=["Skill Impact"])
app.include_router(match_gig_router,prefix="/v1",tags=["Match Gig"])
app.include_router(vectorDB_router,prefix="/v1",tags=["VectorDB Operation"])

@app.get("/")
def read_root():
     return {"message": "Welcome to SkillQuix AI API"}

@app.on_event("startup")
async def startup_event():
     print("SkillQuix AI API is starting...")

@app.on_event("shutdown")
async def shutdown_event():
     print("SkillQuix AI API is shutting down...")

if __name__ == "__main__":
     import uvicorn
     uvicorn.run("main:app", 
               host="0.0.0.0", 
               port=8000, 
               reload=True
          ) 