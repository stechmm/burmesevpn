import os
import io
import json
import time
import base64
import jinja2
from fastapi import FastAPI, Request, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, JSONResponse, FileResponse, RedirectResponse
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List

from wg_manager import WireGuardManager
from key_manager import AccessKeyManager
from node_manager import NodeManager
from auth import AuthManager
from watchdog import watchdog_engine

app = FastAPI(title="Burmese VPN - Dual-Engine Hub")
app.add_middleware(GZipMiddleware, minimum_size=500)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES_DIR))

wg_manager = WireGuardManager()
key_manager = AccessKeyManager()
node_manager = NodeManager()
auth_manager = AuthManager()

# ================= High-Load Rate Limiter =================
RATE_LIMIT_STORE: Dict[str, list] = {}

def apply_rate_limit(request: Request, max_reqs: int = 120, window_secs: int = 60):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    if client_ip not in RATE_LIMIT_STORE:
        RATE_LIMIT_STORE[client_ip] = []
    
    RATE_LIMIT_STORE[client_ip] = [t for t in RATE_LIMIT_STORE[client_ip] if now - t < window_secs]
    if len(RATE_LIMIT_STORE[client_ip]) >= max_reqs:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a moment before sending more requests."
        )
    RATE_LIMIT_STORE[client_ip].append(now)

@app.on_event("startup")
def on_startup():
    watchdog_engine.start()

@app.on_event("shutdown")
def on_shutdown():
    watchdog_engine.stop()

# ================= Auth Dependency =================

def is_authenticated(request: Request) -> bool:
    session_token = request.cookies.get("session_token")
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    return auth_manager.validate_session(session_token)

async def require_admin_api(request: Request):
    if not is_authenticated(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Please sign in as admin"
        )
    return True

# ================= Data Models =================

class RouterClientCreateRequest(BaseModel):
    name: str
    type: str = "openwrt"
    custom_ip: Optional[str] = None

class MobileKeyCreateRequest(BaseModel):
    name: str
    data_limit_gb: float = 20.0
    expire_days: int = 30
    max_devices: int = 1

class MobileKeyUpdateRequest(BaseModel):
    name: str
    data_limit_gb: float = 20.0
    max_devices: int = 1
    enabled: bool = True

class NodeCreateRequest(BaseModel):
    name: str
    country_code: str = "SG"
    endpoint: str
    wg_port: int = 51820
    description: Optional[str] = ""

class NodeUpdateRequest(BaseModel):
    name: str
    endpoint: str
    status: str = "online"
    description: Optional[str] = ""

class ServerSettingsRequest(BaseModel):
    endpoint: str
    dns: str = "1.1.1.1, 8.8.8.8"
    mtu: int = 1420
    admin_password: Optional[str] = None

class TrafficSimulateRequest(BaseModel):
    added_mb: float = 500.0

# ================= Authentication Routes =================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    apply_rate_limit(request, max_reqs=30, window_secs=60)
    if is_authenticated(request):
        return RedirectResponse(url="/", status_code=302)
    template = jinja_env.get_template("login.html")
    return HTMLResponse(content=template.render(error=error))

@app.post("/login")
async def login_action(request: Request, username: str = Form(...), password: str = Form(...)):
    apply_rate_limit(request, max_reqs=15, window_secs=60)
    token = auth_manager.authenticate(username, password)
    if not token:
        template = jinja_env.get_template("login.html")
        return HTMLResponse(
            content=template.render(error="Invalid username or password! Default is admin / password"),
            status_code=400
        )
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=60*60*24*30, # 30 days
        samesite="lax"
    )
    return response

@app.get("/logout")
async def logout_action(request: Request):
    session_token = request.cookies.get("session_token")
    if session_token:
        auth_manager.revoke_session(session_token)
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_token")
    return response

# ================= Web Dashboard Route =================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=302)

    server_info = wg_manager.get_server_info()
    router_clients = wg_manager.get_clients()
    mobile_keys = key_manager.get_all_keys()
    nodes_list = node_manager.get_all_nodes()
    watchdog_metrics = watchdog_engine.get_metrics()
    
    template = jinja_env.get_template("index.html")
    html_content = template.render(
        server=server_info,
        router_clients=router_clients,
        total_routers=len(router_clients),
        mobile_keys=mobile_keys,
        total_keys=len(mobile_keys),
        active_keys=sum(1 for k in mobile_keys if k.get("status") == "active"),
        nodes=nodes_list,
        total_nodes=len(nodes_list),
        watchdog=watchdog_metrics
    )
    return HTMLResponse(content=html_content)

# ================= Node Cluster Management API Routes =================

@app.get("/api/nodes")
async def api_get_nodes(auth=Depends(require_admin_api)):
    return node_manager.get_all_nodes()

@app.post("/api/nodes")
async def api_add_node(data: NodeCreateRequest, auth=Depends(require_admin_api)):
    if not data.name or not data.endpoint:
        raise HTTPException(status_code=400, detail="Name and endpoint are required")
    new_node = node_manager.add_node(
        name=data.name,
        country_code=data.country_code,
        endpoint=data.endpoint,
        wg_port=data.wg_port,
        description=data.description or ""
    )
    return {"success": True, "node": new_node}

@app.post("/api/nodes/{node_id}/update")
async def api_update_node(node_id: str, data: NodeUpdateRequest, auth=Depends(require_admin_api)):
    updated = node_manager.update_node(
        node_id=node_id,
        name=data.name,
        endpoint=data.endpoint,
        status=data.status,
        description=data.description or ""
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"success": True, "node": updated}

@app.delete("/api/nodes/{node_id}")
async def api_delete_node(node_id: str, auth=Depends(require_admin_api)):
    success = node_manager.delete_node(node_id)
    if not success:
        raise HTTPException(status_code=404, detail="Node not found or cannot delete master node")
    return {"success": True, "message": "Node removed"}

# ================= Part 1: Router API Routes =================

@app.get("/api/routers")
async def api_get_routers(auth=Depends(require_admin_api)):
    return wg_manager.get_clients()

@app.post("/api/routers")
async def api_add_router(data: RouterClientCreateRequest, auth=Depends(require_admin_api)):
    if not data.name or not data.name.strip():
        raise HTTPException(status_code=400, detail="Router name is required")
    try:
        new_client = wg_manager.add_client(
            name=data.name.strip(),
            client_type=data.type,
            custom_ip=data.custom_ip.strip() if data.custom_ip else None
        )
        return {"success": True, "client": new_client}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/routers/{client_id}")
async def api_delete_router(client_id: str, auth=Depends(require_admin_api)):
    wg_manager.delete_client(client_id)
    return {"success": True, "message": "Router gateway removed"}

# Router script generators (Public for 1-click execution)
@app.get("/api/routers/{client_id}/openwrt")
async def api_get_openwrt(client_id: str):
    script = wg_manager.generate_openwrt_script(client_id)
    if not script:
        raise HTTPException(status_code=404, detail="Router profile not found")
    clients = wg_manager.get_clients()
    client = next((c for c in clients if c["id"] == client_id), None)
    filename = f"openwrt_{client['name'].replace(' ', '_') if client else 'setup'}.sh"
    return Response(
        content=script,
        media_type="text/x-sh",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/routers/{client_id}/mikrotik")
async def api_get_mikrotik(client_id: str):
    rsc = wg_manager.generate_mikrotik_script(client_id)
    if not rsc:
        raise HTTPException(status_code=404, detail="Router profile not found")
    clients = wg_manager.get_clients()
    client = next((c for c in clients if c["id"] == client_id), None)
    filename = f"mikrotik_{client['name'].replace(' ', '_') if client else 'setup'}.rsc"
    return Response(
        content=rsc,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/routers/{client_id}/h3c")
async def api_get_h3c(client_id: str):
    script = wg_manager.generate_h3c_script(client_id)
    if not script:
        raise HTTPException(status_code=404, detail="Router profile not found")
    clients = wg_manager.get_clients()
    client = next((c for c in clients if c["id"] == client_id), None)
    filename = f"h3c_magic_{client['name'].replace(' ', '_') if client else 'setup'}.sh"
    return Response(
        content=script,
        media_type="text/x-sh",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@app.get("/api/routers/{client_id}/conf")
async def api_get_router_conf(client_id: str):
    conf = wg_manager.generate_standard_conf(client_id)
    if not conf:
        raise HTTPException(status_code=404, detail="Router profile not found")
    clients = wg_manager.get_clients()
    client = next((c for c in clients if c["id"] == client_id), None)
    filename = f"{client['name'].replace(' ', '_') if client else 'wireguard'}.conf"
    return Response(
        content=conf,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

# ================= Part 2: Mobile Access Key Routes =================

@app.get("/api/keys")
async def api_get_keys(auth=Depends(require_admin_api)):
    return key_manager.get_all_keys()

@app.post("/api/keys")
async def api_create_key(data: MobileKeyCreateRequest, auth=Depends(require_admin_api)):
    if not data.name or not data.name.strip():
        raise HTTPException(status_code=400, detail="Key/User name is required")
    try:
        new_key = key_manager.create_key(
            name=data.name.strip(),
            data_limit_gb=data.data_limit_gb,
            expire_days=data.expire_days,
            max_devices=data.max_devices
        )
        return {"success": True, "key": new_key}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/keys/{key_id}/update")
async def api_update_key(key_id: str, data: MobileKeyUpdateRequest, auth=Depends(require_admin_api)):
    updated = key_manager.update_key(
        key_id=key_id,
        name=data.name,
        data_limit_gb=data.data_limit_gb,
        max_devices=data.max_devices,
        enabled=data.enabled
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"success": True, "key": updated}

@app.delete("/api/keys/{key_id}")
async def api_delete_key(key_id: str, auth=Depends(require_admin_api)):
    key_manager.delete_key(key_id)
    return {"success": True, "message": "Key deleted"}

@app.post("/api/keys/{key_id}/toggle")
async def api_toggle_key(key_id: str, auth=Depends(require_admin_api)):
    is_enabled = key_manager.toggle_key(key_id)
    return {"success": True, "enabled": is_enabled}

@app.post("/api/keys/{key_id}/reset-usage")
async def api_reset_key_usage(key_id: str, auth=Depends(require_admin_api)):
    key_manager.reset_data_usage(key_id)
    return {"success": True, "message": "Data usage reset to 0 GB"}

@app.post("/api/keys/{key_id}/extend")
async def api_extend_key_expiry(key_id: str, auth=Depends(require_admin_api)):
    key_manager.extend_expiry(key_id, extra_days=30)
    return {"success": True, "message": "Extended 30 days"}

@app.post("/api/keys/{key_id}/simulate-traffic")
async def api_simulate_traffic(key_id: str, data: TrafficSimulateRequest, auth=Depends(require_admin_api)):
    key_manager.simulate_add_traffic(key_id, data.added_mb)
    return {"success": True, "message": f"Added {data.added_mb} MB traffic"}

# Multi-Node Subscription link endpoint for mobile apps (v2rayNG, Shadowrocket, Sing-box, Clash, Outline)
@app.get("/sub/{key_id}")
async def api_get_subscription(key_id: str, request: Request):
    apply_rate_limit(request, max_reqs=60, window_secs=60)
    keys = key_manager.get_all_keys()
    key = next((k for k in keys if k["id"] == key_id), None)
    if not key:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    nodes = node_manager.get_all_nodes()
    cipher = key.get("cipher", "chacha20-ietf-poly1305")
    password = key.get("password", "")
    port = key.get("port", 8388)
    
    node_urls = []
    for node in nodes:
        if node.get("status") == "online":
            flag = node.get("flag", "🌐")
            node_name = node.get("name", "Node")
            endpoint = node.get("endpoint", "127.0.0.1")
            
            # Shadowsocks AEAD format: ss://BASE64(cipher:password@endpoint:port)#Tag
            user_info_raw = f"{cipher}:{password}@{endpoint}:{port}"
            encoded_user_info = base64.b64encode(user_info_raw.encode('utf-8')).decode('utf-8')
            tag = f"{flag} Burmese VPN - {node_name}"
            ss_url = f"ss://{encoded_user_info}#{tag}"
            node_urls.append(ss_url)
            
    if not node_urls:
        node_urls.append(key.get("access_url", ""))
        
    combined_content = "\n".join(node_urls)
    b64_content = base64.b64encode(combined_content.encode('utf-8')).decode('utf-8')
    
    used_bytes = int(key.get("used_bytes", 0))
    limit_bytes = int(key.get("data_limit_gb", 0) * 1024 * 1024 * 1024)
    expire_timestamp = int(key.get("expire_timestamp", 0))
    
    headers = {
        "Subscription-Userinfo": f"upload=0; download={used_bytes}; total={limit_bytes}; expire={expire_timestamp}",
        "Profile-Update-Interval": "12",
        "Content-Disposition": f'inline; filename="{key.get("name", "vpn")}.txt"'
    }
    return Response(content=b64_content, media_type="text/plain; charset=utf-8", headers=headers)

@app.get("/api/keys/export")
async def api_export_keys(auth=Depends(require_admin_api)):
    keys = key_manager.get_all_keys()
    active_urls = [k["access_url"] for k in keys if k.get("status") == "active" and k.get("access_url")]
    content = "\n".join(active_urls)
    return Response(
        content=content,
        media_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="burmese_vpn_active_keys.txt"'}
    )

@app.get("/api/status")
async def api_get_live_status(auth=Depends(require_admin_api)):
    server_info = wg_manager.get_server_info()
    router_clients = wg_manager.get_clients()
    mobile_keys = key_manager.get_all_keys()
    nodes_list = node_manager.get_all_nodes()
    watchdog_metrics = watchdog_engine.get_metrics()
    return {
        "server": server_info,
        "total_routers": len(router_clients),
        "total_keys": len(mobile_keys),
        "total_nodes": len(nodes_list),
        "active_keys": sum(1 for k in mobile_keys if k.get("status") == "active"),
        "nodes": nodes_list,
        "watchdog": watchdog_metrics,
        "keys": mobile_keys,
        "routers": router_clients
    }

# ================= Automated High-Load Optimization & Server Settings =================

@app.post("/api/server/optimize")
async def api_optimize_server(auth=Depends(require_admin_api)):
    """Trigger manual instant memory reclamation & garbage collection"""
    res = watchdog_engine.trigger_optimization(reason="Admin Manual 1-Click Optimization")
    return res

@app.post("/api/server/settings")
async def api_update_settings(data: ServerSettingsRequest, auth=Depends(require_admin_api)):
    endpoint = data.endpoint.strip()
    wg_manager.update_server_endpoint(
        endpoint=endpoint,
        dns=data.dns.strip(),
        mtu=data.mtu
    )
    key_manager.update_server_host(endpoint)
    if data.admin_password and data.admin_password.strip():
        auth_manager.update_credentials("admin", data.admin_password.strip())
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    workers = max(1, min(4, os.cpu_count() or 1))
    print(f"🚀 Starting Dual-Engine VPN Hub on http://{host}:{port} with {workers} workers")
    uvicorn.run("app:app", host=host, port=port, reload=True)
