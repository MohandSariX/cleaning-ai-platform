import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.email_outreach import run_email_outreach

run_email_outreach()