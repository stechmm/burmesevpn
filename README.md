# Lightweight WireGuard VPN Server & Multi-Router Management Hub 🛡️🚀

Linux Server ပေါ်တွင် အလွန်ပေါ့ပါးမြန်ဆန်သည့် **WireGuard Protocol** ကို အခြေခံပြီး တည်ဆောက်ထားသော VPN Server နှင့် Multi-Router Management System ဖြစ်ပါသည်။

မိုဘိုင်းဖုန်း၊ ကွန်ပျူတာများအပြင် **OpenWrt, MikroTik RouterOS v7, AsusWRT, GL.iNet** စသည့် Router များတွင် အိမ်သုံး/ရုံးသုံး Network Gateway အဖြစ် မိနစ်ပိုင်းအတွင်း တပ်ဆင်အသုံးပြုနိုင်ပါသည်။

---

## 🌟 အဓိက ပါဝင်သော စွမ်းဆောင်ရည်များ

* ⚡ **Ultra-Fast & Kernel-Level Performance**: ChaCha20-Poly1305 encryption ဖြင့် CPU/RAM အသုံးပြုမှု အလွန်နည်းပါးခြင်း။
* 🌐 **Multi-Router Ready**:
  * **OpenWrt**: 1-Click Copy-Paste SSH Setup Script ပါဝင်ခြင်း။
  * **MikroTik RouterOS v7**: Terminal Command Script (`.rsc`) အပြည့်အစုံ ထုတ်ပေးနိုင်ခြင်း။
  * **AsusWRT / GL.iNet**: `.conf` file upload ဖြင့် တိုက်ရိုက် သုံးနိုင်ခြင်း။
* 📱 **Mobile & Desktop QR Setup**: ဖုန်းများအတွက် WireGuard App ဖြင့် ချက်ချင်း Scan ဖတ်နိုင်မည့် Live QR Code Generator ပါဝင်ခြင်း။
* 💻 **Modern Web Admin Dashboard**: Tailwind CSS ဖြင့် ပြုလုပ်ထားသော Dark UI ဖြစ်ပြီး Peer များ ထည့်ခြင်း၊ ဖျက်ခြင်း၊ IP ခွဲဝေခြင်းနှင့် Traffic စောင့်ကြည့်ခြင်းများကို အလွယ်တကူ ပြုလုပ်နိုင်ခြင်း။
* 🛠️ **Dual Deployment Options**: Linux Server ပေါ်တွင် **1-Click Native Installer** ဖြင့်ဖြစ်စေ **Docker Compose** ဖြင့်ဖြစ်စေ နှစ်သက်ရာ run နိုင်ခြင်း။

---

## 🚀 နည်းလမ်း (၁) - Linux Server ပေါ်တွင် 1-Click Script ဖြင့် Run ခြင်း (အကြံပြုချက်)

Ubuntu (20.04/22.04/24.04), Debian (11/12), CentOS/AlmaLinux ရှိသော Linux Server ပေါ်သို့ root အနေဖြင့် ဝင်ရောက်ပြီး အောက်ပါ command ဖြင့် run ပါ:

```bash
sudo bash install.sh
```

Setup ပြီးဆုံးပါက Terminal တွင် အောက်ပါအတိုင်း ပေါ်လာပါမည်:
* **Web Admin Dashboard:** `http://<YOUR_SERVER_PUBLIC_IP>:8080`
* **WireGuard UDP Port:** `51820`

---

## 🐳 နည်းလမ်း (၂) - Docker Compose ဖြင့် Run ခြင်း

Docker သုံးလိုပါက အောက်ပါ command ကို run နိုင်ပါသည်:

```bash
# Server Public IP ကို သတ်မှတ်ပါ
export WG_SERVER_ENDPOINT="YOUR_SERVER_PUBLIC_IP"

# Container ကို စတင် run ပါ
docker-compose up -d
```

---

## 📖 Router များနှင့် ချိတ်ဆက်အသုံးပြုနည်း လမ်းညွှန်များ

* [OpenWrt Router တပ်ဆင်နည်း လမ်းညွှန်](router-configs/openwrt/README.md)
* [MikroTik RouterOS v7 တပ်ဆင်နည်း လမ်းညွှန်](router-configs/mikrotik/README.md)
* [AsusWRT, GL.iNet, Phones & PC တပ်ဆင်နည်း လမ်းညွှန်](router-configs/asuswrt-glinet/README.md)

---

## ⚙️ Ports & Firewall Requirements (VPS / Cloud Provider)

Cloud Provider (AWS, DigitalOcean, Hetzner, Linode, Google Cloud, Oracle Cloud) များတွင် အောက်ပါ Ports များကို Firewall / Security Group တွင် ဖွင့်ပေးရန် လိုအပ်ပါသည်:

| Protocol | Port | Description |
| :--- | :--- | :--- |
| **UDP** | `51820` | WireGuard VPN Tunnel Traffic |
| **TCP** | `8080` | Web Admin Management Dashboard |

---

## 📁 Project Structure

```
lightweight-vpn-router-hub/
├── install.sh                     # Linux 1-Click Automated Installer
├── docker-compose.yml             # Docker containerized setup
├── Dockerfile                     # Container definition
├── server/
│   ├── app.py                     # FastAPI Web Application
│   ├── wg_manager.py              # Core WireGuard key & config engine
│   ├── requirements.txt           # Python dependencies
│   └── templates/
│       └── index.html             # Modern Glassmorphic Dashboard UI
└── router-configs/
    ├── openwrt/                   # OpenWrt scripts and docs
    ├── mikrotik/                  # MikroTik RouterOS scripts and docs
    └── asuswrt-glinet/            # Asus & GL.iNet docs
```
