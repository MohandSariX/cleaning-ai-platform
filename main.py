from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import Base, engine
from app.models import prospect, client, devis, chantier, facture, email_log, conversation, activity_log, ai_memory, tenant, product, escalation
from app.api import api_chantier, api_clients, api_devis, api_prospects, api_factures, api_scraping, api_scheduler, api_watchdog, api_outreach, api_devis_rules, api_pappers, api_activity, api_permis, api_email_finder, api_dvf, api_claude, api_products, api_tenants, api_dashboard, api_escalations
from app.scheduler import start_scheduler, stop_scheduler
from app.agents.telegram_polling import start_polling, stop_polling

load_dotenv()

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage — lancer le scheduler + Telegram polling
    start_scheduler()
    start_polling()
    yield
    # Arrêt — stopper proprement
    stop_scheduler()
    stop_polling()


app = FastAPI(title="Proprexis CRM", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_prospects.router,  prefix="/api")
app.include_router(api_clients.router,    prefix="/api")
app.include_router(api_devis.router,      prefix="/api")
app.include_router(api_chantier.router,   prefix="/api")
app.include_router(api_factures.router,   prefix="/api")
app.include_router(api_scraping.router,   prefix="/api")
app.include_router(api_scheduler.router,  prefix="/api")
app.include_router(api_watchdog.router,   prefix="/api")
app.include_router(api_outreach.router,      prefix="/api")
app.include_router(api_devis_rules.router,   prefix="/api")
app.include_router(api_pappers.router,       prefix="/api")
app.include_router(api_activity.router,      prefix="/api")
app.include_router(api_permis.router,        prefix="/api")
app.include_router(api_dvf.router,           prefix="/api")
app.include_router(api_email_finder.router,  prefix="/api")
app.include_router(api_claude.router,        prefix="/api")
app.include_router(api_products.router)
app.include_router(api_tenants.router)
app.include_router(api_dashboard.router)
app.include_router(api_escalations.router)


@app.get("/")
def root():
    return {"status": "ok", "message": "Proprexis API"}
