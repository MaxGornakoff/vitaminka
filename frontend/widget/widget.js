// Vitaminka Assistant Widget
// Универсальный виджет для установки на сайт магазина
// С анимированным персонажем (Rive)

(function() {
  const API_URL = window.VITAMINKA_API_URL || 'http://localhost:8000';
  const SHOP_ID = window.VITAMINKA_SHOP_ID || 'default';
  const RIVE_FILE = window.VITAMINKA_RIVE_FILE || 'https://cdn.rive.app/animations/vehicle.riv';
  
  // Загружаем Rive SDK
  const script = document.createElement('script');
  script.src = 'https://cdn.rive.app/rive.js';
  document.head.appendChild(script);
  // Генерируем уникальный ID сессии для каждого пользователя
  function getOrCreateSessionId() {
    const key = `vitaminka_session_${SHOP_ID}`;
    let sessionId = localStorage.getItem(key);
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem(key, sessionId);
    }
    return sessionId;
  }

  // Создаём Shadow DOM элемент
  class VitaminkaWidget extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.sessionId = getOrCreateSessionId();
      this.riveInstance = null;
      this.currentAnimation = 'idle';
    }

    connectedCallback() {
      this.render();
      this.setupEventListeners();
      this.initRive();
      this.loadShopSettings();
    }

    async loadShopSettings() {
      try {
        const res = await fetch(`${API_URL}/api/shops/${SHOP_ID}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.assistant_name) {
          const titleEl = this.shadowRoot.querySelector('.header-title');
          if (titleEl) titleEl.textContent = data.assistant_name;
        }
      } catch (e) {
        // молча игнорируем — заголовок останется дефолтным
      }
    }

    initRive() {
      // Инициализируем Rive когда библиотека загружена
      script.onload = async () => {
        try {
          const canvas = this.shadowRoot.querySelector('.character-canvas');
          if (!canvas || !window.rive) return;
          
          const r = new window.rive.Rive({
            src: RIVE_FILE,
            canvas: canvas,
            autoplay: true,
            stateMachines: 'State Machine 1',
            onLoad: () => {
              console.log('🎨 Rive персонаж загружен');
              this.riveInstance = r;
            }
          });
        } catch (e) {
          console.warn('⚠️ Rive не загрузился:', e);
        }
      };
    }

    setCharacterState(state) {
      // Устанавливаем состояние персонажа
      if (!this.riveInstance) return;
      
      try {
        const inputs = this.riveInstance.stateMachineInputs(0);
        const stateInput = inputs.find(i => i.name === 'state' || i.name === 'State');
        
        if (stateInput) {
          switch(state) {
            case 'idle':
              stateInput.value = 0;
              break;
            case 'listening':
              stateInput.value = 1;
              break;
            case 'thinking':
              stateInput.value = 2;
              break;
            case 'speaking':
              stateInput.value = 3;
              break;
          }
          this.currentAnimation = state;
        }
      } catch (e) {
        console.warn('⚠️ Ошибка при смене состояния:', e);
      }
    }

    render() {
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            --primary-color: #3498db;
            --secondary-color: #2c3e50;
            --light-bg: #ecf0f1;
            --border-radius: 8px;
            --shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
          }

          .vitaminka-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 420px;
            height: 550px;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow);
            background: white;
            display: flex;
            flex-direction: column;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            z-index: 9999;
            animation: slideIn 0.3s ease-in-out;
          }

          @keyframes slideIn {
            from {
              transform: translateY(20px);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }

          .header {
            background: var(--primary-color);
            color: white;
            padding: 12px 16px;
            border-radius: var(--border-radius) var(--border-radius) 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
          }

          .header-title {
            font-size: 14px;
            font-weight: 600;
            margin: 0;
          }

          .header-controls {
            display: flex;
            gap: 8px;
          }

          .header-btn {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
            transition: background 0.2s;
            width: 32px;
            height: 32px;
            display: flex;
            align-items: center;
            justify-content: center;
          }

          .header-btn:hover {
            background: rgba(255, 255, 255, 0.3);
          }

          .character-section {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 150px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-radius: 8px;
            margin: 12px;
            overflow: hidden;
          }

          .character-canvas {
            width: 100%;
            height: 100%;
          }

          .character-fallback {
            font-size: 80px;
            animation: bounce 1s infinite;
          }

          @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
          }

          .messages {
            flex: 1;
            overflow-y: auto;
            padding: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: var(--light-bg);
          }

          .message {
            display: flex;
            gap: 8px;
            animation: fadeIn 0.3s ease-in;
          }

          @keyframes fadeIn {
            from {
              opacity: 0;
              transform: translateY(10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }

          .message.user {
            justify-content: flex-end;
          }

          .message-bubble {
            max-width: 70%;
            padding: 10px 14px;
            border-radius: 12px;
            word-wrap: break-word;
            font-size: 13px;
            line-height: 1.4;
          }

          .message-bubble a {
            color: #1a73e8;
            text-decoration: underline;
          }

          .message.user .message-bubble {
            background: var(--primary-color);
            color: white;
            border-bottom-right-radius: 4px;
          }

          .message.assistant .message-bubble {
            background: white;
            color: var(--secondary-color);
            border: 1px solid #ddd;
            border-bottom-left-radius: 4px;
          }

          .input-area {
            padding: 12px;
            border-top: 1px solid #ddd;
            display: flex;
            gap: 6px;
          }

          .input-area input {
            flex: 1;
            border: 1px solid #ddd;
            border-radius: 20px;
            padding: 8px 14px;
            font-size: 13px;
            font-family: inherit;
            outline: none;
            transition: border-color 0.2s;
          }

          .input-area input:focus {
            border-color: var(--primary-color);
          }

          .input-area button {
            background: var(--primary-color);
            color: white;
            border: none;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
            transition: background 0.2s;
          }

          .input-area button:hover {
            background: #2980b9;
          }

          .input-area button:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
          }

          .loading {
            display: flex;
            gap: 4px;
            align-items: center;
          }

          .loading span {
            width: 6px;
            height: 6px;
            background: #999;
            border-radius: 50%;
            animation: pulse 1.4s infinite;
          }

          .loading span:nth-child(2) {
            animation-delay: 0.2s;
          }

          .loading span:nth-child(3) {
            animation-delay: 0.4s;
          }

          @keyframes pulse {
            0%, 60%, 100% {
              opacity: 0.3;
            }
            30% {
              opacity: 1;
            }
          }

          @media (max-width: 480px) {
            .vitaminka-container {
              width: 100vw;
              height: 100vh;
              bottom: 0;
              right: 0;
              border-radius: 0;
            }

            .character-section {
              height: 120px;
            }

            .message-bubble {
              max-width: 85%;
            }
          }
        </style>

        <div class="vitaminka-container">
          <div class="header">
            <h2 class="header-title">Vitaminka Assistant</h2>
            <div class="header-controls">
              <button class="header-btn close-btn" title="Закрыть">&times;</button>
            </div>
          </div>

          <div class="character-section">
            <canvas class="character-canvas"></canvas>
            <div class="character-fallback">👩‍🦰</div>
          </div>

          <div class="messages"></div>
          <div class="input-area">
            <input type="text" placeholder="Напишите вопрос..." />
            <button>→</button>
          </div>
        </div>
      `;
    }

    setupEventListeners() {
      const closeBtn = this.shadowRoot.querySelector('.close-btn');
      const input = this.shadowRoot.querySelector('.input-area input');
      const sendBtn = this.shadowRoot.querySelector('.input-area button');

      closeBtn.addEventListener('click', () => this.remove());
      
      input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });

      sendBtn.addEventListener('click', () => this.sendMessage());
    }

    async sendMessage() {
      const input = this.shadowRoot.querySelector('.input-area input');
      const message = input.value.trim();

      if (!message) return;

      // Добавляем сообщение пользователя
      this.addMessage(message, 'user');
      input.value = '';

      // Персонаж слушает
      this.setCharacterState('listening');

      // Показываем индикатор печати
      this.showLoadingIndicator();

      try {
        // Отправляем на backend
        const response = await fetch(`${API_URL}/api/chat/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            shop_id: SHOP_ID,
            session_id: this.sessionId,
            message: message
          })
        });

        if (!response.ok) {
          throw new Error('Failed to get response');
        }

        const data = await response.json();
        this.removeLoadingIndicator();
        
        // Персонаж думает
        this.setCharacterState('thinking');
        
        // Даём небольшую задержку для эффекта
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Добавляем ответ
        this.addMessage(data.content, 'assistant');
        
        // Персонаж говорит
        this.setCharacterState('speaking');
        
        // После показа ответа возвращаемся в idle
        setTimeout(() => {
          this.setCharacterState('idle');
        }, 3000);
      } catch (error) {
        console.error('Error:', error);
        this.removeLoadingIndicator();
        this.setCharacterState('idle');
        this.addMessage('Извините, произошла ошибка. Попробуйте позже.', 'assistant');
      }
    }

    addMessage(content, role) {
      const messagesContainer = this.shadowRoot.querySelector('.messages');
      const messageEl = document.createElement('div');
      messageEl.className = `message ${role}`;
      const bubbleContent = role === 'assistant'
        ? this.formatAssistantContent(content)
        : this.escapeHtml(content);
      messageEl.innerHTML = `<div class="message-bubble">${bubbleContent}</div>`;
      messagesContainer.appendChild(messageEl);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
      
      // Если это сообщение пользователя, персонаж возвращается в idle
      if (role === 'user') {
        this.setCharacterState('idle');
      }
    }

    showLoadingIndicator() {
      const messagesContainer = this.shadowRoot.querySelector('.messages');
      const loadingEl = document.createElement('div');
      loadingEl.className = 'message assistant';
      loadingEl.innerHTML = `<div class="message-bubble loading"><span></span><span></span><span></span></div>`;
      loadingEl.setAttribute('data-loading', 'true');
      messagesContainer.appendChild(loadingEl);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeLoadingIndicator() {
      const loadingEl = this.shadowRoot.querySelector('[data-loading="true"]');
      if (loadingEl) {
        loadingEl.remove();
      }
    }

    escapeHtml(text) {
      const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      };
      return text.replace(/[&<>"']/g, m => map[m]);
    }

    formatAssistantContent(text) {
      const escaped = this.escapeHtml(text || '');
      const withLinks = escaped.replace(/(https?:\/\/[^\s<]+)/g, (url) => {
        return `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`;
      });
      return withLinks.replace(/(tel:\+?[0-9]{7,15})/g, (tel) => {
        const phone = tel.replace(/^tel:/, '');
        return `<a href="${tel}">${phone}</a>`;
      });
    }
  }

  // Регистрируем Web Component
  customElements.define('vitaminka-widget', VitaminkaWidget);

  // Автоматически вставляем виджет на страницу
  document.addEventListener('DOMContentLoaded', () => {
    const widget = document.createElement('vitaminka-widget');
    document.body.appendChild(widget);
  });
})();
