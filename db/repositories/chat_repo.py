"""
Chat Session & Message Repository (db/repositories/chat_repo.py)
Fully-typed repository supporting both Synchronous and Async SQLAlchemy 2.0 sessions
with full PostgreSQL and SQLite compatibility.
"""

import json
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, delete, update
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import ChatSession, ChatMessage
from db.repositories.base import BaseRepository, AsyncBaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    def __init__(self, session: Session):
        super().__init__(ChatSession, session)

    def create_chat_session(self, session_id: Optional[str] = None, title: str = "محادثة جديدة", role: str = "property_manager") -> Dict[str, Any]:
        sid = session_id or f"session_{uuid.uuid4().hex[:12]}"
        chat_sess = ChatSession(session_id=sid, title=title, user_role=role)
        self.session.add(chat_sess)
        self.session.commit()
        self.session.refresh(chat_sess)
        return {
            "session_id": chat_sess.session_id,
            "title": chat_sess.title,
            "role": chat_sess.user_role,
            "created_at": chat_sess.created_at.isoformat() if chat_sess.created_at else None,
            "updated_at": chat_sess.updated_at.isoformat() if chat_sess.updated_at else None
        }

    def get_all_chat_sessions(self) -> List[Dict[str, Any]]:
        stmt = select(ChatSession).order_by(ChatSession.updated_at.desc())
        sessions = self.session.scalars(stmt).all()
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "role": s.user_role,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in sessions
        ]

    def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.message_id.asc())
        messages = self.session.scalars(stmt).all()
        formatted = []
        for m in messages:
            item = {
                "id": m.message_id,
                "type": m.msg_type or m.sender or "assistant",
                "content": m.content or m.message_text or "",
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            if m.tool_name:
                item["tool"] = m.tool_name
                try:
                    item["args"] = json.loads(m.tool_args) if m.tool_args else {}
                except Exception:
                    item["args"] = m.tool_args
                try:
                    item["result"] = json.loads(m.tool_result) if m.tool_result else {}
                except Exception:
                    item["result"] = m.tool_result
            if m.elicitation_payload:
                try:
                    item["elicitation"] = json.loads(m.elicitation_payload)
                except Exception:
                    item["elicitation"] = m.elicitation_payload
            if m.sse_payload:
                item["sse_payload"] = m.sse_payload
            formatted.append(item)
        return formatted

    def save_chat_message(
        self,
        session_id: str,
        msg_type: str,
        content: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Dict[str, Any]] = None,
        elicitation_payload: Optional[Dict[str, Any]] = None,
        sse_payload: Optional[str] = None
    ) -> int:
        # Ensure session exists
        existing = self.session.get(ChatSession, session_id)
        if not existing:
            init_title = (content.strip()[:40] + ("..." if len(content.strip()) > 40 else "")) if (msg_type == "user" and content) else "New conversation"
            self.create_chat_session(session_id=session_id, title=init_title)
        else:
            existing.updated_at = datetime.utcnow()
            if msg_type == "user" and content and (not existing.title or existing.title in ["محادثة جديدة", "New conversation", "New Conversation"]):
                existing.title = content.strip()[:40] + ("..." if len(content.strip()) > 40 else "")

        msg = ChatMessage(
            session_id=session_id,
            sender=msg_type,
            msg_type=msg_type,
            message_text=content or "",
            content=content or "",
            tool_name=tool_name,
            tool_args=json.dumps(tool_args) if tool_args else None,
            tool_result=json.dumps(tool_result) if tool_result else None,
            elicitation_payload=json.dumps(elicitation_payload) if elicitation_payload else None,
            sse_payload=sse_payload
        )
        self.session.add(msg)
        self.session.commit()
        self.session.refresh(msg)
        return msg.message_id

    def update_chat_session_title(self, session_id: str, title: str) -> bool:
        chat_sess = self.session.get(ChatSession, session_id)
        if chat_sess:
            chat_sess.title = title
            chat_sess.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        return False

    def update_chat_session_role(self, session_id: str, role: str) -> bool:
        chat_sess = self.session.get(ChatSession, session_id)
        if chat_sess:
            chat_sess.user_role = role
            chat_sess.updated_at = datetime.utcnow()
            self.session.commit()
            return True
        return False

    def get_chat_session_role(self, session_id: str) -> str:
        chat_sess = self.session.get(ChatSession, session_id)
        return chat_sess.user_role if chat_sess else "property_manager"

    def delete_chat_session(self, session_id: str) -> bool:
        chat_sess = self.session.get(ChatSession, session_id)
        if chat_sess:
            self.session.delete(chat_sess)
            self.session.commit()
            return True
        return False


class AsyncChatRepository(AsyncBaseRepository[ChatSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(ChatSession, session)

    async def create_chat_session(self, session_id: Optional[str] = None, title: str = "محادثة جديدة", role: str = "property_manager", user_id: Optional[int] = None) -> Dict[str, Any]:
        sid = session_id or f"session_{uuid.uuid4().hex[:12]}"
        chat_sess = ChatSession(session_id=sid, title=title, user_role=role, user_id=user_id)
        self.session.add(chat_sess)
        await self.session.commit()
        await self.session.refresh(chat_sess)
        return {
            "session_id": chat_sess.session_id,
            "title": chat_sess.title,
            "role": chat_sess.user_role,
            "created_at": chat_sess.created_at.isoformat() if chat_sess.created_at else None,
            "updated_at": chat_sess.updated_at.isoformat() if chat_sess.updated_at else None
        }

    async def get_all_chat_sessions(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List sessions. If user_id given, return only that user's sessions."""
        if user_id is not None:
            stmt = select(ChatSession).where(
                (ChatSession.user_id == user_id) | (ChatSession.user_id.is_(None))
            ).order_by(ChatSession.updated_at.desc())
        else:
            stmt = select(ChatSession).order_by(ChatSession.updated_at.desc())
        result = await self.session.scalars(stmt)
        sessions = result.all()
        return [
            {
                "session_id": s.session_id,
                "title": s.title,
                "role": s.user_role,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None
            }
            for s in sessions
        ]

    async def get_chat_messages(self, session_id: str) -> List[Dict[str, Any]]:
        stmt = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.message_id.asc())
        result = await self.session.scalars(stmt)
        messages = result.all()
        formatted = []
        for m in messages:
            item = {
                "id": m.message_id,
                "type": m.msg_type or m.sender or "assistant",
                "content": m.content or m.message_text or "",
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            if m.tool_name:
                item["tool"] = m.tool_name
                try:
                    item["args"] = json.loads(m.tool_args) if m.tool_args else {}
                except Exception:
                    item["args"] = m.tool_args
                try:
                    item["result"] = json.loads(m.tool_result) if m.tool_result else {}
                except Exception:
                    item["result"] = m.tool_result
            if m.elicitation_payload:
                try:
                    item["elicitation"] = json.loads(m.elicitation_payload)
                except Exception:
                    item["elicitation"] = m.elicitation_payload
            if m.sse_payload:
                item["sse_payload"] = m.sse_payload
            formatted.append(item)
        return formatted

    async def save_chat_message(
        self,
        session_id: str,
        msg_type: str,
        content: Optional[str] = None,
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        tool_result: Optional[Dict[str, Any]] = None,
        elicitation_payload: Optional[Dict[str, Any]] = None,
        sse_payload: Optional[str] = None
    ) -> int:
        existing = await self.session.get(ChatSession, session_id)
        if not existing:
            init_title = (content.strip()[:40] + ("..." if len(content.strip()) > 40 else "")) if (msg_type == "user" and content) else "New conversation"
            await self.create_chat_session(session_id=session_id, title=init_title)
        else:
            existing.updated_at = datetime.utcnow()
            if msg_type == "user" and content and (not existing.title or existing.title in ["محادثة جديدة", "New conversation", "New Conversation"]):
                existing.title = content.strip()[:40] + ("..." if len(content.strip()) > 40 else "")

        msg = ChatMessage(
            session_id=session_id,
            sender=msg_type,
            msg_type=msg_type,
            message_text=content or "",
            content=content or "",
            tool_name=tool_name,
            tool_args=json.dumps(tool_args) if tool_args else None,
            tool_result=json.dumps(tool_result) if tool_result else None,
            elicitation_payload=json.dumps(elicitation_payload) if elicitation_payload else None,
            sse_payload=sse_payload
        )
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg.message_id

    async def update_chat_session_title(self, session_id: str, title: str) -> bool:
        chat_sess = await self.session.get(ChatSession, session_id)
        if chat_sess:
            chat_sess.title = title
            chat_sess.updated_at = datetime.utcnow()
            await self.session.commit()
            return True
        return False

    async def update_chat_session_role(self, session_id: str, role: str) -> bool:
        chat_sess = await self.session.get(ChatSession, session_id)
        if chat_sess:
            chat_sess.user_role = role
            chat_sess.updated_at = datetime.utcnow()
            await self.session.commit()
            return True
        return False

    async def get_chat_session_role(self, session_id: str) -> str:
        chat_sess = await self.session.get(ChatSession, session_id)
        return chat_sess.user_role if chat_sess else "property_manager"

    async def delete_chat_session(self, session_id: str) -> bool:
        chat_sess = await self.session.get(ChatSession, session_id)
        if chat_sess:
            await self.session.delete(chat_sess)
            await self.session.commit()
            return True
        return False
