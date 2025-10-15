VALID = {"new":["accepted"], "accepted":["enroute"], "enroute":["arrived"], "arrived":["resolved"], "resolved":[]}

def can_transition(cur: str, nxt: str) -> bool:
    return nxt in VALID.get(cur, [])
