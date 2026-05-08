# Vitaminka Assistant — Progress Log

> Последнее обновление: 08.05.2026

## Обновление 08.05.2026

- ✅ Убрали инструкцию из system prompt, из-за которой LLM сам добавлял телефон менеджера
- ✅ Убрали автодобавление товарных ссылок после негативного ответа по наличию
- ✅ Добавили intent `cutting` (сушка/жиросжигание) и фильтрацию явно нерелевантных товаров
- ✅ Убрали fallback-подмену негативного ответа на «да, есть варианты»
- ⏳ Не реализовано: автоматический сценарий «если у выбранного бренда нет товаров нужной тематики, сразу предложить эту же тематику из других брендов без дополнительного запроса пользователя»

### План на следующий спринт

1. Добавить двухэтапный поиск: сначала внутри активного бренда по intent, при пустом результате — повторный поиск по другим брендам с сохранением intent.
2. Формировать прозрачный ответ: «У {brand} по теме {intent} сейчас нет, но есть варианты у других брендов» + релевантные позиции.
3. Покрыть сценарий интеграционным тестом диалога (brand -> no items -> cross-brand suggestion).

## Архитектура

| Слой | Технология |
|------|-----------|
| Backend | Python 3.11 + FastAPI, порт 8000 |
| БД | PostgreSQL 16 (локально: Docker `vitaminka_db`; прод: Render managed) |
| LLM | Cohere `command-r-plus-08-2024` |
| Embeddings | Cohere `embed-multilingual-v3.0` |
| Vector store | ChromaDB (persistent `/var/data/chroma` на Render) |
| Admin | sqladmin 0.16.1 на `/admin` |
| Миграции | Alembic (текущая голова: `20260507_0008`) |
| Deploy | Render.com, Docker, auto-deploy при push в main |
| Widget | Vanilla JS Web Component, Shadow DOM |

**Production URL:** `https://vitaminka.onrender.com`  
**Admin:** login `admin` / `vitaminka-admin-2026`

---

## Встраивание виджета на сайт клиента

```html
<script>
  window.VITAMINKA_API_URL = 'https://vitaminka.onrender.com';
  window.VITAMINKA_SHOP_ID = 'your_shop_id';
</script>
<script src="https://vitaminka.onrender.com/static/widget.js"></script>
```

---

## Выполненные задачи

### Инфраструктура
- ✅ FastAPI backend + PostgreSQL + ChromaDB
- ✅ Docker + Render deploy (auto-deploy при push в main)
- ✅ Alembic миграции (0001–0008)
- ✅ sqladmin панель
- ✅ Каталог товаров из YML/XML фида (синхронизация)
- ✅ Semantic search через ChromaDB, fallback на SQL LIKE
- ✅ Widget.js раздаётся как статика из FastAPI `/static/widget.js`

### Виджет (frontend)
- ✅ Web Component с Shadow DOM (нет зависимостей)
- ✅ Лаунчер (круглая кнопка внизу справа)
- ✅ Pulse-анимация лаунчера через `::before` + `@keyframes pulseRing` (стабильно, не конфликтует с hover)
- ✅ Окно чата: шапка, список сообщений, поле ввода
- ✅ `.avatar-section` скрыта (`display: none`), Rive отключён
- ✅ Динамическая тема из API магазина (`THEME.blue`, `THEME.dark`, `THEME.bg`, `THEME.borderRadius`)
- ✅ Лаунчер перерисовывается после загрузки темы (тень и градиент актуальны)
- ✅ `hexToRgba()` — конвертация HEX в rgba для динамических теней
- ✅ Hover кнопки отправки использует `var(--vk-dark)` (цвет темы, не захардкожен)
- ✅ Greeting с именем ассистента из БД
- ✅ Форматирование сообщений: параграфы (`<p>`), списки товаров (`<ul class="vk-list">`)
- ✅ Телефоны в формате `8 (XXX) XXX-XX-XX` → `<a href="tel:+7...">` (regex)
- ✅ Ссылки `tel:+7...` → кликабельные
- ✅ Скролл к началу нового сообщения ассистента (не к концу)

### Кастомизация магазина (Admin + DB + API)
- ✅ Поля темы в БД: `widget_color_primary`, `widget_color_secondary`, `widget_color_bg`, `widget_border_radius`, `widget_custom_css`, `widget_currency_symbol`
- ✅ Admin-форма с русскими лейблами, плейсхолдерами, TextArea для CSS
- ✅ API `/api/shops/{shop_id}` возвращает `widget_theme` включая `currency_symbol`
- ✅ `currency_symbol` применяется при отображении цен в сообщениях

### Диалог и RAG (backend)
- ✅ Мультитёрновый контекст (история 12 последних реплик)
- ✅ Определение активного бренда (`active_vendor`) из текущей реплики и истории
- ✅ Бренд инжектируется в search query если найден в контексте
- ✅ Детектирование отказа от бренда («не обязательно», «другой бренд» и т.п.) → `active_vendor = None`
- ✅ Follow-up detection: короткие реплики и брендовые уточнения обогащаются предыдущим контекстом
- ✅ Брендовые уточнения («Есть что-то от X?») подтягивают intent из истории (напр., «набор массы»)
- ✅ Нормализация единиц объёма: `1кг → 1000 г`, `500г → 500 г`, `1л → 1000 мл`, `60кап → 60 капс` и т.п.
- ✅ Follow-up вопрос не повторяет уже указанную цель или объём
- ✅ Адаптивный follow-up: спрашивает только то, что ещё не указано (из цель/объём/вкус)
- ✅ Детектирование и замена fallback если LLM говорит «не нашёл» при наличии товаров
- ✅ LLM знает: гейнер/протеин = набор массы; понимает единицы объёма; предлагает ближайшую фасовку

---

## Workflow (деплой)

```powershell
# После правки widget.js:
Copy-Item frontend\widget\widget.js backend\static\widget.js -Force
node --check backend\static\widget.js
python -m py_compile backend\app\...

git add -A
git commit -m "..."
git push
# Render автодеплой ~7-10 минут
```

## Ключевые файлы

| Файл | Назначение |
|------|-----------|
| `frontend/widget/widget.js` | Исходник виджета (→ копируется в `backend/static/`) |
| `backend/app/services/chat_service.py` | Вся логика диалога, RAG, follow-up |
| `backend/app/rag/llm.py` | Cohere клиент, системный промпт |
| `backend/app/models/shop.py` | Модель магазина с полями темы |
| `backend/app/admin.py` | sqladmin конфигурация |
| `backend/app/api/shops.py` | REST API магазинов |
| `backend/alembic/versions/` | Миграции БД |
| `render.yaml` | Render deploy конфиг |

---

## TODO

- [ ] Rive-аватар отключён — нужна замена (SVG-анимация или Lottie)
- [ ] Нет механизма поиска «ближайшего объёма» на уровне SQL/vector (только через LLM-промпт)
- [ ] Аналитика диалогов (конверсии, популярные запросы)
- [ ] Многоязычность (сейчас только RU)
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
