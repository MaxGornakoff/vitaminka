// Vitaminka Assistant Widget
// Универсальный виджет для установки на сайт магазина

(function () {
  const API_URL = window.VITAMINKA_API_URL || 'https://vitaminka.onrender.com';
  const SHOP_ID = window.VITAMINKA_SHOP_ID || 'test_vitaminof';
  const RIVE_CDN = window.VITAMINKA_RIVE_CDN || 'https://unpkg.com/@rive-app/canvas@2.21.6/rive.js';
  const RIVE_FILE = window.VITAMINKA_RIVE_FILE || 'https://public.rive.app/community/runtime-files/2195-4346-avatar-pack-use-case.riv';

  const THEME = Object.assign(
    {
      blue: '#3498db',
      dark: '#2c3e50',
      bg: '#f0f4f8',
      bottom: 24,
      right: 24,
      zIndex: 9999,
      launcherIcon: '💬',
      borderRadius: 20,
    },
    window.VITAMINKA_THEME || {}
  );

  const LABELS = Object.assign(
    {
      assistantName: 'Vitaminka Assistant',
      statusOnline: '● Онлайн',
      inputPlaceholder: 'Напишите вопрос о товарах…',
      openTitle: 'Открыть ассистента',
      closeTitle: 'Закрыть',
      greeting: 'Привет! Я Vitaminka Assistant 👋 Чем могу помочь?',
      connectionError: 'Не удалось подключиться к серверу. Попробуйте еще раз чуть позже.',
    },
    window.VITAMINKA_LABELS || {}
  );

  function getSession() {
    const key = `vitaminka_session_${SHOP_ID}`;
    let id = localStorage.getItem(key);
    if (!id) {
      id = `sess_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
      localStorage.setItem(key, id);
    }
    return id;
  }

  class VitaminkaWidget extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: 'open' });
      this.riveInstance = null;
      this.session = getSession();
      this.isOpen = Boolean(window.VITAMINKA_START_OPEN);
      this.greeted = false;
      this.assistantName = LABELS.assistantName;
    }

    connectedCallback() {
      if (this.isOpen) {
        this.openChat();
      } else {
        this.renderLauncher();
      }
      this.loadShopSettings();
    }

    async loadShopSettings() {
      try {
        const res = await fetch(`${API_URL}/api/shops/${SHOP_ID}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.assistant_name && String(data.assistant_name).trim()) {
          this.assistantName = String(data.assistant_name).trim();
          const nameEl = this.shadowRoot.querySelector('.header-name');
          if (nameEl) nameEl.textContent = this.assistantName;
        }
      } catch (_) {
        // Ignore silently, defaults are enough.
      }
    }

    renderLauncher() {
      this.shadowRoot.innerHTML = `
        <style>
          .launcher {
            position: fixed;
            bottom: ${Number(THEME.bottom) || 24}px;
            right: ${Number(THEME.right) || 24}px;
            z-index: ${Number(THEME.zIndex) || 9999};
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: linear-gradient(135deg, ${THEME.blue}, ${THEME.dark});
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 20px rgba(52, 152, 219, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            transition: transform 0.2s, box-shadow 0.2s;
            animation: pulse 2.5s infinite;
          }
          .launcher:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 28px rgba(52, 152, 219, 0.7);
          }
          @keyframes pulse {
            0%, 100% { box-shadow: 0 4px 20px rgba(52, 152, 219, 0.5); }
            50% { box-shadow: 0 4px 32px rgba(52, 152, 219, 0.9); }
          }
        </style>
        <button class="launcher" title="${LABELS.openTitle}">${THEME.launcherIcon}</button>
      `;

      this.shadowRoot.querySelector('.launcher').addEventListener('click', () => this.openChat());
    }

    renderChat() {
      this.shadowRoot.innerHTML = `
        <style>
          :host {
            --vk-blue: ${THEME.blue};
            --vk-dark: ${THEME.dark};
            --vk-bg: ${THEME.bg};
          }
          * { box-sizing: border-box; }

          .wrap {
            position: fixed;
            bottom: ${Number(THEME.bottom) || 24}px;
            right: ${Number(THEME.right) || 24}px;
            z-index: ${Number(THEME.zIndex) || 9999};
            width: min(380px, calc(100vw - 24px));
            height: min(560px, calc(100vh - 24px));
            border-radius: ${Number(THEME.borderRadius) || 20}px;
            background: white;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            animation: popIn 0.3s cubic-bezier(.34,1.56,.64,1);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
          }
          @keyframes popIn {
            from { transform: scale(0.85) translateY(20px); opacity: 0; }
            to { transform: scale(1) translateY(0); opacity: 1; }
          }

          .header {
            background: linear-gradient(135deg, var(--vk-blue), var(--vk-dark));
            padding: 14px 16px;
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .header-avatar {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: rgba(255,255,255,0.2);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            flex-shrink: 0;
          }
          .header-info { flex: 1; }
          .header-name { color: white; font-weight: 700; font-size: 14px; }
          .header-status { color: rgba(255,255,255,0.75); font-size: 11px; }
          .hbtn {
            background: rgba(255,255,255,0.15);
            border: none;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background .2s;
          }
          .hbtn:hover { background: rgba(255,255,255,0.25); }

          .avatar-section {
            height: 160px;
            position: relative;
            overflow: hidden;
            background: linear-gradient(160deg, #e8f4fd 0%, #d1ecf1 100%);
            display: flex;
            align-items: center;
            justify-content: center;
          }
          canvas.rive-canvas { position: absolute; inset: 0; width: 100%; height: 100%; }

          .avatar-css {
            position: relative;
            z-index: 2;
            pointer-events: none;
            display: flex;
            flex-direction: column;
            align-items: center;
          }
          .av-head {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: linear-gradient(135deg, #f9c74f, #f3722c);
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
            transition: transform .3s;
          }
          .av-face { font-size: 36px; line-height: 1; }
          .av-body {
            width: 52px;
            height: 42px;
            border-radius: 26px 26px 10px 10px;
            background: linear-gradient(135deg, #4cc9f0, #4361ee);
            margin-top: -8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
          }

          .avatar-css.state-idle .av-head { animation: idleFloat 2.5s ease-in-out infinite; }
          .avatar-css.state-listening .av-head { animation: listenBob 0.5s ease-in-out infinite alternate; }
          .avatar-css.state-thinking .av-face::after {
            content: '💭';
            position: absolute;
            top: -18px;
            right: -18px;
            font-size: 18px;
            animation: thinkPop 0.6s ease-in-out infinite alternate;
          }
          .avatar-css.state-speaking .av-head { animation: speakShake 0.18s ease-in-out infinite alternate; }

          @keyframes idleFloat { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-6px); } }
          @keyframes listenBob { from { transform: rotate(-5deg); } to { transform: rotate(5deg); } }
          @keyframes thinkPop { from { transform: scale(0.8); opacity: 0.7; } to { transform: scale(1.1); opacity: 1; } }
          @keyframes speakShake { from { transform: scaleY(0.96); } to { transform: scaleY(1.04); } }

          .state-bar {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: rgba(0,0,0,0.05);
          }
          .state-fill {
            height: 100%;
            background: var(--vk-blue);
            width: 0;
            transition: width .4s ease;
          }
          .state-label {
            position: absolute;
            top: 10px;
            left: 12px;
            background: rgba(255,255,255,0.85);
            border-radius: 20px;
            padding: 3px 10px;
            font-size: 11px;
            color: var(--vk-dark);
            font-weight: 600;
            letter-spacing: .3px;
            backdrop-filter: blur(4px);
            transition: opacity .3s;
          }

          .messages {
            flex: 1;
            overflow-y: auto;
            padding: 14px 14px 6px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            background: var(--vk-bg);
          }
          .messages::-webkit-scrollbar { width: 4px; }
          .messages::-webkit-scrollbar-thumb { background: #ccc; border-radius: 4px; }

          .msg { display: flex; gap: 8px; animation: msgIn .25s ease-out; }
          .msg.user { justify-content: flex-end; }
          @keyframes msgIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }

          .bubble {
            max-width: 72%;
            padding: 9px 13px;
            border-radius: 14px;
            font-size: 13px;
            line-height: 1.45;
            word-break: break-word;
          }
          .bubble a { color: #1a73e8; text-decoration: underline; }
          .msg.user .bubble {
            background: var(--vk-blue);
            color: white;
            border-bottom-right-radius: 3px;
          }
          .msg.assistant .bubble {
            background: white;
            color: var(--vk-dark);
            border: 1px solid #e0e7ef;
            border-bottom-left-radius: 3px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06);
          }

          .typing { display: flex; gap: 4px; align-items: center; padding: 2px 0; }
          .typing span { width: 7px; height: 7px; background: #aaa; border-radius: 50%; animation: dot 1.3s infinite; }
          .typing span:nth-child(2) { animation-delay: .2s; }
          .typing span:nth-child(3) { animation-delay: .4s; }
          @keyframes dot { 0%,60%,100% { opacity:.25; } 30% { opacity:1; } }

          .input-row {
            padding: 10px 12px;
            background: white;
            border-top: 1px solid #e8eef4;
            display: flex;
            gap: 8px;
            align-items: center;
          }
          .input-row input {
            flex: 1;
            border: 1.5px solid #e0e7ef;
            border-radius: 20px;
            padding: 9px 15px;
            font-size: 13px;
            outline: none;
            transition: border-color .2s;
            font-family: inherit;
          }
          .input-row input:focus { border-color: var(--vk-blue); }
          .input-row input:disabled { background: #f8f9fa; }

          .send-btn {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            border: none;
            background: var(--vk-blue);
            color: white;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background .2s, transform .15s;
            flex-shrink: 0;
          }
          .send-btn:hover { background: #2980b9; transform: scale(1.07); }
          .send-btn:disabled { background: #bdc3c7; cursor: not-allowed; transform: none; }

          @media (max-width: 520px) {
            .wrap {
              right: 12px;
              bottom: 12px;
              width: calc(100vw - 24px);
              height: calc(100vh - 24px);
              border-radius: 16px;
            }
          }
        </style>

        <div class="wrap">
          <div class="header">
            <div class="header-avatar">🤖</div>
            <div class="header-info">
              <div class="header-name">${this.assistantName}</div>
              <div class="header-status" id="status-text">${LABELS.statusOnline}</div>
            </div>
            <button class="hbtn close-btn" title="${LABELS.closeTitle}">✕</button>
          </div>

          <div class="avatar-section">
            <canvas class="rive-canvas" id="rive-canvas"></canvas>
            <div class="avatar-css state-idle" id="av">
              <div class="av-head"><span class="av-face">😊</span></div>
              <div class="av-body"></div>
            </div>
            <div class="state-label" id="state-label">Готов помочь</div>
            <div class="state-bar"><div class="state-fill" id="state-fill"></div></div>
          </div>

          <div class="messages" id="messages"></div>

          <div class="input-row">
            <input type="text" id="msg-input" placeholder="${LABELS.inputPlaceholder}" />
            <button class="send-btn" id="send-btn">➤</button>
          </div>
        </div>
      `;

      this.shadowRoot.querySelector('.close-btn').addEventListener('click', () => this.closeChat());
      this.shadowRoot.querySelector('#send-btn').addEventListener('click', () => this.sendMessage());
      this.shadowRoot.querySelector('#msg-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
    }

    openChat() {
      this.isOpen = true;
      this.renderChat();
      this.loadRive();
      if (!this.greeted) {
        this.greeted = true;
        setTimeout(() => this.addMessage(LABELS.greeting, 'assistant'), 300);
      }
      this.loadShopSettings();
    }

    closeChat() {
      if (this.riveInstance) {
        try {
          this.riveInstance.cleanup();
        } catch (_) {
          // noop
        }
      }
      this.riveInstance = null;
      this.isOpen = false;
      this.renderLauncher();
    }

    loadRive() {
      const existing = document.querySelector('script[data-vitaminka-rive="1"]');
      if (existing && window.Rive) {
        this.initRiveInstance();
        return;
      }

      const script = document.createElement('script');
      script.src = RIVE_CDN;
      script.async = true;
      script.dataset.vitaminkaRive = '1';
      script.onload = () => this.initRiveInstance();
      document.head.appendChild(script);
    }

    initRiveInstance() {
      try {
        const canvas = this.shadowRoot.querySelector('#rive-canvas');
        if (!canvas || !window.Rive) return;

        const r = new window.Rive({
          src: RIVE_FILE,
          canvas,
          autoplay: true,
          stateMachines: 'State Machine 1',
          onLoad: () => {
            this.riveInstance = r;
            const av = this.shadowRoot.querySelector('#av');
            if (av) av.style.opacity = '0';
          },
        });
      } catch (_) {
        // Keep CSS avatar as fallback.
      }
    }

    setState(state) {
      const av = this.shadowRoot.querySelector('#av');
      const label = this.shadowRoot.querySelector('#state-label');
      const fill = this.shadowRoot.querySelector('#state-fill');
      const status = this.shadowRoot.querySelector('#status-text');

      const map = {
        idle: { cls: 'state-idle', face: '😊', lbl: 'Готов помочь', fill: '20%', status: LABELS.statusOnline },
        listening: { cls: 'state-listening', face: '👂', lbl: 'Слушаю…', fill: '50%', status: '● Слушаю…' },
        thinking: { cls: 'state-thinking', face: '🤔', lbl: 'Думаю…', fill: '75%', status: '● Печатает…' },
        speaking: { cls: 'state-speaking', face: '😄', lbl: 'Отвечаю', fill: '100%', status: '● Отвечает' },
      };
      const cfg = map[state] || map.idle;

      if (av) {
        av.className = `avatar-css ${cfg.cls}`;
        const face = av.querySelector('.av-face');
        if (face) face.textContent = cfg.face;
      }
      if (label) label.textContent = cfg.lbl;
      if (fill) fill.style.width = cfg.fill;
      if (status) status.textContent = cfg.status;

      if (!this.riveInstance) return;
      try {
        const inputs = this.riveInstance.stateMachineInputs('State Machine 1');
        const stateInput = inputs && inputs.find((i) => i.name.toLowerCase() === 'state');
        if (stateInput) stateInput.value = { idle: 0, listening: 1, thinking: 2, speaking: 3 }[state] ?? 0;
      } catch (_) {
        // noop
      }
    }

    async sendMessage() {
      const input = this.shadowRoot.querySelector('#msg-input');
      const sendBtn = this.shadowRoot.querySelector('#send-btn');
      const text = input.value.trim();
      if (!text) return;

      input.value = '';
      input.disabled = true;
      sendBtn.disabled = true;

      this.addMessage(text, 'user');
      this.setState('listening');
      await new Promise((r) => setTimeout(r, 250));
      this.setState('thinking');
      this.showTyping();

      let reply = '';
      try {
        const response = await fetch(`${API_URL}/api/chat/message`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            shop_id: SHOP_ID,
            session_id: this.session,
            message: text,
          }),
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        reply = data.content || data.message || LABELS.connectionError;
      } catch (_) {
        reply = LABELS.connectionError;
      }

      this.removeTyping();
      this.setState('speaking');
      this.addMessage(reply, 'assistant');

      setTimeout(() => this.setState('idle'), 3000);
      input.disabled = false;
      sendBtn.disabled = false;
      input.focus();
    }

    addMessage(text, role) {
      const container = this.shadowRoot.querySelector('#messages');
      if (!container) return;
      const el = document.createElement('div');
      el.className = `msg ${role}`;
      const bubbleContent = role === 'assistant' ? this.formatAssistantContent(text) : this.esc(text);
      el.innerHTML = `<div class="bubble">${bubbleContent}</div>`;
      container.appendChild(el);
      container.scrollTop = container.scrollHeight;
    }

    showTyping() {
      const container = this.shadowRoot.querySelector('#messages');
      if (!container) return;
      const el = document.createElement('div');
      el.className = 'msg assistant';
      el.id = 'typing-msg';
      el.innerHTML = '<div class="bubble"><div class="typing"><span></span><span></span><span></span></div></div>';
      container.appendChild(el);
      container.scrollTop = container.scrollHeight;
    }

    removeTyping() {
      const el = this.shadowRoot.querySelector('#typing-msg');
      if (el) el.remove();
    }

    esc(text) {
      return String(text || '').replace(/[&<>"']/g, (m) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m]));
    }

    formatAssistantContent(text) {
      const escaped = this.esc(text || '');
      const withLinks = escaped.replace(/(https?:\/\/[^\s<]+)/g, (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`);
      return withLinks.replace(/(tel:\+?[0-9]{7,15})/g, (tel) => {
        const phone = tel.replace(/^tel:/, '');
        return `<a href="${tel}">${phone}</a>`;
      });
    }
  }

  if (!customElements.get('vitaminka-widget')) {
    customElements.define('vitaminka-widget', VitaminkaWidget);
  }

  const mount = () => {
    if (document.querySelector('vitaminka-widget')) return;
    const widget = document.createElement('vitaminka-widget');
    document.body.appendChild(widget);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
