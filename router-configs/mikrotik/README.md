# MikroTik RouterOS v7 WireGuard Setup Guide (မြန်မာဘာသာ)

MikroTik RouterOS version 7 (v7.1+) မှစတင်၍ WireGuard ကို Native အဖြစ် တိုက်ရိုက် ထည့်သွင်းပေးထားပါသည်။

---

## နည်းလမ်း (၁) - Winbox Terminal ဖြင့် 1-Click Paste ထည့်သွင်းနည်း (အကြံပြုချက်)

1. Web Admin Dashboard (`http://<YOUR_SERVER_IP>:8080`) သို့ သွားပါ။
2. **Add Client / Router** နှိပ်ပြီး Type တွင် `MikroTik Router (RouterOS v7)` ကို ရွေးပါ။
3. Client Card ရှိ **MikroTik** ခလုတ်ကို နှိပ်ပြီး **Copy All Commands** ကို နှိပ်ပါ။
4. MikroTik Winbox ကို ဖွင့်ပြီး ဘယ်ဘက် menu ရှိ **New Terminal** ကို ဖွင့်ပါ။
5. Copy ကူးလာသော script အားလုံးကို **Paste** လုပ်လိုက်ရုံဖြင့် Interface, Peer, IP Address, NAT နှင့် Routing အားလုံး အလိုအလျောက် သတ်မှတ်ပြီးဖြစ်သွားပါမည်။

---

## နည်းလမ်း (၂) - Specific Device များကိုသာ VPN သုံးစေလိုသည့် Policy Routing (Split Tunnel) နည်းလမ်း

အကယ်၍ Router နောက်ရှိ Device အားလုံး မဟုတ်ဘဲ သတ်မှတ်ထားသော IP (ဥပမာ: `192.168.88.50`) သို့မဟုတ် IP List တစ်ခုကိုသာ VPN ဖြတ်သန်းစေလိုပါက အောက်ပါ commands များကို Winbox Terminal တွင် run ပါ-

```routeros
# ၁။ Routing Table အသစ် ဆောက်ခြင်း
/routing table add name=to-vpn fib

# ၂။ WireGuard interface သို့ ညွှန်မည့် Default Route သတ်မှတ်ခြင်း
/ip route add dst-address=0.0.0.0/0 gateway=wg-client-vpn routing-table=to-vpn comment="VPN Only Routing"

# ၃။ သီးသန့်သုံးမည့် Device IP အတွက် Routing Rule သတ်မှတ်ခြင်း
/routing rule add src-address=192.168.88.50/32 table=to-vpn comment="Route IP 192.168.88.50 via VPN"
```

---

## စစ်ဆေးခြင်း (Status Check)
Winbox ရှိ **WireGuard** -> **Peers** tab သို့ သွား၍:
* **Tx / Rx Bytes** တက်နေခြင်းနှင့်
* **Last Handshake** အချိန် စက္ကန့်အနည်းငယ်အတွင်း ပြသနေပါက VPN ချိတ်ဆက်မှု အောင်မြင်ပါသည်။
