#!/bin/bash

# Инициализация проекта

echo "🚀 Инициализация проекта Vitaminka Assistant..."

# Копируем .env файл если его нет
if [ ! -f backend/.env ]; then
  echo "📝 Копирую backend/.env.example → backend/.env"
  cp backend/.env.example backend/.env
fi

# Запускаем docker-compose
echo "🐳 Запускаю Docker контейнеры..."
docker-compose up -d

echo "✅ Проект инициализирован!"
echo ""
echo "📍 API доступен на: http://localhost:8000"
echo "📚 Swagger docs: http://localhost:8000/docs"
echo ""
echo "Чтобы посмотреть логи: docker-compose logs -f backend"
