"""
Notification Service — per-user SSE pub/sub for background graph updates.
In-memory, with DB persistence via chat_messages for days-later delivery.
Non-blocking with periodic heartbeat to enable clean server shutdown.
"""
import asyncio
import json
from collections import defaultdict
from typing import AsyncGenerator, Dict, Any

_subscribers: Dict[int, set[asyncio.Queue]] = defaultdict(set)
_lock = asyncio.Lock()


class NotificationService:
    @staticmethod
    async def publish(user_id: int, event: Dict[str, Any]):
        """Publish event to all subscribers for user_id."""
        if user_id is None:
            return
        async with _lock:
            queues = list(_subscribers.get(user_id, set()))
        for q in queues:
            try:
                await q.put(event)
            except Exception:
                pass

    @staticmethod
    async def subscribe(user_id: int) -> AsyncGenerator[Dict[str, Any], None]:
        """Yield events for user_id with periodic heartbeat until cancelled."""
        queue: asyncio.Queue = asyncio.Queue()
        async with _lock:
            _subscribers[user_id].add(queue)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.5)
                    yield event
                except asyncio.TimeoutError:
                    yield {"type": "ping"}
        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            async with _lock:
                _subscribers[user_id].discard(queue)
                if not _subscribers[user_id]:
                    _subscribers.pop(user_id, None)

    @staticmethod
    def subscriber_count(user_id: int) -> int:
        return len(_subscribers.get(user_id, set()))
