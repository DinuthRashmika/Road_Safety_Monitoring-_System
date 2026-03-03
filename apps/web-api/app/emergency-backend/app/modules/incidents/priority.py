from __future__ import annotations
from datetime import datetime
from app.modules.incidents.schemas import Incident

def get_temporal_impact() -> float:
    """
    Calculates Tr (Time-of-Day Risk).
    Red Zone (1.0)   = Rush Hours (School/Office)
    Yellow Zone (0.6) = Normal Day Activity
    Green Zone (0.2) = Late Night / Sleeping
    """
    now = datetime.now()
    t = now.time()
    is_weekend = now.weekday() >= 5  # 5=Saturday, 6=Sunday

    # Convert to minutes for easier comparison (Hour * 60 + Minute)
    current_min = t.hour * 60 + t.minute

    if is_weekend:
        # Weekend Strategy: Active during day, Quiet at night
        if 480 <= current_min < 1320: # 08:00 AM to 10:00 PM
            return 0.6
        return 0.2
    else:
        # Weekday Strategy 
        # RED ZONE 1: Morning Rush (06:30 - 09:00)
        if 390 <= current_min < 540:
            return 1.0
        # RED ZONE 2: School End Rush (13:30 - 14:30)
        elif 810 <= current_min < 870:
            return 1.0
        # GREEN ZONE: Night Time (22:00 - 06:30 next day)
        elif current_min >= 1320 or current_min < 390:
            return 0.2
        # YELLOW ZONE: Everything else
        else:
            return 0.6

def get_holiday_surge(reported_at: datetime = None) -> float:
    """
    Calculates Hs (Holiday & Festival Surge).
    High Risk (1.0) = Avurudu (April) and Late December holidays.
    Normal (0.4) = Standard days.
    """
    dt = reported_at if reported_at else datetime.now()
    month = dt.month
    day = dt.day

    # Check for Sri Lankan High-Risk Travel Seasons
    is_avurudu_rush = (month == 4 and 10 <= day <= 20)
    is_december_rush = (month == 12 and 20 <= day <= 31)

    if is_avurudu_rush or is_december_rush:
        return 1.0
    return 0.4

def map_risk(s: str) -> float:
    return {"low": 0.35, "medium": 0.65, "high": 0.90}.get(s, 0.35)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

# --- MAIN SCORING ENGINE ---

def score_incident(inc: Incident) -> Incident:
    # Parse the incident time if available, otherwise use now
    dt = datetime.now()
    if inc.reported_at:
        try:
            dt = datetime.fromisoformat(inc.reported_at.replace("Z", "+00:00"))
        except ValueError:
            pass

    # 1. Get Context Parameters for MFIPA
    Lr = map_risk(inc.camera_risk_class)  # Location & Infrastructure Risk
    Tr = get_temporal_impact()            # Time-of-Day Risk
    Hs = get_holiday_surge(dt)            # Holiday Surge
    
    explain: list[str] = []
    
    # Check for Fire (Global Override)
    fire_detected = (inc.accident and inc.accident.fire_present) or \
                    (inc.violence and hasattr(inc.violence, 'fire_present') and inc.violence.fire_present)
    
    # --- SCENARIO A: ACCIDENT (MFIPA ALGORITHM) ---
    if inc.accident:
        if inc.accident.fire_present:
            inc.score = 100
            explain.append("Fire detected → Critical Override")
            inc.required_roles = ["ambulance", "police", "fire"]
        else:
            # Vu (Vulnerability Index): Defaults to 0.4 for standard cars
            Vu = getattr(inc.accident, 'vulnerability', 0.4) 
            
            # THE NEW MFIPA FORMULA: 40% Vu + 30% Lr + 20% Tr + 10% Hs
            raw_score = 100 * (0.40 * Vu + 0.30 * Lr + 0.20 * Tr + 0.10 * Hs)
            inc.score = round(raw_score)
            
            explain.append(f"MFIPA Calculated: Vu={Vu:.2f}, Lr={Lr:.2f}, Tr={Tr:.2f}, Hs={Hs:.2f}")
            inc.required_roles = ["ambulance", "police"]

    # --- SCENARIO B: VIOLENCE ---
    elif inc.violence:
        W = clamp01(inc.violence.weapon_conf) # Weapon Confidence
        P = clamp01((inc.violence.participants_count - 1) / 4.0) # Crowd Density
        
        # Formula: 50% W + 20% P + 20% Tr + 10% Lr
        raw_score = 100 * (0.50 * W + 0.20 * P + 0.20 * Tr + 0.10 * Lr)
        inc.score = round(raw_score)
        
        explain.append(f"Violence: W={W:.2f}, P={P:.2f}, Tr={Tr:.2f}, Lr={Lr:.2f}")

        if fire_detected:
            inc.required_roles = ["ambulance", "police", "fire"]
            explain.append("Fire Service added due to Fire Risk")
        else:
            inc.required_roles = ["police"]
            # If score is very high (likely weapon), add ambulance proactively
            if inc.score > 75:
                inc.required_roles.append("ambulance")
                explain.append("Ambulance added due to High Threat Level")
            
    # --- SCENARIO C: UNKNOWN / OTHER ---
    else:
        G = {"low": 0.35, "medium": 0.65, "high": 0.90}.get(inc.severity_grade, 0.35)
        inc.score = round(100 * G)
        inc.required_roles = []

    inc.explain = explain
    return inc

def tie_breaker_key(doc: dict):
    # Sorts by: Score (Desc), Time (Newest)
    return (-doc.get("score", 0), -doc.get("timestamp", 0))