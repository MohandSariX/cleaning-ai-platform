from fastapi import FastAPI
from app.api import prospects
from app.core.database import Base, engine
from app.models import prospect

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(prospects.router)