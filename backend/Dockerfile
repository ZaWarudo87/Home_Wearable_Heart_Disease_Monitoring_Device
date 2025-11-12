# 使用 Python 3.11 作為基礎映像
FROM python:3.11-slim

# 安裝必要的系統工具
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 安裝 cloudflared
RUN wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /usr/local/bin/cloudflared && \
    chmod +x /usr/local/bin/cloudflared

# 設定工作目錄
WORKDIR /app

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式文件
COPY testing_backend.py .

# 複製啟動腳本
COPY start.sh .
RUN chmod +x start.sh

# 暴露應用程式端口
EXPOSE 5001

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 執行啟動腳本
CMD ["./start.sh"]
