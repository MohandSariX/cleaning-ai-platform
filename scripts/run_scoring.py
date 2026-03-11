import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.lead_scorer import run_lead_scoring

run_lead_scoring()