# ==============================================================================
# MikroTik RouterOS v7 WireGuard Full Client Script Template
# Compatible with: RouterOS v7.1 and above
# ==============================================================================

# 1. WireGuard Interface Setup
/interface wireguard
add comment="WireGuard VPN Tunnel" listen-port=13231 mtu=1420 name=wg-client-vpn private-key="CLIENT_PRIVATE_KEY_HERE"

# 2. Add WireGuard Peer (Server)
/interface wireguard peers
add allowed-address=0.0.0.0/0 comment="VPN-Server-Peer" endpoint-address="SERVER_PUBLIC_IP" endpoint-port=51820 interface=wg-client-vpn persistent-keepalive=25s public-key="SERVER_PUBLIC_KEY_HERE"

# 3. Assign Client VPN IP
/ip address
add address=10.8.0.2/24 comment="WireGuard VPN IP" interface=wg-client-vpn network=10.8.0.0

# 4. Add NAT Masquerade Rule
/ip firewall nat
add action=masquerade chain=srcnat comment="WireGuard VPN NAT" out-interface=wg-client-vpn

# 5. Route Traffic
# Option 1: Route All Devices Through VPN
/ip route
add comment="Default VPN Route" distance=2 dst-address=0.0.0.0/0 gateway=wg-client-vpn
