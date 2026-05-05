import logging
import re
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.config import settings
from app.models.chat import ChatMessage, ChatSession
from app.models.product import Product
from app.models.shop import Shop
from app.rag.indexer import ProductIndexer
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
        self.indexer = ProductIndexer()
    
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

    def _search_products_sql(self, shop_id: str, query: str, limit: int = 5) -> List[Dict]:
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

    @staticmethod
    def _has_url(text: str) -> bool:
        return bool(re.search(r"https?://\S+", text or ""))

    def _build_product_links_block(self, products: List[Dict], limit: int = 3) -> str:
        with_links = [p for p in products if (p.get("url") or "").strip()][:limit]
        if not with_links:
            return ""

        lines = ["\n\nРекомендованные товары:"]
        for p in with_links:
            price = p.get("price")
            currency = p.get("currency") or "RUB"
            price_text = f"{price} {currency}" if price is not None else "цена не указана"
            lines.append(f"- {p.get('name')} ({price_text}): {p.get('url')}")
        return "\n".join(lines)

    def _ensure_links_in_reply(self, reply: str, products: List[Dict]) -> str:
        if not products:
            return reply
        if self._has_url(reply):
            return reply

        links_block = self._build_product_links_block(products)
        if not links_block:
            return reply
        return f"{reply.rstrip()}{links_block}"

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        cleaned = re.sub(r"[^\d+]", "", phone or "")
        if cleaned.startswith("8"):
            return "+7" + cleaned[1:]
        if cleaned.startswith("7"):
            return "+" + cleaned
        return cleaned

    @staticmethod
    def _mentions_manager(text: str) -> bool:
        return bool(re.search(r"менеджер|оператор|поддержк|консультант", (text or "").lower()))

    def _ensure_manager_phone(self, reply: str, manager_phone: str | None) -> str:
        if not manager_phone:
            return reply
        if not self._mentions_manager(reply):
            return reply
        if "tel:" in (reply or ""):
            return reply

        normalized = self._normalize_phone(manager_phone)
        if not normalized:
            return reply
        return f"{reply.rstrip()}\n\nТелефон менеджера: tel:{normalized}"

    async def _search_products(self, shop_id: str, query: str, limit: int = 5) -> List[Dict]:
        try:
            semantic_products = await self.indexer.search(query=query, shop_id=shop_id, limit=limit)
            if semantic_products:
                return semantic_products
        except Exception:
            logger.exception("Semantic search failed, fallback to SQL")

        return self._search_products_sql(shop_id=shop_id, query=query, limit=limit)
    
    async def process_message(self, shop_id: str, session_id: str, user_message: str) -> str:
        """
        Обработать сообщение пользователя и вернуть ответ
        """
        logger.info(f"Processing message from {shop_id}: {user_message}")

        shop = self.db.query(Shop).filter(Shop.shop_id == shop_id).first()
        manager_phone = shop.manager_phone if shop else None
        
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

        relevant_products = await self._search_products(
            shop_id=shop_id,
            query=user_message,
            limit=settings.RAG_TOP_K,
        )

        context = {
            "shop_id": shop_id,
            "session_id": session_id,
            "manager_phone": manager_phone,
            "history": [{"role": m.role, "content": m.content} for m in recent_history],
            "products": relevant_products,
        }

        assistant_message = await self.llm.generate_response(
            query=user_message,
            context=context,
        )
        assistant_message = self._ensure_links_in_reply(assistant_message, relevant_products)
        assistant_message = self._ensure_manager_phone(assistant_message, manager_phone)

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
