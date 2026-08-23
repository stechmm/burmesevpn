# 🇲🇲 Burmese VPN - Dual-Engine Enterprise Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Framework-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Protocols](https://img.shields.io/badge/Protocols-WireGuard%20%7C%20Shadowsocks-orange.svg)]()

**Burmese VPN** သည် မြန်မာနိုင်ငံရှိ အင်တာနက် အသုံးပြုသူများနှင့် လုပ်ငန်းများအတွက် ရည်ရွယ်၍ အထူးဒီဇိုင်းဆင်ထားသော **Dual-Engine VPN & Gateway Management System** ဖြစ်ပါသည်။

---

## 🌟 အဓိက အပိုင်း (၂) ပိုင်း (Dual-Engine Architecture)

```
                       ┌─────────────────────────────────────────┐
                       │     🇲🇲 Burmese VPN Core Hub Server      │
                       │          (FastAPI Web Dashboard)        │
                       └───────────────────┬─────────────────────┘
                                           │
             ┌─────────────────────────────┴─────────────────────────────┐
             ▼                                                           ▼
┌───────────────────────────┐                               ┌───────────────────────────┐
│ Part 1: Router Hub Engine │                               │ Part 2: Mobile Key Hub    │
│  (WireGuard Tunnel Subnet)│                               │ (Shadowsocks/Outline ss:) │
├───────────────────────────┤                               ├───────────────────────────┤
│ • OpenWrt Routers         │                               │ • Outline App             │
│ • MikroTik (RouterOS v7)  │                               │ • v2rayNG / Shadowrocket  │
│ • H3C Magic Routers       │                               │ • Data Quota & Expiry     │
│ • AsusWRT / GL.iNet       │                               │ • Device Limitations      │
└───────────────────────────┘                               └───────────────────────────┘
```

### 1. 🌐 Router Gateway Hub (OpenWrt / MikroTik / H3C Magic)
- **Engine**: Kernel-level WireGuard Subnet (`10.8.0.x/24`).
- **Target**: အိမ်သုံး/ရုံးသုံး Router များ (OpenWrt, MikroTik RouterOS v7, H3C Magic NX30 Pro / B365, GL.iNet)။
- **Feature**: Router တစ်လုံးတွင် ချိတ်ဆက်ထားရုံဖြင့် Router အောက်ရှိ ဖုန်း၊ Laptop၊ TV အားလုံး အလိုအလျောက် VPN ဖြတ်သန်းသွားမည် ဖြစ်ပါသည်။
- **Setup**: Web Dashboard မှ **1-Click Copy Script** ကို Router Terminal ထဲ paste လုပ်ရုံဖြင့် အသင့်အသုံးပြုနိုင်ပါသည်။

### 2. 📱 Mobile Client Key Hub (Android / iOS / Desktop)
- **Engine**: Shadowsocks AEAD (`chacha20-ietf-poly1305`) & Dynamic Subscription.
- **Target**: Android (Outline, v2rayNG), iOS (Shadowrocket, Outline, Sing-box), PC/Mac (Outline, Clash)။
- **Feature**:
  - 📊 **Byte-Level Data Quota**: 10GB, 20GB, 50GB, 100GB သို့မဟုတ် Unlimited သတ်မှတ်နိုင်ခြင်း။
  - ⏳ **Expiration Enforcement**: 7 ရက်၊ 30 ရက်၊ 90 ရက်၊ 1 နှစ် သက်တမ်း ကန့်သတ်ချက်များ။
  - 📱 **Device Limit**: ချိတ်ဆက်နိုင်သည့် စက်အလုံးရေ ကန့်သတ်ခြင်း။
  - ⚙️ **Key Settings Form**: Data Reset, +30 Days Extend, Toggle Active/Pause စသည်တို့ကို Web Form မှ တိုက်ရိုက် စီမံနိုင်ခြင်း။
  - 📥 **Batch Export & Subscription**: Keys အားလုံးကို 1-Click .txt export လုပ်နိုင်ပြီး `/sub/{key_id}` မှတစ်ဆင့် App အတွင်း Data လက်ကျန်နှင့် သက်တမ်း တိုက်ရိုက် ကြည့်ရှုနိုင်ခြင်း။

---

## 🚀 VPS ပေါ်တွင် ၁ ချက်နှိပ် တင်ဆင်နည်း (1-Click Linux VPS Deployment)

Ubuntu / Debian VPS တစ်လုံး (Singapore, Tokyo, US စသည်) တွင် root ဖြင့် အောက်ပါ command ကို run လိုက်ပါ:

```bash
git clone https://github.com/stechmm/burmesevpn.git
cd burmesevpn
sudo bash install.sh
```

တပ်ဆင်မှု ပြီးဆုံးပါက Web Dashboard URL ပေါ်လာပါမည်:
👉 `http://<YOUR_VPS_IP>:8080`

---

## 🛠 Manual Local Run (Development / Testing)

```bash
# 1. Clone repository
git clone https://github.com/stechmm/burmesevpn.git
cd burmesevpn

# 2. Virtual Environment ပြုလုပ်ပြီး dependencies သွင်းပါ
python -m venv .venv
source .venv/bin/activate  # (Windows: .\.venv\Scripts\activate)
pip install -r server/requirements.txt

# 3. Server စတင် run ပါ
cd server
python -m uvicorn app:app --host 0.0.0.0 --port 8080 --reload
```

---

## 📖 Router Setup Instructions (လမ်းညွှန်များ)

- [OpenWrt Setup Guide](file:///C:/Users/ST/.gemini/antigravity/scratch/lightweight-vpn-router-hub/router-configs/openwrt/README.md)
- [MikroTik RouterOS v7 Setup Guide](file:///C:/Users/ST/.gemini/antigravity/scratch/lightweight-vpn-router-hub/router-configs/mikrotik/README.md)
- [H3C Magic Series Setup Guide](file:///C:/Users/ST/.gemini/antigravity/scratch/lightweight-vpn-router-hub/router-configs/h3c-magic/README.md)

---

## 📄 License
MIT License - Developed with ❤️ for Myanmar Community.
