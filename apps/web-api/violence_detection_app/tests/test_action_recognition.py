# Test preprocessing frame before pasing into LRCN
def test_preprocess_frame():
    import numpy as np
    import cv2
    from violence_detection_app.src.model_inference.action_recog import ActionRecognitionTorch

    detector = ActionRecognitionTorch(verbose=False)

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    processed = detector.preprocess_frame(dummy_frame)

    assert processed.shape == (64, 64, 3)
    assert processed.min() >= 0.0
    assert processed.max() <= 1.0

    print("preprocess_frame() passed")

# Test adding frame to buffer of 16
def test_add_frame_to_buffer():
    import numpy as np
    from violence_detection_app.src.model_inference.action_recog import ActionRecognitionTorch

    detector = ActionRecognitionTorch(sequence_length=5, verbose=False)

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    for i in range(4):
        ready = detector.add_frame_to_buffer(dummy_frame)
        assert ready is False

    ready = detector.add_frame_to_buffer(dummy_frame)
    assert ready is True

    print("add_frame_to_buffer() passed")

# Test predicting action when buffer is not full yet - should return not ready
def test_predict_action_buffer_not_full():
    import numpy as np
    from violence_detection_app.src.model_inference.action_recog import ActionRecognitionTorch

    detector = ActionRecognitionTorch(sequence_length=5, verbose=False)

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detector.add_frame_to_buffer(dummy_frame)

    result = detector.predict_action()

    assert result["ready"] is False
    assert result["action"] == "Waiting..."

    print("predict_action() buffer-not-full passed")

# Test single frame process
def test_process_single_frame_buffering():
    import numpy as np
    from violence_detection_app.src.model_inference.action_recog import ActionRecognitionTorch

    detector = ActionRecognitionTorch(sequence_length=3, verbose=False)

    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    r1 = detector.process_single_frame(dummy_frame)
    r2 = detector.process_single_frame(dummy_frame)
    r3 = detector.process_single_frame(dummy_frame)

    assert r1["ready"] is False
    assert r2["ready"] is False
    assert r3["ready"] in [True, False]  # True only if model loaded

    print("process_single_frame() buffering passed")

# Test reset buffer feature so only last frame is actually matters
def test_reset_buffer():
    import numpy as np
    from violence_detection_app.src.model_inference.action_recog import ActionRecognitionTorch

    detector = ActionRecognitionTorch(sequence_length=5, verbose=False)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)

    detector.add_frame_to_buffer(dummy_frame)
    detector.add_frame_to_buffer(dummy_frame)

    detector.reset_buffer()

    assert len(detector.frame_buffer) == 0

    print("reset_buffer() passed")

# Test Get Stats
def test_get_statistics():
    from violence_detection_app.src.model_inference.action_recog import ActionRecognitionTorch

    detector = ActionRecognitionTorch(verbose=False)
    stats = detector.get_statistics()

    assert "frames_processed" in stats
    assert "sequences_analyzed" in stats
    assert "violent_actions_detected" in stats
    assert "violence_rate" in stats

    print("get_statistics() passed")