# Vitaminka Assistant — Универсальный AI-ассистент для интернет-магазинов

## Описание

Vitaminka Assistant — это независимый от платформы виджет с искусственным интеллектом, который помогает покупателям консультироваться о товарах на сайтах интернет-магазинов. Ассистент использует RAG (Retrieval-Augmented Generation) для предоставления персонализированных рекомендаций на основе каталога товаров магазина.

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
- **Web Speech API** — синтез речи на русском языке (вкл/выкл)

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

**Звук:** Синтез речи включен по умолчанию, пользователь может отключить кнопкой 🔊/🔇

## Анимированный персонаж (Rive)

Виджет включает интерактивного персонажа, который меняет свою анимацию в зависимости от состояния диалога:

- **Idle** 😴 — ожидание, фоновая анимация
- **Listening** 👂 — пользователь пишет сообщение
- **Thinking** 🤔 — ассистент обрабатывает запрос
- **Speaking** 💬 — ассистент отвечает, синхронизировано с синтезом речи

**Настройка персонажа:** см. [RIVE_SETUP.md](frontend/RIVE_SETUP.md)

### Синтез речи (Text-to-Speech)

- ✅ Поддерживаемые браузеры: Chrome, Firefox, Safari, Edge
- 🇷🇺 Язык: Русский
- 🔕 Пользователь может отключить звук
- 🚀 Встроено в виджет, без дополнительных API

Для лучшего качества голоса можно подключить Google Cloud TTS или Azure Speech Services.

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
- [x] Web Speech API синтез речи (вкл/выкл)
- [ ] Интеграция ChromaDB RAG
- [ ] Настройка OpenAI GPT-4 интеграции
- [ ] WebSocket для real-time чата
- [ ] Миграции БД (Alembic)
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

## Лицензия

MIT

## Контакты

Если у вас есть вопросы, создайте Issue в GitHub репозитории.
