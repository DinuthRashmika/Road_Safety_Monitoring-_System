from typing import Protocol

class Notifier(Protocol):
    async def send(self, to: str, message: str) -> None: ...
