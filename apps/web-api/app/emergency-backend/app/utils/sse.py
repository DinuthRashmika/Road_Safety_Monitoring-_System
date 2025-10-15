import asyncio
from typing import AsyncGenerator

HEARTBEAT = b":keep-alive\n\n"

async def event_stream(queue: "asyncio.Queue[bytes]") -> AsyncGenerator[bytes, None]:
    try:
        while True:
            try:
                data = await asyncio.wait_for(queue.get(), timeout=15)
                yield b"data: " + data + b"\n\n"
            except asyncio.TimeoutError:
                yield HEARTBEAT
    except asyncio.CancelledError:
        return
