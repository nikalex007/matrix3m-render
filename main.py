from keep_alive import keep_alive
from manipulation_detector import analyze_market
from telegram_notifier import send_telegram_message
from datetime import datetime, timedelta
import time

keep_alive()
send_telegram_message("✅ Matrix3M bot je aktiviran i analizira BTCUSDT na 5 timeframe-ova.")

symbol = "BTCUSDT"
timeframes = ["1m", "5m", "15m", "1h", "4h"]
last_status = datetime.now()

while True:
    signal_sent = False

    for tf in timeframes:
        print(f"📊 Proveravam: {symbol} / {tf}")
        signal = analyze_market(symbol, tf)

        if signal:
            setup = signal.get('setup', '')
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

            if len(active) >= 2:
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
                signal_sent = True
            else:
                print(f"⚠️ {symbol} / {tf} - Samo {len(active)}/5 detektovano. Signal NIJE poslat.")
        else:
            print(f"⛔ Nema signala za {symbol} / {tf}")

    # ⏱ Status poruka svaka 2h ako NIJE poslat nijedan signal
    if not signal_sent and datetime.now() - last_status >= timedelta(hours=2):
        send_telegram_message("⏳ Matrix3M bot je aktivan, ali još nema validnih signala (2/5). Pratim BTCUSDT...")
        last_status = datetime.now()

    print("🕒 Spavanje 60s...\n")
    time.sleep(60)
