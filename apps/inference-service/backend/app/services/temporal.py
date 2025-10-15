class TemporalDebouncer:
    """
    Fires once when `active` stays true for `min_secs`,
    then suppresses further fires for `cooldown` seconds.
    """
    def __init__(self, min_secs: float, cooldown: float):
        self.min_secs = min_secs
        self.cooldown = cooldown
        self.active_since = None
        self.last_fired = 0.0

    def update(self, active: bool, now: float) -> bool:
        # If not active → reset timer.
        if not active:
            self.active_since = None
            return False

        # Start timing when it becomes active.
        if self.active_since is None:
            self.active_since = now

        long_enough = (now - self.active_since) >= self.min_secs
        past_cooldown = (now - self.last_fired) >= self.cooldown

        if long_enough and past_cooldown:
            self.last_fired = now
            self.active_since = None
            return True
        return False
