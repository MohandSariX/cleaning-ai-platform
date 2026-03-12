from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import Base, engine
from app.models import prospect, client, devis, chantier, facture
from app.api import api_chantier, api_clients, api_devis, api_prospects, api_factures

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Proprexis CRM")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_prospects.router, prefix="/api")
app.include_router(api_clients.router,   prefix="/api")
app.include_router(api_devis.router,     prefix="/api")
app.include_router(api_chantier.router, prefix="/api")
app.include_router(api_factures.router,  prefix="/api")


@app.get("/")
def root():
    return {"status": "ok", "message": "Proprexis API"}