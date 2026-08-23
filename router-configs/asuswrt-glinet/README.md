# AsusWRT, GL.iNet, Phones & Desktop Setup Guide (မြန်မာဘာသာ)

## ၁။ Asus Routers (AsusWRT / Merlin)
1. Asus Router Web GUI (`http://router.asus.com` သို့မဟုတ် `192.168.50.1`) သို့ ဝင်ပါ။
2. ဘယ်ဘက် menu မှ **VPN** -> **VPN Fusion** (သို့မဟုတ် **VPN Client**) သို့ သွားပါ။
3. **Add profile** ကို နှိပ်ပြီး **WireGuard** ကို ရွေးပါ။
4. Web Admin Dashboard မှ Download လုပ်ထားသော `.conf` file ကို **Upload Configuration File** ဖြင့် တင်ပေးပါ။
5. Apply နှိပ်ပြီး ဖွင့်လိုက်သည်နှင့် Router အောက်ရှိ Device များ VPN ချိတ်ဆက်သွားမည် ဖြစ်ပါသည်။

---

## ၂။ GL.iNet Routers
1. GL.iNet Admin Panel (`http://192.168.8.1`) သို့ ဝင်ပါ။
2. **VPN** -> **WireGuard Client** သို့ သွားပါ။
3. **Add New Profile** ကို နှိပ်ပြီး Dashboard မှ download ပြုလုပ်ထားသော `.conf` file ကို upload ပြုလုပ်ပေးပါ။
4. **Connect** နှိပ်ရုံဖြင့် ချိတ်ဆက်သွားမည် ဖြစ်ပါသည်။

---

## ၃။ Mobile Phones (Android / iPhone)
1. Google Play Store သို့မဟုတ် Apple App Store မှ **WireGuard** Official App ကို Download ရယူပါ။
2. App ထဲသို့ ဝင်ပြီး ညာဘက်အောက်ထောင့်ရှိ `+` (Plus) ခလုတ်ကို နှိပ်ပါ။
3. **Scan from QR code** ကို ရွေးချယ်ပြီး Dashboard တွင် ပေါ်နေသော **QR Code** ကို Scan ဖတ်ပေးလိုက်ရုံဖြင့် အလွယ်တကူ ချိတ်ဆက်နိုင်ပါသည်။

---

## ၄။ Windows & macOS Desktop
1. [wireguard.com/install](https://www.wireguard.com/install/) မှ WireGuard client app ကို download ရယူ install လုပ်ပါ။
2. App ကို ဖွင့်ပြီး **Add Tunnel** ကို နှိပ်ကာ Web Dashboard မှ Download ပြုလုပ်ထားသော `.conf` file ကို ရွေးချယ်ပေးပြီး **Activate** ကို နှိပ်ပါ။
