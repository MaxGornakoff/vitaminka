import logging
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.chat import ChatMessage, ChatSession
from app.models.product import Product
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

    def _search_products(self, shop_id: str, query: str, limit: int = 5) -> List[Dict]:
        tokens = [t.strip() for t in query.lower().split() if len(t.strip()) >= 3]

        db_query = self.db.query(Product).filter(Product.shop_id == shop_id)
        if tokens:
            conditions = []
            for token in tokens[:6]:
                pattern = f"%{token}%"
                conditions.extend(
                    [
                        Product.name.ilike(pattern),
                        Product.description.ilike(pattern),
                        Product.category.ilike(pattern),
                    ]
                )
            db_query = db_query.filter(or_(*conditions))

        products = (
            db_query.order_by(Product.updated_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "name": p.name,
                "description": p.description or "",
                "price": p.price,
                "currency": p.currency,
                "category": p.category,
                "url": p.url,
            }
            for p in products
        ]
    
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
            .order_by(ChatMessage.created_at.desc())
            .limit(20)
            .all()
        )
        recent_history.reverse()

        relevant_products = self._search_products(shop_id=shop_id, query=user_message, limit=5)

        context = {
            "shop_id": shop_id,
            "session_id": session_id,
            "history": [{"role": m.role, "content": m.content} for m in recent_history],
            "products": relevant_products,
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
