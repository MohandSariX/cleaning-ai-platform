import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.prospect import Prospect
from sqlalchemy import func

db = SessionLocal()

total      = db.query(Prospect).count()
with_email = db.query(Prospect).filter(Prospect.email.isnot(None)).count()
with_phone = db.query(Prospect).filter(Prospect.phone.isnot(None)).count()
with_web   = db.query(Prospect).filter(Prospect.website.isnot(None)).count()
scored     = db.query(Prospect).filter(Prospect.lead_score > 0).count()

# Distribution des scores
haute    = db.query(Prospect).filter(Prospect.lead_score >= 75).count()
moyenne  = db.query(Prospect).filter(Prospect.lead_score >= 50, Prospect.lead_score < 75).count()
faible   = db.query(Prospect).filter(Prospect.lead_score >= 25, Prospect.lead_score < 50).count()
nulle    = db.query(Prospect).filter(Prospect.lead_score < 25).count()

# Top 10 prospects
top10 = (db.query(Prospect)
    .filter(Prospect.lead_score > 0)
    .order_by(Prospect.lead_score.desc())
    .limit(10)
    .all())

# Répartition par ville
villes = (db.query(Prospect.city, func.count(Prospect.id))
    .group_by(Prospect.city)
    .order_by(func.count(Prospect.id).desc())
    .all())

db.close()

print(f"\n{'='*50}")
print(f"  📊 STATS BASE PROSPECTS")
print(f"{'='*50}")
print(f"  Total prospects    : {total}")
print(f"  Avec email         : {with_email} ({round(with_email/total*100) if total else 0}%)")
print(f"  Avec téléphone     : {with_phone} ({round(with_phone/total*100) if total else 0}%)")
print(f"  Avec site web      : {with_web} ({round(with_web/total*100) if total else 0}%)")
print(f"  Scorés             : {scored}")

print(f"\n{'='*50}")
print(f"  🎯 DISTRIBUTION DES SCORES")
print(f"{'='*50}")
print(f"  🔥 Priorité haute  (75-100) : {haute}")
print(f"  ⚡ Priorité moyenne (50-74) : {moyenne}")
print(f"  🌱 Priorité faible  (25-49) : {faible}")
print(f"  ❄️  Non prioritaire  (0-24)  : {nulle}")

print(f"\n{'='*50}")
print(f"  🏆 TOP 10 PROSPECTS")
print(f"{'='*50}")
for p in top10:
    email_str = f"📧 {p.email}" if p.email else "❌ pas d'email"
    print(f"  {p.lead_score:5.0f}pts — {p.company_name} ({p.city})")
    print(f"         {p.score_label} | {email_str}")

print(f"\n{'='*50}")
print(f"  📍 PROSPECTS PAR VILLE")
print(f"{'='*50}")
for ville, count in villes:
    print(f"  {str(ville or 'Inconnue'):<30} : {count}")

print(f"{'='*50}\n")