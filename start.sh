#!/bin/bash
# Vet Anesthesia Records — Startup Script
# Run: bash start.sh  (default port 8100)
# Or:  PORT=9000 bash start.sh

cd "$(dirname "$0")"
PORT=${PORT:-8100}

# Get local network IP (Wi-Fi en0, then Ethernet en1, then any)
LAN_IP=$(ipconfig getifaddr en0 2>/dev/null \
      || ipconfig getifaddr en1 2>/dev/null \
      || ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)

echo "======================================================"
echo "  VetAnesthesia Records"
echo "======================================================"
echo ""
echo "  This computer:"
echo "    http://localhost:$PORT"
echo ""
if [ -n "$LAN_IP" ]; then
echo "  Other devices on the same Wi-Fi/network:"
echo "    http://$LAN_IP:$PORT"
echo ""
echo "  Share the second link with other computers,"
echo "  tablets, or phones on the same network."
fi
echo "======================================================"
echo "  Default login:  admin / admin1234"
echo "======================================================"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload
