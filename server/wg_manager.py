import os
import json
import subprocess
import ipaddress
import base64
import secrets
from typing import Dict, List, Optional

WG_INTERFACE = os.environ.get("WG_INTERFACE", "wg-burmese")
CONFIG_DIR = os.environ.get("WG_CONFIG_DIR", "/etc/wireguard")
CONFIG_FILE = os.path.join(CONFIG_DIR, f"{WG_INTERFACE}.conf")
DATA_FILE = os.environ.get("WG_DATA_FILE", os.path.join(os.path.dirname(__file__), "vpn_data.json"))

class WireGuardManager:
    def __init__(self, interface: str = WG_INTERFACE, server_ip_range: str = "10.66.0.0/24", server_port: int = 51820):
        self.interface = interface
        self.server_ip_range = ipaddress.IPv4Network(server_ip_range, strict=False)
        self.server_port = int(os.environ.get("WG_PORT", server_port))
        self.server_vpn_ip = str(list(self.server_ip_range.hosts())[0])  # e.g., 10.66.0.1
        self.data_file = DATA_FILE
        self._ensure_initialized()
        self._auto_start_if_linux()

    def _auto_start_if_linux(self):
        """Auto-start WireGuard interface on Linux without requiring manual commands"""
        if os.name == 'nt':
            return
        try:
            # Check if interface is already up
            out = subprocess.run(["ip", "link", "show", self.interface], capture_output=True, text=True)
            if out.returncode != 0:
                # Interface not up, start via wg-quick
                if os.path.exists(CONFIG_FILE):
                    subprocess.run(["wg-quick", "up", CONFIG_FILE], capture_output=True, text=True)
        except Exception:
            pass

    def _generate_keys_native(self):
        """Generate WireGuard Curve25519 private/public key pair using wg command if available, or fallback."""
        try:
            priv = subprocess.check_output(["wg", "genkey"], text=True).strip()
            pub = subprocess.check_output(["wg", "pubkey"], input=priv, text=True).strip()
            return priv, pub
        except Exception:
            try:
                from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
                from cryptography.hazmat.primitives import serialization
                key = X25519PrivateKey.generate()
                priv_bytes = key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption()
                )
                pub_bytes = key.public_key().public_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PublicFormat.Raw
                )
                return base64.b64encode(priv_bytes).decode('ascii'), base64.b64encode(pub_bytes).decode('ascii')
            except ImportError:
                random_bytes = secrets.token_bytes(32)
                mock_key = base64.b64encode(random_bytes).decode('ascii')
                return mock_key, mock_key

    def _load_data(self) -> dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_data(self, data: dict):
        os.makedirs(os.path.dirname(os.path.abspath(self.data_file)), exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)

    def _ensure_initialized(self):
        data = self._load_data()
        if not data.get("server"):
            priv, pub = self._generate_keys_native()
            data["server"] = {
                "private_key": priv,
                "public_key": pub,
                "address": f"{self.server_vpn_ip}/24",
                "listen_port": self.server_port,
                "endpoint": os.environ.get("WG_SERVER_ENDPOINT", "YOUR_SERVER_PUBLIC_IP"),
                "dns": "1.1.1.1, 8.8.8.8",
                "mtu": 1420
            }
            data["clients"] = []
            self._save_data(data)
            self._sync_wg_conf()

    def get_server_info(self) -> dict:
        data = self._load_data()
        return data.get("server", {})

    def update_server_endpoint(self, endpoint: str, dns: str = "1.1.1.1, 8.8.8.8", mtu: int = 1420):
        data = self._load_data()
        if "server" not in data:
            self._ensure_initialized()
            data = self._load_data()
        data["server"]["endpoint"] = endpoint
        data["server"]["dns"] = dns
        data["server"]["mtu"] = mtu
        self._save_data(data)
        self._sync_wg_conf()

    def get_clients(self) -> List[dict]:
        data = self._load_data()
        clients = data.get("clients", [])
        status_map = self._get_active_wg_status()
        for client in clients:
            pub = client.get("public_key")
            if pub in status_map:
                client["latest_handshake"] = status_map[pub].get("latest_handshake", 0)
                client["transfer_rx"] = status_map[pub].get("transfer_rx", 0)
                client["transfer_tx"] = status_map[pub].get("transfer_tx", 0)
                client["endpoint_ip"] = status_map[pub].get("endpoint", "")
                client["is_online"] = (status_map[pub].get("latest_handshake", 0) > 0)
            else:
                client["latest_handshake"] = 0
                client["transfer_rx"] = 0
                client["transfer_tx"] = 0
                client["endpoint_ip"] = ""
                client["is_online"] = False
        return clients

    def _get_next_available_ip(self) -> str:
        data = self._load_data()
        used_ips = {self.server_vpn_ip}
        for c in data.get("clients", []):
            ip_only = c.get("allocated_ip", "").split("/")[0]
            if ip_only:
                used_ips.add(ip_only)

        for host in self.server_ip_range.hosts():
            host_str = str(host)
            if host_str not in used_ips:
                return host_str
        raise Exception("IP Pool exhausted (all 253 client IPs assigned)")

    def add_client(self, name: str, client_type: str = "device", custom_ip: Optional[str] = None) -> dict:
        data = self._load_data()
        allocated_ip = custom_ip if custom_ip else self._get_next_available_ip()
        priv, pub = self._generate_keys_native()

        client_entry = {
            "id": secrets.token_hex(6),
            "name": name,
            "type": client_type,
            "private_key": priv,
            "public_key": pub,
            "allocated_ip": f"{allocated_ip}/32",
            "allowed_ips": f"{allocated_ip}/32",
            "created_at": "2026-08-23 16:40:00",
            "enabled": True
        }

        if "clients" not in data:
            data["clients"] = []
        data["clients"].append(client_entry)
        self._save_data(data)
        self._sync_wg_conf()
        self._apply_runtime_peer(client_entry, action="add")
        return client_entry

    def delete_client(self, client_id: str):
        data = self._load_data()
        client_to_remove = None
        new_clients = []
        for c in data.get("clients", []):
            if c["id"] == client_id:
                client_to_remove = c
            else:
                new_clients.append(c)

        if client_to_remove:
            data["clients"] = new_clients
            self._save_data(data)
            self._sync_wg_conf()
            self._apply_runtime_peer(client_to_remove, action="remove")

    def _sync_wg_conf(self):
        """Generate and write the master wg0.conf on Linux Server"""
        data = self._load_data()
        server = data.get("server", {})
        if not server:
            return

        lines = [
            "[Interface]",
            f"Address = {server.get('address', '10.8.0.1/24')}",
            f"ListenPort = {server.get('listen_port', 51820)}",
            f"PrivateKey = {server.get('private_key', '')}",
            "SaveConfig = false",
            "# Non-destructive firewall NAT rules that coexist cleanly with other VPNs",
            f"PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -s {self.server_ip_range} -j MASQUERADE",
            f"PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -s {self.server_ip_range} -j MASQUERADE",
            ""
        ]

        for client in data.get("clients", []):
            if client.get("enabled", True):
                lines.extend([
                    f"# Peer: {client.get('name')} ({client.get('type')})",
                    "[Peer]",
                    f"PublicKey = {client.get('public_key')}",
                    f"AllowedIPs = {client.get('allowed_ips')}",
                    ""
                ])

        conf_content = "\n".join(lines)
        if os.name != 'nt' and os.path.exists(CONFIG_DIR):
            try:
                with open(CONFIG_FILE, "w") as f:
                    f.write(conf_content)
                os.chmod(CONFIG_FILE, 0o600)
            except Exception as e:
                print(f"[Warn] Could not write wg0.conf directly: {e}")

    def _apply_runtime_peer(self, client: dict, action: str = "add"):
        """Live update WireGuard kernel state without restarting interface"""
        if os.name == 'nt':
            return
        try:
            if action == "add":
                subprocess.run([
                    "wg", "set", self.interface,
                    "peer", client["public_key"],
                    "allowed-ips", client["allowed_ips"]
                ], check=False)
            elif action == "remove":
                subprocess.run([
                    "wg", "set", self.interface,
                    "peer", client["public_key"],
                    "remove"
                ], check=False)
        except Exception:
            pass

    def _get_active_wg_status(self) -> dict:
        """Parse `wg show wg0 dump` output"""
        status = {}
        if os.name == 'nt':
            return status
        try:
            output = subprocess.check_output(["wg", "show", self.interface, "dump"], text=True)
            lines = output.strip().split("\n")
            for line in lines[1:]:
                parts = line.split("\t")
                if len(parts) >= 8:
                    pubkey, psk, endpoint, allowed_ips, latest_handshake, rx, tx, keepalive = parts[:8]
                    status[pubkey] = {
                        "endpoint": endpoint,
                        "allowed_ips": allowed_ips,
                        "latest_handshake": int(latest_handshake) if latest_handshake.isdigit() else 0,
                        "transfer_rx": int(rx) if rx.isdigit() else 0,
                        "transfer_tx": int(tx) if tx.isdigit() else 0
                    }
        except Exception:
            pass
        return status

    # ================= Client / Router Configuration Exporters =================

    def generate_standard_conf(self, client_id: str) -> str:
        """Generate standard .conf file for Mobile, Windows, Mac, Linux"""
        data = self._load_data()
        server = data.get("server", {})
        client = next((c for c in data.get("clients", []) if c["id"] == client_id), None)
        if not client:
            return ""

        endpoint = server.get("endpoint", "YOUR_SERVER_IP")
        port = server.get("listen_port", 51820)
        dns = server.get("dns", "1.1.1.1, 8.8.8.8")
        mtu = server.get("mtu", 1420)

        conf = f"""[Interface]
PrivateKey = {client.get('private_key')}
Address = {client.get('allocated_ip')}
DNS = {dns}
MTU = {mtu}

[Peer]
PublicKey = {server.get('public_key')}
Endpoint = {endpoint}:{port}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
        return conf

    def generate_openwrt_script(self, client_id: str) -> str:
        """Generate 1-Click copy-paste setup script for OpenWrt Router (SSH)"""
        data = self._load_data()
        server = data.get("server", {})
        client = next((c for c in data.get("clients", []) if c["id"] == client_id), None)
        if not client:
            return ""

        endpoint = server.get("endpoint", "YOUR_SERVER_IP")
        port = server.get("listen_port", 51820)
        client_ip = client.get("allocated_ip")
        ip_without_mask = client_ip.split("/")[0]

        script = f"""#!/bin/sh
# ==========================================
# OpenWrt WireGuard Automated Setup Script
# Client: {client.get('name')}
# ==========================================

echo "[1/4] Installing WireGuard packages..."
opkg update
opkg install luci-proto-wireguard wireguard-tools luci-app-wireguard

echo "[2/4] Configuring WireGuard Network Interface (wg0)..."
uci set network.wg0=interface
uci set network.wg0.proto='wireguard'
uci set network.wg0.private_key='{client.get('private_key')}'
uci add_list network.wg0.addresses='{ip_without_mask}/24'

uci delete network.wgserver 2>/dev/null
uci set network.wgserver=wireguard_wg0
uci set network.wgserver.public_key='{server.get('public_key')}'
uci set network.wgserver.endpoint_host='{endpoint}'
uci set network.wgserver.endpoint_port='{port}'
uci set network.wgserver.persistent_keepalive='25'
uci set network.wgserver.route_allowed_ips='1'
uci add_list network.wgserver.allowed_ips='0.0.0.0/0'

echo "[3/4] Configuring Firewall Rules for WAN/VPN routing..."
uci add_list firewall.@zone[1].network='wg0'

echo "[4/4] Applying changes..."
uci commit network
uci commit firewall
/etc/init.d/network restart
/etc/init.d/firewall restart

echo "=========================================="
echo " WireGuard VPN Setup Completed on OpenWrt!"
echo " Check status with: wg show"
echo "=========================================="
"""
        return script

    def generate_mikrotik_script(self, client_id: str) -> str:
        """Generate RouterOS v7 Terminal command script for MikroTik Router"""
        data = self._load_data()
        server = data.get("server", {})
        client = next((c for c in data.get("clients", []) if c["id"] == client_id), None)
        if not client:
            return ""

        endpoint = server.get("endpoint", "YOUR_SERVER_IP")
        port = server.get("listen_port", 51820)
        client_ip = client.get("allocated_ip").split("/")[0]

        rsc = f"""# ====================================================
# MikroTik RouterOS v7 WireGuard VPN Client Script
# Client: {client.get('name')}
# Paste this entire block into MikroTik Terminal:
# ====================================================

# 1. Create WireGuard Client Interface
/interface wireguard add name=wg-client-vpn listen-port=13231 private-key="{client.get('private_key')}" comment="WireGuard VPN Tunnel"

# 2. Add WireGuard Server Peer
/interface wireguard peers add interface=wg-client-vpn public-key="{server.get('public_key')}" endpoint-address="{endpoint}" endpoint-port={port} allowed-address=0.0.0.0/0 persistent-keepalive=25s comment="{client.get('name')}-Peer"

# 3. Assign Client VPN IP Address
/ip address add address={client_ip}/24 interface=wg-client-vpn network=10.8.0.0 comment="WireGuard VPN IP"

# 4. Add NAT Masquerade Rule for WireGuard Interface
/ip firewall nat add chain=srcnat out-interface=wg-client-vpn action=masquerade comment="WireGuard NAT Masquerade"

# 5. Route Options:
# OPTION A: Route ALL internet traffic through VPN:
/ip route add dst-address=0.0.0.0/0 gateway=wg-client-vpn distance=2 comment="WireGuard Full Internet Route"

# OPTION B (Policy Based Routing / Split Tunnel):
# /routing table add name=to-vpn fib
# /ip route add dst-address=0.0.0.0/0 gateway=wg-client-vpn routing-table=to-vpn
# /routing rule add src-address=192.168.88.100/32 table=to-vpn comment="Specific Local Device -> VPN"
"""
        return rsc

    def generate_h3c_script(self, client_id: str) -> str:
        """Generate setup script and configuration commands for H3C Magic Routers (NX30 Pro, B365, etc.)"""
        data = self._load_data()
        server = data.get("server", {})
        client = next((c for c in data.get("clients", []) if c["id"] == client_id), None)
        if not client:
            return ""

        endpoint = server.get("endpoint", "YOUR_SERVER_IP")
        port = server.get("listen_port", 51820)
        client_ip = client.get("allocated_ip")
        ip_without_mask = client_ip.split("/")[0]

        script = f"""#!/bin/sh
# ==============================================================================
# H3C Magic Series (NX30 Pro, B365, R300) WireGuard VPN Automated Setup
# Client: {client.get('name')}
# ==============================================================================

echo "[1/4] Checking H3C Magic system packages..."
opkg update 2>/dev/null || true
opkg install kmod-wireguard wireguard-tools luci-proto-wireguard 2>/dev/null || true

echo "[2/4] Initializing WireGuard Interface (wg0)..."
uci delete network.wg0 2>/dev/null || true
uci set network.wg0=interface
uci set network.wg0.proto='wireguard'
uci set network.wg0.private_key='{client.get('private_key')}'
uci add_list network.wg0.addresses='{ip_without_mask}/24'

echo "[3/4] Configuring Burmese VPN Gateway Peer..."
uci delete network.wgserver 2>/dev/null || true
uci set network.wgserver=wireguard_wg0
uci set network.wgserver.public_key='{server.get('public_key')}'
uci set network.wgserver.endpoint_host='{endpoint}'
uci set network.wgserver.endpoint_port='{port}'
uci set network.wgserver.persistent_keepalive='25'
uci set network.wgserver.route_allowed_ips='1'
uci add_list network.wgserver.allowed_ips='0.0.0.0/0'

echo "[4/4] Setting up Firewall & Gateway Masquerade..."
uci add_list firewall.@zone[1].network='wg0' 2>/dev/null || true
uci commit network
uci commit firewall

/etc/init.d/network restart
/etc/init.d/firewall restart 2>/dev/null || true

echo "=========================================================="
echo " ✅ H3C Magic Router successfully configured for VPN!"
echo " Check tunnel status with: wg show"
echo "=========================================================="
"""
        return script
