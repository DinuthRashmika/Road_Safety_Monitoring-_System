from __future__ import annotations
from datetime import datetime
from app.modules.incidents.schemas import Incident
from enum import Enum
import math
from typing import Tuple, List

# Vehicle Types and their Vulnerability Scores
class VehicleType(Enum):
    # High Vulnerability (0.9-1.0)
    BICYCLE = "bicycle"
    MOTORCYCLE = "motorcycle"
    PEDESTRIAN = "pedestrian"
    
    # Medium-High Vulnerability (0.7-0.8)
    AUTO_RICKSHAW = "auto_rickshaw"  # Common in Sri Lanka
    THREE_WHEELER = "three_wheeler"  # Tuk-tuks
    
    # Medium Vulnerability (0.5-0.6)
    CAR = "car"
    SUV = "suv"
    VAN = "van"
    
    # Medium-Low Vulnerability (0.3-0.4)
    BUS = "bus"
    TRUCK = "truck"
    LORRY = "lorry"
    
    # Low Vulnerability (0.1-0.2)
    HEAVY_TRUCK = "heavy_truck"
    CONSTRUCTION = "construction_vehicle"

# Vehicle vulnerability base scores
VEHICLE_VULNERABILITY = {
    # High vulnerability - unprotected road users
    "pedestrian": 1.0,
    "bicycle": 0.95,
    "motorcycle": 0.9,
    "scooter": 0.88,
    "moped": 0.88,
    
    # Medium-high - light vehicles
    "auto_rickshaw": 0.8,
    "three_wheeler": 0.78,
    "tuk_tuk": 0.78,
    
    # Medium - passenger vehicles
    "car": 0.6,
    "suv": 0.55,
    "van": 0.5,
    "jeep": 0.52,
    "taxi": 0.58,
    
    # Medium-low - commercial vehicles
    "pickup": 0.45,
    "minibus": 0.4,
    "bus": 0.35,
    "lorry": 0.32,
    "truck": 0.3,
    
    # Low - heavy vehicles
    "heavy_truck": 0.2,
    "container": 0.15,
    "trailer": 0.18,
    "construction": 0.22,
    
    # Default if unknown
    "unknown": 0.5
}

# Camera risk class scores
CAMERA_RISK_SCORES = {
    "low": 0.3,
    "medium": 0.6,
    "high": 0.9,
    "critical": 1.0
}

# ============================================
# PARAMETER 1: VEHICLE TYPE VULNERABILITY (Vu)
# ============================================
def detect_vehicle_type(vehicle_description: str) -> str:
    """
    Detect vehicle type from description or violation data
    """
    if not vehicle_description:
        return "unknown"
    
    vehicle_desc = vehicle_description.lower()
    
    # Pedestrian
    if any(word in vehicle_desc for word in ["pedestrian", "person", "human", "walker"]):
        return "pedestrian"
    
    # Motorcycles
    if any(word in vehicle_desc for word in ["motorcycle", "bike", "scooter", "moped", "motorbike"]):
        return "motorcycle"
    
    # Bicycle
    if any(word in vehicle_desc for word in ["bicycle", "cycle", "bike"]):
        return "bicycle"
    
    # Three-wheelers (common in Sri Lanka)
    if any(word in vehicle_desc for word in ["three", "tuk", "auto", "rickshaw"]):
        return "three_wheeler"
    
    # Cars/SUVs
    if any(word in vehicle_desc for word in ["car", "sedan", "hatchback"]):
        return "car"
    if any(word in vehicle_desc for word in ["suv", "jeep", "crossover"]):
        return "suv"
    
    # Commercial vehicles
    if any(word in vehicle_desc for word in ["van", "minivan"]):
        return "van"
    if any(word in vehicle_desc for word in ["bus", "minibus", "coach"]):
        return "bus"
    if any(word in vehicle_desc for word in ["truck", "lorry", "container"]):
        return "truck"
    
    # Heavy vehicles
    if any(word in vehicle_desc for word in ["heavy", "trailer", "construction", "excavator"]):
        return "heavy_truck"
    
    return "unknown"

def calculate_vulnerability_index(inc: Incident) -> float:
    """
    Calculate Vulnerability Index (Vu) based on:
    - Vehicle type (primary factor)
    - Number of vehicles involved
    """
    # Base vulnerability from vehicle type
    vehicle_type = "unknown"
    vehicle_count = 1
    
    if inc.accident:
        # Try to get vehicle type
        if hasattr(inc.accident, 'vehicle_type') and inc.accident.vehicle_type:
            vehicle_type = detect_vehicle_type(inc.accident.vehicle_type)
        vehicle_count = max(1, inc.accident.vehicles_involved)
    elif inc.violence:
        # For violence, consider participants as "vehicles" for vulnerability
        if hasattr(inc.violence, 'participants_count'):
            vehicle_count = inc.violence.participants_count
    
    # Get base vulnerability score
    base_vu = VEHICLE_VULNERABILITY.get(vehicle_type, 0.5)
    
    # Apply vehicle count factor (more vehicles/people = higher vulnerability)
    # But with diminishing returns
    vehicle_factor = 1.0 + (min(vehicle_count, 5) * 0.1)
    
    # Calculate final Vu
    Vu = base_vu * vehicle_factor
    
    # Clamp between 0.2 and 1.0
    return max(0.2, min(1.0, Vu))

# ============================================
# PARAMETER 2: LOCATION & INFRASTRUCTURE RISK (Lr)
# ============================================
def map_risk(risk_class: str) -> float:
    """Map camera risk class to score"""
    return CAMERA_RISK_SCORES.get(risk_class, 0.6)

# ============================================
# PARAMETER 3: TIME-OF-DAY RISK (Tr)
# ============================================
def _is_school_holiday(dt: datetime) -> bool:
    """Check if it's a school holiday in Sri Lanka"""
    # Sri Lankan school holidays
    month = dt.month
    day = dt.day
    
    # April school holidays (Avurudu)
    if month == 4 and 5 <= day <= 20:
        return True
    # August school holidays
    if month == 8 and 15 <= day <= 31:
        return True
    # December school holidays
    if month == 12 and 15 <= day <= 31:
        return True
    # January (New Year)
    if month == 1 and 1 <= day <= 5:
        return True
    
    return False

def get_temporal_impact(dt: datetime = None) -> float:
    """
    Enhanced Time-of-Day Risk (Tr) with Sri Lankan context
    Returns score between 0.2 and 1.0
    """
    if dt is None:
        dt = datetime.now()
    
    hour = dt.hour
    minute = dt.minute
    current_min = hour * 60 + minute
    is_weekend = dt.weekday() >= 5  # 5=Sat, 6=Sun
    is_school_holiday = _is_school_holiday(dt)
    
    # Rush Hours (Highest Risk)
    # Morning Rush: 6:30-9:00 AM (school/office)
    if 390 <= current_min < 540:
        return 1.0
    # Evening Rush: 4:00-7:00 PM (office closing)
    elif 960 <= current_min < 1140:
        return 1.0
    # School End: 1:30-2:30 PM
    elif 810 <= current_min < 870 and not is_school_holiday:
        return 0.95
    
    # High Risk Periods
    # Late Night (high speed, fatigue): 10:00 PM - 4:00 AM
    elif current_min >= 1320 or current_min < 240:
        return 0.85
    # Early Morning (low visibility): 4:00-6:30 AM
    elif 240 <= current_min < 390:
        return 0.8
    
    # Moderate Risk
    # Weekend daytime
    elif is_weekend and 480 <= current_min < 1320:
        return 0.7
    # Weekday daytime
    elif not is_weekend and 540 <= current_min < 960:
        return 0.6
    
    # Low Risk
    # Late night weekend
    else:
        return 0.3

# ============================================
# PARAMETER 4: HOLIDAY SURGE (Hs) - UPDATED WITH 2026 SRI LANKAN HOLIDAYS
# ============================================
def get_holiday_surge(dt: datetime = None) -> float:
    """
    Enhanced Holiday Surge (Hs) with official Sri Lankan 2026 holiday calendar
    Returns score between 0.3 and 1.0
    
    Based on official Public, Bank, Mercantile and Full Moon Poya Holidays 2026
    """
    if dt is None:
        dt = datetime.now()
    
    month = dt.month
    day = dt.day
    weekday = dt.weekday()  # 0=Monday, 6=Sunday
    
    # All Saturdays and Sundays are Bank Holidays
    is_weekend = weekday >= 5  # 5=Sat, 6=Sun
    
    # ===== MAJOR FESTIVAL PERIODS (SCORE: 1.0) =====
    # These are high-risk periods with mass travel and celebrations
    
    # Duruthu Full Moon Poya Day - January 3
    if month == 1 and day == 3:
        return 1.0
    
    # Nawam Full Moon Poya Day - March 1
    if month == 3 and day == 1:
        return 1.0
    
    # Medin Full Moon Poya Day - June 21
    if month == 6 and day == 21:
        return 1.0
    
    # Bak Full Moon Poya Day - July 1
    if month == 7 and day == 1:
        return 1.0
    
    # Vesak Full Moon Poya Day - September 28
    if month == 9 and day == 28:
        return 1.0
    
    # Asadha Full Moon Poya Day - October 29
    if month == 10 and day == 29:
        return 1.0
    
    # Il Full Moon Poya Day - November 24
    if month == 11 and day == 24:
        return 1.0
    
    # Unduvap Full Moon Poya Day - December 13
    if month == 12 and day == 13:
        return 1.0
    
    # ===== PUBLIC HOLIDAYS (SCORE: 0.9) =====
    # These are single-day public holidays with increased travel
    
    # Tamil Thai Pongal Day - February 15
    if month == 2 and day == 15:
        return 0.9
    
    # Maha Sivarathri Day - May 2
    if month == 5 and day == 2:
        return 0.9
    
    # Id-Ul-Fitr (Ramazan Festival Day) - July 1
    if month == 7 and day == 1:
        return 0.9
    
    # Christmas Day - December 25
    if month == 12 and day == 25:
        return 0.9
    
    # ===== LONG WEEKEND PERIODS (SCORE: 0.85) =====
    # When holidays create long weekends
    
    # Check if it's a Friday before a Saturday holiday
    if weekday == 4:  # Friday
        next_day = day + 1
        if (month == 1 and next_day == 3) or \
           (month == 2 and next_day == 15) or \
           (month == 3 and next_day == 1) or \
           (month == 5 and next_day == 2) or \
           (month == 6 and next_day == 21) or \
           (month == 7 and next_day == 1) or \
           (month == 9 and next_day == 28) or \
           (month == 10 and next_day == 29) or \
           (month == 11 and next_day == 24) or \
           (month == 12 and next_day == 13):
            return 0.85
    
    # Check if it's a Monday after a Sunday holiday
    if weekday == 0:  # Monday
        prev_day = day - 1
        if (month == 1 and prev_day == 3) or \
           (month == 2 and prev_day == 15) or \
           (month == 3 and prev_day == 1) or \
           (month == 5 and prev_day == 2) or \
           (month == 6 and prev_day == 21) or \
           (month == 7 and prev_day == 1) or \
           (month == 9 and prev_day == 28) or \
           (month == 10 and prev_day == 29) or \
           (month == 11 and prev_day == 24) or \
           (month == 12 and prev_day == 13):
            return 0.85
    
    # ===== WEEKEND (SCORE: 0.7) =====
    # Saturdays and Sundays (Bank Holidays) have increased traffic
    if is_weekend:
        return 0.7
    
    # ===== NORMAL DAYS (SCORE: 0.4) =====
    return 0.4

# ============================================
# PARAMETER 5: SEVERITY GRADE (Sg) - NEW AS FULL PARAMETER
# ============================================
def get_severity_score(severity_grade: str) -> float:
    """
    Convert severity grade to numerical score (0.3, 0.6, 0.9)
    Now used as a direct parameter, not a multiplier
    """
    severity_map = {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.9,
        "critical": 1.0
    }
    return severity_map.get(severity_grade, 0.6)  # Default to medium

# ============================================
# PARAMETER 6: DISTANCE URGENCY (Du)
# ============================================
def calculate_distance_urgency(inc: Incident, responder_location: dict = None) -> float:
    """
    Calculate urgency based on distance to nearest responder
    Returns score between 0.2 and 1.0
    
    < 5 km: 0.3 (Close - can arrive quickly)
    5-15 km: 0.5 (Moderate)
    15-30 km: 0.7 (Far - needs priority)
    30-50 km: 0.85 (Very far)
    > 50 km: 1.0 (Extremely far - highest priority)
    """
    if not responder_location or not inc.location:
        return 0.5  # Default if no location data
    
    try:
        # Get coordinates
        lat1 = responder_location.get('lat', 0)
        lon1 = responder_location.get('lng', 0)
        lat2 = inc.location.get('lat', 0)
        lon2 = inc.location.get('lng', 0)
        
        if lat1 == 0 or lon1 == 0 or lat2 == 0 or lon2 == 0:
            return 0.5
        
        # Haversine formula for accurate distance
        R = 6371  # Earth's radius in km
        
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        
        a = math.sin(delta_phi/2) * math.sin(delta_phi/2) + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda/2) * math.sin(delta_lambda/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c  # Distance in km
        
        # Map distance to urgency score
        if distance < 5:
            return 0.3
        elif distance < 15:
            return 0.5
        elif distance < 30:
            return 0.7
        elif distance < 50:
            return 0.85
        else:
            return 1.0
            
    except Exception:
        return 0.5  # Default on error

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

# ============================================
# UPDATED: Violence scoring with Pamalis parameters
# ============================================
def score_violence_incident(inc: Incident, Tr: float, Lr: float, Hs: float, Sg: float, Du: float) -> Tuple[int, List[str]]:
    """
    Enhanced violence scoring with Pamalis parameters.
    ALWAYS requires Police + Ambulance for human behavior incidents.
    """
    
    explain = []
    
    # Base violence parameters
    W = clamp01(inc.violence.weapon_conf) if inc.violence and inc.violence.weapon_conf else 0
    P = clamp01((inc.violence.participants_count - 1) / 4.0) if inc.violence and inc.violence.participants_count else 0
    
    # Pamalis parameters
    threat_score = clamp01(inc.violence.threat_score) if inc.violence and inc.violence.threat_score else 0
    has_weapon = 1.0 if inc.violence and inc.violence.has_weapon else 0
    action_conf = clamp01(inc.violence.action_confidence) if inc.violence and inc.violence.action_confidence else 0
    sustained = clamp01(inc.violence.sustained_seconds / 10.0) if inc.violence and inc.violence.sustained_seconds else 0
    
    # Objects detected factor
    objects_factor = 0
    if inc.violence and inc.violence.objects_detected:
        obj_count = len(inc.violence.objects_detected)
        avg_conf = sum(obj.confidence for obj in inc.violence.objects_detected) / obj_count if obj_count > 0 else 0
        objects_factor = clamp01((obj_count * avg_conf) / 5.0)
    
    # Weighted combination
    weighted_sum = (
        0.25 * threat_score +
        0.20 * has_weapon +
        0.15 * action_conf +
        0.10 * sustained +
        0.10 * objects_factor +
        0.10 * W +
        0.10 * P
    )
    
    # Apply time, location, holiday factors
    final_weighted = weighted_sum * (0.6) + (0.2 * Tr) + (0.1 * Lr) + (0.1 * Hs)
    
    raw_score = 100 * final_weighted * Sg
    final_score = min(100, round(raw_score))
    
    # Build explanation
    explain.append(f"👥 Violence Incident Scoring:")
    explain.append(f"  Threat Score: {threat_score:.2f} [25%] = {threat_score*0.25:.3f}")
    explain.append(f"  Has Weapon: {has_weapon:.2f} [20%] = {has_weapon*0.20:.3f}")
    explain.append(f"  Action Confidence: {action_conf:.2f} [15%] = {action_conf*0.15:.3f}")
    explain.append(f"  Duration: {sustained:.2f} [10%] = {sustained*0.10:.3f}")
    explain.append(f"  Objects: {objects_factor:.2f} [10%] = {objects_factor*0.10:.3f}")
    explain.append(f"  Weapon Conf: {W:.2f} [10%] = {W*0.10:.3f}")
    explain.append(f"  Participants: {P:.2f} [10%] = {P*0.10:.3f}")
    explain.append(f"  Time Risk: {Tr:.2f} [20%] = {Tr*0.20:.3f}")
    explain.append(f"  Location Risk: {Lr:.2f} [10%] = {Lr*0.10:.3f}")
    explain.append(f"  Holiday Surge: {Hs:.2f} [10%] = {Hs*0.10:.3f}")
    explain.append(f"  Severity Multiplier: {Sg:.2f}")
    explain.append(f"  Final Score: {final_score}")
    
    return final_score, explain

# ============================================
# MAIN SCORING ENGINE - UPDATED WITH NEW REQUIREMENTS
# ============================================
def score_incident(inc: Incident, responder_location: dict = None) -> Incident:
    """
    MFIPA+ Algorithm with updated responder requirements:
    - Shenal (traffic): Fire → 3 responders, No fire → Police + Ambulance
    - Pamalis (human): Always Police + Ambulance (no fire)
    """
    # Parse incident time
    dt = datetime.now()
    if inc.reported_at:
        try:
            dt = datetime.fromisoformat(inc.reported_at.replace("Z", "+00:00"))
        except ValueError:
            pass

    # Calculate all 6 parameters
    Vu = calculate_vulnerability_index(inc) if inc.accident else 0.5
    Lr = map_risk(inc.camera_risk_class)
    Tr = get_temporal_impact(dt)
    Hs = get_holiday_surge(dt)
    Sg = get_severity_score(inc.severity_grade)
    Du = calculate_distance_urgency(inc, responder_location)
    
    explain: list[str] = []
    
    # Check for Fire (Global Override)
    fire_detected = (inc.accident and inc.accident.fire_present) or \
                    (inc.violence and hasattr(inc.violence, 'fire_present') and inc.violence.fire_present)
    
    # --- SCENARIO A: ACCIDENT (Shenal's traffic) ---
    if inc.accident:
        if inc.accident.fire_present:
            inc.score = 100
            explain.append("🔥 Fire detected → Critical Override (Score: 100)")
            inc.required_roles = ["ambulance", "police", "fire"]
        else:
            # Get vehicle type for explanation
            vehicle_type = "unknown"
            if hasattr(inc.accident, 'vehicle_type') and inc.accident.vehicle_type:
                vehicle_type = inc.accident.vehicle_type
            
            # MFIPA+ Formula with 6 parameters
            weighted_sum = (
                0.25 * Vu +
                0.20 * Lr +
                0.15 * Tr +
                0.10 * Hs +
                0.15 * Sg +
                0.15 * Du
            )
            
            raw_score = 100 * weighted_sum
            inc.score = min(100, round(raw_score))
            
            explain.append(f"📊 MFIPA+ Calculation (6 Parameters):")
            explain.append(f"  1. Vehicle Vulnerability (Vu): {Vu:.2f} (Vehicle: {vehicle_type}) [25%] = {Vu*0.25:.3f}")
            explain.append(f"  2. Location Risk (Lr): {Lr:.2f} [20%] = {Lr*0.20:.3f}")
            explain.append(f"  3. Time Risk (Tr): {Tr:.2f} [15%] = {Tr*0.15:.3f}")
            
            # Enhanced holiday explanation
            holiday_note = ""
            if Hs >= 0.9:
                holiday_note = " (Major Festival)"
            elif Hs >= 0.8:
                holiday_note = " (Public Holiday)"
            elif Hs >= 0.7:
                holiday_note = " (Weekend/Bank Holiday)"
            
            explain.append(f"  4. Holiday Surge (Hs): {Hs:.2f}{holiday_note} [10%] = {Hs*0.10:.3f}")
            explain.append(f"  5. Severity Grade (Sg): {Sg:.2f} [15%] = {Sg*0.15:.3f}")
            explain.append(f"  6. Distance Urgency (Du): {Du:.2f} [15%] = {Du*0.15:.3f}")
            explain.append(f"  Weighted Sum: {weighted_sum:.3f}")
            explain.append(f"  Final Score: {inc.score}")
            
            # UPDATED: Shenal's traffic accidents ALWAYS get Police + Ambulance
            inc.required_roles = ["ambulance", "police"]
            
            # Add fire if heavy vehicle (more likely to need fire rescue)
            if vehicle_type in ["truck", "heavy_truck", "bus", "container"] and inc.score > 70:
                inc.required_roles.append("fire")
                explain.append("🚒 Fire services added due to heavy vehicle involvement")

    # --- SCENARIO B: VIOLENCE (Pamalis human behavior) ---
    elif inc.violence:
        inc.score, explain = score_violence_incident(inc, Tr, Lr, Hs, Sg, Du)
        
        # UPDATED: Pamalis ALWAYS gets Police + Ambulance (no fire)
        inc.required_roles = ["police", "ambulance"]
        explain.append("🚑 Ambulance dispatched for human behavior incident")
        
        # Never add fire for Pamalis incidents
            
    # --- SCENARIO C: UNKNOWN ---
    else:
        inc.score = round(100 * Sg * 0.5)  # Default based on severity
        inc.required_roles = ["police"]
        explain.append(f"Unknown incident type - scored based on severity: {Sg}")

    inc.explain = explain
    return inc

def tie_breaker_key(doc: dict):
    """
    Tie-breaking logic with 6 parameters:
    1. Score (descending)
    2. Severity grade (descending)
    3. Vehicle vulnerability (descending)
    4. Distance (ascending - closer incidents first)
    5. Time (newest first)
    """
    score = doc.get("score", 0)
    
    # Convert severity to numeric
    severity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
    severity = severity_map.get(doc.get("severity_grade", "medium"), 2)
    
    # Try to get vehicle vulnerability from incident data
    vehicle_vuln = 0.5  # default
    if "accident" in doc and doc["accident"]:
        if "vehicle_type" in doc["accident"]:
            vehicle_type = detect_vehicle_type(doc["accident"]["vehicle_type"])
            vehicle_vuln = VEHICLE_VULNERABILITY.get(vehicle_type, 0.5)
    
    # Distance (lower distance = better for tie-breaking)
    distance = 999
    if "location" in doc and doc["location"]:
        distance = doc.get("distance_km", 999)
    
    # Timestamp (convert to numeric for sorting)
    timestamp = 0
    if doc.get("reported_at"):
        try:
            dt = datetime.fromisoformat(doc["reported_at"].replace("Z", "+00:00"))
            timestamp = dt.timestamp()
        except:
            timestamp = 0
    
    return (-score, -severity, -vehicle_vuln, distance, -timestamp)