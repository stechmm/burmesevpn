import os
import json
import secrets
from typing import List, Dict, Optional

NODES_FILE = os.environ.get("NODES_DATA_FILE", os.path.join(os.path.dirname(__file__), "nodes_data.json"))

class NodeManager:
    def __init__(self):
        self.data_file = NODES_FILE
        self._ensure_initialized()

    def _load_data(self) -> dict:
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_data(self, data: dict):
        os.makedirs(os.path.dirname(os.path.abspath(self.data_file)), exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _ensure_initialized(self):
        data = self._load_data()
        if not data.get("nodes"):
            default_host = os.environ.get("WG_SERVER_ENDPOINT", "sg1.burmesevpn.com")
            default_nodes = [
                {
                    "id": "node-sg-01",
                    "name": "Singapore SG-01 (Direct Fiber)",
                    "country": "Singapore",
                    "country_code": "SG",
                    "flag": "🇸🇬",
                    "endpoint": default_host,
                    "wg_port": 51820,
                    "status": "online",
                    "ping_ms": 36,
                    "load_percent": 28,
                    "is_master": True,
                    "description": "Lowest Latency for Myanmar users (Yangon/Mandalay)"
                },
                {
                    "id": "node-jp-01",
                    "name": "Tokyo JP-01 (Express Gaming)",
                    "country": "Japan",
                    "country_code": "JP",
                    "flag": "🇯🇵",
                    "endpoint": "jp1.burmesevpn.com",
                    "wg_port": 51820,
                    "status": "online",
                    "ping_ms": 68,
                    "load_percent": 42,
                    "is_master": False,
                    "description": "Optimized for Low Latency Gaming & Japanese Media"
                },
                {
                    "id": "node-us-01",
                    "name": "Silicon Valley US-01 (High Bandwidth)",
                    "country": "United States",
                    "country_code": "US",
                    "flag": "🇺🇸",
                    "endpoint": "us1.burmesevpn.com",
                    "wg_port": 51820,
                    "status": "online",
                    "ping_ms": 175,
                    "load_percent": 35,
                    "is_master": False,
                    "description": "Unrestricted US Streaming & Enterprise IP"
                },
                {
                    "id": "node-de-01",
                    "name": "Frankfurt DE-01 (Europe Core)",
                    "country": "Germany",
                    "country_code": "DE",
                    "flag": "🇩🇪",
                    "endpoint": "de1.burmesevpn.com",
                    "wg_port": 51820,
                    "status": "online",
                    "ping_ms": 195,
                    "load_percent": 19,
                    "is_master": False,
                    "description": "Strict Privacy & European Routing"
                }
            ]
            data["nodes"] = default_nodes
            self._save_data(data)

    def get_all_nodes(self) -> List[dict]:
        data = self._load_data()
        return data.get("nodes", [])

    def get_node(self, node_id: str) -> Optional[dict]:
        nodes = self.get_all_nodes()
        return next((n for n in nodes if n["id"] == node_id), None)

    def add_node(self, name: str, country_code: str, endpoint: str, wg_port: int = 51820, description: str = "") -> dict:
        data = self._load_data()
        if "nodes" not in data:
            data["nodes"] = []

        flag_map = {
            "SG": "🇸🇬", "JP": "🇯🇵", "US": "🇺🇸", "DE": "🇩🇪",
            "UK": "🇬🇧", "HK": "🇭🇰", "TH": "🇹🇭", "MM": "🇲🇲",
            "KR": "🇰🇷", "AU": "🇦🇺", "CA": "🇨🇦", "IN": "🇮🇳"
        }
        country_map = {
            "SG": "Singapore", "JP": "Japan", "US": "United States", "DE": "Germany",
            "UK": "United Kingdom", "HK": "Hong Kong", "TH": "Thailand", "MM": "Myanmar",
            "KR": "South Korea", "AU": "Australia", "CA": "Canada", "IN": "India"
        }

        cc = country_code.upper().strip()
        flag = flag_map.get(cc, "🌐")
        country = country_map.get(cc, cc)

        new_node = {
            "id": f"node-{cc.lower()}-{secrets.token_hex(3)}",
            "name": name.strip(),
            "country": country,
            "country_code": cc,
            "flag": flag,
            "endpoint": endpoint.strip(),
            "wg_port": int(wg_port),
            "status": "online",
            "ping_ms": 45 if cc in ["SG", "TH"] else 80 if cc in ["JP", "HK"] else 185,
            "load_percent": 15,
            "is_master": False,
            "description": description.strip()
        }

        data["nodes"].append(new_node)
        self._save_data(data)
        return new_node

    def update_node(self, node_id: str, name: str, endpoint: str, status: str = "online", description: str = "") -> Optional[dict]:
        data = self._load_data()
        for node in data.get("nodes", []):
            if node["id"] == node_id:
                node["name"] = name.strip()
                node["endpoint"] = endpoint.strip()
                node["status"] = status
                if description:
                    node["description"] = description.strip()
                self._save_data(data)
                return node
        return None

    def delete_node(self, node_id: str) -> bool:
        data = self._load_data()
        nodes = data.get("nodes", [])
        new_nodes = [n for n in nodes if n["id"] != node_id]
        if len(new_nodes) != len(nodes):
            data["nodes"] = new_nodes
            self._save_data(data)
            return True
        return False
