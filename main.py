from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import prospects
from app.core.database import Base, engine
from app.models import prospect

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Proprexis CRM")

# CORS — autorise Next.js (port 3000) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes API préfixées /api
app.include_router(prospects.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "message": "Proprexis API"}