# Интеграция Rive для анимированного персонажа

## Что такое Rive?

Rive — это платформа для создания интерактивных векторных анимаций. Для нашего виджета используется Rive Runtime, который позволяет воспроизводить `.riv` файлы в браузере.

**Сайт:** https://rive.app

---

## Быстрый старт

### 1. Получить Rive файл

Есть несколько способов:

#### Вариант A: Использовать готовую анимацию (бесплатно)

1. Перейти на https://rive.app/community
2. Скачать бесплатную анимацию (например, `character.riv`)
3. Загрузить на свой CDN или использовать публичный URL

#### Вариант B: Создать свой персонаж

1. Регистрация на https://rive.app
2. Создать новый проект
3. Нарисовать персонажа или импортировать SVG
4. Добавить анимации (idle, listening, thinking, speaking)
5. Экспортировать как `.riv` файл

#### Вариант C: Использовать готовый (быстро)

```
https://cdn.rive.app/animations/vehicle.riv  # Пример (машина)
```

### 2. Загрузить Rive в виджет

При подключении виджета к сайту магазина:

```html
<script>
  window.VITAMINKA_API_URL = 'https://your-api-domain.com';
  window.VITAMINKA_SHOP_ID = 'your_shop_id';
  
  // Указываем путь к Rive файлу
  window.VITAMINKA_RIVE_FILE = 'https://your-cdn.com/your-character.riv';
</script>
<script src="https://your-api-domain.com/widget.js"></script>
```

---

## Состояния персонажа

Виджет автоматически переключает состояния персонажа:

| Состояние | Когда | Значение |
|-----------|-------|---------|
| **idle** | По умолчанию | 0 |
| **listening** | Пользователь пишет, персонаж слушает | 1 |
| **thinking** | Ассистент обрабатывает запрос | 2 |
| **speaking** | Ассистент отвечает | 3 |

Для этого в вашем Rive файле должна быть **State Machine** с входом `state` (0-3).

---

## Создание Rive персонажа с состояниями

### В Rive Editor:

1. **Создать State Machine:**
   - Нажать `+` → `State Machine`
   - Назвать `State Machine 1`

2. **Добавить входной параметр:**
   - `Input` → `Number` → назвать `state`

3. **Создать состояния:**
   - `Entry` → `Idle` (состояние 0)
   - `Listening` (состояние 1)
   - `Thinking` (состояние 2)
   - `Speaking` (состояние 3)

4. **Добавить анимации:**
   - Для каждого состояния добавить соответствующую анимацию

5. **Настроить переходы:**
   ```
   Idle →(state=1)→ Listening
   Listening →(state=2)→ Thinking
   Thinking →(state=3)→ Speaking
   Speaking →(state=0)→ Idle
   ```

---

## Синтез речи (Text-to-Speech)

### Как работает:

1. **Кнопка звука в виджете** — включение/отключение
2. **Web Speech API** — браузерный синтез речи (бесплатно)
3. **Язык:** Русский (ru-RU)

### Поддержка браузерами:

- ✅ Chrome/Edge/Opera
- ✅ Firefox
- ✅ Safari
- ⚠️ IE (не поддерживается)

### Отключение звука:

```javascript
// Звук отключен по умолчанию для определённого магазина
localStorage.setItem('vitaminka_speech_shop_id', 'false');
```

### Улучшение качества голоса:

Можно использовать Google Cloud Text-to-Speech API для лучшего качества (требует API ключ и оплата):

```javascript
// Будущая опция (не реализована)
window.VITAMINKA_TTS_API = 'google'; // или 'azure', 'aws'
```

---

## Примеры готовых Rive персонажей

**Бесплатные:**
- https://rive.app/community
- https://cdn.rive.app/animations/...

**Платные (от $10):**
- https://sketchfab.com (экспортировать в SVG → Rive)

---

## Отладка

### Если Rive не загружается:

1. Открыть DevTools (F12)
2. Проверить консоль на ошибки
3. Убедиться, что URL файла доступен
4. Проверить, что `.riv` файл валидный

```javascript
// Добавить в консоль для отладки
window.rive // должно быть не undefined
```

### Если состояния не меняются:

```javascript
// В console
const widget = document.querySelector('vitaminka-widget');
widget.setCharacterState('thinking'); // тест
```

---

## Production готовой конфигурации

```html
<!-- Для продакшена -->
<script>
  window.VITAMINKA_API_URL = 'https://api.vitaminka.com';
  window.VITAMINKA_SHOP_ID = 'shop_12345';
  window.VITAMINKA_RIVE_FILE = 'https://cdn.vitaminka.com/characters/assistant.riv';
</script>
<script src="https://cdn.vitaminka.com/widget.js"></script>
```

---

## Дальнейшее улучшение

- [ ] Lip-sync (синхронизация движений губ с речью)
- [ ] Multiple characters (выбор персонажа)
- [ ] Custom themes
- [ ] Реакции на эмоции (happy, sad, confused)
