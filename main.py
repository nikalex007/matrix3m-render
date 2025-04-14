from keep_alive import keep_alive
from manipulation_detector import analyze_market
from telegram_notifier import send_telegram_message
import time

# Aktiviraj web server da bi Render držao bot živim
keep_alive()

# Pošalji start poruku
send_telegram_message("🤖 Matrix3M bot je aktiviran i prati BTCUSDT manipulacije...")

symbol = "BTCUSDT"
timeframes = ["1m", "5m", "15m"]

while True:
    for tf in timeframes:
        print(f"🔍 Proveravam: {symbol} / {tf}")
        signal = analyze_market(symbol, tf)

        if signal:
            setup = signal.get('setup', 'Nepoznat setup')
            verovatnoca = signal.get('verovatnoća', 'N/A')
            napomena = signal.get('napomena', '')
            active = setup.split('+') if '+' in setup else [setup]

            all_manips = ["Spoofing", "Delta Flip", "Imbalance Spike", "CHoCH Break", "Trap Wick"]
            manip_list = []
            for m in all_manips:
                if any(m.lower() in a.lower() for a in active):
                    manip_list.append(f"[x] {m}")
                else:
                    manip_list.append(f"[ ] {m}")
            manip_summary = ', '.join(manip_list)

            msg = f"""✅ Analiza za {symbol} [{tf}]
Manipulacije: {manip_summary}
Ukupno: {len(active)}/5 → SIGNAL AKTIVAN
Setup: {setup}
Verovatnoća: {verovatnoca}%
Napomena: {napomena}"""
            print(msg)
            send_telegram_message(msg)
        else:
            msg = f"""ℹ️ Analiza za {symbol} [{tf}]
Manipulacije: Ispod praga
Signal NIJE poslat"""
            print(msg)
            send_telegram_message(msg)

    print("⏳ Spavanje 60s...\n")
    time.sleep(60)
