import uuid
def emg_id(prefix="EMG") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"
