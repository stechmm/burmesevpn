import os
import io
import json
import jinja2
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from wg_manager import WireGuardManager
from key_manager import AccessKeyManager

app = FastAPI(title="Dual-Engine VPN & Router Hub")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(TEMPLATES_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES_DIR))

wg_manager = WireGuardManager()
key_manager = AccessKeyManager()

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

class ServerSettingsRequest(BaseModel):
    endpoint: str
    dns: str = "1.1.1.1, 8.8.8.8"
    mtu: int = 1420

class TrafficSimulateRequest(BaseModel):
    added_mb: float = 500.0

# ================= Web Dashboard Route =================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    server_info = wg_manager.get_server_info()
    router_clients = wg_manager.get_clients()
    mobile_keys = key_manager.get_all_keys()
    
    template = jinja_env.get_template("index.html")
    html_content = template.render(
        server=server_info,
        router_clients=router_clients,
        total_routers=len(router_clients),
        mobile_keys=mobile_keys,
        total_keys=len(mobile_keys),
        active_keys=sum(1 for k in mobile_keys if k.get("status") == "active")
    )
    return HTMLResponse(content=html_content)

# ================= Part 1: Router API Routes =================

@app.get("/api/routers")
async def api_get_routers():
    return wg_manager.get_clients()

@app.post("/api/routers")
async def api_add_router(data: RouterClientCreateRequest):
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
async def api_delete_router(client_id: str):
    wg_manager.delete_client(client_id)
    return {"success": True, "message": "Router profile deleted"}

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

# ================= Part 2: Mobile Access Key API Routes =================

@app.get("/api/keys")
async def api_get_keys():
    return key_manager.get_all_keys()

@app.post("/api/keys")
async def api_create_key(data: MobileKeyCreateRequest):
    if not data.name or not data.name.strip():
        raise HTTPException(status_code=400, detail="Key/User name is required")
    try:
        new_key = key_manager.create_access_key(
            name=data.name.strip(),
            data_limit_gb=data.data_limit_gb,
            expire_days=data.expire_days,
            max_devices=data.max_devices
        )
        return {"success": True, "key": new_key}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/keys/{key_id}")
async def api_delete_key(key_id: str):
    key_manager.delete_key(key_id)
    return {"success": True, "message": "Key deleted"}

@app.post("/api/keys/{key_id}/toggle")
async def api_toggle_key(key_id: str):
    is_enabled = key_manager.toggle_key(key_id)
    return {"success": True, "enabled": is_enabled}

@app.post("/api/keys/{key_id}/reset-usage")
async def api_reset_key_usage(key_id: str):
    key_manager.reset_data_usage(key_id)
    return {"success": True, "message": "Data usage reset to 0 GB"}

@app.post("/api/keys/{key_id}/extend")
async def api_extend_key_expiry(key_id: str):
    key_manager.extend_expiry(key_id, extra_days=30)
    return {"success": True, "message": "Extended 30 days"}

@app.post("/api/keys/{key_id}/simulate-traffic")
async def api_simulate_traffic(key_id: str, data: TrafficSimulateRequest):
    key_manager.simulate_add_traffic(key_id, data.added_mb)
    return {"success": True, "message": f"Added {data.added_mb} MB traffic"}

# Subscription link endpoint for mobile apps
@app.get("/sub/{key_id}", response_class=PlainTextResponse)
async def api_get_subscription(key_id: str):
    keys = key_manager.get_all_keys()
    key = next((k for k in keys if k["id"] == key_id), None)
    if not key:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if key.get("status") != "active":
        return f"# Key {key.get('status')}: {key.get('status_text')}"
    return key.get("access_url", "")

# ================= General Server Settings =================

@app.post("/api/server/settings")
async def api_update_settings(data: ServerSettingsRequest):
    endpoint = data.endpoint.strip()
    wg_manager.update_server_endpoint(
        endpoint=endpoint,
        dns=data.dns.strip(),
        mtu=data.mtu
    )
    key_manager.update_server_host(endpoint)
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"🚀 Starting Dual-Engine VPN Hub on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)
