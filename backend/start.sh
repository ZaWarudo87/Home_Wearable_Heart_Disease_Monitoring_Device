#!/bin/bash

# 顏色定義
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  心臟健康監測系統 - 後端服務啟動中${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 啟動 Python 後端服務（背景執行）
echo -e "${YELLOW}[1/3] 啟動 Flask 後端服務...${NC}"
python testing_backend.py &
BACKEND_PID=$!

# 等待後端服務啟動
sleep 3

# 檢查後端是否成功啟動
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}✓ 後端服務已啟動 (PID: $BACKEND_PID)${NC}"
    echo -e "${GREEN}  本地端口: http://localhost:5001${NC}"
else
    echo -e "${RED}✗ 後端服務啟動失敗${NC}"
    exit 1
fi

echo ""

# 啟動 Cloudflare Tunnel
echo -e "${YELLOW}[2/3] 啟動 Cloudflare Tunnel...${NC}"
cloudflared tunnel --url http://localhost:5001 --logfile /tmp/cloudflared.log &
TUNNEL_PID=$!

# 等待 Cloudflare Tunnel 啟動並獲取 URL
sleep 8

echo ""
echo -e "${YELLOW}[3/3] 正在取得 Cloudflare Tunnel URL...${NC}"

# 嘗試從日誌文件中提取 URL
TUNNEL_URL=""
for i in {1..15}; do
    if [ -f /tmp/cloudflared.log ]; then
        TUNNEL_URL=$(grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cloudflared.log | head -1)
        if [ ! -z "$TUNNEL_URL" ]; then
            echo -e "${GREEN}✓ Tunnel URL 已取得！${NC}"
            break
        fi
    fi
    echo -e "  嘗試 $i/15..."
    sleep 2
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ 所有服務已成功啟動！${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ! -z "$TUNNEL_URL" ]; then
    echo -e "${GREEN}📡 Cloudflare Tunnel URL:${NC}"
    echo -e "${YELLOW}   $TUNNEL_URL${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Cloudflare Tunnel 仍在建立連接...${NC}"
    echo -e "  請稍候片刻後執行以下命令查看 URL：${NC}"
    echo -e "  ${YELLOW}docker logs heart-monitor-backend | grep trycloudflare${NC}"
    echo ""
fi

echo -e "${GREEN}🔧 本地 URL:${NC}"
echo -e "${YELLOW}   http://localhost:5001${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}提示：${NC}"
echo -e "  • 請將上述 Cloudflare URL 更新到前端的 script.js"
echo -e "  • 修改 API_BASE_URL 變數"
echo -e "  • Tunnel URL 每次重啟都會改變"
echo -e "${BLUE}========================================${NC}"
echo ""

# 持續顯示 Cloudflare Tunnel 日誌
echo -e "${YELLOW}正在監控服務日誌...${NC}"
echo ""

# 保持容器運行並顯示日誌
tail -f /tmp/cloudflared.log
