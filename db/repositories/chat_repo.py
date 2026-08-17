"""
Chat Session & Message Repository (db/repositories/chat_repo.py)
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import ChatSession, ChatMessage
from db.repositories.base import BaseRepository, AsyncBaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    def __init__(self, session: Session):
        super().__init__(ChatSession, session)

    def create_chat_session(self, title: str = "محادثة جديدة", user_role: str = "property_manager") -> ChatSession:
        session_id = str(uuid.uuid4())
        chat_sess = ChatSession(session_id=session_id, title=title, user_role=user_role)
        self.session.add(chat_sess)
        self.session.commit()
        self.session.refresh(chat_sess)
        return chat_sess

    def save_message(self, session_id: str, sender: str, message_text: str, sse_payload: Optional[str] = None) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, sender=sender, message_text=message_text, sse_payload=sse_payload)
        self.session.add(msg)
        self.session.commit()
        self.session.refresh(msg)
        return msg

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        return list(self.session.scalars(stmt).all())


class AsyncChatRepository(AsyncBaseRepository[ChatSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(ChatSession, session)

    async def create_chat_session(self, title: str = "محادثة جديدة", user_role: str = "property_manager") -> ChatSession:
        session_id = str(uuid.uuid4())
        chat_sess = ChatSession(session_id=session_id, title=title, user_role=user_role)
        self.session.add(chat_sess)
        await self.session.commit()
        await self.session.refresh(chat_sess)
        return chat_sess

    async def save_message(self, session_id: str, sender: str, message_text: str, sse_payload: Optional[str] = None) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, sender=sender, message_text=message_text, sse_payload=sse_payload)
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_messages(self, session_id: str) -> List[ChatMessage]:
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc())
        result = await self.session.scalars(stmt)
        return list(result.all())
