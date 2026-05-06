# Vitaminka — статус проекта

## Текущее состояние системы (06.05.2026)

| Компонент | Статус |
|---|---|
| Backend (FastAPI) | ✅ Порт 8000, hot-reload |
| PostgreSQL | ✅ 792 товара `test_vitaminof`, vendor в БД |
| ChromaDB (локально) | ✅ 797 документов, vendor в метадате |
| ChromaDB (Render) | ⏳ Пустая — нужна индексация на проде |
| Cohere embeddings | ✅ `embed-multilingual-v3.0`, батчи по 96 + пауза 65с |
| Cohere LLM | ✅ `command-r-plus-08-2024`, timeout 12s + fallback |
| Admin-панель | ✅ `/admin` — синхронизация + проверка ассистента |
| Frontend demo | ✅ `test_vitaminof` |
| Render.com | ✅ Задеплоен: https://vitaminka.onrender.com |
| Контекст диалога | ✅ Multi-turn, follow-up с query rewrite |

---

## Сделано в сессии 06.05.2026

- **Контекст диалога**: история предыдущих реплик передается в Cohere без дублирования текущего вопроса
- **Query rewrite для follow-up**: короткие вопросы ("а что подешевле?") обогащаются предыдущим user-сообщением — поиск держит тему разговора
- **Деплой на Render**: https://vitaminka.onrender.com
  - Docker runtime, persistent disk для Chroma (`/var/data`)
  - `start.sh` — автоматически применяет миграции перед стартом
  - `render.yaml` — Blueprint для воспроизводимого деплоя
  - CORS, env vars настроены
- **Smoke test на проде**: health ✅, chat ✅, multi-turn контекст ✅
- **CORS**: переведен на `settings.allowed_origins_list` вместо `"*"` в коде
- **Release SOP**: добавлен в README как ultra-short чеклист

---

## Следующая сессия: что делать

1. **Проиндексировать каталог на Render** — зайти в `/admin` на продакшене, запустить синхронизацию для `test_vitaminof`. После этого семантический поиск Chroma заработает на проде.
2. **Зарегистрировать магазин vitaminof.ru на проде** через `/api/shops/register` или через `/admin`.
3. **Протестировать виджет на реальном сайте** — вставить `<script>` на vitaminof.ru и проверить полный сценарий.
4. **Заменить `ALLOWED_ORIGINS=*`** на реальный домен после подключения виджета к сайту.

---

## Идеи на следующую сессию

- Исправлен парсер фида: поддержка XML/YML (Яндекс.Маркет), поле `<vendor>` передаётся в БД, ChromaDB и LLM
- Добавлены миграции 0005 (sync/index timestamps) и 0006 (vendor)
- Исправлены Cohere 429: батчинг + пауза между батчами; graceful degradation при сбоях
- 792 товара проиндексированы для `test_vitaminof`
- Admin-панель: кнопка синхронизации + тест-форма ассистента
- LLM промпт: явно указывает что товары ЕСТЬ, показывает бренд отдельно
- Fallback: если LLM упал или отрицает наличие при найденных товарах — сервис формирует корректный ответ сам
- «Умный» follow-up: тип вопроса (протеин/омега/БАД/общий) определяется по запросу И по категориям найденных товаров
- `demo-standalone.html` переключён с `demo_shop` на `test_vitaminof`

---

## Идеи на следующую сессию

1. **Расширить follow-up шаблоны** — добавить категории: жиросжигатели, аминокислоты, пробиотики, предтреники. Определять тип точнее через поле `category` из Chroma метадаты, а не только через regex по тексту запроса.

2. **Персонализация в рамках сессии** — хранить в контексте диалога явно заявленные цели пользователя (набор массы, похудение, ЖКТ и т.п.) и учитывать их в следующих рекомендациях, не переспрашивая каждый раз.

3. **Устойчивость к опечаткам** — пользователи пишут «протеиин», «омеrа», «NOW Фудс» и т.п. Варианты: нечёткий поиск (fuzzy) через `rapidfuzz` перед SQL/Chroma запросом, или передавать запрос через Cohere embed «как есть» (семантика уже помогает), но добавить pre-processing с транслитерацией и исправлением типичных опечаток в названиях брендов.

4. **Удержание контекста в диалоге** — сейчас история передаётся в LLM (20 сообщений), но `relevant_products` каждый раз ищутся только по последнему сообщению. Нужно накапливать «стейт сессии»: запомненный бренд, категория, цель, бюджет — и подмешивать их в поисковый запрос к Chroma при следующих репликах. Например, если пользователь сказал «нужен протеин от Optimum Nutrition», а потом спросил «что дешевле?» — ассистент должен понимать, что речь всё ещё про протеин Optimum Nutrition.

5. **Деплой на Render.com** — переменные окружения, персистентность ChromaDB volume, автозапуск `alembic upgrade head` при старте.

---

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
