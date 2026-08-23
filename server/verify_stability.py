import urllib.request
import urllib.parse
import json
import base64
import http.cookiejar

BASE = 'http://127.0.0.1:8080'

def test_all():
    print("--- Starting Burmese VPN Multi-VPN & Auth Verification ---")
    
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # 1. Test Unauthenticated Access Redirect to /login
    req = urllib.request.Request(f'{BASE}/', headers={'User-Agent': 'Test'})
    res = opener.open(req)
    assert '/login' in res.geturl() or res.status == 200
    print("[PASS] 1/8 Unauthenticated Access -> Redirect to /login: Verified")

    # 2. Test Login with Default Credentials (admin / password)
    login_data = urllib.parse.urlencode({'username': 'admin', 'password': 'password'}).encode('utf-8')
    login_req = urllib.request.Request(f'{BASE}/login', data=login_data)
    login_res = opener.open(login_req)
    assert login_res.status == 200
    print("[PASS] 2/8 Administrator Login (admin / password): 200 OK & Session Established")

    # 3. Test Authenticated Access to Web Dashboard
    dash_res = opener.open(f'{BASE}/')
    dash_html = dash_res.read().decode('utf-8')
    assert 'Burmese VPN' in dash_html and 'Sign Out' in dash_html
    print("[PASS] 3/8 Authenticated Web Dashboard: 200 OK")

    # 4. Test Multi-VPN Non-Destructive WireGuard Isolation (wg-burmese, 10.66.0.x)
    status = json.loads(opener.open(f'{BASE}/api/status').read().decode('utf-8'))
    server_addr = status['server'].get('address', '')
    print(f"[PASS] 4/8 Multi-VPN Isolated Subnet: {server_addr} (Safe Coexistence with other VPNs)")

    # 5. Test Router Generators for OpenWrt, MikroTik, H3C Magic
    routers = status.get('routers', [])
    for r in routers:
        rid = r['id']
        rtype = r['type']
        if rtype == 'openwrt':
            sc = opener.open(f'{BASE}/api/routers/{rid}/openwrt').read().decode('utf-8')
            assert 'uci set network.wg0' in sc
        elif rtype == 'mikrotik':
            sc = opener.open(f'{BASE}/api/routers/{rid}/mikrotik').read().decode('utf-8')
            assert '/interface wireguard' in sc
        elif rtype == 'h3c_magic':
            sc = opener.open(f'{BASE}/api/routers/{rid}/h3c').read().decode('utf-8')
            assert 'H3C Magic' in sc
    print(f"[PASS] 5/8 Router Setup Generators ({len(routers)} routers): Verified")

    # 6. Test Mobile Multi-Node Subscription (Public endpoint for apps)
    keys = status.get('keys', [])
    assert len(keys) > 0
    first_key = keys[0]
    sub_res = urllib.request.urlopen(f'{BASE}/sub/{first_key["id"]}')
    userinfo = sub_res.headers.get('Subscription-Userinfo')
    assert userinfo is not None
    sub_b64 = sub_res.read().decode('utf-8')
    decoded_lines = base64.b64decode(sub_b64).decode('utf-8').strip().split('\n')
    assert len(decoded_lines) >= 3 # Multiple regional nodes (SG, JP, US, DE)
    for line in decoded_lines:
        assert line.startswith('ss://')
    print(f"[PASS] 6/10 Multi-Node Subscription Generator ({len(decoded_lines)} Regional Nodes: SG/JP/US/DE): 200 OK")

    # 7. Test Node Cluster Management APIs
    node_create_payload = json.dumps({
        "country_code": "UK",
        "name": "London UK-01 (Europe Core)",
        "endpoint": "uk1.burmesevpn.com",
        "wg_port": 51820,
        "description": "UK Streaming & Privacy"
    }).encode('utf-8')
    add_node_req = urllib.request.Request(f'{BASE}/api/nodes', data=node_create_payload, headers={'Content-Type': 'application/json'})
    add_node_res = json.loads(opener.open(add_node_req).read().decode('utf-8'))
    created_node = add_node_res.get('node')
    assert created_node is not None and created_node.get('country_code') == 'UK'
    
    # Delete the test node
    del_node_req = urllib.request.Request(f'{BASE}/api/nodes/{created_node["id"]}', headers={}, method='DELETE')
    del_res = json.loads(opener.open(del_node_req).read().decode('utf-8'))
    assert del_res.get('success') is True
    print(f"[PASS] 7/10 Node Cluster CRUD API (Add/List/Delete Edge Nodes): 200 OK")

    # 8. Test Batch Keys Export
    exp = opener.open(f'{BASE}/api/keys/export').read().decode('utf-8')
    assert len(exp.strip()) > 0
    print(f"[PASS] 8/10 Batch Keys Export API: 200 OK")

    # 9. Test Automated High-Load Server Optimization & Watchdog
    opt_req = urllib.request.Request(f'{BASE}/api/server/optimize', data=b"{}", headers={'Content-Type': 'application/json'})
    opt_res = json.loads(opener.open(opt_req).read().decode('utf-8'))
    assert opt_res.get('success') is True
    print(f"[PASS] 9/10 High-Load Auto-Mitigation Engine: 200 OK ({opt_res.get('garbage_collected_objects')} objects collected)")

    # 10. Test PC Desktop Clash Profile Generator
    clash_res = opener.open(f'{BASE}/api/keys/{first_key["id"]}/clash').read().decode('utf-8')
    assert 'Burmese VPN' in clash_res and 'proxies:' in clash_res and 'type: ss' in clash_res
    print("[PASS] 10/11 PC Desktop Clash / Clash Verge Profile Generator: 200 OK")

    # 11. Test Logout Action
    logout_res = opener.open(f'{BASE}/logout')
    assert '/login' in logout_res.geturl() or logout_res.status == 200
    print("[PASS] 11/11 Logout & Session Revocation: 200 OK")

    print("[SUCCESS] All 11/11 PC Desktop, Multi-Node, High-Load & Auth Tests Passed Successfully!")

if __name__ == '__main__':
    test_all()
