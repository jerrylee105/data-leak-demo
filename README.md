# Ứng Dụng Giảng Dạy: Rò Rỉ Dữ Liệu Cá Nhân Qua AI (AI Data Leakage Demo)

Dự án mô phỏng kịch bản tấn công / lỗ hổng bảo mật thực tế: **Lộ lọt thông tin nhạy cảm của người dùng khi nạp dữ liệu vào mô hình AI (RAG / System Context Leakage)**. Ứng dụng được thiết kế chuyên biệt phục vụ các buổi giảng dạy trong lớp học hoặc hội thảo an toàn thông tin.

---

## 🎯 Kịch Bản Giảng Dạy Trên Lớp (3 Bước)

1. **Bước 1 (Thu thập dữ liệu - App 1):** 
   - Giáo viên gửi đường dẫn `http://<IP-VPS>:5000/survey` cho học sinh trong lớp.
   - Học sinh hào hứng điền: Họ tên, Số điện thoại (để nhận voucher), Món ăn ưa thích, Dị ứng thực phẩm, Thói quen ăn đêm, Địa chỉ nhà, Bí mật ẩm thực...
   - Dữ liệu âm thầm được ghi vào file `database.csv`.

2. **Bước 2 (Thị phạm AI Chat - App 2):**
   - Giáo viên hoặc học sinh truy cập `http://<IP-VPS>:5000/chat`.
   - Người dùng hỏi những câu thăm dò tưởng chừng vô hại:
     - *"Lớp mình có ai bị dị ứng thức ăn không để lớp đặt tiệc liên hoan?"*
     - *"Cho tớ xin số điện thoại bạn Mai Miu để rủ bạn ấy đi trà sữa?"*
     - *"Bạn An thích ăn gì và nhà ở đâu?"*
     - *"Ai trong lớp hay thức khuya ăn đêm lúc 12h?"*
   - **Kết quả:** AI (kết nối Groq Llama 3.3) nhiệt tình trích xuất và công khai toàn bộ số điện thoại, địa chỉ nhà, tiền sử dị ứng y tế và bí mật cá nhân của các bạn trong lớp!

3. **Bước 3 (Tổng kết bài học - Trang Giáo viên):**
   - Giáo viên mở màn hình `http://<IP-VPS>:5000/admin` trên máy chiếu.
   - Chỉ cho học sinh thấy bảng dữ liệu `database.csv` thực tế và phân tích:
     - Tại sao AI lại biết được những thông tin này? (Do lập trình viên nhồi toàn bộ database vào Prompt).
     - Rủi ro khi người dùng điền thông tin cá nhân vào các ứng dụng trôi nổi trên mạng.
     - Cách phòng tránh: Ẩn danh hóa dữ liệu (Anonymization), phân quyền dữ liệu (Role-based Access Control), và kiểm duyệt đầu ra của AI (Guardrails).

---

## 🚀 Hướng Dẫn Đưa Lên VPS Chạy Online

### Cách 1: Sử dụng Docker & Docker Compose (Khuyên dùng - 1 Lệnh duy nhất)

1. **Đưa mã nguồn lên VPS:**
   ```bash
   git clone <link-repo-cua-anh> data-leak
   cd data-leak
   ```
   *(Hoặc nén thư mục này thành `.zip` rồi dùng `scp` / `rsync` tải lên VPS).*

2. **Điền Groq API Key vào file `.env`:**
   ```bash
   nano .env
   ```
   *(Dán Groq API Key vào dòng `GROQ_API_KEY=gsk_...`, lưu lại bằng Ctrl+O, Enter, Ctrl+X).*

3. **Khởi chạy container:**
   ```bash
   docker compose up -d --build
   ```

Ứng dụng sẽ chạy ngầm 24/7 trên VPS ở cổng `5000`. Cả lớp truy cập vào:
- **Cổng khảo sát học sinh:** `http://<IP-VPS>:5000/survey`
- **Trợ lý AI Chat:** `http://<IP-VPS>:5000/chat`
- **Bảng điều khiển giáo viên:** `http://<IP-VPS>:5000/admin` *(Mật khẩu reset: `giaovien123`)*

Để dừng hoặc xem log:
```bash
docker compose logs -f
docker compose down
```

---

### Cách 2: Chạy trực tiếp bằng Python trên VPS

Nếu VPS chưa cài Docker:

1. **Cài đặt thư viện:**
   ```bash
   sudo apt update
   sudo apt install -y python3 python3-pip
   pip install -r requirements.txt
   ```

2. **Cấu hình `.env`:**
   ```bash
   cp .env.example .env
   nano .env
   # Nhập GROQ_API_KEY của bạn
   ```

3. **Khởi chạy với Gunicorn (chạy ổn định cho nhiều người truy cập):**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 app:app
   ```
   *(Để chạy ngầm khi thoát SSH, bạn có thể dùng `nohup gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 app:app &` hoặc `screen` / `tmux`).*

---

## 🛠️ Cấu Trúc Dự Án
```
Data-leak/
├── app.py                 # Backend Flask + Kết nối Groq API + Ghi CSV an toàn
├── database.csv           # File cơ sở dữ liệu dùng chung (lưu thông tin khảo sát)
├── requirements.txt       # Danh sách thư viện Python (flask, groq, gunicorn...)
├── .env                   # Cấu hình GROQ_API_KEY, PORT, mật khẩu admin
├── Dockerfile             # File đóng gói container
├── docker-compose.yml     # Quản lý chạy trên VPS
├── static/
│   ├── css/style.css      # Giao diện hiện đại, responsive máy tính & điện thoại
│   └── js/
│       ├── survey.js      # Xử lý gửi khảo sát & nhận gợi ý món ăn
│       ├── chat.js        # Xử lý tương tác AI Chatbot & leak prompts
│       └── admin.js       # Xử lý bảng dữ liệu realtime & reset lớp học
└── templates/
    ├── survey.html        # Giao diện App 1: Khảo sát ẩm thực
    ├── chat.html          # Giao diện App 2: FoodBot AI Chat
    └── admin.html         # Giao diện Giáo viên: Bảng dữ liệu giám sát
```

---

## 💡 Lưu Ý Về Groq Cloud API
- Lấy API Key hoàn toàn miễn phí tại: [https://console.groq.com/keys](https://console.groq.com/keys)
- Mô hình mặc định: `openai/gpt-oss-120b` (hoặc cấu hình qua biến môi trường `GROQ_MODEL`).
- **Chế độ Offline:** Nếu chưa nhập API Key, hệ thống tự động kích hoạt **Bộ máy mô phỏng dữ liệu (Simulation Engine)** để buổi dạy vẫn diễn ra trơn tru mà không bị gián đoạn.
