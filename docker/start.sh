#!/bin/bash

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================================${NC}"
echo -e "${BLUE}  Home Wearable Heart Disease Monitoring Device - Backend Service  ${NC}"
echo -e "${BLUE}===================================================================${NC}"
echo ""

echo -e "${YELLOW}[1/3] Starting Cloudflare Tunnel...${NC}"
cloudflared tunnel --url http://localhost:39244 --logfile /tmp/cloudflared.log &
TUNNEL_PID=$!
sleep 8

echo ""
echo -e "${YELLOW}[2/3] Retrieving Cloudflare Tunnel URL...${NC}"

TUNNEL_URL=""
for i in {1..15}; do
    if [ -f /tmp/cloudflared.log ]; then
        TUNNEL_URL=$(grep -oP 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' /tmp/cloudflared.log | head -1)
        if [ ! -z "$TUNNEL_URL" ]; then
            echo -e "${GREEN}✓ Tunnel URL obtained!${NC}"
            break
        fi
    fi
    echo -e "  Attempt $i/15..."
    sleep 2
done

echo ""
echo -e "${YELLOW}[3/3] Starting Flask backend service...${NC}"
python backend/backend_main.py &
BACKEND_PID=$!
sleep 3

if kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${GREEN}✓ Backend service started (PID: $BACKEND_PID)${NC}"
    echo -e "${GREEN}  Local port: http://localhost:39244${NC}"
else
    echo -e "${RED}✗ Backend service failed to start${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All services started successfully!  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ! -z "$TUNNEL_URL" ]; then
    echo -e "${GREEN}📡 Cloudflare Tunnel URL:${NC}"
    echo -e "${YELLOW}   $TUNNEL_URL${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠ Cloudflare Tunnel is still establishing connection...${NC}"
    echo -e "  Please wait a moment and then run the following command to check the URL:${NC}"
    echo -e "  ${YELLOW}docker logs heart-monitor-backend | grep trycloudflare${NC}"
    echo ""
fi

echo -e "${GREEN}🔧 Local URL:${NC}"
echo -e "${YELLOW}   http://localhost:39244${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Note:${NC}"
echo -e "  • Please update the Cloudflare URL above in the frontend's script.js"
echo -e "  • Modify the API_BASE_URL variable"
echo -e "  • Tunnel URL changes every time it restarts"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}Monitoring service logs...${NC}"
echo ""

tail -f /tmp/cloudflared.log
