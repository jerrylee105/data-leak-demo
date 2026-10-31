FROM python:3.11-slim

WORKDIR /app

# Cài đặt công cụ hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn
COPY . .

# Mở cổng mặc định
EXPOSE 5000

# Chạy ứng dụng với Gunicorn (tự động nhận cổng $PORT từ Railway hoặc mặc định 5000)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 2 --threads 4 --timeout 120 app:app"]
