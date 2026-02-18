from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.Services.resume_parse.resume_parse_router import router as resume_parse_router


app = FastAPI(
     title="SkillQuix",
     description="SkillQuix AI API",
     version="1.0.0",
     docs_url="/docs",
     redoc_url="/redoc",
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