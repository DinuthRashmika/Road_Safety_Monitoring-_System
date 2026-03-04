"""
model_fusion.py (REDESIGNED)
────────────────────────────────
Action-First Priority Fusion System

Philosophy:
  • Action Recognition = PRIMARY threat indicator (can trigger alone)
  • Object Detection = AMPLIFIER (boosts existing threats)
  • Synergy = CONTEXT-AWARE multipliers

Threat Tiers:
  1. CRITICAL (90%+): Immediate danger requiring instant response
  2. HIGH     (70%+): Active violence requiring urgent action
  3. MEDIUM   (50%+): Suspicious activity requiring monitoring
  4. LOW      (30%+): Minor concern
  5. NONE     (<30%): Safe
"""

from typing import Dict, Tuple


class ModelFusion:
    """Action-first fusion with intelligent threat escalation"""

    def __init__(self):
        # ═══════════════════════════════════════════════════════════════
        #  ACTION WEIGHTS (PRIMARY THREAT INDICATORS)
        # ═══════════════════════════════════════════════════════════════
        # model_fusion.py — updated weights only (replace these sections)

        self.action_severity = {
            "shooting":   1.00,  # CRITICAL alone (0.85×1.0 = 0.85 = CRITICAL)
            "attacking":  0.65,  # MEDIUM alone  (0.85×0.65 = 0.5525)
            "fighting":   0.65,  # MEDIUM alone  (0.85×0.65 = 0.5525)
            "stabbing":   0.75,
            "running":    0.30,  # NONE alone    (0.85×0.30 = 0.255)
            "shouting":   0.40,
            "walking":    0.15,
            "standing":   0.10,
            "sitting":    0.10,
        }

        self.object_severity = {
            "gun":    0.90,
            "knife":  0.80,
            "stick":  0.60,
            "bat":    0.60,
            "hammer": 0.55,
        }

        self.synergy_rules = {
            # shooting + anything → already CRITICAL, synergy keeps it there
            ("shooting", "gun"):    0.15,
            ("shooting", "knife"):  0.15,
            ("shooting", "stick"):  0.15,

            # attacking + knife → CRITICAL, gun/stick → HIGH
            ("attacking", "knife"): 0.30,  # 0.5525 + object_boost + 0.30 → CRITICAL
            ("attacking", "gun"):   0.15,  # → HIGH
            ("attacking", "stick"): 0.12,  # → HIGH

            # fighting + gun/knife → HIGH, stick stays MEDIUM (no rule)
            ("fighting", "gun"):    0.15,  # → HIGH
            ("fighting", "knife"):  0.15,  # → HIGH

            # running + weapon → MEDIUM
            ("running", "gun"):     0.10,
            ("running", "knife"):   0.08,
            ("running", "stick"):   0.06,
        }

        print("✓ Action-First Fusion System initialized")


    # ═══════════════════════════════════════════════════════════════════
    #  STEP 1: Calculate Base Action Threat
    # ═══════════════════════════════════════════════════════════════════
    def calculate_action_threat(self, lrcn_result: Dict) -> Tuple[float, str]:
        if not lrcn_result.get("ready", False):
            return 0.0, "LRCN buffer filling"

        action     = lrcn_result.get("action", "unknown").lower()
        confidence = lrcn_result.get("confidence", 0.0)
        severity   = self.action_severity.get(action, 0.5)
        action_score = confidence * severity

        if action_score >= 0.85:
            reason = f"CRITICAL action: {action.upper()} detected with {confidence*100:.0f}% confidence"
        elif action_score >= 0.70:
            reason = f"HIGH severity action: {action.upper()} at {confidence*100:.0f}% confidence"
        elif action_score >= 0.50:
            reason = f"MEDIUM concern: {action.upper()} behavior detected"
        elif action_score >= 0.30:
            reason = f"LOW concern: {action.upper()} detected"
        else:
            reason = f"No threat: {action.upper()}"

        return action_score, reason


    # ═══════════════════════════════════════════════════════════════════
    #  STEP 2: Calculate Object Amplification
    # ═══════════════════════════════════════════════════════════════════
    def calculate_object_amplification(self, yolo_result: Dict, action_score: float) -> Tuple[float, str]:
        detections = yolo_result.get("detections", [])
        if not detections:
            return action_score, "No weapons detected"

        max_object_severity = 0.0
        detected_object = None

        for det in detections:
            obj_name = det.get("object", "").lower()
            obj_conf = det.get("confidence", 0.0)
            severity = self.object_severity.get(obj_name, 0.0)
            weighted = obj_conf * severity
            if weighted > max_object_severity:
                max_object_severity = weighted
                detected_object = (obj_name, obj_conf)

        if max_object_severity == 0.0:
            return action_score, "Objects detected but not weapons"

        # Tighter boost tiers to prevent unintended CRITICAL
        if action_score >= 0.70:
            boost_factor = 0.10   # already HIGH — small boost
        elif action_score >= 0.50:
            boost_factor = 0.15   # MEDIUM — moderate boost (was 0.25, now tighter)
        elif action_score >= 0.30:
            boost_factor = 0.20   # LOW — enough to reach MEDIUM with weapon
        else:
            boost_factor = 0.05   # NONE — minimal

        amplified_score = action_score + (max_object_severity * boost_factor)
        obj_name, obj_conf = detected_object
        reason = f"{obj_name.upper()} detected ({obj_conf*100:.0f}% conf) — boost ×{boost_factor}"

        return amplified_score, reason


    # ═══════════════════════════════════════════════════════════════════
    #  STEP 3: Apply Synergy Bonuses
    # ═══════════════════════════════════════════════════════════════════
    def calculate_synergy_bonus(self, lrcn_result: Dict, yolo_result: Dict, current_score: float) -> Tuple[float, str]:
        action     = lrcn_result.get("action", "").lower()
        detections = yolo_result.get("detections", [])
        if not detections:
            return current_score, ""

        max_bonus    = 0.0
        synergy_match = None

        for det in detections:
            obj_name = det.get("object", "").lower()
            combo    = (action, obj_name)
            if combo in self.synergy_rules:
                bonus = self.synergy_rules[combo]
                if bonus > max_bonus:
                    max_bonus     = bonus
                    synergy_match = (action, obj_name)

        if max_bonus == 0.0:
            return current_score, ""

        final_score = min(current_score + max_bonus, 1.0)
        a, o = synergy_match
        reason = f"SYNERGY: {a.upper()}+{o.upper()} (+{max_bonus*100:.0f}%)"
        return final_score, reason

    def classify_threat_level(self, score: float) -> str:
        if   score >= 0.85: return "CRITICAL"
        elif score >= 0.70: return "HIGH"
        elif score >= 0.50: return "MEDIUM"
        elif score >= 0.30: return "LOW"
        else:               return "NONE"

    def combine_results(self, yolo_result: Dict, lrcn_result: Dict) -> Dict:
        action_score, action_reason = self.calculate_action_threat(lrcn_result)

        amplified_score, object_reason = self.calculate_object_amplification(yolo_result, action_score)
        object_contribution = amplified_score - action_score

        final_score, synergy_reason = self.calculate_synergy_bonus(lrcn_result, yolo_result, amplified_score)
        synergy_bonus = final_score - amplified_score

        threat_level = self.classify_threat_level(final_score)

        reasoning_parts = [action_reason]
        if object_reason: reasoning_parts.append(object_reason)
        if synergy_reason: reasoning_parts.append(synergy_reason)

        return {
            "threat_score":         round(final_score, 4),
            "weight_level":         threat_level,
            "action_contribution":  round(action_score, 4),
            "object_contribution":  round(object_contribution, 4),
            "synergy_bonus":        round(synergy_bonus, 4),
            "reasoning":            " → ".join(reasoning_parts),
            "breakdown": {
                "base_action_score":   round(action_score, 4),
                "after_objects":       round(amplified_score, 4),
                "final_with_synergy":  round(final_score, 4),
            }
        }

    def calculate_lrcn_threat_score(self, lrcn_result: Dict) -> float:
        score, _ = self.calculate_action_threat(lrcn_result)
        return score

    def calculate_yolo_threat_score(self, yolo_result: Dict) -> float:
        detections = yolo_result.get("detections", [])
        if not detections:
            return 0.0
        max_severity = 0.0
        for det in detections:
            obj_name = det.get("object", "").lower()
            obj_conf = det.get("confidence", 0.0)
            severity = self.object_severity.get(obj_name, 0.0)
            max_severity = max(max_severity, obj_conf * severity)
        return max_severity

