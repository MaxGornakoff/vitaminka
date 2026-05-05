# Vitaminka — статус проекта

## Стек
- Python 3.11 + FastAPI 0.104.1
- PostgreSQL 16 + SQLAlchemy 2.0 + Alembic
- Redis 7 (настроен, не используется активно)
- Docker Compose (db + redis + backend на порту 8000)
- **LLM: Cohere `command-r-plus-08-2024`** через `api.cohere.ai/v1/chat`

## Ключевые файлы
| Файл | Назначение |
|------|-----------|
| `backend/app/rag/llm.py` | LLM клиент (Cohere v1, preamble + chat_history) |
| `backend/app/core/config.py` | Настройки: COHERE_API_KEY, COHERE_MODEL, LLM_PROVIDER |
| `backend/app/services/chat_service.py` | Бизнес-логика: сессии, история, вызов LLM |
| `backend/app/api/chat.py` | POST /api/chat/message, GET /api/chat/history/{session_id} |
| `backend/app/api/shops.py` | POST/GET /api/shops |
| `backend/alembic/` | Миграции, таблицы: shops, chat_sessions, chat_messages, products |
| `backend/.env` | Реальные ключи (не в git) |
| `frontend/widget/widget.js` | Web Component `<vitaminka-widget>`, TTS удалён |
| `frontend/demo-standalone.html` | Standalone демо без backend |

## Готово ✅
- Docker Compose, все контейнеры работают
- FastAPI + health endpoint
- SQLAlchemy модели + Alembic миграции применены
- PostgreSQL persistence: чаты, сессии, магазины
- TTS/voice удалён из frontend
- Cohere LLM интеграция работает — отвечает на русском

## Осталось ⏳
1. **RAG** — загрузка каталога товаров + поиск перед LLM вызовом
2. **POST /api/shops/{shop_id}/catalog** — endpoint загрузки каталога
3. **ChromaDB** для векторного поиска по товарам
4. **API key аутентификация** для владельцев магазинов
5. **Деплой на Render.com**

## Важные нюансы
- GigaChat и Groq недоступны без РФ IP — используем Cohere
- Cohere: старое имя `command-r-plus` удалено в 2025, актуальное — `command-r-plus-08-2024`
- Cohere API URL: `https://api.cohere.ai/v1/chat` (v2/chat даёт 404 на trial-ключах)
- `.env` не в git, хранится только локально
