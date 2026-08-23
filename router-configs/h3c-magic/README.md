# H3C Magic Series Router Setup Guide (မြန်မာဘာသာ)

ဤလမ်းညွှန်သည် **H3C Magic Routers (NX30 Pro, B365, R300, etc.)** များကို **Burmese VPN** နှင့် ချိတ်ဆက်ပြီး Router အောက်ရှိ ဖုန်း၊ ကွန်ပျူတာ၊ Smart TV အားလုံးကို VPN ဖြတ်သန်းစေရန် အသုံးပြုနည်း ဖြစ်ပါသည်။

---

## 🌟 နည်းလမ်း (၁) - SSH / Telnet မှ 1-Click Script ဖြင့် ထည့်သွင်းခြင်း (အကြံပြုချက်)

1. Burmese VPN Web Dashboard (`http://<YOUR_SERVER_IP>:8080`) သို့ သွားပါ။
2. **Add Router Gateway** ကို နှိပ်ပြီး Router System တွင် `🏢 H3C Magic Router` ကို ရွေးချယ်ပါ။
3. ထွက်လာသော Table Row ရှိ **`H3C Magic Script`** ခလုတ်ကို နှိပ်ပြီး Script အားလုံးကို Copy ကူးပါ။
4. H3C Magic Router ထဲသို့ SSH / Telnet ဖြင့် ဝင်ရောက်ပါ (ဥပမာ: `ssh root@192.168.124.1` သို့မဟုတ် Web Telnet):
5. Copy ကူးလာသော Script များကို Paste လုပ်ပြီး Enter ခေါက်လိုက်ရုံဖြင့် WireGuard interface နှင့် NAT Forwarding အားလုံး အလိုအလျောက် သတ်မှတ်ပြီး ဖြစ်သွားပါမည်။

---

## 🌟 နည်းလမ်း (၂) - H3C Magic Web Management GUI မှတစ်ဆင့် ထည့်သွင်းခြင်း

1. H3C Magic Router Web Interface (`http://192.168.124.1` သို့မဟုတ် Router IP) သို့ ဝင်ပါ။
2. **Advanced Settings (高级设置)** -> **VPN** သို့မဟုတ် **Plugin Management** သို့ သွားပါ။
3. Dashboard မှ Download လုပ်ထားသော `.conf` file ကို Upload ပြုလုပ်ပါ (သို့မဟုတ် Private Key, Server IP `51820`, AllowedIPs `0.0.0.0/0` ကို ထည့်ပါ)။
4. **Save & Apply** နှိပ်ပြီး ဖွင့်လိုက်ပါက Router တစ်ခုလုံး VPN ချိတ်ဆက်သွားမည် ဖြစ်ပါသည်။

---

## 🔍 ချိတ်ဆက်မှု စစ်ဆေးခြင်း
H3C Terminal ထဲတွင် အောက်ပါ command ဖြင့် handshake စစ်ဆေးနိုင်ပါသည်:
```bash
wg show
```
`latest handshake` အချိန်နှင့် `transfer: ... KiB received, ... KiB sent` ပြနေပါက ချိတ်ဆက်မှု အောင်မြင်ပါသည်။
