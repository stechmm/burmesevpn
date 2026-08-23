import os
import json
import base64
import secrets
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict

DATA_FILE = os.environ.get("VPN_KEYS_DATA_FILE", os.path.join(os.path.dirname(__file__), "access_keys_data.json"))

class AccessKeyManager:
    """
    Manages Mobile / Client Access Keys (Outline / Shadowsocks / V2Ray style)
    with strict Data Quotas, Expiration Dates, and Max Device Limits.
    """
    def __init__(self, default_server_host: str = "YOUR_SERVER_PUBLIC_IP", base_port: int = 8388):
        self.data_file = DATA_FILE
        self.default_server_host = default_server_host
        self.base_port = base_port
        self.cipher_method = "chacha20-ietf-poly1305"
        self._ensure_initialized()

    def _load_data(self) -> dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"keys": [], "server_config": {"host": self.default_server_host, "base_port": self.base_port}}

    def _save_data(self, data: dict):
        os.makedirs(os.path.dirname(os.path.abspath(self.data_file)), exist_ok=True)
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)

    def _ensure_initialized(self):
        data = self._load_data()
        if not data.get("keys"):
            data["server_config"] = {
                "host": os.environ.get("WG_SERVER_ENDPOINT", self.default_server_host),
                "cipher": self.cipher_method,
                "base_port": self.base_port
            }
            self._save_data(data)

    def get_server_config(self) -> dict:
        data = self._load_data()
        return data.get("server_config", {})

    def update_server_host(self, host: str):
        data = self._load_data()
        data["server_config"]["host"] = host
        self._save_data(data)

    def _get_next_port(self) -> int:
        data = self._load_data()
        used_ports = {k.get("port") for k in data.get("keys", []) if k.get("port")}
        port = self.base_port
        while port in used_ports:
            port += 1
        return port

    def create_access_key(
        self,
        name: str,
        data_limit_gb: float = 0.0,   # 0 = Unlimited
        expire_days: int = 30,        # 0 = Unlimited days
        max_devices: int = 1,         # Concurrent devices limit
        custom_port: Optional[int] = None
    ) -> dict:
        data = self._load_data()
        key_id = secrets.token_hex(6)
        password = secrets.token_urlsafe(16)
        port = custom_port if custom_port else self._get_next_port()
        
        now = datetime.now()
        created_at_str = now.strftime("%Y-%m-%d %H:%M:%S")
        
        if expire_days > 0:
            expire_date = now + timedelta(days=expire_days)
            expire_date_str = expire_date.strftime("%Y-%m-%d %H:%M:%S")
            expire_timestamp = int(expire_date.timestamp())
        else:
            expire_date_str = "Never (Unlimited)"
            expire_timestamp = 0

        data_limit_bytes = int(data_limit_gb * 1024 * 1024 * 1024) if data_limit_gb > 0 else 0

        key_entry = {
            "id": key_id,
            "name": name,
            "port": port,
            "password": password,
            "cipher": self.cipher_method,
            "created_at": created_at_str,
            "expire_days": expire_days,
            "expire_date": expire_date_str,
            "expire_timestamp": expire_timestamp,
            "data_limit_gb": data_limit_gb,
            "data_limit_bytes": data_limit_bytes,
            "used_bytes": 0,
            "max_devices": max_devices,
            "active_devices_count": 0,
            "active_device_ips": [],
            "enabled": True,
            "status": "active" # active, expired, quota_exceeded, disabled
        }

        data["keys"].append(key_entry)
        self._save_data(data)
        return key_entry

    def get_all_keys(self) -> List[dict]:
        """Evaluates auto-expiration and quota limits and returns live statuses"""
        data = self._load_data()
        server_host = data.get("server_config", {}).get("host", self.default_server_host)
        now_ts = int(time.time())

        for k in data.get("keys", []):
            # Check 1: Manual disabled
            if not k.get("enabled", True):
                k["status"] = "disabled"
                k["status_text"] = "ပိတ်ထားသည် (Disabled)"
            # Check 2: Expiration Date
            elif k.get("expire_timestamp", 0) > 0 and now_ts >= k.get("expire_timestamp"):
                k["status"] = "expired"
                k["status_text"] = "ရက်စေ့သွားပါပြီ (Expired)"
                k["enabled"] = False
            # Check 3: Data Quota Limit
            elif k.get("data_limit_bytes", 0) > 0 and k.get("used_bytes", 0) >= k.get("data_limit_bytes"):
                k["status"] = "quota_exceeded"
                k["status_text"] = "ဒေတာပြည့်သွားပါပြီ (Quota Exceeded)"
                k["enabled"] = False
            else:
                k["status"] = "active"
                k["status_text"] = "အသုံးပြုနိုင်သည် (Active)"

            # Calculate percentages & human readable strings
            used_mb = k.get("used_bytes", 0) / (1024 * 1024)
            if used_mb >= 1024:
                k["used_readable"] = f"{used_mb / 1024:.2f} GB"
            else:
                k["used_readable"] = f"{used_mb:.1f} MB"

            if k.get("data_limit_gb", 0) > 0:
                k["limit_readable"] = f"{k.get('data_limit_gb'):.1f} GB"
                k["usage_percent"] = min(100, round((k.get("used_bytes", 0) / k.get("data_limit_bytes")) * 100, 1))
            else:
                k["limit_readable"] = "Unlimited"
                k["usage_percent"] = 0

            # Calculate remaining days
            if k.get("expire_timestamp", 0) > 0:
                diff_sec = k.get("expire_timestamp") - now_ts
                if diff_sec > 0:
                    days_left = diff_sec // 86400
                    hours_left = (diff_sec % 86400) // 3600
                    k["time_left_readable"] = f"{days_left}d {hours_left}h remaining"
                else:
                    k["time_left_readable"] = "Expired"
            else:
                k["time_left_readable"] = "No Expiry (သက်တမ်းအကန့်အသတ်မရှိ)"

            # Build standard ss:// URL (Outline / V2Ray / Shadowrocket compatible)
            k["access_url"] = self._build_ss_url(k, server_host)

        self._save_data(data)
        return data.get("keys", [])

    def _build_ss_url(self, key: dict, host: str) -> str:
        """
        Creates standard Outline/Shadowsocks URI:
        ss://BASE64(cipher:password@host:port)#Tag
        """
        raw_userinfo = f"{key['cipher']}:{key['password']}@{host}:{key['port']}"
        b64_userinfo = base64.urlsafe_b64encode(raw_userinfo.encode('utf-8')).decode('utf-8').rstrip('=')
        tag = key.get("name", "VPN-Key").replace(" ", "_")
        return f"ss://{b64_userinfo}#{tag}"

    def delete_key(self, key_id: str):
        data = self._load_data()
        data["keys"] = [k for k in data.get("keys", []) if k["id"] != key_id]
        self._save_data(data)

    def toggle_key(self, key_id: str) -> bool:
        data = self._load_data()
        for k in data.get("keys", []):
            if k["id"] == key_id:
                k["enabled"] = not k.get("enabled", True)
                if k["enabled"]:
                    k["status"] = "active"
                self._save_data(data)
                return k["enabled"]
        return False

    def reset_data_usage(self, key_id: str):
        data = self._load_data()
        for k in data.get("keys", []):
            if k["id"] == key_id:
                k["used_bytes"] = 0
                k["status"] = "active"
                k["enabled"] = True
                self._save_data(data)
                return

    def extend_expiry(self, key_id: str, extra_days: int = 30):
        data = self._load_data()
        for k in data.get("keys", []):
            if k["id"] == key_id:
                now = datetime.now()
                new_expiry = now + timedelta(days=extra_days)
                k["expire_date"] = new_expiry.strftime("%Y-%m-%d %H:%M:%S")
                k["expire_timestamp"] = int(new_expiry.timestamp())
                k["status"] = "active"
                k["enabled"] = True
                self._save_data(data)
                return

    def simulate_add_traffic(self, key_id: str, added_mb: float):
        """Simulate data consumption for testing/demo purposes"""
        data = self._load_data()
        for k in data.get("keys", []):
            if k["id"] == key_id:
                k["used_bytes"] = k.get("used_bytes", 0) + int(added_mb * 1024 * 1024)
                self._save_data(data)
                return
