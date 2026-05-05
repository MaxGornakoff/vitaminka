import logging
from typing import List, Dict
from sqlalchemy.orm import Session

from app.models.chat import ChatMessage, ChatSession
from app.rag.llm import LLMClient

logger = logging.getLogger(__name__)

class ChatService:
    """
    Сервис для обработки чат-сообщений
    TODO: Интегрировать RAG и LLM
    """
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMClient()
    
    def _get_or_create_session(self, shop_id: str, session_id: str) -> ChatSession:
        session = (
            self.db.query(ChatSession)
            .filter(ChatSession.session_id == session_id)
            .first()
        )

        if session is None:
            session = ChatSession(shop_id=shop_id, session_id=session_id)
            self.db.add(session)
            self.db.flush()

        return session
    
    async def process_message(self, shop_id: str, session_id: str, user_message: str) -> str:
        """
        Обработать сообщение пользователя и вернуть ответ
        """
        logger.info(f"Processing message from {shop_id}: {user_message}")
        
        self._get_or_create_session(shop_id=shop_id, session_id=session_id)

        self.db.add(
            ChatMessage(
                session_id=session_id,
                role="user",
                content=user_message,
            )
        )

        self.db.flush()

        recent_history = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        context = {
            "shop_id": shop_id,
            "session_id": session_id,
            "history": [{"role": m.role, "content": m.content} for m in recent_history],
            "products": [],
        }

        assistant_message = await self.llm.generate_response(
            query=user_message,
            context=context,
        )

        self.db.add(
            ChatMessage(
                session_id=session_id,
                role="assistant",
                content=assistant_message,
            )
        )
        self.db.commit()

        return assistant_message
    
    async def get_chat_history(self, session_id: str) -> List[Dict]:
        """
        Получить историю диалога
        """
        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        return [{"role": m.role, "content": m.content} for m in messages]
