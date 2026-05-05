import logging
from typing import Dict, List

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Клиент для работы с LLM (Cohere)
    """

    COHERE_API_URL = "https://api.cohere.ai/v1/chat"

    def __init__(self):
        self.provider = (settings.LLM_PROVIDER or "cohere").lower()

    def _build_system_prompt(self, shop_id: str) -> str:
        return (
            "Ты AI-консультант интернет-магазина. "
            "Отвечай вежливо, кратко и по делу на русском языке. "
            "Если данных недостаточно, честно скажи, что нужно уточнение. "
            f"Текущий магазин: {shop_id}."
        )

    async def _generate_cohere(self, query: str, context: Dict) -> str:
        if not settings.COHERE_API_KEY:
            logger.warning("Cohere API key is not configured")
            return "Я пока не настроен: добавьте COHERE_API_KEY в .env файл."

        system_prompt = self._build_system_prompt(context.get("shop_id", "unknown"))

        # Cohere v1 uses chat_history + message format
        history_items: List[Dict] = context.get("history", [])[-8:]
        chat_history = []
        for item in history_items:
            role = item.get("role", "user")
            text = item.get("content", "")
            if text:
                # Cohere v1 roles: USER / CHATBOT
                cohere_role = "CHATBOT" if role == "assistant" else "USER"
                chat_history.append({"role": cohere_role, "message": text})

        payload = {
            "model": settings.COHERE_MODEL,
            "message": query,
            "preamble": system_prompt,
            "chat_history": chat_history,
        }
        headers = {
            "Authorization": f"Bearer {settings.COHERE_API_KEY}",
            "Content-Type": "application/json",
        }

        timeout = httpx.Timeout(30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(self.COHERE_API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Cohere v1: data["text"]
        text = data.get("text", "").strip()
        if not text:
            logger.warning("Cohere returned no text")
            return "Не удалось получить ответ от модели. Попробуйте еще раз."
        return text

    async def generate_response(self, query: str, context: dict) -> str:
        """
        Сгенерировать ответ ассистента на основе вопроса и контекста

        Args:
            query: Вопрос пользователя
            context: Контекст (товары, история диалога и т.д.)

        Returns:
            Ответ ассистента
        """
        logger.info(f"Generating response for query: {query}")

        try:
            if self.provider == "cohere":
                return await self._generate_cohere(query=query, context=context)

            logger.warning("Unsupported LLM_PROVIDER '%s', fallback to cohere", self.provider)
            return await self._generate_cohere(query=query, context=context)
        except Exception:
            logger.exception("LLM generation failed")
            return "Сейчас не удалось получить ответ от AI. Попробуйте еще раз чуть позже."
