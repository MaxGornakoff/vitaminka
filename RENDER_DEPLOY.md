# Render.com Deploy Configuration

# Этот файл содержит инструкции для деплоя на Render

## Переменные окружения, которые нужно установить в Render:

```
DATABASE_URL=postgresql://user:password@host/dbname
REDIS_URL=redis://default:password@host:port
OPENAI_API_KEY=sk-your-api-key
ALLOWED_ORIGINS=https://your-domain.com,https://widget.your-domain.com
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your-random-secret-key
```

## Build Command (указать в Render):
```bash
pip install -r backend/requirements.txt
```

## Start Command:
```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## PostgreSQL сервис:
- Создайте PostgreSQL инстанс в Render
- Получите `DATABASE_URL` из переменных окружения Render
- Добавьте эту URL в Web Service

## Redis сервис:
- Создайте Redis инстанс в Render
- Получите `REDIS_URL` из переменных окружения Render
- Добавьте в Web Service

## Автоматический деплой:
1. Подключите GitHub репозиторий к Render
2. Установите webhook для автоматического деплоя при push в main
3. При каждом commit в main ветку будет автоматический деплой

## Health Check:
Render будет автоматически проверять `/api/health` endpoint
