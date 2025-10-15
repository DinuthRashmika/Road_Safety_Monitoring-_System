def test_status_transition_guard_exists():
    from app.modules.incidents.status import can_transition
    assert can_transition("new","accepted")
    assert not can_transition("new","resolved")
