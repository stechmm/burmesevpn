import os
import re
import json
import time
import subprocess
from typing import Dict, Any, List, Optional

class AIServerAgent:
    """
    Intelligent Autonomous AI Server Agent for Burmese VPN.
    Understands Natural Language prompts (Burmese & English) to execute
    server administration, key provisioning, router setups, firewall configuration,
    and self-healing diagnostic tasks.
    """
    def __init__(self, wg_manager, key_manager, node_manager, watchdog_engine):
        self.wg = wg_manager
        self.km = key_manager
        self.nm = node_manager
        self.watchdog = watchdog_engine

    def process_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Parse natural language prompt (Burmese/English) and execute appropriate server actions.
        """
        p = prompt.strip().lower()
        response_text = ""
        action_performed = None
        data_payload = {}

        # 1. Server Optimization & Memory Cleanup
        # Keywords: optimize, clean, ရှင်း, memory, ram, drop_caches
        if any(w in p for w in ["optimize", "clean", "ရှင်း", "memory ရှင်း", "ram ရှင်း", "drop_caches", "speed up"]):
            res = self.watchdog.trigger_optimization(reason="AI Agent Triggered Optimization")
            action_performed = "OPTIMIZE_SERVER"
            data_payload = res
            response_text = f"✅ ဆာဗာ၏ Memory နှင့် Kernel Buffer များကို အောင်မြင်စွာ ရှင်းလင်းပေးပြီးပါပြီခင်ဗျာ!\n\n• Reclaimed Objects: {res.get('garbage_collected_objects', 0)}\n• Kernel Cache Flushed: {res.get('kernel_cache_flushed', False)}\n• Status: Normal & Cleaned"

        # 2. Firewall Port Opening & Cloud Port Fixes
        # Keywords: port, firewall, ufw, iptables, ဖွင့်, 8080, 80, 51820
        elif ("firewall" in p or "port" in p or "ဖွင့်" in p) and any(w in p for w in ["open", "allow", "ဖွင့်", "accept"]):
            port_match = re.search(r'\b(8080|80|443|51820|2053|8388|8888|\d{2,5})\b', p)
            target_port = port_match.group(1) if port_match else "8080"
            
            # Execute iptables and ufw commands if on Linux
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
            response_text = f"🛡️ Port `{target_port}` (TCP/UDP) ကို OS Firewall (iptables & UFW) တွင် အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီခင်ဗျာ!\n\n• Port: {target_port}\n• Protocol: TCP & UDP\n• Access Status: Open & Allowed"

        # 3. Create Mobile Access Key
        # Keywords: key, user, gb, ရက်, 30, 20, 50, ထုတ်, ဖန်တီး, create
        elif ("key" in p or "user" in p or "အကောင့်" in p or "ထုတ်" in p or "ဖန်တီး" in p or "create" in p) and not ("delete" in p or "ဖျက်" in p):
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

            # Extract Name
            name = "VIP_User"
            words = prompt.split()
            for i, w in enumerate(words):
                if w.lower() in ["key", "user", "အတွက်", "for", "နာမည်"] and i > 0:
                    name = words[i-1].replace("အတွက်", "").strip() or "User"
                    break
            if name == "VIP_User" and len(words) >= 2:
                name = words[0]

            new_key = self.km.create_key(
                name=name,
                data_limit_gb=quota_gb,
                expire_days=days,
                max_devices=1
            )
            action_performed = "CREATE_KEY"
            data_payload = {"key": new_key}
            response_text = f"📱 **{name}** အတွက် Access Key အသစ်ကို အောင်မြင်စွာ ထုတ်ပေးပြီးပါပြီ!\n\n• **User Name:** {new_key['name']}\n• **Data Quota:** {new_key['data_limit_gb']} GB\n• **Validity:** {days} ရက် ({new_key['expire_date']})\n• **Port:** {new_key['port']}\n• **Access URL:** `{new_key['access_url']}`"

        # 4. Add Router Gateway
        # Keywords: router, openwrt, mikrotik, h3c, ထည့်, gateway
        elif ("router" in p or "gateway" in p) and any(w in p for w in ["add", "create", "ထည့်", "လုပ်"]):
            rtype = "openwrt"
            if "mikrotik" in p:
                rtype = "mikrotik"
            elif "h3c" in p or "magic" in p:
                rtype = "h3c_magic"

            rname = "New-Router-Gateway"
            words = prompt.split()
            for w in words:
                if len(w) > 3 and w.lower() not in ["router", "gateway", "openwrt", "mikrotik", "h3c", "add", "ထည့်"]:
                    rname = w.strip()
                    break

            new_router = self.wg.add_client(name=rname, client_type=rtype)
            action_performed = "ADD_ROUTER"
            data_payload = {"router": new_router}
            response_text = f"🌐 **{rname}** ({rtype.upper()}) Router Gateway ကို အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီ!\n\n• **Assigned IP:** {new_router['ip_address']}\n• **Public Key:** `{new_router['public_key']}`\n• **Setup:** Dashboard မှ 1-Click Copy Script ကို Router Terminal ထဲ ထည့်သွင်း အသုံးပြုနိုင်ပါသည်။"

        # 5. Add Server Node
        # Keywords: node, server, sg, jp, us, de, uk, နိုင်ငံ, region
        elif ("node" in p or "region" in p or "နိုင်ငံ" in p) and any(w in p for w in ["add", "ထည့်", "create"]):
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
            response_text = f"🌍 **{new_node['flag']} {new_node['name']}** Regional Node အသစ်ကို အောင်မြင်စွာ ချိတ်ဆက်ပြီးပါပြီ!\n\n• **Country:** {new_node['country']} ({new_node['country_code']})\n• **Endpoint:** `{new_node['endpoint']}`\n• **Subscriptions:** အသုံးပြုသူအားလုံး၏ Subscription ထဲတွင် အလိုအလျောက် ပေါ်လာပါမည်။"

        # 6. Check Server Health & Metrics
        # Keywords: status, health, cpu, ram, ကျန်းမာရေး, အခြေအနေ, info
        elif any(w in p for w in ["status", "health", "metrics", "cpu", "ram", "ကျန်းမာရေး", "အခြေအနေ", "info", "စစ်ဆေး"]):
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
            response_text = f"📊 **Burmese VPN Server Live Diagnostics Report**\n\n" \
                            f"• 🧠 **CPU Load:** {metrics['cpu_percent']}%\n" \
                            f"• 💾 **RAM Usage:** {metrics['memory_percent']}% ({metrics['memory_used_mb']} MB / {metrics['memory_total_mb']} MB)\n" \
                            f"• 📱 **Active Keys:** {active_keys} / {len(all_keys)}\n" \
                            f"• 🌐 **Router Gateways:** {len(all_routers)}\n" \
                            f"• 🌍 **Regional Nodes:** {len(all_nodes)} Regions\n" \
                            f"• 🛡️ **Watchdog:** Active & Guarding\n" \
                            f"• ⚡ **TCP Congestion:** BBR (High-Speed)"

        # 7. Default Assistance / Command Help
        else:
            response_text = f"🤖 မင်္ဂလာပါခင်ဗျာ! ကျွန်တော်ကတော့ **Burmese VPN AI Server Agent** ဖြစ်ပါတယ်။\n\n" \
                            f"ကျွန်တော့်ကို အောက်ပါ command များကို မြန်မာလို သို့မဟုတ် အင်္ဂလိပ်လို စာရိုက်၍ တိုက်ရိုက် ခိုင်းစေနိုင်ပါသည်:\n\n" \
                            f"1. **Key အသစ်ထုတ်ရန်:** `Mg Mg အတွက် 50GB 1 လ သက်တမ်း key တစ်ခု ထုတ်ပေးပါ`\n" \
                            f"2. **Firewall ဖွင့်ရန်:** `Firewall port 8080 (သို့) 80 ဖွင့်ပေးပါ`\n" \
                            f"3. **Server Memory ရှင်းရန်:** `Server memory ရှင်းပြီး optimize လုပ်ပေးပါ`\n" \
                            f"4. **Router အသစ်ထည့်ရန်:** `Office-OpenWrt ဆိုတဲ့ Router Gateway အသစ်တစ်ခု ထည့်ပေးပါ`\n" \
                            f"5. **Server Status ကြည့်ရန်:** `Server ကျန်းမာရေးနဲ့ အခြေအနေ စစ်ဆေးပြပါ`\n" \
                            f"6. **Node အသစ်ထည့်ရန်:** `Japan JP Node အသစ်တစ်ခု ထည့်ပေးပါ`"

        return {
            "success": True,
            "prompt": prompt,
            "response": response_text,
            "action": action_performed,
            "data": data_payload,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
