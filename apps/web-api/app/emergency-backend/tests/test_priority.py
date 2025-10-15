from app.modules.incidents.schemas import Incident, Location, Accident
from app.modules.incidents.service import compute_scores

def test_accident_no_fire_scoring():
    inc = Incident(
        id="T1",
        source="traffic",
        reported_at="2025-10-14T00:00:00Z",
        location=Location(lat=0.0, lng=0.0),
        severity_grade="medium",
        camera_risk_class="high",
        accident=Accident(vehicles_involved=2, fire_present=False)
    )
    scored = compute_scores(inc)
    assert 0 < scored.score < 100
