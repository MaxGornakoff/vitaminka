# Git workflow

## Ветки

- `main` — прод. Render деплоит автоматически при каждом пуше сюда.
- `staging` — рабочая ветка для локальной разработки и тестирования.

## Обычный рабочий процесс

1. Убедись, что ты на `staging`:
   ```
   git branch --show-current
   ```
2. Вноси правки, проверяй локально.
3. Пуш в `staging` (прод не трогается):
   ```
   git add -A
   git commit -m "описание изменений"
   git push
   ```

## Когда всё проверено — выкатить на прод

```
git checkout main
git merge staging
git push
git checkout staging
```

## Локальный стек

Запустить:
```
docker compose up -d
```

Обновить backend после правок в Python:
```
docker compose up -d --force-recreate backend
```

Применить миграции БД:
```
docker compose exec backend alembic upgrade head
```

## Демо-страница

Открывай локально: `frontend/demo-standalone.html`
Виджет загружается с `http://localhost:8000/static/widget.js`.

После правок в `frontend/widget/widget.js` скопируй файл и перезагрузи страницу:
```
Copy-Item frontend\widget\widget.js backend\static\widget.js -Force
```
