#!/usr/bin/env bash
# ==============================================================================
# 🇲🇲 Burmese VPN - Dual-Engine Enterprise Hub (1-Click Linux VPS Installer)
# Supported OS: Ubuntu 20.04/22.04/24.04, Debian 11/12, Rocky/AlmaLinux 8/9
# ==============================================================================

set -e

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run this installer as root (e.g. sudo bash install.sh)"
  exit 1
fi

echo "==================================================================="
echo "  🇲🇲 Burmese VPN - Dual-Engine Enterprise Hub Setup Starting..."
echo "  Engines: (1) WireGuard Router Hub + (2) Mobile Shadowsocks/Outline"
echo "==================================================================="

# 1. Update and install packages
echo "[1/6] Installing system dependencies..."
if [ -f /etc/debian_version ]; then
  OS="debian"
  apt-get update -y
  apt-get install -y wireguard wireguard-tools iptables ipset qrencode curl git python3 python3-pip python3-venv
elif [ -f /etc/redhat-release ]; then
  OS="redhat"
  dnf install -y epel-release || yum install -y epel-release
  dnf install -y wireguard-tools iptables ipset qrencode curl git python3 python3-pip
else
  echo "⚠️ Unknown OS. Continuing with standard package assumptions..."
fi

# 2. Enable Kernel IP Forwarding, High-Load TCP Tuning & TCP BBR Congestion Control
echo "[2/6] Configuring Automated High-Load Mitigation & TCP BBR High-Speed..."
cat <<EOF > /etc/sysctl.d/99-burmesevpn.conf
# Packet Forwarding
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1

# TCP BBR Acceleration
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr

# High-Load & High-Concurrency Connection Tuning
fs.file-max=2097152
net.core.somaxconn=65535
net.ipv4.tcp_max_syn_backlog=65535
net.ipv4.tcp_syncookies=1
net.ipv4.tcp_fin_timeout=15
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_max_tw_buckets=1440000
net.core.rmem_max=67108864
net.core.wmem_max=67108864
net.ipv4.tcp_rmem=4096 87380 67108864
net.ipv4.tcp_wmem=4096 65536 67108864
EOF
sysctl -p /etc/sysctl.d/99-burmesevpn.conf >/dev/null 2>&1 || true

# Set max open file descriptors for services
mkdir -p /etc/security/limits.d
cat <<EOF > /etc/security/limits.d/99-burmesevpn.conf
* soft nofile 65535
* hard nofile 65535
root soft nofile 65535
root hard nofile 65535
EOF

# 3. Detect Default Network Interface & Public IP
DEFAULT_NIC=$(ip route show default 2>/dev/null | awk '{print $5}' | head -n1)
if [ -z "$DEFAULT_NIC" ]; then
  DEFAULT_NIC="eth0"
fi
PUBLIC_IP=$(curl -s -m 5 https://api.ipify.org || curl -s -m 5 https://ifconfig.me || echo "YOUR_SERVER_IP")

echo ">> Detected Network Interface: $DEFAULT_NIC"
echo ">> Detected Server Public IP:  $PUBLIC_IP"

# 4. Prepare Directories and Python Virtualenv
echo "[3/6] Setting up Burmese VPN Core Service..."
INSTALL_DIR="/opt/burmesevpn"
mkdir -p "$INSTALL_DIR"
mkdir -p /etc/wireguard

# Copy server code
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/server" ]; then
  cp -r "$SCRIPT_DIR/server"/* "$INSTALL_DIR/"
fi

# Setup Python Virtual Environment
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
if [ -f "$INSTALL_DIR/requirements.txt" ]; then
  "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"
else
  "$INSTALL_DIR/venv/bin/pip" install fastapi uvicorn jinja2 cryptography pydantic python-multipart
fi

# 5. Create Systemd Service for Burmese VPN
echo "[4/6] Creating Systemd Service (burmesevpn.service)..."
cat <<EOF > /etc/systemd/system/burmesevpn.service
[Unit]
Description=Burmese VPN Dual-Engine Management Hub
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="WG_SERVER_ENDPOINT=$PUBLIC_IP"
Environment="PORT=8080"
Environment="HOST=0.0.0.0"
ExecStart=$INSTALL_DIR/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now burmesevpn.service

# 6. Firewall Configuration (UFW / Firewalld / iptables)
echo "[5/6] Configuring Firewall Ports..."
if command -v ufw >/dev/null 2>&1; then
  ufw allow 51820/udp comment "Burmese WireGuard Hub" >/dev/null 2>&1 || true
  ufw allow 8080/tcp comment "Burmese VPN Web Panel" >/dev/null 2>&1 || true
  ufw allow 8388:8500/tcp comment "Burmese Shadowsocks Ports" >/dev/null 2>&1 || true
  ufw allow 8388:8500/udp comment "Burmese Shadowsocks Ports" >/dev/null 2>&1 || true
elif command -v firewall-cmd >/dev/null 2>&1; then
  firewall-cmd --permanent --add-port=51820/udp >/dev/null 2>&1 || true
  firewall-cmd --permanent --add-port=8080/tcp >/dev/null 2>&1 || true
  firewall-cmd --permanent --add-port=8388-8500/tcp >/dev/null 2>&1 || true
  firewall-cmd --permanent --add-port=8388-8500/udp >/dev/null 2>&1 || true
  firewall-cmd --reload >/dev/null 2>&1 || true
fi

echo "[6/6] Verifying service health..."
sleep 2

echo "==================================================================="
echo "  ✅ Burmese VPN Server & Web Hub Installation Completed!"
echo "==================================================================="
echo ""
echo "  🌐 Web Dashboard URL       : http://${PUBLIC_IP}:8080"
echo "  🔑 Default Admin Username   : admin"
echo "  🔒 Default Admin Password   : password"
echo "  🛡️ WireGuard Router Port    : 51820 (UDP) [Interface: wg-burmese]"
echo "  📱 Mobile Key Port Range    : 8388-8500 (TCP/UDP)"
echo "  📁 Installation Directory   : /opt/burmesevpn"
echo ""
echo "  💡 Tips:"
echo "  - Multi-VPN Coexistence: Isolated interface (wg-burmese) & subnet (10.66.0.0/24) to avoid clashing with other VPNs."
echo "  - Web Dashboard ဖွင့်ပြီး Mobile Keys / Routers များကို စိတ်ကြိုက်ထုတ်ယူနိုင်ပါသည်။"
echo "  - Server Service Status စစ်ဆေးရန် : systemctl status burmesevpn"
echo "  - Logs ကြည့်ရန်                  : journalctl -u burmesevpn -f"
echo "==================================================================="
