#!/bin/sh
# ==============================================================================
# H3C Magic Series (NX30 Pro, B365, R300, etc.) Automated WireGuard VPN Setup
# Usage: ./setup_h3c.sh <CLIENT_PRIV_KEY> <SERVER_PUB_KEY> <SERVER_ENDPOINT> <SERVER_PORT> <CLIENT_VPN_IP>
# ==============================================================================

set -e

CLIENT_PRIV_KEY="$1"
SERVER_PUB_KEY="$2"
SERVER_ENDPOINT="$3"
SERVER_PORT="${4:-51820}"
CLIENT_IP="${5:-10.8.0.2}"

if [ -z "$CLIENT_PRIV_KEY" ] || [ -z "$SERVER_PUB_KEY" ] || [ -z "$SERVER_ENDPOINT" ]; then
  echo "Usage: $0 <CLIENT_PRIV_KEY> <SERVER_PUB_KEY> <SERVER_ENDPOINT> [SERVER_PORT] [CLIENT_IP]"
  echo "Or generate auto-script directly from Burmese VPN Web Dashboard!"
  exit 1
fi

echo ">> 1. Installing H3C WireGuard Kernel Modules & Tools..."
opkg update 2>/dev/null || true
opkg install kmod-wireguard wireguard-tools luci-proto-wireguard 2>/dev/null || true

echo ">> 2. Configuring WireGuard Interface (wg0)..."
uci delete network.wg0 2>/dev/null || true
uci set network.wg0=interface
uci set network.wg0.proto='wireguard'
uci set network.wg0.private_key="$CLIENT_PRIV_KEY"
uci add_list network.wg0.addresses="${CLIENT_IP}/24"

echo ">> 3. Configuring Burmese VPN Server Peer..."
uci delete network.wgserver 2>/dev/null || true
uci set network.wgserver=wireguard_wg0
uci set network.wgserver.public_key="$SERVER_PUB_KEY"
uci set network.wgserver.endpoint_host="$SERVER_ENDPOINT"
uci set network.wgserver.endpoint_port="$SERVER_PORT"
uci set network.wgserver.persistent_keepalive='25'
uci set network.wgserver.route_allowed_ips='1'
uci add_list network.wgserver.allowed_ips='0.0.0.0/0'

echo ">> 4. Setting up Firewall Zone for H3C WAN..."
uci add_list firewall.@zone[1].network='wg0' 2>/dev/null || true

echo ">> 5. Committing and Restarting Services..."
uci commit network
uci commit firewall 2>/dev/null || true

/etc/init.d/network restart
/etc/init.d/firewall restart 2>/dev/null || true

echo "=========================================================="
echo " ✅ H3C Magic Router successfully configured for VPN!"
echo " Check status with: wg show"
echo "=========================================================="
