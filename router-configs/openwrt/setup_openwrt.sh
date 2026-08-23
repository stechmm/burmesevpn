#!/bin/sh
# ==============================================================================
# OpenWrt WireGuard Full Client & Gateway Setup Script
# Usage: ./setup_openwrt.sh <PRIVATE_KEY> <SERVER_PUB_KEY> <SERVER_ENDPOINT> <SERVER_PORT> <CLIENT_VPN_IP>
# Example: ./setup_openwrt.sh "aBcD...=" "xYz1...=" "203.0.113.195" 51820 "10.8.0.2"
# ==============================================================================

set -e

CLIENT_PRIV_KEY="$1"
SERVER_PUB_KEY="$2"
SERVER_ENDPOINT="$3"
SERVER_PORT="${4:-51820}"
CLIENT_IP="${5:-10.8.0.2}"

if [ -z "$CLIENT_PRIV_KEY" ] || [ -z "$SERVER_PUB_KEY" ] || [ -z "$SERVER_ENDPOINT" ]; then
  echo "Usage: $0 <CLIENT_PRIV_KEY> <SERVER_PUB_KEY> <SERVER_ENDPOINT> [SERVER_PORT] [CLIENT_IP]"
  echo "Or generate auto-script directly from the Web Admin Dashboard!"
  exit 1
fi

echo ">> 1. Installing WireGuard Packages..."
opkg update
opkg install luci-proto-wireguard wireguard-tools luci-app-wireguard

echo ">> 2. Setting up WireGuard Interface (wg0)..."
uci delete network.wg0 2>/dev/null || true
uci set network.wg0=interface
uci set network.wg0.proto='wireguard'
uci set network.wg0.private_key="$CLIENT_PRIV_KEY"
uci add_list network.wg0.addresses="${CLIENT_IP}/24"

echo ">> 3. Setting up WireGuard Peer (Server)..."
uci delete network.wgserver 2>/dev/null || true
uci set network.wgserver=wireguard_wg0
uci set network.wgserver.public_key="$SERVER_PUB_KEY"
uci set network.wgserver.endpoint_host="$SERVER_ENDPOINT"
uci set network.wgserver.endpoint_port="$SERVER_PORT"
uci set network.wgserver.persistent_keepalive='25'
uci set network.wgserver.route_allowed_ips='1'
uci add_list network.wgserver.allowed_ips='0.0.0.0/0'

echo ">> 4. Configuring Firewall Zone..."
uci add_list firewall.@zone[1].network='wg0'

echo ">> 5. Committing and Restarting Services..."
uci commit network
uci commit firewall

/etc/init.d/network restart
/etc/init.d/firewall restart

echo "=========================================================="
echo " ✅ WireGuard successfully configured on OpenWrt!"
echo " Test with: wg show"
echo "=========================================================="
