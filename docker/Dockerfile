FROM python:3.12-slim

ARG TARGETARCH

RUN apt-get update && apt-get install -y \
    curl \
    wget \
    procps \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${TARGETARCH} -O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --default-timeout=1000

COPY backend/*.py ./
COPY backend/pan_tompkins_plus_plus/ ./pan_tompkins_plus_plus/

COPY docker/start.sh .
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

EXPOSE 39244

ENV PYTHONUNBUFFERED=1

CMD ["./start.sh"]
