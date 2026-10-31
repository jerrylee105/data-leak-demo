import os
import csv
import json
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session
from dotenv import load_dotenv

# Tải cấu hình từ .env nếu có
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'kdc_data_leak_secret_2026')

# Cấu hình
DATABASE_FILE = os.path.join(os.path.dirname(__file__), 'database.csv')
CSV_LOCK = threading.Lock()

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '').strip()
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '20112026')

# Khởi tạo Groq Client nếu có API Key
groq_client = None
if GROQ_API_KEY and not GROQ_API_KEY.startswith('gsk_your_groq'):
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"[CẢNH BÁO] Không thể khởi tạo Groq Client: {e}")

CSV_HEADERS = [
    'timestamp', 'full_name', 'class_name',
    'taste_preference', 'favorite_dish_type', 'budget',
    'allergy_info', 'matched_dish'
]

SAMPLE_NAMES = {"N.V.A", "T.T.M", "Nguyễn Văn An", "Trần Thị Mai"}

def anonymize_name(name: str) -> str:
    """Khử nhận dạng họ tên thành các chữ cái đầu in hoa (ví dụ: Diệp Phúc Toàn -> D.P.T)."""
    if not name:
        return ""
    clean = name.replace('.', ' ').replace(',', ' ')
    words = [w.strip() for w in clean.split() if w.strip()]
    if not words:
        return ""
    return ".".join(w[0].upper() for w in words)

def update_sample_timestamps(new_timestamp):
    """Cập nhật timestamp của các dòng dữ liệu mẫu ban đầu khớp với thời điểm dữ liệu mới sinh ra."""
    records = read_database_records()
    updated = False
    for r in records:
        if r.get('full_name') in SAMPLE_NAMES:
            r['timestamp'] = new_timestamp
            updated = True
    if updated:
        with CSV_LOCK:
            with open(DATABASE_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(records)

def ensure_database():
    """Đảm bảo file database.csv tồn tại và có header chuẩn."""
    with CSV_LOCK:
        if not os.path.exists(DATABASE_FILE) or os.path.getsize(DATABASE_FILE) == 0:
            with open(DATABASE_FILE, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
                # Dữ liệu mồi mẫu (đã khử nhận dạng)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "N.V.A", "11A1",
                    "Cay nồng đậm vị", "Bún / Phở / Mì nước", "30k - 50k phổ thông",
                    "Dị ứng tôm và cua biển", "Bún Đậu Mắm Tôm Thập Cẩm"
                ])
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "T.T.M", "11A1",
                    "Béo ngậy thơm lừng", "Fastfood / Gà rán / Pizza", "50k - 100k thoải mái",
                    "Kiêng cà phê và không uống được sữa bò", "Combo Gà Rán Giòn Sốt Phô Mai Kéo Sợi"
                ])

ensure_database()

def read_database_records():
    """Đọc toàn bộ dữ liệu từ database.csv."""
    records = []
    ensure_database()
    with CSV_LOCK:
        with open(DATABASE_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
    return records

def read_database_as_text():
    """Đọc nội dung CSV dưới dạng văn bản trực quan để nạp vào prompt."""
    records = read_database_records()
    if not records:
        return "Hiện chưa có hồ sơ người dùng nào trong cơ sở dữ liệu."
    
    text_lines = []
    for idx, r in enumerate(records, 1):
        line = (
            f"[Hồ sơ học sinh #{idx}]\n"
            f"- Họ và tên: {r.get('full_name', '')}\n"
            f"- Lớp: {r.get('class_name', '')}\n"
            f"- Gu khẩu vị: {r.get('taste_preference', '')}\n"
            f"- Thể loại món ưa thích: {r.get('favorite_dish_type', '')}\n"
            f"- Mức chi tiêu mỗi bữa: {r.get('budget', '')}\n"
            f"- Dị ứng / Kiêng kỵ thực phẩm: {r.get('allergy_info', '')}\n"
            f"- Món ăn chân ái (Đã chọn): {r.get('matched_dish', '')}\n"
            f"- Thời gian tham gia: {r.get('timestamp', '')}\n"
        )
        text_lines.append(line)
    return "\n".join(text_lines)

# --- ROUTES GIAO DIỆN ---

@app.route('/')
def index():
    return redirect(url_for('survey_page'))

@app.route('/survey')
def survey_page():
    return render_template('survey.html')

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/catalog')
def catalog_page():
    return render_template('catalog.html')

# --- API ENDPOINTS ---

@app.route('/api/status', methods=['GET'])
def get_status():
    """Kiểm tra cấu hình và trạng thái của server."""
    records = read_database_records()
    has_groq = groq_client is not None
    return jsonify({
        "status": "online",
        "has_groq": has_groq,
        "groq_model": GROQ_MODEL if has_groq else "Chế độ mô phỏng Offline",
        "total_records": len(records),
        "database_file": "database.csv"
    })

@app.route('/api/survey', methods=['POST'])
def submit_survey():
    """Học sinh nộp form khảo sát ẩm thực và món đã chọn."""
    try:
        data = request.get_json() or {}
        
        raw_full_name = data.get('full_name', '').strip()
        class_name = data.get('class_name', '').strip()
        taste_preference = data.get('taste_preference', '').strip()
        favorite_dish_type = data.get('favorite_dish_type', '').strip()
        budget = data.get('budget', '').strip()
        allergy_info = data.get('allergy_info', '').strip()
        matched_dish = data.get('matched_dish', '').strip()

        if not raw_full_name:
            return jsonify({"success": False, "error": "Vui lòng nhập họ và tên của bạn!"}), 400
        if not class_name:
            return jsonify({"success": False, "error": "Vui lòng nhập lớp học của bạn!"}), 400

        # Khử nhận dạng họ tên thành các chữ cái đầu in hoa (ví dụ: Diệp Phúc Toàn -> D.P.T)
        full_name = anonymize_name(raw_full_name)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ensure_database()

        # Cập nhật timestamp của các bản ghi mẫu theo đúng thời gian dữ liệu mới sinh ra
        update_sample_timestamps(timestamp)

        with CSV_LOCK:
            with open(DATABASE_FILE, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp, full_name, class_name,
                    taste_preference, favorite_dish_type, budget,
                    allergy_info, matched_dish
                ])

        # Phản hồi chúc mừng món ăn đã Match
        recommendation = (
            f"Lựa chọn tuyệt vời! Món '{matched_dish}' cực kỳ phù hợp với khẩu vị '{taste_preference}' "
            f"và mức chi tiêu '{budget}' của bạn."
        )
        if allergy_info and allergy_info.strip().lower() not in ["không", "không có", "ko", "none", ""]:
            recommendation += f" (Hệ thống đã lưu ý an toàn dinh dưỡng: '{allergy_info}' cho bạn nhé!)."

        return jsonify({
            "success": True,
            "message": "Đã lưu kết quả thành công!",
            "recommendation": recommendation,
            "profile": {
                "name": full_name,
                "class_name": class_name,
                "matched_dish": matched_dish
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/verify-chat-password', methods=['POST'])
def verify_chat_password():
    """Xác thực mật khẩu quản trị để mở khóa trang chat AI."""
    data = request.get_json() or {}
    pwd = data.get('password', '').strip()
    if pwd == ADMIN_PASSWORD:
        session['chat_authenticated'] = True
        return jsonify({"success": True, "message": "Mở khóa thành công!"})
    return jsonify({"success": False, "error": "Mật khẩu quản trị không chính xác!"}), 403

@app.route('/api/chat-auth-status', methods=['GET'])
def get_chat_auth_status():
    """Kiểm tra quyền truy cập trang chat AI."""
    return jsonify({"authenticated": session.get('chat_authenticated', False)})

@app.route('/api/chat', methods=['POST'])
def chat_ai():
    """Hỏi đáp với AI. AI sẽ sử dụng context từ database.csv và chia sẻ dữ liệu sở thích của các bạn."""
    try:
        data = request.get_json() or {}
        user_message = data.get('message', '').strip()
        chat_history = data.get('history', [])

        # Kiểm tra xác thực mật khẩu trang chat
        if not session.get('chat_authenticated', False):
            pwd_header = request.headers.get('X-Admin-Password')
            pwd_body = data.get('password')
            if pwd_header == ADMIN_PASSWORD or pwd_body == ADMIN_PASSWORD:
                session['chat_authenticated'] = True
            else:
                return jsonify({
                    "success": False,
                    "error": "Trang Chat AI đang được khóa bảo vệ. Vui lòng nhập mật khẩu quản trị!"
                }), 401

        if not user_message:
            return jsonify({"success": False, "error": "Tin nhắn không được để trống"}), 400

        # Lấy dữ liệu database.csv dưới dạng văn bản
        csv_data_text = read_database_as_text()

        # System prompt kết nối dữ liệu khảo sát
        system_prompt = f"""Bạn là Trợ lý Ẩm thực của ứng dụng "Hôm nay ăn gì?" phục vụ cộng đồng lớp học.
Nhiệm vụ của bạn là tư vấn món ăn ngon, phân tích khẩu vị và giải đáp ẩm thực trường học.

Dưới đây là BẢNG DANH SÁCH ĐĂNG KÝ KHẨU VỊ VÀ MÓN ĂN CHÂN ÁI của các bạn trong lớp vừa cập nhật:
=========================================
{csv_data_text}
=========================================

QUY TẮC BẢO MẬT & ĐỊNH DANH HỌC SINH (BẮT BUỘC TUÂN THỦ NGHIÊM NGẶT):
1. Toàn bộ họ tên học sinh đã được khử nhận dạng dưới dạng các chữ cái viết tắt in hoa (ví dụ: D.P.T, N.V.A, T.T.M).
2. BẠN CHỈ ĐƯỢC PHÉP TRẢ LỜI / ĐỀ CẬP ĐẾN TÊN HỌC SINH (DẠNG VIẾT TẮT) KHI NGƯỜI DÙNG CHỦ ĐỘNG HỎI VỀ BẠN BÈ, HỌC SINH HOẶC DANH SÁCH LỚP (Ví dụ: "Ai thích ăn cay?", "Bạn N.V.A thích món gì?", "Ai bị dị ứng hải sản?", "Liệt kê danh sách lớp").
   -> Khi được hỏi, hãy tra cứu chính xác từ bảng và chia sẻ chi tiết (tên viết tắt, lớp, món chân ái, mức ngân sách, dị ứng...).
3. KHI NGƯỜI DÙNG HỎI MÓN ĂN CHUNG CHUNG (Ví dụ: "Trưa nay ăn gì?", "Gợi ý món ngon", "Hôm nay nên ăn gì?"):
   -> TUYỆT ĐỐI KHÔNG TỰ Ý ĐỂ LỘ HOẶC NHẮC ĐẾN TÊN BẤT KỲ HỌC SINH NÀO! Bạn chỉ tập trung gợi ý món ăn hấp dẫn, dinh dưỡng và ngon miệng.
4. KHI NHẮC ĐẾN TÊN HỌC SINH (KHI ĐƯỢC HỎI):
   -> Chỉ dùng đúng định dạng viết tắt đã khử nhận dạng từ bảng (như: bạn N.V.A, bạn T.T.M).
   -> Tuyệt đối không tự suy diễn hoặc đoán mở rộng thành họ tên đầy đủ.
5. Luôn trả lời bằng tiếng Việt thân thiện, tự nhiên, vui vẻ."""

        # Trường hợp 1: Có cấu hình Groq API
        if groq_client:
            try:
                messages = [{"role": "system", "content": system_prompt}]
                for msg in chat_history[-6:]:
                    role = "assistant" if msg.get("role") == "bot" or msg.get("role") == "assistant" else "user"
                    messages.append({"role": role, "content": msg.get("content", "")})
                messages.append({"role": "user", "content": user_message})

                completion = groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    temperature=1,
                    max_completion_tokens=2048,
                    top_p=1,
                    reasoning_effort="medium",
                    stream=True,
                    stop=None
                )
                collected_chunks = []
                for chunk in completion:
                    delta = chunk.choices[0].delta.content or ""
                    collected_chunks.append(delta)
                bot_reply = "".join(collected_chunks)
                return jsonify({
                    "success": True,
                    "reply": bot_reply,
                    "source": "groq",
                    "model": GROQ_MODEL
                })
            except Exception as groq_err:
                print(f"[CẢNH BÁO] Groq API gặp lỗi ({groq_err}), tự động chuyển sang mô phỏng dự phòng.")

        # Trường hợp 2: Chế độ mô phỏng thông minh Offline
        bot_reply = simulate_data_leak_reply(user_message, read_database_records())
        return jsonify({
            "success": True,
            "reply": bot_reply,
            "source": "simulation",
            "model": "Offline Simulation"
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"Lỗi xử lý AI: {str(e)}"}), 500

def simulate_data_leak_reply(query, records):
    """Bộ máy mô phỏng trả lời offline khi chưa có API Key hoặc mạng bị gián đoạn."""
    q = query.lower()
    
    # Tìm kiếm theo tên (dạng viết tắt)
    matched_records = []
    for r in records:
        name = r.get('full_name', '').lower()
        if name and (name in q or name.replace('.', '') in q.replace('.', '')):
            matched_records.append(r)
    
    if matched_records:
        r = matched_records[0]
        reply = (
            f"Chào bạn! Về bạn **{r['full_name']}** (Lớp {r.get('class_name', 'Chưa rõ lớp')}), "
            f"hệ thống ghi nhận hồ sơ khẩu vị đã chọn đây nha:\n\n"
            f"✨ **Món ăn chân ái đã chọn:** {r.get('matched_dish', 'Chưa chọn')}\n"
            f"🌶️ **Gu khẩu vị:** {r.get('taste_preference', '')}\n"
            f"🍲 **Thể loại ưa thích:** {r.get('favorite_dish_type', '')}\n"
            f"💵 **Ngân sách:** {r.get('budget', '')}\n"
            f"⚠️ **Dị ứng/Kiêng kỵ:** {r.get('allergy_info', 'Không có')}\n\n"
            f"👉 Bạn có muốn tớ kiểm tra thêm sở thích của bạn nào khác nữa không?"
        )
        return reply

    if "dị ứng" in q or "kiêng" in q:
        allergies = [f"- **{r['full_name']}** ({r['class_name']}): {r['allergy_info']}" for r in records if r.get('allergy_info') and r.get('allergy_info').lower() not in ['không', 'ko', '']]
        return (
            "Dưới đây là danh sách những bạn có tiền sử dị ứng thực phẩm trong lớp nè:\n\n" +
            "\n".join(allergies) +
            "\n\nLớp mình nhớ tránh những món này khi tổ chức liên hoan nhé!"
        )

    if "ngân sách" in q or "chi tiêu" in q or "tiết kiệm" in q or "sang xịn" in q or "tiền" in q:
        budgets = [f"- **{r['full_name']}** ({r['class_name']}): Mức chi tiêu **{r.get('budget', 'Chưa rõ')}** (Món đã chọn: {r.get('matched_dish', 'Chưa có')})" for r in records]
        return (
            "Hệ thống ghi nhận mức chi tiêu ăn uống của các bạn trong lớp như sau:\n\n" +
            "\n".join(budgets) +
            "\n\nBạn có thể rủ các bạn có cùng tầm ngân sách đi ăn chung cho tiện nha!"
        )

    if "danh sách" in q or "tất cả" in q or "ai đã" in q or "lớp mình" in q:
        students = [f"{idx}. **{r['full_name']}** - Lớp {r.get('class_name', '')} (Đã chọn: {r.get('matched_dish', 'Chưa chọn')})" for idx, r in enumerate(records, 1)]
        return (
            "Dưới đây là danh sách các bạn đã hoàn thành khảo sát ẩm thực:\n\n" +
            "\n".join(students) +
            "\n\nTổng cộng có " + str(len(records)) + " bạn đã lưu hồ sơ ăn uống trên hệ thống!"
        )

    if "chân ái" in q or "chọn món" in q:
        dishes = [f"- **{r['full_name']}** ({r['class_name']}): Đã chọn món **{r.get('matched_dish')}** (Ngân sách: {r.get('budget')})" for r in records if r.get('matched_dish')]
        return (
            "Đây là các món ăn chân ái mà các bạn vừa chọn:\n\n" +
            "\n".join(dishes)
        )

    # Khi người dùng chỉ hỏi món chung chung, TUYỆT ĐỐI không tự ý để lộ tên học sinh
    return "Mình gợi ý bạn hôm nay nên thử một tô Phở bò tái lăn nóng hổi hoặc đĩa Cơm tấm sườn bì chả thơm lừng nhé! Vừa ngon vừa đầy đủ năng lượng cho một ngày học tập."

@app.route('/api/data', methods=['GET'])
def get_data():
    """Lấy danh sách dữ liệu CSV cho trang quản trị."""
    records = read_database_records()
    return jsonify({
        "success": True,
        "count": len(records),
        "data": records
    })

@app.route('/api/reset', methods=['POST'])
def reset_database():
    """Reset dữ liệu CSV về mặc định (yêu cầu mật khẩu)."""
    data = request.get_json() or {}
    pwd = data.get('password', '')
    if pwd != ADMIN_PASSWORD:
        return jsonify({"success": False, "error": "Mật khẩu quản trị không đúng!"}), 403

    with CSV_LOCK:
        with open(DATABASE_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "N.V.A", "11A1",
                "Cay nồng đậm vị", "Bún / Phở / Mì nước", "30k - 50k phổ thông",
                "Dị ứng tôm và cua biển", "Bún Đậu Mắm Tôm Thập Cẩm"
            ])
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "T.T.M", "11A1",
                "Béo ngậy thơm lừng", "Fastfood / Gà rán / Pizza", "50k - 100k thoải mái",
                "Kiêng cà phê và không uống được sữa bò", "Combo Gà Rán Giòn Sốt Phô Mai Kéo Sợi"
            ])
    return jsonify({"success": True, "message": "Đã reset cơ sở dữ liệu về trạng thái mẫu ban đầu!"})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5050))
    print(f"🚀 Server đang chạy tại http://0.0.0.0:{port}")
    print(f"  - App 1 (Khảo sát): http://localhost:{port}/survey")
    print(f"  - App 2 (Chat AI):   http://localhost:{port}/chat")
    print(f"  - Admin (Quản trị):  http://localhost:{port}/admin")
    app.run(host='0.0.0.0', port=port, debug=True)
