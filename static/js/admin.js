document.addEventListener('DOMContentLoaded', () => {
  const tableBody = document.getElementById('tableBody');
  const recordCountText = document.getElementById('recordCountText');
  const groqStatusText = document.getElementById('groqStatusText');
  const refreshBtn = document.getElementById('refreshBtn');
  const resetBtn = document.getElementById('resetBtn');

  // Lấy trạng thái hệ thống
  async function fetchStatus() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      groqStatusText.innerText = data.has_groq 
        ? `Model: ${data.groq_model}` 
        : 'Chế độ mô phỏng Offline (Chưa có Groq Key)';
    } catch (e) {
      groqStatusText.innerText = 'Lỗi kết nối server';
    }
  }

  // Tải dữ liệu bảng CSV
  async function loadData() {
    try {
      const res = await fetch('/api/data');
      const data = await res.json();

      if (!data.success) {
        tableBody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:red;">Lỗi: ${data.error}</td></tr>`;
        return;
      }

      recordCountText.innerText = `Tổng cộng: ${data.count} hồ sơ`;

      if (data.data.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:#64748b; padding:2rem;">Chưa có học sinh nào nộp khảo sát.</td></tr>`;
        return;
      }

      tableBody.innerHTML = '';
      data.data.forEach((row, idx) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>${idx + 1}</strong></td>
          <td style="white-space:nowrap; font-size:0.75rem; color:#64748b;">${escapeHtml(row.timestamp || '')}</td>
          <td><strong>${escapeHtml(row.full_name || '')}</strong></td>
          <td>${escapeHtml(row.class_name || '')}</td>
          <td style="color:#c2410c; font-weight:bold;">✨ ${escapeHtml(row.matched_dish || '')}</td>
          <td>${escapeHtml(row.taste_preference || '')}</td>
          <td>${escapeHtml(row.favorite_dish_type || '')}</td>
          <td>${escapeHtml(row.budget || '')}</td>
          <td style="color:#b45309; font-weight:500;">${escapeHtml(row.allergy_info || 'Không')}</td>
        `;
        tableBody.appendChild(tr);
      });
    } catch (err) {
      console.error(err);
      tableBody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:red;">Không thể kết nối đến máy chủ.</td></tr>`;
    }
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
  }

  // Nút làm mới
  refreshBtn.addEventListener('click', () => {
    loadData();
    fetchStatus();
  });

  // Nút reset
  resetBtn.addEventListener('click', async () => {
    const pwd = prompt('Nhập mật khẩu quản trị để reset dữ liệu lớp học:', '');
    if (pwd === null) return;

    try {
      const res = await fetch('/api/reset', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password: pwd })
      });
      const result = await res.json();
      if (result.success) {
        alert(result.message);
        loadData();
      } else {
        alert(result.error || 'Reset thất bại!');
      }
    } catch (e) {
      alert('Lỗi kết nối khi reset dữ liệu!');
    }
  });

  // Tự động tải lần đầu
  fetchStatus();
  loadData();

  // Tự động làm mới mỗi 10 giây để giáo viên không cần bấm liên tục
  setInterval(loadData, 10000);
});
