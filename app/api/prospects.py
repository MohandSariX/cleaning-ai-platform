from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.prospect import Prospect

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/prospects")
def list_prospects(db: Session = Depends(get_db)):
    return db.query(Prospect).all()

@router.post("/prospects")
def create_prospect(data: dict, db: Session = Depends(get_db)):
    
    prospect = Prospect(**data)
    
    db.add(prospect)
    db.commit()
    
    return prospect