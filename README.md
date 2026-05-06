# Vitaminka Assistant — Универсальный AI-ассистент для интернет-магазинов

## Описание

Vitaminka Assistant — это независимый от платформы виджет с искусственным интеллектом, который помогает покупателям консультироваться о товарах на сайтах интернет-магазинов. Ассистент использует RAG (Retrieval-Augmented Generation) для предоставления персонализированных рекомендаций на основе каталога товаров магазина.

## Статус На 29.04.2026 И План На 30.04.2026

### Что Сделано Сегодня
- Удален голос (TTS) из виджета и standalone-демо, оставлен текстовый режим
- Подключены Alembic миграции и создана initial schema
- Выполнена миграция БД в контейнере backend (`alembic upgrade head`)
- Подключена персистентность чата в PostgreSQL:
   - создание/поиск сессии
   - сохранение user/assistant сообщений
   - выдача истории диалога из БД
- Подключена регистрация и чтение магазинов из PostgreSQL
- Пройден smoke test API (`/api/shops/register`, `/api/chat/message`, `/api/chat/history/{session_id}`)

### План На Завтра (Приоритет)
1. Подключить реальный OpenAI вызов в `backend/app/rag/llm.py`
2. Интегрировать LLM в `backend/app/services/chat_service.py` вместо заглушки
3. Подключить RAG-поиск товаров в `backend/app/rag/indexer.py` и подмешивать контекст в ответ
4. Добавить базовые проверки качества: обработка ошибок OpenAI, таймауты, fallback-ответ
5. Добавить минимальные автотесты на happy path чата и историю

## Стек технологий

### Backend
- **Python 3.11+** + **FastAPI** — асинхронный REST API
- **PostgreSQL** — хранение данных о магазинах, чатах, товарах
- **Redis** — кеширование сессий, rate limiting
- **LangChain** + **ChromaDB** — RAG для поиска товаров
- **OpenAI GPT-4** — генерация ответов

### Frontend
- **Vanilla JavaScript** + **Web Components** — универсальный виджет
- **Shadow DOM** — изоляция стилей
- **Rive** — анимированный персонаж с состояниями (idle, listening, thinking, speaking)
- **Text-only режим** — голос временно отключен, можно вернуть как опциональную функцию

### DevOps
- **Docker** + **Docker Compose** — локальная разработка
- **Render** — production деплой

## Структура проекта

```
vitaminka/
├── backend/                 # Python FastAPI приложение
│   ├── app/
│   │   ├── api/            # REST endpoints
│   │   ├── core/           # Конфиги, настройки
│   │   ├── db/             # Работа с БД
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── services/       # Бизнес-логика
│   │   ├── rag/            # RAG пайплайн, LLM
│   │   └── main.py         # Entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   └── widget/
│       └── widget.js       # Web Component виджета
├── docker-compose.yml      # Docker Compose конфиг
└── README.md
```

## Быстрый старт (локальная разработка)

### Требования
- Docker & Docker Compose
- Или: Python 3.11+, PostgreSQL, Redis

### Установка через Docker

1. **Клонируйте репозиторий:**
   ```bash
   git clone https://github.com/yourusername/vitaminka
   cd vitaminka
   ```

2. **Скопируйте .env файл:**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Отредактируйте `backend/.env` (добавьте OpenAI API ключ):**
   ```env
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

4. **Запустите контейнеры:**
   ```bash
   docker-compose up -d
   ```

5. **Проверьте статус:**
   ```bash
   # API должен быть доступен на http://localhost:8000
   curl http://localhost:8000/api/health
   ```

6. **Откройте в браузере:**
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Без Docker (локально)

1. **Установите зависимости:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # или `venv\Scripts\activate` на Windows
   pip install -r backend/requirements.txt
   ```

2. **Создайте базы данных:**
   ```bash
   # PostgreSQL и Redis должны быть установлены
   createdb vitaminka_db
   ```

3. **Запустите FastAPI:**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

## Использование виджета на магазине

Добавьте одну строку кода перед закрытием `</body>` тега:

```html
<script>
  window.VITAMINKA_API_URL = 'https://your-api-domain.com';
  window.VITAMINKA_SHOP_ID = 'your_unique_shop_id';
  window.VITAMINKA_RIVE_FILE = 'https://your-cdn.com/character.riv'; // Путь к Rive персонажу
</script>
<script src="https://your-api-domain.com/widget.js"></script>
```

**Опции:**
- `VITAMINKA_API_URL` — URL вашего API (обязательно)
- `VITAMINKA_SHOP_ID` — уникальный ID магазина (обязательно)
- `VITAMINKA_RIVE_FILE` — путь к `.riv` файлу персонажа (опционально, есть fallback)

**Звук:** Сейчас отключен в текущей версии (можно вернуть позже как feature toggle).

## Анимированный персонаж (Rive)

Виджет включает интерактивного персонажа, который меняет свою анимацию в зависимости от состояния диалога:

- **Idle** 😴 — ожидание, фоновая анимация
- **Listening** 👂 — пользователь пишет сообщение
- **Thinking** 🤔 — ассистент обрабатывает запрос
- **Speaking** 💬 — ассистент показывает фазу ответа (без озвучивания)

**Настройка персонажа:** см. [RIVE_SETUP.md](frontend/RIVE_SETUP.md)

### Синтез речи (Text-to-Speech)

Голос временно отключен, текущий фокус разработки — стабильный backend, RAG и LLM.
TTS можно вернуть позже как отдельный опциональный модуль.

## API Endpoints

### Chat
- `POST /api/chat/message` — Отправить сообщение
- `GET /api/chat/history/{session_id}` — Получить историю

### Shops
- `POST /api/shops/register` — Зарегистрировать магазин
- `GET /api/shops/{shop_id}` — Получить информацию о магазине

### Health
- `GET /api/health` — Проверка статуса API

## Roadmap

- [x] Rive персонаж с состояниями (idle, listening, thinking, speaking)
- [x] Голос временно отключен (решение для фокуса на core backend)
- [ ] Интеграция ChromaDB RAG
- [ ] Настройка OpenAI GPT-4 интеграции
- [ ] WebSocket для real-time чата
- [x] Миграции БД (Alembic)
- [x] Персистентность чата и магазинов в PostgreSQL
- [ ] Плагины для Shopify, WooCommerce
- [ ] Admin dashboard
- [ ] Аналитика диалогов
- [ ] Lip-sync синхронизация
- [ ] Multiple characters

## Деплой на Render

1. Создайте аккаунт на [render.com](https://render.com)
2. Создайте PostgreSQL инстанс
3. Создайте Web Service, подключённый к GitHub репозиторию
4. Установите переменные окружения (особенно `OPENAI_API_KEY`)
5. Дождитесь автоматического деплоя

### Release SOP (Ultra-Short)

Перед push:
1. `git status` без мусора и временных правок.
2. Локальный smoke: 1 обычный chat + 1 follow-up в той же сессии.
3. Если меняли схему, проверить миграции и локально выполнить `alembic upgrade head`.

После deploy:
1. Проверить `GET /api/health` и логи старта без traceback.
2. Проверить `/admin` и один реальный chat-сценарий с контекстом.
3. При критичной ошибке: откат на предыдущий стабильный commit и redeploy.

## Лицензия

MIT

## Контакты

Если у вас есть вопросы, создайте Issue в GitHub репозитории.
