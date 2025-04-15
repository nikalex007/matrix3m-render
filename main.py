from keep_alive import keep_alive
from manipulation_detector import analyze_market
from telegram_notifier import send_telegram_message
from datetime import datetime, timedelta
import time

# Aktiviraj web server
keep_alive()

# Početna poruka
send_telegram_message("✅ Matrix3M bot je aktiviran i analizira BTCUSDT na 1m, 5m i 15m timeframe-ovima.")

symbol = "BTCUSDT"
timeframes = ["1m", "5m", "15m"]
last_status = datetime.now()

while True:
    for tf in timeframes:
        print(f"📊 Proveravam: {symbol} / {tf}")
        signal = analyze_market(symbol, tf)

        if signal:
            setup = signal.get('setup', 'Nepoznat setup')
            verovatnoca = signal.get('verovatnoća', 'N/A')
            napomena = signal.get('napomena', '')
            entry = signal.get('entry', 'N/A')
            sl = signal.get('sl', 'N/A')
            tp = signal.get('tp', 'N/A')

            active = setup.split('+') if '+' in setup else [setup]
            all_manips = ["Spoofing", "Delta Flip", "Imbalance Spike", "CHoCH Break", "Trap Wick"]
            manip_list = []
            for m in all_manips:
                if any(m.lower() in a.lower() for a in active):
                    manip_list.append(f"[x] {m}")
                else:
                    manip_list.append(f"[ ] {m}")
            manip_summary = ', '.join(manip_list)

            msg = f"""🎯 SIGNAL AKTIVAN
Symbol: {symbol} [{tf}]
Manipulacije: {manip_summary}
Ukupno: {len(active)}/5 → ✅ SIGNAL POSLAT
Setup: {setup}
Verovatnoća: {verovatnoca}%
Entry: {entry}
SL: {sl}
TP: {tp}
Napomena: {napomena}"""

            print(msg)
            send_telegram_message(msg)
        else:
            print(f"⛔ Nema signala za {symbol} / {tf}")

    if datetime.now() - last_status >= timedelta(hours=2):
        send_telegram_message("⏳ Matrix3M bot je aktivan, ali još nema validnih signala. Pratim BTCUSDT...")
        last_status = datetime.now()

    print("🕒 Spavanje 60s...\n")
    time.sleep(60)
