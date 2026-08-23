# 🖥️ Burmese VPN - PC Desktop Client Setup Guide (Windows / macOS / Linux)

မြန်မာနိုင်ငံရှိ PC / Laptop အသုံးပြုသူများအတွက် အလွယ်ကူဆုံးနှင့် အမြန်ဆုံး ချိတ်ဆက်နိုင်သော နည်းလမ်း (၃) မျိုး:

---

## 🌟 နည်းလမ်း ၁။ Outline Windows / Mac Client ဖြင့် ၁ ချက်နှိပ် ချိတ်ဆက်ခြင်း (အလွယ်ကူဆုံး ⭐⭐⭐⭐⭐)

1. **Official Outline PC Client** ကို ဒေါင်းလုဒ်ရယူပါ:
   - **Windows:** [https://getoutline.org/get-outline/#windows-app](https://getoutline.org/get-outline/#windows-app)
   - **macOS:** [https://getoutline.org/get-outline/#macos-app](https://getoutline.org/get-outline/#macos-app)
   - **Linux:** [https://getoutline.org/get-outline/#linux-app](https://getoutline.org/get-outline/#linux-app)
2. Outline App ကို ဖွင့်ပြီး Dashboard မှ ရရှိသော `ss://...` Access Key ကို **Copy** ယူလိုက်ပါ (App မှ အလိုအလျောက် detect လုပ်ပြီး **"Add Server"** ပေါ်လာပါမည်)။
3. **"Connect"** ခလုတ်ကို နှိပ်လိုက်ရုံဖြင့် တစ်ကွန်ပျူတာလုံး VPN အပြည့်အဝ ဖြတ်သန်းသွားမည် ဖြစ်ပါသည်။

---

## 🚀 နည်းလမ်း ၂။ Clash Verge / v2rayN PC Client ဖြင့် Node ပြောင်းလဲ သုံးစွဲခြင်း (Gaming & Multi-Node)

Clash Verge Rev သို့မဟုတ် v2rayN အသုံးပြုခြင်းဖြင့် **Singapore, Tokyo, US, Germany** Node များကို PC ပေါ်တွင် ၁ ချက်နှိပ် ပြောင်းလဲနိုင်ပြီး အမြန်ဆုံး Node ကို Auto ရွေးချယ်ပေးနိုင်ပါသည်။

1. **Clash Verge Rev (Windows/Mac)** ဒေါင်းလုဒ်လုပ်ပါ:
   - [https://github.com/clash-verge-rev/clash-verge-rev/releases](https://github.com/clash-verge-rev/clash-verge-rev/releases)
2. Dashboard ရှိ မိမိ Key ၏ **"PC Setup"** ခလုတ်မှတစ်ဆင့် `burmesevpn_clash.yaml` config ကို ဒေါင်းလုဒ်လုပ်ပြီး Clash Verge ထဲသို့ **Import** လုပ်ပါ (သို့မဟုတ် Subscription URL ထည့်သွင်းပါ)။
3. **System Proxy** သို့မဟုတ် **TUN Mode** ကို ON ပေးလိုက်ရုံဖြင့် Browser၊ Telegram၊ Discord၊ Games အားလုံး High Speed ဖြင့် ပွင့်သွားမည် ဖြစ်ပါသည်။

---

## 🛡️ နည်းလမ်း ၃။ WireGuard Windows Client ဖြင့် ချိတ်ဆက်ခြင်း (Kernel Level Speed)

1. **WireGuard PC Client** ကို ဒေါင်းလုဒ်လုပ်ပါ:
   - [https://www.wireguard.com/install/](https://www.wireguard.com/install/)
2. Web Dashboard မှ Router / PC အတွက် ထုတ်ယူထားသော `.conf` file ကို Import လုပ်ပြီး **"Activate"** နှိပ်ပါ။

---

### 💡 Tips for Myanmar PC Users:
- YouTube, Netflix, Discord, Telegram အားလုံးကို Bypass Traffic စားသက်သာစေရန် Clash Verge ၏ **"Rule Mode"** ကို အသုံးပြုနိုင်ပါသည်။
- Game ကစားလိုပါက **🇸🇬 Singapore** သို့မဟုတ် **🇯🇵 Tokyo** Node ကို ရွေးချယ်အသုံးပြုပါက Latency အနိမ့်ဆုံး ရရှိပါမည်။
