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

    @staticmethod
    def _build_llm_history(messages: List[ChatMessage], current_query: str, max_items: int = 12) -> List[Dict]:
        """
        Подготовить историю для LLM: только предыдущие реплики без дублирования текущего запроса.
        """
        history: List[Dict] = []
        trimmed_query = (current_query or "").strip()

        for m in messages:
            role = (m.role or "").strip().lower()
            content = (m.content or "").strip()
            if role not in {"user", "assistant"} or not content:
                continue
            history.append({"role": role, "content": content})

        # process_message уже сохраняет текущее сообщение в БД до генерации,
        # поэтому удаляем его из истории, чтобы не дублировать с message=query.
        if history and history[-1]["role"] == "user" and history[-1]["content"] == trimmed_query:
            history.pop()

        if max_items > 0:
            return history[-max_items:]
        return history

    @staticmethod
    def _looks_like_followup_query(query: str) -> bool:
        text = (query or "").lower()
        if not text:
            return False

        # Короткие уточнения обычно требуют контекста предыдущего вопроса.
        followup_markers = [
            "подешев",
            "дороже",
            "лучше",
            "из них",
            "из этого",
            "а что",
            "а какой",
            "какой из",
            "что из",
            "этот",
            "эта",
            "эти",
            "их",
            # Отказ от конкретного бренда — нужен контекст продукта из предыдущей реплики
            "другие бренды",
            "другой бренд",
            "другие марки",
            "другой марки",
            "не обязательно",
            "необязательно",
            "любого бренда",
            "любой бренд",
            "не только от",
            "не от ",
        ]
        if any(marker in text for marker in followup_markers):
            return True

        return len(text.split()) <= 4

    @staticmethod
    def _build_search_query(user_message: str, history: List[Dict], active_vendor: str | None = None) -> str:
        query = (user_message or "").strip()
        if not query:
            return query

        if ChatService._looks_like_followup_query(query):
            # Для уточняющих реплик обогащаем запрос темой предыдущего сообщения пользователя.
            prev_user_message = ""
            for item in reversed(history):
                if (item.get("role") or "") == "user":
                    prev_user_message = (item.get("content") or "").strip()
                    if prev_user_message:
                        break

            if prev_user_message:
                query = f"{prev_user_message}. Уточнение: {query}"

        # Всегда добавляем активный бренд, если он обнаружен в контексте диалога
        # и ещё не упомянут в запросе — так поиск находит товары именно этого бренда.
        if active_vendor and active_vendor.lower() not in query.lower():
            query = f"{query}. Бренд: {active_vendor}"

        return query

    def _find_vendor_in_text(self, shop_id: str, text: str) -> str | None:
        source = (text or "").lower()
        if not source:
            return None

        vendor_rows = (
            self.db.query(Product.vendor)
            .filter(
                Product.shop_id == shop_id,
                Product.vendor.isnot(None),
                Product.vendor != "",
            )
            .distinct()
            .all()
        )

        vendors = [row[0].strip() for row in vendor_rows if row and row[0] and row[0].strip()]
        if not vendors:
            return None

        # Берем самый длинный матч, чтобы корректно ловить бренды из 2-3 слов.
        vendors.sort(key=len, reverse=True)
        for vendor in vendors:
            if vendor.lower() in source:
                return vendor
        return None

    def _detect_active_vendor(self, shop_id: str, user_message: str, history: List[Dict]) -> str | None:
        current_vendor = self._find_vendor_in_text(shop_id=shop_id, text=user_message)
        if current_vendor:
            return current_vendor

        for item in reversed(history):
            content = (item.get("content") or "").strip()
            if not content:
                continue
            vendor = self._find_vendor_in_text(shop_id=shop_id, text=content)
            if vendor:
                return vendor

        return None

    @staticmethod
    def _user_rejects_vendor(user_message: str) -> bool:
        """Returns True when the user explicitly asks to not filter by the current brand."""
        text = (user_message or "").lower()
        rejection_phrases = [
            "не обязательно",
            "необязательно",
            "не только от",
            "не только",
            "любого бренда",
            "любой бренд",
            "другие бренды",
            "другой бренд",
            "не от",
            "любую марку",
            "любой марки",
        ]
        return any(phrase in text for phrase in rejection_phrases)

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
                        Product.vendor.ilike(pattern),
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
                "vendor": p.vendor or "",
                "description": p.description or "",
                "price": p.price,
                "currency": p.currency,
                "category": p.category,
                "url": p.url,
            }
            for p in products
        ]

    @staticmethod
    def _is_llm_error_reply(reply: str) -> bool:
        text = (reply or "").lower()
        return (
            "сейчас не удалось получить ответ от ai" in text
            or "попробуйте еще раз чуть позже" in text
        )

    @staticmethod
    def _is_negative_availability_reply(reply: str) -> bool:
        text = (reply or "").lower()
        negative_markers = [
            "нет товара",
            "нет в магазине",
            "к сожалению, в текущем магазине нет",
            "такого товара у нас нет",
            "данного товара нет",
            "не нашла подходящих товаров",
            "не нашел подходящих товаров",
            "не нашёл подходящих товаров",
            "нет подходящих товаров",
            "не удалось найти подходящих",
            "не смогла найти подходящих",
            "не смог найти подходящих",
            "к сожалению, не нашла",
            "к сожалению, не нашел",
            "к сожалению, не нашёл",
        ]
        return any(marker in text for marker in negative_markers)

    @staticmethod
    def _extract_brand_from_query(query: str) -> str | None:
        q = (query or "").strip()
        if not q:
            return None

        match = re.search(r"(?:бренд[а]?|от)\s+([A-Za-zА-Яа-я0-9\-\+\. ]{2,40})", q, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip(" ?!,.\"'")

        upper_tokens = re.findall(r"\b[A-Z][A-Z0-9\-\+\.]{1,}\b", q)
        if upper_tokens:
            return upper_tokens[0]

        return None

    @staticmethod
    def _pick_variant(seed_text: str, variants: List[str]) -> str:
        if not variants:
            return ""
        seed = sum(ord(ch) for ch in (seed_text or ""))
        return variants[seed % len(variants)]

    def _build_products_fallback_reply(self, user_message: str, products: List[Dict]) -> str:
        if not products:
            return "Не нашел подходящих товаров в каталоге по этому запросу. Уточните, пожалуйста, бренд, форму или цель приема."

        brand = self._extract_brand_from_query(user_message)
        if brand:
            brand_l = brand.lower()
            matched = [
                p
                for p in products
                if brand_l in (p.get("vendor") or "").lower() or brand_l in (p.get("name") or "").lower()
            ]
            if matched:
                brand_openers = [
                    "Да, товары бренда {brand} есть в наличии.",
                    "Да, у нас доступны позиции от {brand}.",
                    "Да, по бренду {brand} есть подходящие варианты.",
                    "Отличный выбор: товары {brand} сейчас есть в каталоге.",
                ]
                opener = self._pick_variant(user_message, brand_openers).format(brand=brand)
                followup = self._build_followup_question(user_message, matched)
                return f"{opener} {followup}"

        generic_openers = [
            "Да, подходящие варианты есть!",
            "Есть несколько подходящих позиций.",
            "Нашёл кое-что подходящее.",
            "В каталоге есть хорошие варианты.",
        ]
        opener = self._pick_variant(user_message, generic_openers)
        followup = self._build_followup_question(user_message, products)
        return f"{opener} {followup}"

    @staticmethod
    def _detect_query_intent(user_message: str) -> str:
        text = (user_message or "").lower()
        if re.search(r"протеин|whey|гейнер|изолят|казеин", text):
            return "protein"
        if re.search(r"омега|omega|рыбий жир", text):
            return "omega"
        if re.search(r"бад|добавк|витамин|минерал|магний|цинк|d3|b-?complex|5-htp", text):
            return "supplements"
        return "generic"

    @staticmethod
    def _detect_products_intent(products: List[Dict]) -> str:
        """Infer intent from top products when user query is too generic."""
        if not products:
            return "generic"

        corpus_parts: List[str] = []
        for p in products[:5]:
            corpus_parts.append((p.get("category") or "").lower())
            corpus_parts.append((p.get("name") or "").lower())
            corpus_parts.append((p.get("description") or "").lower())
        corpus = " ".join(corpus_parts)

        if re.search(r"протеин|whey|гейнер|изолят|казеин", corpus):
            return "protein"
        if re.search(r"омега|omega|рыбий жир", corpus):
            return "omega"
        if re.search(r"бад|добавк|витамин|минерал|магний|цинк|аминокислот|5-htp|tryptophan|enzym", corpus):
            return "supplements"
        return "generic"

    @staticmethod
    def _build_followup_question(user_message: str, products: List[Dict]) -> str:
        intent = ChatService._detect_query_intent(user_message)
        if intent == "generic":
            intent = ChatService._detect_products_intent(products)

        already_has_goal = bool(
            re.search(
                r"набор|набрат|набрать|мышечн|массы|массу|восстановлен|поддержан",
                (user_message or "").lower(),
            )
        )

        if intent == "protein":
            if already_has_goal:
                return "Подскажите, пожалуйста, какой вкус и объем вам подходят?"
            return "Подскажите, пожалуйста, какой вкус, объем и цель приема вам подходят (набор массы, поддержание или восстановление)?"
        if intent == "omega":
            return "Уточните, пожалуйста, какой процент EPA/DHA и формат вам удобнее: 60%, 70% или 90%, и какое количество капсул?"
        if intent == "supplements":
            return "Уточните, пожалуйста, цель приема и предпочтения по форме (капсулы/таблетки), а также желаемую дозировку?"
        return "Подскажите, пожалуйста, для какой цели подбираем товар и какой у вас ориентир по бюджету?"

    @staticmethod
    def _has_question(text: str) -> bool:
        return "?" in (text or "")

    def _ensure_followup_question(self, reply: str, user_message: str, products: List[Dict]) -> str:
        if not products:
            return reply
        if self._has_question(reply):
            return reply
        followup = self._build_followup_question(user_message, products)
        return f"{reply.rstrip()}\n\n{followup}"

    @staticmethod
    def _has_url(text: str) -> bool:
        return bool(re.search(r"https?://\S+", text or ""))

    def _build_product_links_block(self, products: List[Dict], limit: int = 3, currency_symbol: str | None = None) -> str:
        with_links = [p for p in products if (p.get("url") or "").strip()][:limit]
        if not with_links:
            return ""

        lines = ["\n\nРекомендованные товары:"]
        for p in with_links:
            price = p.get("price")
            currency = currency_symbol or p.get("currency") or "RUB"
            price_text = f"{price} {currency}" if price is not None else "цена не указана"
            lines.append(f"- {p.get('name')} ({price_text}): {p.get('url')}")
        return "\n".join(lines)

    def _ensure_links_in_reply(self, reply: str, products: List[Dict], currency_symbol: str | None = None) -> str:
        if not products:
            return reply
        if self._has_url(reply):
            return reply

        links_block = self._build_product_links_block(products, currency_symbol=currency_symbol)
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
        currency_symbol = shop.widget_currency_symbol if shop else None
        
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
            .limit(30)
            .all()
        )
        recent_history.reverse()
        llm_history = self._build_llm_history(recent_history, user_message, max_items=12)
        active_vendor = self._detect_active_vendor(shop_id=shop_id, user_message=user_message, history=llm_history)
        if active_vendor and self._user_rejects_vendor(user_message):
            active_vendor = None
        search_query = self._build_search_query(user_message, llm_history, active_vendor=active_vendor)

        relevant_products = await self._search_products(
            shop_id=shop_id,
            query=search_query,
            limit=settings.RAG_TOP_K,
        )

        context = {
            "shop_id": shop_id,
            "session_id": session_id,
            "manager_phone": manager_phone,
            "history": llm_history,
            "products": relevant_products,
        }

        assistant_message = await self.llm.generate_response(
            query=user_message,
            context=context,
        )

        if relevant_products and (
            self._is_llm_error_reply(assistant_message)
            or self._is_negative_availability_reply(assistant_message)
        ):
            assistant_message = self._build_products_fallback_reply(user_message, relevant_products)

        assistant_message = self._ensure_followup_question(assistant_message, user_message, relevant_products)
        assistant_message = self._ensure_links_in_reply(assistant_message, relevant_products, currency_symbol=currency_symbol)
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
