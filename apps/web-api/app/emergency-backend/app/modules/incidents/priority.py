from .schemas import Incident

def map_grade(s: str) -> float:
    return {"low":0.35,"medium":0.65,"high":0.90}.get(s,0.35)

def map_risk(s: str) -> float:
    return {"low":0.35,"medium":0.65,"high":0.90}.get(s,0.35)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def score_incident(inc: Incident) -> Incident:
    G = map_grade(inc.severity_grade)
    R = map_risk(inc.camera_risk_class)
    explain = []

    if inc.accident:
        if inc.accident.fire_present:
            inc.score = 100
            explain.append("Fire detected → hard override")
        else:
            V = clamp01((inc.accident.vehicles_involved - 1) / 3)
            inc.score = round(100 * (0.50*G + 0.35*V + 0.15*R))
            explain.append(f"Accident: G={G:.2f}, V={V:.2f}, R={R:.2f}")
        inc.required_units = ["ambulance","police"] + (["fire"] if inc.accident.fire_present else [])
    elif inc.violence:
        W = clamp01(inc.violence.weapon_conf)
        P = clamp01((inc.violence.participants_count - 1) / 4)
        inc.score = round(100 * (0.40*G + 0.35*W + 0.15*P + 0.10*R))
        explain.append(f"Violence: G={G:.2f}, W={W:.2f}, P={P:.2f}, R={R:.2f}")
        inc.required_units = ["police"]
    else:
        inc.score = round(100 * G)

    inc.explain = explain
    return inc

def tie_breaker_key(doc: dict):
    # severity > reported_at older first > accidents preferred > risk
    sev = {"high":3,"medium":2,"low":1}.get(doc["severity_grade"],1)
    is_acc = 1 if doc.get("accident") else 0
    risk = {"high":3,"medium":2,"low":1}.get(doc["camera_risk_class"],1)
    return (-sev, doc["reported_at"], -is_acc, -risk)
