from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import Base, engine, get_db, SessionLocal
from backend.models import User, Assessment, Prediction, Recommendation
from backend.schemas import RegisterIn, LoginIn, AssessmentIn
from backend.config import ADMIN_EMAIL, ADMIN_PASSWORD
from backend.services.security import hash_password, verify_password, create_token, decode_token
from backend.services.assessment import calculate_bmi, screen_assessment, recommendations
from backend.services.pdf import build_report
from backend.ml.anomaly import explore_anomaly

app = FastAPI(title="NutriTrack API", version="1.0.0", description="Educational nutrition screening prototype. Not a diagnostic service.")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/")
def home():
    return FileResponse("frontend/index.html")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

def initialize():
    Path("data").mkdir(exist_ok=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(func.lower(User.email) == ADMIN_EMAIL).first()
        if not admin:
            db.add(User(name="NutriTrack Admin", email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD), role="admin"))
            db.commit()
    finally:
        db.close()

@app.on_event("startup")
def startup():
    initialize()

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please log in to continue.")
    payload = decode_token(authorization[7:])
    if not payload:
        raise HTTPException(401, "Session expired. Please log in again.")
    user = db.get(User, int(payload["sub"]))
    if not user:
        raise HTTPException(401, "Account not found.")
    return user

def admin_user(user: User = Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required.")
    return user

def assessment_dict(row):
    return {
        "id": row.id, "participant_name": row.participant_name, "age_years": row.age_years,
        "gender": row.gender, "height_cm": row.height_cm, "weight_kg": row.weight_kg,
        "bmi": row.bmi, "indicator_status": row.indicator_status, "risk_level": row.risk_level,
        "observations": row.observations, "created_at": row.created_at.isoformat(),
        "dietary_preference": row.dietary_preference, "meals_per_day": row.meals_per_day
    }

@app.get("/api/health")
def health():
    return {"status": "ok", "application": "NutriTrack"}

@app.post("/api/auth/register")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(409, "An account with this email already exists.")
    user = User(name=payload.name.strip(), email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id, user.role), "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}

@app.post("/api/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    return {"token": create_token(user.id, user.role), "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}

@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

@app.get("/api/summary")
def summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = db.query(Assessment).filter(Assessment.user_id == user.id)
    rows = q.order_by(Assessment.created_at.desc()).all()
    latest = assessment_dict(rows[0]) if rows else None
    return {"total_assessments": len(rows), "latest_assessment": latest,
            "review_flags": sum(1 for r in rows if r.risk_level == "review_recommended"),
            "adult_records": sum(1 for r in rows if r.age_years >= 20),
            "under_20_records": sum(1 for r in rows if r.age_years < 20)}

@app.get("/api/assessments")
def list_assessments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Assessment).filter(Assessment.user_id == user.id).order_by(Assessment.created_at.desc()).all()
    return [assessment_dict(r) for r in rows]

@app.post("/api/assessments")
def create_assessment(payload: AssessmentIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    bmi = calculate_bmi(payload.height_cm, payload.weight_kg)
    status, risk, observation = screen_assessment(payload.age_years, bmi)
    row = Assessment(user_id=user.id, **payload.model_dump(), bmi=bmi, indicator_status=status, risk_level=risk, observations=observation)
    db.add(row)
    db.flush()
    pred = Prediction(assessment_id=row.id, method="Transparent prototype screening rules", result=risk,
                      explanation=observation, anomaly_flag=False)
    db.add(pred)
    for category, message in recommendations(payload.model_dump()):
        db.add(Recommendation(assessment_id=row.id, category=category, message=message))
    db.commit()
    db.refresh(row)
    return assessment_dict(row)

@app.get("/api/assessments/{assessment_id}")
def get_assessment(assessment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(Assessment).filter_by(id=assessment_id, user_id=user.id).first()
    if not row:
        raise HTTPException(404, "Assessment not found.")
    return {**assessment_dict(row), "recommendations": [{"category": x.category, "message": x.message} for x in row.recommendations]}

@app.delete("/api/assessments/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(Assessment).filter_by(id=assessment_id, user_id=user.id).first()
    if not row:
        raise HTTPException(404, "Assessment not found.")
    db.delete(row)
    db.commit()
    return None

@app.get("/api/assessments/{assessment_id}/report")
def report(assessment_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(Assessment).filter_by(id=assessment_id, user_id=user.id).first()
    if not row:
        raise HTTPException(404, "Assessment not found.")
    pdf = build_report(user, row, row.recommendations)
    return StreamingResponse(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="nutritrack-report-{row.id}.pdf"'})

@app.get("/api/recommendations")
def get_recommendations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.query(Assessment).filter_by(user_id=user.id).order_by(Assessment.created_at.desc()).first()
    if not row:
        return {"assessment": None, "recommendations": []}
    return {"assessment": assessment_dict(row), "recommendations": [{"category": x.category, "message": x.message} for x in row.recommendations]}

@app.get("/api/ml/status")
def ml_status(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.query(Assessment).filter_by(user_id=user.id).all()
    flags, message = explore_anomaly(rows)
    return {"available": len(rows) >= 5, "message": message, "flagged_ids": [k for k, v in flags.items() if v],
            "method": "Unsupervised Isolation Forest exploratory analysis"}

@app.get("/api/admin/stats")
def admin_stats(admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    return {"users": db.query(User).count(), "assessments": db.query(Assessment).count(),
            "adult_records": db.query(Assessment).filter(Assessment.age_years >= 20).count(),
            "under_20_records": db.query(Assessment).filter(Assessment.age_years < 20).count()}

@app.get("/api/admin/users")
def admin_users(admin: User = Depends(admin_user), db: Session = Depends(get_db)):
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role, "created_at": u.created_at.isoformat()}
            for u in db.query(User).order_by(User.created_at.desc()).all()]
