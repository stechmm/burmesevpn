# OpenWrt Router WireGuard Setup Guide (မြန်မာဘာသာ)

ဤလမ်းညွှန်သည် OpenWrt Router ကို WireGuard VPN Client/Gateway အဖြစ် ချိတ်ဆက်ပြီး Router နောက်ကွယ်ရှိ ဖုန်း၊ TV၊ ကွန်ပျူတာ အားလုံးကို VPN အလိုအလျောက် ဖြတ်သန်းစေရန် ပြုလုပ်နည်း ဖြစ်ပါသည်။

---

## နည်းလမ်း (၁) - SSH Terminal မှ 1-Click Script ဖြင့် အလွယ်တကူ ထည့်သွင်းခြင်း (အကြံပြုချက်)

1. Web Admin Dashboard (`http://<YOUR_SERVER_IP>:8080`) သို့ သွားပါ။
2. **Add Client / Router** ကို နှိပ်ပြီး Type တွင် `OpenWrt Router` ကို ရွေးချယ်ပါ။
3. ထွက်လာသော Client Card ရှိ **OpenWrt** ခလုတ်ကို နှိပ်ပြီး **Copy All Commands** ကို ယူပါ။
4. OpenWrt Router ထဲသို့ SSH ဖြင့် ဝင်ရောက်ပါ (ဥပမာ: `ssh root@192.168.1.1`):
5. Copy ကူးလာသော commands များကို Paste လုပ်ပြီး Enter ခေါက်လိုက်ရုံဖြင့် အားလုံးပြီးစီးသွားမည် ဖြစ်ပါသည်။

---

## နည်းလမ်း (၂) - LuCI Web Interface မှတစ်ဆင့် Manual ထည့်သွင်းခြင်း

### အဆင့် ၁: Package များ သွင်းယူခြင်း
* LuCI Web Panel (`http://192.168.1.1`) သို့ သွားပါ -> **System** -> **Software**
* `luci-proto-wireguard` နှင့် `luci-app-wireguard` ကို ရှာပြီး Install လုပ်ပါ။ (ပြီးလျှင် Router ကို Reboot ချပါ)

### အဆင့် ၂: WireGuard Interface ဖန်တီးခြင်း
* **Network** -> **Interfaces** -> **Add new interface...**
  * **Name**: `wg0`
  * **Protocol**: `WireGuard VPN`
* **General Settings**:
  * **Private Key**: Dashboard မှ Client Private Key ကို ထည့်ပါ
  * **IP Addresses**: `10.8.0.x/24`
* **Peers tab**:
  * **Public Key**: Server Public Key ထည့်ပါ
  * **Allowed IPs**: `0.0.0.0/0`
  * **Route Allowed IPs**: အမှန်ခြစ် (Check) ပေးပါ
  * **Endpoint Host**: Server Public IP
  * **Endpoint Port**: `51820`
  * **Persistent Keep Alive**: `25`

### အဆင့် ၃: Firewall Zone သတ်မှတ်ခြင်း
* **Network** -> **Firewall** သို့ သွားပါ။
* **wan zone** တွင် Edit ကို နှိပ်ပြီး **Covered networks** အောက်တွင် `wg0` ကို အမှန်ခြစ်ထည့်ပေးပြီး **Save & Apply** နှိပ်ပါ။

---

## စစ်ဆေးခြင်း
Router SSH ထဲတွင် အောက်ပါ command ဖြင့် handshake မိမမိ စစ်ဆေးနိုင်ပါသည်-
```bash
wg show
```
`latest handshake` အချိန်ပြနေပါက VPN အောင်မြင်စွာ ချိတ်ဆက်ပြီး ဖြစ်ပါသည်။
