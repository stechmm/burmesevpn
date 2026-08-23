#!/bin/bash
# ==============================================================================
# Burmese VPN — 1-Click Connection & Port Fix Script
# Resolves Endless Spinner / Blocked Port 8080 by switching to Standard HTTP Port 80
# ==============================================================================

set -e

if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run as root (sudo bash fix_connection.sh)"
  exit 1
fi

echo "=========================================================="
echo "🔧 Fixing Burmese VPN Web Panel Connection & Port Access..."
echo "=========================================================="

# 1. Open all necessary ports in iptables and UFW
echo "[1/4] Opening OS Firewall Ports (80, 8080, 51820, 8388-8500)..."
iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT 2>/dev/null || true
iptables -I INPUT 1 -p tcp --dport 8080 -j ACCEPT 2>/dev/null || true
iptables -I INPUT 1 -p udp --dport 51820 -j ACCEPT 2>/dev/null || true
iptables -I INPUT 1 -p tcp --dport 8388:8500 -j ACCEPT 2>/dev/null || true
iptables -I INPUT 1 -p udp --dport 8388:8500 -j ACCEPT 2>/dev/null || true

if command -v ufw >/dev/null 2>&1; then
  ufw allow 80/tcp >/dev/null 2>&1 || true
  ufw allow 8080/tcp >/dev/null 2>&1 || true
  ufw allow 51820/udp >/dev/null 2>&1 || true
  ufw allow 8388:8500/tcp >/dev/null 2>&1 || true
  ufw allow 8388:8500/udp >/dev/null 2>&1 || true
  ufw reload >/dev/null 2>&1 || true
fi

# 2. Switch Service to Standard HTTP Port 80 (Avoids ISP blocking of 8080)
echo "[2/4] Switching Web Dashboard to Port 80 (Standard Web Port)..."
if [ -f /etc/systemd/system/burmesevpn.service ]; then
  sed -i 's/PORT=8080/PORT=80/g' /etc/systemd/system/burmesevpn.service
  systemctl daemon-reload
  systemctl restart burmesevpn
fi

# 3. Test Local Connectivity
echo "[3/4] Testing Local Web Server Connectivity..."
sleep 2
LOCAL_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80/login 2>/dev/null || curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8080/login 2>/dev/null || echo "FAILED")

PUBLIC_IP=$(curl -s -m 5 https://api.ipify.org || curl -s -m 5 https://ifconfig.me || echo "YOUR_SERVER_IP")

echo "=========================================================="
if [ "$LOCAL_TEST" == "200" ] || [ "$LOCAL_TEST" == "302" ]; then
  echo "✅ SUCCESS! Burmese VPN is responding perfectly (HTTP $LOCAL_TEST)!"
else
  echo "⚠️ Status code: $LOCAL_TEST (Service is starting up...)"
fi
echo "=========================================================="
echo ""
echo "🌐 Browser မှ အောက်ပါ Link အသစ်ကို ဖွင့်ကြည့်ပေးပါ:"
echo "👉 URL:      http://$PUBLIC_IP"
echo "             (Port 80 သို့ ပြောင်းလိုက်သဖြင့် :8080 ရိုက်စရာမလိုတော့ပါ)"
echo "🔑 Username: admin"
echo "🔒 Password: password"
echo ""
echo "💡 Note: Browser တွင် https:// မဟုတ်ဘဲ http:// ဖြစ်နေစေရန် သတိပြုပါ"
echo "=========================================================="
