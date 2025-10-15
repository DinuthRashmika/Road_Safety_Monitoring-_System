import logging
from .dispatcher import Notifier

log = logging.getLogger("ers.notifications")

class ConsoleNotifier(Notifier):
    async def send(self, to: str, message: str) -> None:
        log.info(f"[notify] to={to} | {message}")
