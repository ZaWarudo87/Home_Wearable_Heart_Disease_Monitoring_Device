FROM python:3.12-slim

ARG TARGETARCH

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    iproute2 \
    iputils-ping \
    libavahi-client3 \
    libavahi-common3 \
    libnss-mdns \
    avahi-utils \
    net-tools \
    procps \
    python3-dev \
    wget \
    && rm -rf /var/lib/apt/lists/* \
    && sed -i 's/hosts:          files dns/hosts:          files mdns4_minimal [NOTFOUND=return] dns/' /etc/nsswitch.conf

RUN wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-${TARGETARCH} -O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --default-timeout=1000

COPY backend/ ./backend/
COPY frontend/ ./frontend/

COPY docker/start.sh .
RUN sed -i 's/\r$//' start.sh && chmod +x start.sh

EXPOSE 39244

ENV PYTHONUNBUFFERED=1

CMD ["./start.sh"]
