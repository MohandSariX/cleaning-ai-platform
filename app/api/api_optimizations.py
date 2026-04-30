from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import SessionLocal
from app.agents.claude_optimizer import (
    analyze_email_performance,
    analyze_lost_prospects,
    adjust_scoring_weights,
    track_ab_test_results,
    suggest_optimizations,
    run_optimization_cycle,
)
from app.agents.claude_memory import search, retrieve

router = APIRouter(prefix="/api/optimizations", tags=["optimizations"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Schemas ──────────────────────────────────────────────────────────────────

class OptimizationSuggestion(BaseModel):
    type: str
    priority: str
    message: str
    action: str
    params: dict | None = None


class EmailPerformance(BaseModel):
    total_sent: int
    replied: int
    reply_rate: float
    best_day: str
    best_day_count: int
    recommendations: list


class LostProspectsAnalysis(BaseModel):
    total: int
    avg_score: float
    by_score_range: dict
    top_lost_industries: list
    recommendations: list


class ScoringAdjustments(BaseModel):
    status: str
    sample_size: dict | None = None
    adjustments: list


class ABTestResults(BaseModel):
    status: str
    started: str | None = None
    variants: list | None = None
    results: dict | None = None
    total_sent: int | None = None
    winner: str | None = None


class LearningEntry(BaseModel):
    id: int
    key: str
    value: str
    context: str
    meta_data: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/suggestions", response_model=List[OptimizationSuggestion])
def get_suggestions():
    """Récupère les suggestions d'optimisation actuelles"""
    suggestions = suggest_optimizations()
    return suggestions


@router.get("/email-performance", response_model=EmailPerformance)
def get_email_performance():
    """Analyse des performances emails"""
    return analyze_email_performance()


@router.get("/lost-prospects", response_model=LostProspectsAnalysis)
def get_lost_prospects_analysis():
    """Analyse des prospects perdus"""
    result = analyze_lost_prospects()
    # Assurer que tous les champs sont présents
    if "avg_score" not in result:
        result["avg_score"] = 0.0
    if "by_score_range" not in result:
        result["by_score_range"] = {}
    if "top_lost_industries" not in result:
        result["top_lost_industries"] = []
    if "recommendations" not in result:
        result["recommendations"] = []
    return result


@router.get("/scoring-adjustments", response_model=ScoringAdjustments)
def get_scoring_adjustments():
    """Suggestions d'ajustements des poids de scoring"""
    result = adjust_scoring_weights()
    if "adjustments" not in result:
        result["adjustments"] = []
    return result


@router.get("/ab-test", response_model=ABTestResults)
def get_ab_test_results():
    """Résultats des A/B tests en cours"""
    return track_ab_test_results()


@router.post("/run-cycle")
def run_cycle():
    """Lance un cycle d'optimisation complet"""
    result = run_optimization_cycle()
    return result


@router.get("/learnings")
def get_learnings(limit: int = 20):
    """Récupère les learnings récents de Claude"""
    results = search("learning", limit=limit)

    return {
        "count": len(results),
        "learnings": [
            {
                "id": r.id,
                "key": r.key,
                "value": r.value,
                "context": r.context,
                "meta_data": r.meta_data,
                "created_at": r.created_at.isoformat(),
            }
            for r in results
        ],
    }


@router.get("/strategy")
def get_current_strategy():
    """Récupère la stratégie actuelle (priorités, A/B tests...)"""
    priority_industry = retrieve("priority_industry")
    priority_city = retrieve("priority_city")
    ab_test = retrieve("ab_test_active")
    top_converting_industry = retrieve("top_converting_industry")
    top_converting_city = retrieve("top_converting_city")

    return {
        "priority_industry": priority_industry.get("value") if priority_industry else None,
        "priority_city": priority_city.get("value") if priority_city else None,
        "ab_test_active": ab_test.get("value") if ab_test else None,
        "top_converting_industry": top_converting_industry.get("value") if top_converting_industry else None,
        "top_converting_city": top_converting_city.get("value") if top_converting_city else None,
        "last_updated": datetime.now().isoformat(),
    }
