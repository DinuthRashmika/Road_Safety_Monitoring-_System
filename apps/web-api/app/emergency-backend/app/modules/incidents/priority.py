from __future__ import annotations
from datetime import datetime
from app.modules.incidents.schemas import Incident
from enum import Enum
import math

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

# Severity grade multipliers
SEVERITY_MULTIPLIERS = {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.3,
    "critical": 1.5
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
    - Severity grade (as a multiplier)
    """
    # Base vulnerability from vehicle type
    vehicle_type = "unknown"
    vehicle_count = 1
    
    if inc.accident:
        # Try to get vehicle type - FIXED: Check if accident has vehicle_type attribute
        if hasattr(inc.accident, 'vehicle_type') and inc.accident.vehicle_type:
            vehicle_type = detect_vehicle_type(inc.accident.vehicle_type)
        vehicle_count = max(1, inc.accident.vehicles_involved)
    elif inc.violence:
        # For violence, consider participants as "vehicles" for vulnerability
        if hasattr(inc.violence, 'participants_count'):
            vehicle_count = inc.violence.participants_count
    
    # Get base vulnerability score
    base_vu = VEHICLE_VULNERABILITY.get(vehicle_type, 0.5)
    
    # Apply severity grade multiplier
    severity_multiplier = SEVERITY_MULTIPLIERS.get(inc.severity_grade, 1.0)
    
    # Apply vehicle count factor (more vehicles/people = higher vulnerability)
    # But with diminishing returns
    vehicle_factor = 1.0 + (min(vehicle_count, 5) * 0.1)
    
    # Calculate final Vu
    Vu = base_vu * severity_multiplier * vehicle_factor
    
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
# PARAMETER 4: HOLIDAY SURGE (Hs)
# ============================================
def get_holiday_surge(dt: datetime = None) -> float:
    """
    Enhanced Holiday Surge (Hs) with Sri Lankan festival calendar
    Returns score between 0.3 and 1.0
    """
    if dt is None:
        dt = datetime.now()
    
    month = dt.month
    day = dt.day
    
    # Major festival periods (Highest Surge)
    # Avurudu (Sinhala & Tamil New Year) - April
    if month == 4 and 10 <= day <= 20:
        return 1.0
    # Christmas/New Year - December 20 - January 5
    elif (month == 12 and day >= 20) or (month == 1 and day <= 5):
        return 1.0
    
    # Minor festival periods (High Surge)
    # Vesak - May (full moon period)
    if month == 5 and 5 <= day <= 15:
        return 0.9
    # Deepavali - October/November (approximate)
    if month == 10 and 20 <= day <= 30:
        return 0.85
    if month == 11 and 1 <= day <= 5:
        return 0.85
    
    # Long weekends / Public holidays
    # Independence Day - February 4
    if month == 2 and day == 4:
        return 0.8
    # May Day - May 1
    if month == 5 and day == 1:
        return 0.8
    
    # Normal days
    return 0.4

# ============================================
# PARAMETER 5: SEVERITY GRADE (Sg)
# ============================================
def get_severity_multiplier(severity_grade: str) -> float:
    """Convert severity grade to multiplier"""
    return SEVERITY_MULTIPLIERS.get(severity_grade, 1.0)

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
# MAIN SCORING ENGINE - MFIPA+ with 6 Parameters
# ============================================
def score_incident(inc: Incident, responder_location: dict = None) -> Incident:
    """
    MFIPA+ Algorithm with 6 Parameters:
    1. Vehicle Vulnerability (Vu) - 25%
    2. Location Risk (Lr) - 20%
    3. Time-of-Day Risk (Tr) - 15%
    4. Holiday Surge (Hs) - 10%
    5. Severity Grade (Sg) - 15% (as multiplier)
    6. Distance Urgency (Du) - 15%
    """
    # Parse incident time
    dt = datetime.now()
    if inc.reported_at:
        try:
            dt = datetime.fromisoformat(inc.reported_at.replace("Z", "+00:00"))
        except ValueError:
            pass

    # Calculate all 6 parameters
    Vu = calculate_vulnerability_index(inc)           # 25% weight
    Lr = map_risk(inc.camera_risk_class)              # 20% weight
    Tr = get_temporal_impact(dt)                       # 15% weight
    Hs = get_holiday_surge(dt)                         # 10% weight
    Sg = get_severity_multiplier(inc.severity_grade)   # 15% weight (as multiplier)
    Du = calculate_distance_urgency(inc, responder_location)  # 15% weight
    
    explain: list[str] = []
    
    # Check for Fire (Global Override)
    fire_detected = (inc.accident and inc.accident.fire_present) or \
                    (inc.violence and hasattr(inc.violence, 'fire_present') and inc.violence.fire_present)
    
    # --- SCENARIO A: ACCIDENT ---
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
            raw_score = 100 * (
                0.25 * Vu +    # Vehicle Vulnerability
                0.20 * Lr +    # Location Risk
                0.15 * Tr +    # Time Risk
                0.10 * Hs +    # Holiday Surge
                0.15 * Du      # Distance Urgency
            ) * Sg  # Severity grade as final multiplier
            
            inc.score = min(100, round(raw_score))
            
            explain.append(f"📊 MFIPA+ Calculation (6 Parameters):")
            explain.append(f"  1. Vehicle Vulnerability (Vu): {Vu:.2f} (Vehicle: {vehicle_type}) [25%]")
            explain.append(f"  2. Location Risk (Lr): {Lr:.2f} [20%]")
            explain.append(f"  3. Time Risk (Tr): {Tr:.2f} [15%]")
            explain.append(f"  4. Holiday Surge (Hs): {Hs:.2f} [10%]")
            explain.append(f"  5. Distance Urgency (Du): {Du:.2f} [15%]")
            explain.append(f"  6. Severity Multiplier (Sg): {Sg:.2f} [15% effect]")
            explain.append(f"  Raw: (25%×{Vu:.2f} + 20%×{Lr:.2f} + 15%×{Tr:.2f} + 10%×{Hs:.2f} + 15%×{Du:.2f}) = {(0.25*Vu + 0.2*Lr + 0.15*Tr + 0.1*Hs + 0.15*Du):.3f}")
            explain.append(f"  Final Score: {inc.score} (×{Sg:.2f} severity multiplier)")
            
            # Determine required roles based on score and vehicle type
            inc.required_roles = ["ambulance", "police"]
            
            # Add fire if heavy vehicle (more likely to need fire rescue)
            if vehicle_type in ["truck", "heavy_truck", "bus", "container"] and inc.score > 70:
                inc.required_roles.append("fire")
                explain.append("🚒 Fire services added due to heavy vehicle involvement")
            
            # Add fire if very high score
            if inc.score > 85:
                inc.required_roles.append("fire")
                explain.append("🚒 Fire services added due to critical score")

    # --- SCENARIO B: VIOLENCE ---
    elif inc.violence:
        # Violence incidents use a modified formula
        W = clamp01(inc.violence.weapon_conf)
        P = clamp01((inc.violence.participants_count - 1) / 4.0)
        
        # Combine with our parameters
        raw_score = 100 * (
            0.30 * W +           # Weapon presence
            0.20 * P +           # Crowd density
            0.15 * Tr +          # Time risk
            0.10 * Lr +          # Location risk
            0.10 * Hs +          # Holiday surge
            0.15 * Du            # Distance urgency
        ) * Sg                   # Severity multiplier
        
        inc.score = min(100, round(raw_score))
        
        explain.append(f"👥 Violence Incident Scoring:")
        explain.append(f"  Weapon Confidence: {W:.2f} [30%]")
        explain.append(f"  Participants: {P:.2f} [20%]")
        explain.append(f"  Time Risk: {Tr:.2f} [15%]")
        explain.append(f"  Location Risk: {Lr:.2f} [10%]")
        explain.append(f"  Holiday Surge: {Hs:.2f} [10%]")
        explain.append(f"  Distance Urgency: {Du:.2f} [15%]")
        explain.append(f"  Severity Multiplier: {Sg:.2f}")
        explain.append(f"  Final Score: {inc.score}")

        if fire_detected:
            inc.required_roles = ["ambulance", "police", "fire"]
            explain.append("Fire Service added due to Fire Risk")
        else:
            inc.required_roles = ["police"]
            if inc.score > 70:
                inc.required_roles.append("ambulance")
                explain.append("🚑 Ambulance added due to High Threat Level")
            
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
        # This would need actual responder location
        # For now, use a default
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