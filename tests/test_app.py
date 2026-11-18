import os
from fastapi.testclient import TestClient
from backend.main import app, initialize
from backend.database import Base, engine
from backend.services.assessment import calculate_bmi, screen_assessment

def setup_module():
    Base.metadata.drop_all(bind=engine)
    initialize()

def test_health():
    with TestClient(app) as c:
        assert c.get("/api/health").json()["status"] == "ok"

def test_registration_assessment_and_history():
    with TestClient(app) as c:
        r = c.post("/api/auth/register", json={"name":"Test User","email":"test@example.com","password":"Password123"})
        assert r.status_code == 200
        token = r.json()["token"]
        h = {"Authorization":f"Bearer {token}"}
        payload = {"participant_name":"Demo Person","age_years":25,"gender":"not_specified","height_cm":170,"weight_kg":65,
                   "dietary_habits":"Dal and vegetables","meals_per_day":3,"food_patterns":"Regular meals",
                   "physical_activity":"moderate","dietary_preference":"vegetarian","notes":"Test"}
        a = c.post("/api/assessments",json=payload,headers=h)
        assert a.status_code == 200
        assert a.json()["bmi"] == 22.49
        assert c.get("/api/assessments",headers=h).json()[0]["participant_name"] == "Demo Person"
        assert c.get("/api/summary",headers=h).json()["total_assessments"] == 1
        assert c.get(f"/api/assessments/{a.json()['id']}/report",headers=h).status_code == 200
        assert c.delete(f"/api/assessments/{a.json()['id']}",headers=h).status_code == 204

def test_login_and_invalid_input():
    with TestClient(app) as c:
        r=c.post("/api/auth/login",json={"email":"test@example.com","password":"Password123"})
        assert r.status_code==200
        bad=c.post("/api/auth/login",json={"email":"test@example.com","password":"wrongpass"})
        assert bad.status_code==401
        reg=c.post("/api/auth/register",json={"name":"X","email":"x@example.com","password":"123"})
        assert reg.status_code==422

def test_under_twenty_uses_growth_reference_notice():
    assert screen_assessment(12, 18)[0] == "growth_reference_required"

def test_recommendation_and_ml_status():
    with TestClient(app) as c:
        r=c.post("/api/auth/login",json={"email":"test@example.com","password":"Password123"})
        h={"Authorization":f"Bearer {r.json()['token']}"}
        assert c.get("/api/recommendations",headers=h).status_code==200
        assert c.get("/api/ml/status",headers=h).status_code==200
