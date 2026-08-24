"""
Notifications Router — per-user SSE for background graph updates.
Persists via chat_messages for days-later delivery, live via in-memory bus.
"""
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_async_db
from db.models import ChatMessage
from services.notification_service import NotificationService
from web.deps import get_optional_user

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("/stream")
async def notifications_stream(
    request: Request,
    db: AsyncSession = Depends(get_async_db),
):
    """SSE stream per-user — emits state_graph_update events live, with Authorization Bearer."""
    user = await get_optional_user(request, db)
    if not user:
        # Try to get user_id from query param token? For EventSource without header, allow ?token=...
        # For now, require auth
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Authentication required for notifications stream")
    user_id = user.tenant_id

    async def event_gen():
        # Send initial hello
        yield f"data: {json.dumps({'type': 'hello', 'user_id': user_id}, ensure_ascii=False)}\n\n"
        try:
            async for evt in NotificationService.subscribe(user_id):
                if await request.is_disconnected():
                    break
                if isinstance(evt, dict) and evt.get("type") == "ping":
                    yield ": ping\n\n"
                else:
                    yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            pass

    return StreamingResponse(event_gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    })

@router.get("/poll")
async def notifications_poll(
    since: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_async_db),
):
    """Poll fallback for days-later: fetch recent state_graph_update messages for user."""
    user = await get_optional_user(request, db)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Authentication required")
    user_id = user.tenant_id
    # Get sessions for user, then messages of type state_graph_update
    from db.repositories.chat_repo import AsyncChatRepository
    repo = AsyncChatRepository(db)
    sessions = await repo.get_all_chat_sessions(user_id=user_id)
    # Collect recent updates from last 30 days
    recent = []
    for sess in sessions[:5]:  # last 5 sessions
        msgs = await repo.get_chat_messages(sess["session_id"])
        for m in msgs:
            if m.get("type") == "state_graph_update":
                try:
                    content = json.loads(m.get("content", "{}"))
                    # Filter by since if provided
                    if since and m.get("created_at") and m.get("created_at") < since:
                        continue
                    recent.append({
                        "session_id": sess["session_id"],
                        "run_id": content.get("run_id"),
                        "graph_id": content.get("graph_id") or content.get("graph_status"),
                        "status": content.get("status") or content.get("graph_status"),
                        "message": content.get("message"),
                        "created_at": m.get("created_at"),
                    })
                except Exception:
                    pass
    return {"status": "success", "updates": recent[:20]}
