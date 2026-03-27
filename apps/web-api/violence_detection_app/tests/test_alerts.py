import asyncio
import time
from violence_detection_app.src.fusion.model_fusion import ModelFusion
from violence_detection_app.app.services.alert_engine import AlertEngine, AlertConfig

fusion = ModelFusion()
config = AlertConfig(
    camera_label="Camera 01",
    location_label="Entrance Hall",
    hub_url="http://localhost:9000/api/alerts",
    sustained_medium=30.0,
)
engine = AlertEngine(config)


def simulate_frames(session_id, lrcn, yolo, num_frames, fps=10.0):
    print(f"\n  Simulating {num_frames} frames @ {fps}fps "
          f"(~{num_frames/fps:.0f}s real time)...")
    alert_fired = None
    for i in range(num_frames):
        fusion_result = fusion.combine_results(yolo, lrcn)
        alert = engine.process_frame(
            session_id=session_id,
            fusion_result=fusion_result,
            lrcn_result=lrcn,
            yolo_result=yolo,
            frame_number=i + 1,
        )
        if alert and alert_fired is None:
            alert_fired = alert
            print(f"  ⚡ Alert fired on frame {i+1} "
                  f"(~{(i+1)/fps:.1f}s)")
        time.sleep(1.0 / fps)
    return alert_fired


def print_result(alert, expected_level, expect_no_alert=False):
    print()
    if not alert:
        ok = "✓ PASS" if expect_no_alert else "✗ FAIL"
        print(f"  {ok} — No alert fired")
        return

    got  = alert['threat_level']
    ok   = "✓ PASS" if (got == expected_level and not expect_no_alert) else f"✗ FAIL (expected {expected_level})"
    print(f"  {ok}")
    print(f"     Level    : {got}")
    print(f"     Score    : {alert['threat_score']*100:.0f}%")
    print(f"     Action   : {alert['action']} ({alert['action_confidence']*100:.0f}%)")
    print(f"     Objects  : {[d['object'] for d in alert['objects_detected']] or 'None'}")
    print(f"     Sustained: {alert['sustained_seconds']}s")
    print(f"     Reasoning: {alert['reasoning']}")


# ═══════════════════════════════════════════════════════════════════════
def test_1():
    """shooting alone → CRITICAL, fires instantly"""
    print("\n" + "="*65)
    print("TEST 1: shooting alone → expect CRITICAL, instant")
    print("="*65)
    lrcn  = {"action": "shooting", "confidence": 0.88, "ready": True, "is_violent": True}
    yolo  = {"detections": []}
    alert = simulate_frames("t1", lrcn, yolo, num_frames=3)
    print_result(alert, "CRITICAL")


def test_2():
    """shooting + gun → CRITICAL, fires instantly"""
    print("\n" + "="*65)
    print("TEST 2: shooting + gun → expect CRITICAL, instant")
    print("="*65)
    lrcn  = {"action": "shooting", "confidence": 0.88, "ready": True, "is_violent": True}
    yolo  = {"detections": [{"object": "gun", "confidence": 0.85}]}
    alert = simulate_frames("t2", lrcn, yolo, num_frames=3)
    print_result(alert, "CRITICAL")


def test_3():
    """attacking alone → MEDIUM, fires after 30s sustain"""
    print("\n" + "="*65)
    print("TEST 3: attacking alone → expect MEDIUM, fires after ~30s")
    print("="*65)
    lrcn  = {"action": "attacking", "confidence": 0.88, "ready": True, "is_violent": True}
    yolo  = {"detections": []}
    # 35s worth of frames to cross 30s threshold
    alert = simulate_frames("t3", lrcn, yolo, num_frames=350, fps=10.0)
    print_result(alert, "MEDIUM")


def test_4():
    """attacking + knife → CRITICAL, fires instantly (weapon present)"""
    print("\n" + "="*65)
    print("TEST 4: attacking + knife → expect CRITICAL, instant")
    print("="*65)
    lrcn  = {"action": "attacking", "confidence": 0.88, "ready": True, "is_violent": True}
    yolo  = {"detections": [{"object": "knife", "confidence": 0.82}]}
    alert = simulate_frames("t4", lrcn, yolo, num_frames=3)
    print_result(alert, "CRITICAL")


def test_5():
    """attacking + gun and attacking + stick → both HIGH, instant"""
    print("\n" + "="*65)
    print("TEST 5a: attacking + gun → expect HIGH, instant")
    print("="*65)
    lrcn  = {"action": "attacking", "confidence": 0.88, "ready": True, "is_violent": True}
    yolo  = {"detections": [{"object": "gun", "confidence": 0.82}]}
    alert = simulate_frames("t5a", lrcn, yolo, num_frames=3)
    print_result(alert, "HIGH")

    print("\n" + "="*65)
    print("TEST 5b: attacking + stick → expect HIGH, instant")
    print("="*65)
    yolo  = {"detections": [{"object": "stick", "confidence": 0.82}]}
    alert = simulate_frames("t5b", lrcn, yolo, num_frames=3)
    print_result(alert, "HIGH")


def test_6():
    """fighting alone → MEDIUM, fires after 30s"""
    print("\n" + "="*65)
    print("TEST 6: fighting alone → expect MEDIUM, fires after ~30s")
    print("="*65)
    lrcn  = {"action": "fighting", "confidence": 0.88, "ready": True, "is_violent": True}
    yolo  = {"detections": []}
    alert = simulate_frames("t6", lrcn, yolo, num_frames=350, fps=10.0)
    print_result(alert, "MEDIUM")


def test_7():
    """fighting + gun/knife → HIGH instant | fighting + stick → MEDIUM"""
    print("\n" + "="*65)
    print("TEST 7a: fighting + gun → expect HIGH, instant")
    print("="*65)
    lrcn  = {"action": "fighting", "confidence": 0.88, "ready": True, "is_violent": True}
    yolo  = {"detections": [{"object": "gun", "confidence": 0.82}]}
    alert = simulate_frames("t7a", lrcn, yolo, num_frames=3)
    print_result(alert, "HIGH")

    print("\n" + "="*65)
    print("TEST 7b: fighting + knife → expect HIGH, instant")
    print("="*65)
    yolo  = {"detections": [{"object": "knife", "confidence": 0.82}]}
    alert = simulate_frames("t7b", lrcn, yolo, num_frames=3)
    print_result(alert, "HIGH")

    print("\n" + "="*65)
    print("TEST 7c: fighting + stick → expect MEDIUM, 30s sustain")
    print("="*65)
    yolo  = {"detections": [{"object": "stick", "confidence": 0.82}]}
    alert = simulate_frames("t7c", lrcn, yolo, num_frames=350, fps=10.0)
    print_result(alert, "MEDIUM")


def test_8():
    """running + any weapon → MEDIUM after 30s | running alone → no alert"""
    print("\n" + "="*65)
    print("TEST 8a: running alone → expect NO alert (NONE filtered)")
    print("="*65)
    lrcn  = {"action": "running", "confidence": 0.88, "ready": True, "is_violent": False}
    yolo  = {"detections": []}
    alert = simulate_frames("t8a", lrcn, yolo, num_frames=30)
    print_result(alert, None, expect_no_alert=True)

    print("\n" + "="*65)
    print("TEST 8b: running + gun → expect MEDIUM, 30s sustain")
    print("="*65)
    yolo  = {"detections": [{"object": "gun", "confidence": 0.85}]}
    alert = simulate_frames("t8b", lrcn, yolo, num_frames=350, fps=10.0)
    print_result(alert, "MEDIUM")

    print("\n" + "="*65)
    print("TEST 8c: running + knife → expect MEDIUM, 30s sustain")
    print("="*65)
    yolo  = {"detections": [{"object": "knife", "confidence": 0.85}]}
    alert = simulate_frames("t8c", lrcn, yolo, num_frames=350, fps=10.0)
    print_result(alert, "MEDIUM")


if __name__ == "__main__":
    print("\nFusion + Alert Engine Tests (v4)")
    print("="*65)
    print("Tests 3, 6, 7c, 8b, 8c each take ~35 real seconds (30s sustain)")
    print("Total runtime: ~3 minutes")
    print("="*65)

    test_1()
    test_2()
    test_3()
    test_4()
    test_5()
    test_6()
    test_7()
    test_8()

    print("\n" + "="*65)
    print("All tests complete")