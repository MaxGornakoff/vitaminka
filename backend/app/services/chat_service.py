import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class ChatService:
    """
    Сервис для обработки чат-сообщений
    TODO: Интегрировать RAG и LLM
    """
    
    async def process_message(self, shop_id: str, session_id: str, user_message: str) -> str:
        """
        Обработать сообщение пользователя и вернуть ответ
        """
        logger.info(f"Processing message from {shop_id}: {user_message}")
        
        # TODO: 
        # 1. Получить контекст магазина
        # 2. Поиск релевантных товаров (RAG)
        # 3. Вызов LLM с контекстом
        # 4. Сохранить в историю
        
        # Placeholder ответ
        return f"Спасибо за вопрос: '{user_message}'. Я пока в разработке! 🚀"
    
    async def get_chat_history(self, session_id: str) -> List[Dict]:
        """
        Получить историю диалога
        """
        # TODO: Получить из БД
        return []
