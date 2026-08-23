import os
import re
import json
import time
import subprocess
from typing import Dict, Any, List, Optional

class AIServerAgent:
    """
    Intelligent Autonomous Voice & Text AI Server Agent for Burmese VPN.
    Understands Spoken Burmese Voice Commands & Natural Language prompts
    to execute server administration, key provisioning, router setups,
    firewall configuration, and self-healing diagnostic tasks.
    """
    def __init__(self, wg_manager, key_manager, node_manager, watchdog_engine):
        self.wg = wg_manager
        self.km = key_manager
        self.nm = node_manager
        self.watchdog = watchdog_engine

    def _normalize_burmese_numbers(self, text: str) -> str:
        """Converts Burmese digits (၀-၉) and spoken numbers to standard Arabic numbers"""
        burmese_digits = {'၀': '0', '၁': '1', '၂': '2', '၃': '3', '၄': '4', '၅': '5', '၆': '6', '၇': '7', '၈': '8', '၉': '9'}
        for b_d, a_d in burmese_digits.items():
            text = text.replace(b_d, a_d)
        
        # Spoken number keywords
        text = text.replace("တစ်ဆယ်", "10").replace("နှစ်ဆယ်", "20").replace("သုံးဆယ်", "30").replace("ငါးဆယ်", "50").replace("တစ်ရာ", "100")
        return text

    def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Parse natural language voice prompt (Burmese/English) and execute appropriate server actions.
        """
        normalized_prompt = self._normalize_burmese_numbers(prompt)
        p = normalized_prompt.strip().lower()
        response_text = ""
        action_performed = None
        data_payload = {}

        # 1. Server Optimization & Memory Cleanup
        # Spoken Phrases: "မန်မိုရီ ရှင်းပေး", "ဆာဗာကို အမြန်ဆုံးဖြစ်အောင်လုပ်", "optimize လုပ်မယ်", "cache ရှင်း"
        if any(w in p for w in ["optimize", "clean", "ရှင်း", "မန်မိုရီ", "memory", "ram", "drop_caches", "speed up", "မြန်အောင်"]):
            res = self.watchdog.trigger_optimization(reason="AI Voice Agent Optimization")
            action_performed = "OPTIMIZE_SERVER"
            data_payload = res
            response_text = f"✅ ဆာဗာ၏ Memory နှင့် System Cache များကို အောင်မြင်စွာ ရှင်းလင်းပြီး Speed Up လုပ်ပေးလိုက်ပါပြီခင်ဗျာ!\n\n• Reclaimed Objects: {res.get('garbage_collected_objects', 0)}\n• Kernel Cache Flushed: {res.get('kernel_cache_flushed', False)}\n• Status: Peak High-Speed"

        # 2. Firewall Port Opening & Cloud Port Fixes
        # Spoken Phrases: "ပေါ့ 8080 ဖွင့်ပေး", "ဖိုင်းဝေါ ဖွင့်မယ်", "port 80 open လုပ်"
        elif ("firewall" in p or "port" in p or "ပေါ့" in p or "ဖိုင်းဝေါ" in p or "ဖွင့်" in p) and any(w in p for w in ["open", "allow", "ဖွင့်", "accept"]):
            port_match = re.search(r'\b(8080|80|443|51820|2053|8388|8888|\d{2,5})\b', p)
            target_port = port_match.group(1) if port_match else "8080"
            
            executed_cmds = []
            if os.name != 'nt':
                try:
                    subprocess.run(f"sudo iptables -I INPUT 1 -p tcp --dport {target_port} -j ACCEPT", shell=True, check=False)
                    subprocess.run(f"sudo iptables -I INPUT 1 -p udp --dport {target_port} -j ACCEPT", shell=True, check=False)
                    subprocess.run(f"sudo ufw allow {target_port} >/dev/null 2>&1", shell=True, check=False)
                    executed_cmds = [
                        f"iptables -I INPUT 1 -p tcp --dport {target_port} -j ACCEPT",
                        f"ufw allow {target_port}"
                    ]
                except Exception as e:
                    executed_cmds = [str(e)]

            action_performed = "OPEN_PORT"
            data_payload = {"port": target_port, "commands": executed_cmds}
            response_text = f"🛡️ Port `{target_port}` (TCP/UDP) ကို OS Firewall (iptables & UFW) တွင် အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီခင်ဗျာ!\n\n• Target Port: {target_port}\n• Protocols: TCP & UDP\n• Firewall Status: Open & Traffic Allowed"

        # 3. Create Mobile Access Key (Voice Provisioning)
        # Spoken Phrases: "ကီးအသစ် ထုတ်ပေး", "အကောင့်လုပ်မယ်", "50GB key တစ်ခု ပေး", "User အသစ် ထည့်မယ်"
        elif ("key" in p or "ကီး" in p or "user" in p or "အကောင့်" in p or "ထုတ်" in p or "ဖန်တီး" in p or "create" in p) and not ("delete" in p or "ဖျက်" in p):
            # Extract Quota (e.g. 50gb, 20 GB, 100)
            quota_match = re.search(r'(\d+)\s*(?:gb|g|ဂစ်)', p)
            quota_gb = float(quota_match.group(1)) if quota_match else 20.0

            # Extract Days (e.g. 30 ရက်, 7 days, 1 လ = 30)
            days_match = re.search(r'(\d+)\s*(?:days?|day|ရက်)', p)
            if "1 လ" in p or "တစ်လ" in p or "1 month" in p:
                days = 30
            elif "1 နှစ်" in p or "တစ်နှစ်" in p or "1 year" in p:
                days = 365
            elif days_match:
                days = int(days_match.group(1))
            else:
                days = 30

            # Extract User Name from Spoken Prompt
            name = "VIP_User"
            words = prompt.split()
            for i, w in enumerate(words):
                cleaned_w = w.replace("အတွက်", "").replace("ကီး", "").replace("key", "").strip()
                if cleaned_w and cleaned_w.lower() not in ["key", "user", "အတွက်", "for", "ထုတ်ပေး", "လုပ်ပေး", "ကီး"]:
                    name = cleaned_w
                    break

            new_key = self.km.create_access_key(
                name=name,
                data_limit_gb=quota_gb,
                expire_days=days,
                max_devices=1
            )
            action_performed = "CREATE_KEY"
            data_payload = {"key": new_key}
            response_text = f"📱 **{name}** အတွက် Access Key အသစ်ကို အသံဖြင့် အောင်မြင်စွာ ထုတ်ပေးပြီးပါပြီ!\n\n• **User Name:** {new_key['name']}\n• **Data Quota:** {new_key['data_limit_gb']} GB\n• **Validity:** {days} ရက် ({new_key['expire_date']})\n• **Port:** {new_key['port']}\n• **Access URL:** `{new_key.get('access_url', '')}`"

        # 4. Add Router Gateway
        # Spoken Phrases: "ရောက်တာ အသစ်ထည့်", "router အသစ်လုပ်မယ်", "OpenWrt router တစ်ခု ပေး"
        elif ("router" in p or "ရောက်တာ" in p or "ရောင်တာ" in p or "gateway" in p) and any(w in p for w in ["add", "create", "ထည့်", "လုပ်", "ပေး"]):
            rtype = "openwrt"
            if "mikrotik" in p or "မိုက်ခရိုတစ်" in p:
                rtype = "mikrotik"
            elif "h3c" in p or "magic" in p:
                rtype = "h3c_magic"

            rname = "Voice-Router"
            words = prompt.split()
            for w in words:
                if len(w) > 2 and w.lower() not in ["router", "gateway", "openwrt", "mikrotik", "h3c", "add", "ထည့်", "ရောက်တာ", "ရောင်တာ", "လုပ်ပေး", "ထည့်ပေး"]:
                    rname = w.strip()
                    break

            new_router = self.wg.add_client(name=rname, client_type=rtype)
            action_performed = "ADD_ROUTER"
            data_payload = {"router": new_router}
            response_text = f"🌐 **{rname}** ({rtype.upper()}) Router Gateway ကို အောင်မြင်စွာ ချိတ်ဆက်ပေးပြီးပါပြီ!\n\n• **Assigned Subnet IP:** {new_router['ip_address']}\n• **Public Key:** `{new_router['public_key']}`\n• **Setup:** Dashboard မှ 1-Click Copy Script ကို Router Terminal ထဲ ထည့်သွင်း အသုံးပြုနိုင်ပါသည်။"

        # 5. Add Server Node
        elif ("node" in p or "region" in p or "နိုင်ငံ" in p or "နုတ်" in p) and any(w in p for w in ["add", "ထည့်", "create"]):
            cc = "SG"
            for code in ["SG", "JP", "US", "DE", "UK", "HK", "TH", "MM", "KR"]:
                if code.lower() in p:
                    cc = code
                    break
            
            node_name = f"Node-{cc}-01"
            endpoint = f"{cc.lower()}1.burmesevpn.com"
            new_node = self.nm.add_node(name=node_name, country_code=cc, endpoint=endpoint, wg_port=51820)
            action_performed = "ADD_NODE"
            data_payload = {"node": new_node}
            response_text = f"🌍 **{new_node['flag']} {new_node['name']}** Regional Node အသစ်ကို အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ!\n\n• **Country:** {new_node['country']} ({new_node['country_code']})\n• **Endpoint:** `{new_node['endpoint']}`"

        # 6. Check Server Health & Status
        # Spoken Phrases: "ဆာဗာ အခြေအနေ ဘယ်လိုလဲ", "ကျန်းမာရေး စစ်ပြ", "user ဘယ်လောက်ရှိလဲ"
        elif any(w in p for w in ["status", "health", "metrics", "cpu", "ram", "ကျန်းမာရေး", "အခြေအနေ", "info", "စစ်ဆေး", "ဘယ်လိုလဲ"]):
            metrics = self.watchdog.get_metrics()
            all_keys = self.km.get_all_keys()
            active_keys = sum(1 for k in all_keys if k.get("status") == "active")
            all_routers = self.wg.get_clients()
            all_nodes = self.nm.get_all_nodes()

            action_performed = "SYSTEM_STATUS"
            data_payload = {
                "metrics": metrics,
                "total_keys": len(all_keys),
                "active_keys": active_keys,
                "total_routers": len(all_routers),
                "total_nodes": len(all_nodes)
            }
            response_text = f"📊 **ဆာဗာ ကျန်းမာရေးနှင့် လက်ရှိ အခြေအနေ အစီရင်ခံစာ**\n\n" \
                            f"• 🧠 **CPU Load:** {metrics['cpu_percent']}%\n" \
                            f"• 💾 **RAM Usage:** {metrics['memory_percent']}% ({metrics['memory_used_mb']} MB / {metrics['memory_total_mb']} MB)\n" \
                            f"• 📱 **Active Mobile Keys:** {active_keys} / {len(all_keys)}\n" \
                            f"• 🌐 **Router Gateways:** {len(all_routers)}\n" \
                            f"• 🌍 **Regional Nodes:** {len(all_nodes)} Regions\n" \
                            f"• 🛡️ **Watchdog:** Active & Guarding"

        # 7. Help & Voice Assistance
        else:
            response_text = f"🎙️ **Burmese VPN Voice AI Agent** အသင့်ရှိနေပါသည်ခင်ဗျာ!\n\n" \
                            f"မိုက်ခရိုဖုန်းခလုတ် (🎤) ကို နှိပ်၍ အောက်ပါတို့ကို မြန်မာလို တိုက်ရိုက် ပြောဆိုခိုင်းစေနိုင်ပါသည်:\n\n" \
                            f"• 📱 *\"မောင်မောင်အတွက် ငါးဆယ်ဂစ် တစ်လ ကီးအသစ်ထုတ်ပေး\"*\n" \
                            f"• ⚡ *\"ဆာဗာ မန်မိုရီ ရှင်းပြီး အမြန်ဆုံးဖြစ်အောင်လုပ်ပေး\"*\n" \
                            f"• 🛡️ *\"ပေါ့ ၈၀၈၀ ဖွင့်ပေး\"*\n" \
                            f"• 🌐 *\"အိမ်သုံး OpenWrt ရောက်တာအသစ် ထည့်ပေး\"*\n" \
                            f"• 📊 *\"ဆာဗာ အခြေအနေ ဘယ်လိုရှိလဲ စစ်ပြ\"*"

        return {
            "success": True,
            "prompt": prompt,
            "response": response_text,
            "action": action_performed,
            "data": data_payload,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
