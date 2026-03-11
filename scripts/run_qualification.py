import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.lead_qualifier import run_lead_qualification

run_lead_qualification()