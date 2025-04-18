from keep_alive import keep_alive
from manipulation_detector import analyze_market
from telegram_notifier import send_telegram_message
from datetime import datetime, timedelta
import time

debug_mode = True  # <=== KLJUČNO za logovanje

keep_alive()
send_telegram_message("✅ Matrix3M bot je pokrenut. Aktivna analiza BTCUSDT na 1m timeframe-u.")

symbol = "BTCUSDT"
timeframes = ["1m"]
last_status = datetime.now()

while True:
    for tf in timeframes:
        if debug_mode:
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
            all_manips = ["Spoofing", "Delta Flip", "Imbalance Spike", "CHoCH Break", "Trap Wick", "Momentum Breakout"]
            manip_list = []
            for m in all_manips:
                if any(m.lower() in a.lower() for a in active):
                    manip_list.append(f"[x] {m}")
                else:
                    manip_list.append(f"[ ] {m}")
            manip_summary = ', '.join(manip_list)

            tag = "✅ SIGNAL POSLAT" if len(active) >= 2 else "🟡 SLAB SIGNAL – Posmatrati"

            msg = f"""🎯 SIGNAL AKTIVAN
Symbol: {symbol} [{tf}]
Manipulacije: {manip_summary}
Ukupno: {len(active)}/6 → {tag}
Setup: {setup}
Verovatnoća: {verovatnoca}%
Entry: {entry}
SL: {sl}
TP: {tp}
Napomena: {napomena}"""

            print(msg)
            send_telegram_message(msg)
        else:
            if debug_mode:
                print(f"⛔ Nema signala za {symbol} / {tf}")

    if datetime.now() - last_status >= timedelta(hours=2):
        msg_stat = "⏳ Matrix3M bot je aktivan, ali još nema validnih signala. Pratim BTCUSDT na 1m..."
        if debug_mode:
            print(msg_stat)
        send_telegram_message(msg_stat)
        last_status = datetime.now()

    if debug_mode:
        print("🕒 Spavanje 30s...\n")
    time.sleep(30)
