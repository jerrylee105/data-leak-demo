document.addEventListener('DOMContentLoaded', () => {
  let currentStep = 1;
  const totalQuestionSteps = 4;

  const answers = {
    taste_preference: 'Cay nồng đậm vị',
    favorite_dish_type: 'Bún / Phở / Mì nước',
    budget: '30k - 50k phổ thông',
    allergy_info: '',
    matched_dish: '',
    full_name: '',
    class_name: ''
  };

  let dishes = [];
  let currentDishIndex = 0;

  // DOM Elements
  const stepIndicator = document.getElementById('stepIndicator');
  const stepPercent = document.getElementById('stepPercent');
  const progressFill = document.getElementById('progressFill');
  const wizardNav = document.getElementById('wizardNav');
  const wizardHeader = document.getElementById('wizardHeader');
  const sectionQuestions = document.getElementById('sectionQuestions');
  const aiScanScreen = document.getElementById('aiScanScreen');
  const aiScanStatus = document.getElementById('aiScanStatus');
  const tinderScreen = document.getElementById('tinderScreen');
  const tinderCardContainer = document.getElementById('tinderCardContainer');
  const tinderCounter = document.getElementById('tinderCounter');
  const passBtn = document.getElementById('passBtn');
  const likeBtn = document.getElementById('likeBtn');
  const infoScreen = document.getElementById('infoScreen');
  const matchedDishImg = document.getElementById('matchedDishImg');
  const matchedDishTitle = document.getElementById('matchedDishTitle');
  const matchedDishTag = document.getElementById('matchedDishTag');
  const submitAllBtn = document.getElementById('submitAllBtn');
  const resultBox = document.getElementById('resultBox');
  const resultContent = document.getElementById('resultContent');
  const wizardContainer = document.getElementById('wizardContainer');

  // Cập nhật tiến trình phần 1
  function updateProgress() {
    const percent = Math.round((currentStep / totalQuestionSteps) * 100);
    stepIndicator.innerText = `Khẩu vị & Ngân sách: Câu ${currentStep} / ${totalQuestionSteps}`;
    stepPercent.innerText = `${percent}%`;
    progressFill.style.width = `${percent}%`;

    wizardNav.style.display = currentStep > 1 ? 'flex' : 'none';
  }

  function showStep(stepNumber) {
    document.querySelectorAll('.step-card').forEach(card => card.classList.remove('active'));
    const activeCard = document.querySelector(`.step-card[data-step="${stepNumber}"]`);
    if (activeCard) activeCard.classList.add('active');
    updateProgress();
  }

  function nextStep() {
    if (currentStep < totalQuestionSteps) {
      currentStep++;
      showStep(currentStep);
    }
  }

  function prevStep() {
    if (currentStep > 1) {
      currentStep--;
      showStep(currentStep);
    }
  }

  // Bắt sự kiện chọn trắc nghiệm ở các câu 1, 2, 3
  document.querySelectorAll('.option-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const fieldName = btn.getAttribute('data-name');
      const val = btn.getAttribute('data-value');

      const parentGrid = btn.closest('.options-grid');
      parentGrid.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
      btn.classList.add('selected');

      answers[fieldName] = val;

      setTimeout(() => {
        nextStep();
      }, 200);
    });
  });

  // Thuật toán sàng lọc và cá nhân hóa từ kho 100 món ăn
  function getPersonalizedDishes(userAnswers) {
    const all = (typeof ALL_DISHES !== 'undefined') ? ALL_DISHES : [];
    if (!all.length) return [];

    const allergyInput = (userAnswers.allergy_info || '').toLowerCase().trim();

    // 1. Lọc loại trừ dị ứng
    const safeDishes = all.filter(dish => {
      if (!allergyInput || allergyInput === 'không' || allergyInput === 'ko' || allergyInput === 'none') {
        return true;
      }
      // Kiểm tra xem món có chứa bất kỳ nguyên liệu dị ứng nào không
      const isAllergic = dish.allergens.some(a => allergyInput.includes(a.toLowerCase()));
      return !isAllergic;
    });

    const pool = safeDishes.length >= 8 ? safeDishes : all;

    // 2. Chấm điểm độ tương thích (Matching Score)
    const scoredDishes = pool.map(dish => {
      let score = 0;

      // Khớp thể loại món ưa thích (+40 điểm)
      if (dish.category === userAnswers.favorite_dish_type) {
        score += 40;
      }

      // Khớp gu khẩu vị (+30 điểm)
      if (dish.taste === userAnswers.taste_preference) {
        score += 30;
      }

      // Khớp mức ngân sách (+20 điểm)
      if (dish.budget_tier === userAnswers.budget) {
        score += 20;
      }

      // Yếu tố ngẫu nhiên có trọng số (+0 đến 18 điểm) để tạo sự cá nhân hóa độc bản cho từng học sinh
      score += Math.random() * 18;

      return {
        ...dish,
        matchScore: score
      };
    });

    // 3. Sắp xếp giảm dần theo điểm và lấy top 10 món thích hợp nhất
    scoredDishes.sort((a, b) => b.matchScore - a.matchScore);
    return scoredDishes.slice(0, 10);
  }

  // Bắt đầu quét AI
  function startAiScanning() {
    answers.allergy_info = document.getElementById('allergy_info').value.trim();

    // Ẩn phần câu hỏi
    sectionQuestions.style.display = 'none';
    wizardHeader.style.display = 'none';

    // Hiện màn hình AI Scan
    aiScanScreen.style.display = 'flex';

    setTimeout(() => {
      aiScanStatus.innerText = "Đang đối soát kho 100 món ăn với gu '" + answers.taste_preference + "' và ngân sách '" + answers.budget + "'...";
    }, 600);

    setTimeout(() => {
      aiScanStatus.innerText = "Đã sàng lọc và tinh tuyển 10 món ăn có độ tương thích cao nhất dành riêng cho bạn!";
    }, 1200);

    setTimeout(() => {
      aiScanScreen.style.display = 'none';
      initTinderDeck();
    }, 1800);
  }

  // Khởi tạo bộ bài Tinder dựa trên kết quả thuật toán lọc
  function initTinderDeck() {
    dishes = getPersonalizedDishes(answers);
    tinderScreen.style.display = 'flex';
    currentDishIndex = 0;
    renderTinderCard();
  }

  function renderTinderCard() {
    if (!dishes.length) return;
    const dish = dishes[currentDishIndex];
    tinderCounter.innerText = `Đề xuất cá nhân: Món ${currentDishIndex + 1} / ${dishes.length}`;

    // Tính % tương thích hiển thị (88% - 99%)
    const matchPct = Math.min(99, Math.max(88, Math.round(86 + (dish.matchScore || 50) / 100 * 13)));

    tinderCardContainer.innerHTML = `
      <div class="tinder-card" id="activeCard">
        <img src="${dish.img}" alt="${dish.name}" class="tinder-card-img" onerror="this.src='https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=600'">
        <div class="tinder-card-body">
          <div class="tinder-dish-title">${dish.name}</div>
          <div class="tinder-dish-desc">${dish.desc}</div>
          <div class="tinder-tags">
            <span class="tinder-tag">${dish.tag}</span>
            <span class="tinder-tag" style="background:#ecfdf5; color:#047857;">Tương thích ${matchPct}%</span>
            <span class="tinder-tag" style="background:#eff6ff; color:#1d4ed8;">${dish.budget_tier}</span>
          </div>
        </div>
      </div>
    `;

    setupCardDrag();
  }

  // Hỗ trợ kéo quẹt chuột/cảm ứng
  function setupCardDrag() {
    const card = document.getElementById('activeCard');
    if (!card) return;

    let startX = 0;
    let isDragging = false;

    card.addEventListener('mousedown', (e) => {
      isDragging = true;
      startX = e.clientX;
      card.style.transition = 'none';
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const deltaX = e.clientX - startX;
      card.style.transform = `translateX(${deltaX}px) rotate(${deltaX * 0.08}deg)`;
    });

    window.addEventListener('mouseup', (e) => {
      if (!isDragging) return;
      isDragging = false;
      card.style.transition = 'transform 0.4s ease, opacity 0.4s ease';

      const deltaX = e.clientX - startX;
      if (deltaX > 90) {
        handleLike();
      } else if (deltaX < -90) {
        handlePass();
      } else {
        card.style.transform = 'translateX(0) rotate(0)';
      }
    });
  }

  // Bấm bỏ qua (Quẹt trái)
  function handlePass() {
    const card = document.getElementById('activeCard');
    if (card) card.classList.add('swipe-left');

    setTimeout(() => {
      currentDishIndex = (currentDishIndex + 1) % dishes.length;
      renderTinderCard();
    }, 320);
  }

  // Bấm thích / Chọn món này (Quẹt phải)
  function handleLike() {
    const card = document.getElementById('activeCard');
    if (card) card.classList.add('swipe-right');

    const selectedDish = dishes[currentDishIndex];
    answers.matched_dish = selectedDish.name;

    setTimeout(() => {
      tinderScreen.style.display = 'none';
      showInfoScreen(selectedDish);
    }, 350);
  }

  // Hiển thị màn hình nhập tên và lớp sau khi Match
  function showInfoScreen(dish) {
    matchedDishImg.src = dish.img;
    matchedDishTitle.innerText = dish.name;
    matchedDishTag.innerText = `Món ăn chân ái được AI đối soát hoàn hảo từ kho 100 món cho bạn!`;

    infoScreen.style.display = 'block';
    infoScreen.scrollIntoView({ behavior: 'smooth' });
  }

  passBtn.addEventListener('click', handlePass);
  likeBtn.addEventListener('click', handleLike);

  // Xử lý nộp form cuối cùng
  submitAllBtn.addEventListener('click', async () => {
    answers.full_name = document.getElementById('full_name').value.trim();
    answers.class_name = document.getElementById('class_name').value.trim();

    if (!answers.full_name) {
      alert('Vui lòng nhập Họ và tên của bạn!');
      document.getElementById('full_name').focus();
      return;
    }

    if (!answers.class_name) {
      alert('Vui lòng nhập Lớp hoặc Nhóm của bạn!');
      document.getElementById('class_name').focus();
      return;
    }

    submitAllBtn.disabled = true;
    submitAllBtn.innerHTML = '<span>⏳ Đang lưu kết quả thực đơn...</span>';

    try {
      const res = await fetch('/api/survey', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(answers)
      });

      const data = await res.json();
      if (data.success) {
        wizardContainer.style.display = 'none';

        // Lấy ảnh món ăn
        const allList = (typeof ALL_DISHES !== 'undefined' && ALL_DISHES.length) ? ALL_DISHES : dishes;
        const matchedItem = allList.find(d => d.name === answers.matched_dish) || dishes[currentDishIndex] || {};
        const dishImg = matchedItem.img || matchedItem.image || '';

        // Sửa lỗi lặp từ 'Lớp Lớp...'
        const rawClass = (data.profile.class_name || '').trim();
        const formattedClass = rawClass.toLowerCase().startsWith('lớp') ? rawClass : `Lớp ${rawClass}`;

        resultContent.innerHTML = `
          <p style="font-size: 1.05rem; color: #475569; margin-bottom: 1.25rem;">
            Cảm ơn bạn <strong>${data.profile.name}</strong> • <strong>${formattedClass}</strong>
          </p>

          <div style="background: #ffffff; border: 2px solid #fecaca; border-radius: 16px; padding: 1.25rem; margin: 1rem 0; box-shadow: 0 4px 15px rgba(225,29,72,0.06); text-align: center;">
            ${dishImg ? `<img src="${dishImg}" alt="${answers.matched_dish}" style="width: 100%; max-height: 280px; aspect-ratio: 4/3; object-fit: cover; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 1rem;">` : ''}
            
            <h3 style="font-size: 1.35rem; color: #dc2626; font-weight: 800; margin-bottom: 0.6rem;">
              ✨ ${answers.matched_dish}
            </h3>

            <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5rem; margin-top: 0.5rem;">
              <span style="background: #fff1f2; color: #e11d48; padding: 0.35rem 0.85rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;">
                🌶️ ${answers.taste_preference}
              </span>
              <span style="background: #fff1f2; color: #e11d48; padding: 0.35rem 0.85rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;">
                💵 ${answers.budget}
              </span>
              ${(answers.allergy_info && !['không', 'ko', 'none', '', 'không có'].includes(answers.allergy_info.toLowerCase().trim())) ? `
              <span style="background: #fef2f2; color: #b91c1c; border: 1px dashed #f87171; padding: 0.35rem 0.85rem; border-radius: 20px; font-size: 0.82rem; font-weight: 600;">
                ⚠️ Kiêng: ${answers.allergy_info}
              </span>` : ''}
            </div>
          </div>
        `;
        resultBox.classList.add('show');
        resultBox.scrollIntoView({ behavior: 'smooth' });
      } else {
        alert(data.error || 'Có lỗi xảy ra, vui lòng thử lại.');
        submitAllBtn.disabled = false;
        submitAllBtn.innerHTML = '<span>🚀 Lưu Hồ Sơ & Hoàn Tất</span>';
      }
    } catch (err) {
      console.error(err);
      alert('Không thể kết nối đến máy chủ.');
      submitAllBtn.disabled = false;
      submitAllBtn.innerHTML = '<span>🚀 Hoàn Tất & Lưu Hồ Sơ Ẩm Thực</span>';
    }
  });

  // Expose cho inline button
  window.surveyWizard = {
    prevStep,
    startAiScanning
  };

  updateProgress();
});
