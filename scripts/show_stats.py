import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.prospect import Prospect

db = SessionLocal()

total = db.query(Prospect).count()
new = db.query(Prospect).filter(Prospect.status == "new").count()
contacted = db.query(Prospect).filter(Prospect.status == "contacted").count()

print("Prospects total :", total)
print("New :", new)
print("Contacted :", contacted)

db.close()