# Render.com Deploy Configuration

Файл `render.yaml` в корне уже готов для Blueprint Deploy.

## Что создается через Blueprint

- Web Service: `vitaminka-backend`
- PostgreSQL: `vitaminka-db`
- Persistent Disk: `chroma-data` (mount `/var/data`)

## Команды

Build:
```bash
pip install -r backend/requirements.txt
```

Start:
```bash
cd backend && alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Обязательные переменные окружения (добавить в Web Service)

```bash
COHERE_API_KEY=your-cohere-key
SECRET_KEY=your-strong-secret
ADMIN_SECRET=your-admin-secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
ALLOWED_ORIGINS=https://your-frontend-domain.com
```

`DATABASE_URL` подтягивается автоматически из `fromDatabase` в `render.yaml`.

## ChromaDB persistence

- `CHROMA_PERSIST_DIR=/var/data/chroma`
- Диск уже описан в `render.yaml`.

Это сохраняет индекс между рестартами/деплоями.

## Деплой шаги

1. Push в GitHub с `render.yaml`.
2. В Render: `New +` -> `Blueprint` -> выбрать репозиторий.
3. После создания сервисов добавить секреты из блока выше.
4. Нажать `Manual Deploy` (или дождаться автодеплоя).
5. Проверить:
	- `GET /api/health`
	- `GET /admin`
	- `POST /api/chat/message`

## Важно

- Первый старт может быть дольше из-за `alembic upgrade head`.
- Если каталог большой, первичная индексация в Chroma также займет время.
