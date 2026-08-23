#!/usr/bin/env bash
# ==============================================================================
# WireGuard VPN & Multi-Router Management Hub - 1-Click Automated Linux Installer
# Supported OS: Ubuntu 20.04/22.04/24.04, Debian 11/12, CentOS/Rocky/AlmaLinux 8/9
# ==============================================================================

set -e

# Ensure running as root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Error: Please run this installer as root (e.g. sudo bash install.sh)"
  exit 1
fi

echo "==================================================================="
echo "  🚀 WireGuard VPN & Multi-Router Management Hub Setup Starting..."
echo "==================================================================="

# 1. Detect Distribution
if [ -f /etc/debian_version ]; then
  OS="debian"
  apt-get update -y
  apt-get install -y wireguard wireguard-tools iptables qrencode curl python3 python3-pip python3-venv
elif [ -f /etc/redhat-release ]; then
  OS="redhat"
  dnf install -y epel-release || yum install -y epel-release
  dnf install -y wireguard-tools iptables qrencode curl python3 python3-pip
else
  echo "⚠️ Unknown OS distribution. Continuing with standard package assumptions..."
fi

# 2. Enable Kernel IP Forwarding
echo "[1/5] Enabling Kernel IPv4/IPv6 packet forwarding..."
cat <<EOF > /etc/sysctl.d/99-wireguard-forwarding.conf
net.ipv4.ip_forward=1
net.ipv6.conf.all.forwarding=1
EOF
sysctl -p /etc/sysctl.d/99-wireguard-forwarding.conf

# 3. Detect Default Network Interface & Public IP
DEFAULT_NIC=$(ip route show default 2>/dev/null | awk '{print $5}' | head -n1)
if [ -z "$DEFAULT_NIC" ]; then
  DEFAULT_NIC="eth0"
fi
PUBLIC_IP=$(curl -s -m 5 https://api.ipify.org || curl -s -m 5 https://ifconfig.me || echo "YOUR_SERVER_IP")

echo "Detected Network Interface: $DEFAULT_NIC"
echo "Detected Server Public IP: $PUBLIC_IP"

# 4. Prepare Directories and Python Virtualenv
echo "[2/5] Setting up Web Admin Hub service..."
INSTALL_DIR="/opt/wireguard-hub"
mkdir -p "$INSTALL_DIR"
mkdir -p /etc/wireguard

# Copy server code
cp -r server/* "$INSTALL_DIR/"

# Setup Python Virtual Environment
python3 -m venv "$INSTALL_DIR/venv"
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Set initial public IP
export WG_SERVER_ENDPOINT="$PUBLIC_IP"

# 5. Create Systemd Service for Web Panel
echo "[3/5] Creating Systemd service for Web Control Panel..."
cat <<EOF > /etc/systemd/system/wireguard-webhub.service
[Unit]
Description=WireGuard VPN & Router Web Management Hub
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
systemctl enable --now wireguard-webhub.service

# 6. Firewall Configuration (UFW / Firewalld)
echo "[4/5] Adjusting Firewall Ports (51820 UDP, 8080 TCP)..."
if command -v ufw >/dev/null 2>&1; then
  ufw allow 51820/udp comment "WireGuard VPN" >/dev/null 2>&1 || true
  ufw allow 8080/tcp comment "WireGuard Web Admin" >/dev/null 2>&1 || true
elif command -v firewall-cmd >/dev/null 2>&1; then
  firewall-cmd --permanent --add-port=51820/udp >/dev/null 2>&1 || true
  firewall-cmd --permanent --add-port=8080/tcp >/dev/null 2>&1 || true
  firewall-cmd --reload >/dev/null 2>&1 || true
fi

echo "[5/5] Finalizing setup..."
sleep 2

echo "==================================================================="
echo "  ✅ WireGuard VPN Server & Web Hub Installation Completed!"
echo "==================================================================="
echo ""
echo "  🌐 Web Admin Dashboard URL : http://${PUBLIC_IP}:8080"
echo "  🛡️ WireGuard VPN Port       : 51820 (UDP)"
echo "  📁 Installation Directory    : /opt/wireguard-hub"
echo ""
echo "  💡 Tips:"
echo "  - Web Dashboard ဖွင့်ပြီး Add Client / Router မှတစ်ဆင့်"
echo "    ဖုန်း၊ PC သို့မဟုတ် OpenWrt / MikroTik အတွက် config များထုတ်ယူနိုင်ပါသည်။"
echo "  - Server service status စစ်ဆေးရန်: systemctl status wireguard-webhub"
echo "==================================================================="
