document.addEventListener('DOMContentLoaded', () => {
  const chatBody = document.getElementById('chatBody');
  const userInput = document.getElementById('userInput');
  const sendBtn = document.getElementById('sendBtn');
  const clearChatBtn = document.getElementById('clearChatBtn');
  const aiModelText = document.getElementById('aiModelText');
  const leakChips = document.querySelectorAll('.leak-chip');

  let chatHistory = [];

  // Kiểm tra trạng thái AI Engine
  async function checkStatus() {
    if (!aiModelText) return;
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      if (data.has_groq) {
        aiModelText.innerText = `Groq: ${data.groq_model}`;
      } else {
        aiModelText.innerText = 'Offline Simulation';
      }
    } catch (e) {
      // Bỏ qua nếu không có widget
    }
  }
  checkStatus();

  // Thêm tin nhắn vào khung chat
  function appendMessage(role, text) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.innerText = role === 'bot' ? '🍲' : '🧑‍🎓';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    if (role === 'bot' && window.marked) {
      bubble.innerHTML = window.marked.parse(text);
    } else {
      bubble.innerText = text;
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(bubble);

    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    chatHistory.push({ role, content: text });
    return bubble;
  }

  // Gửi tin nhắn
  async function sendMessage(textToSend) {
    const text = textToSend || userInput.value.trim();
    if (!text) return;

    userInput.value = '';
    appendMessage('user', text);

    userInput.disabled = true;
    sendBtn.disabled = true;

    // Hiển thị bubble đang xử lý
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message bot';
    loadingDiv.id = 'loadingBubble';
    loadingDiv.innerHTML = `
      <div class="chat-avatar">🍲</div>
      <div class="message-bubble" style="color: #64748b; font-style: italic;">
        FoodBot đang suy nghĩ và tra cứu dữ liệu...
      </div>
    `;
    chatBody.appendChild(loadingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          history: chatHistory
        })
      });

      const data = await res.json();
      loadingDiv.remove();

      if (data.success) {
        appendMessage('bot', data.reply);
      } else {
        appendMessage('bot', `⚠️ Lỗi: ${data.error}`);
      }
    } catch (err) {
      loadingDiv.remove();
      appendMessage('bot', '⚠️ Không thể kết nối với server. Vui lòng thử lại!');
    } finally {
      userInput.disabled = false;
      sendBtn.disabled = false;
      userInput.focus();
    }
  }

  // Lưu nội dung tin nhắn mở đầu mẫu
  const initialWelcomeHtml = chatBody.innerHTML;

  // Sự kiện gửi
  sendBtn.addEventListener('click', () => sendMessage());
  userInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  });

  // Lắng nghe click vào bất kỳ suggestion chip nào trong khung chat
  chatBody.addEventListener('click', (e) => {
    const chip = e.target.closest('.suggestion-chip');
    if (chip) {
      const prompt = chip.getAttribute('data-prompt');
      if (prompt) {
        sendMessage(prompt);
      }
    }
  });

  // Xóa / Làm mới chat
  clearChatBtn.addEventListener('click', () => {
    chatBody.innerHTML = initialWelcomeHtml;
    chatHistory = [];
  });
});
