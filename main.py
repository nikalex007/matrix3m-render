from keep_alive import keep_alive
from manipulation_detector import analyze_market
from telegram_notifier import send_telegram_message
from datetime import datetime, timedelta
import time

debug_mode = True
keep_alive()

send_telegram_message("✅ Matrix3M bot pokrenut. Aktivni simboli: BTCUSDT, ETHUSDT na 1m i 5m (Greedy mod 1/6).")

symbols = ["BTCUSDT", "ETHUSDT"]
timeframes = ["1m", "5m"]
last_status = datetime.now()

while True:
    for symbol in symbols:
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

                tag = "✅ SIGNAL POSLAT" if len(active) >= 1 else "🟡 SLAB SIGNAL – Posmatrati"

                msg = f"""🎯 SIGNAL AKTIVAN
Symbol: {symbol} [{tf}]
Manipulacije: {manip_summary}
Ukupno: {len(active)}/{len(all_manips)} → {tag}
Setup: {setup}
Verovatnoća: {verovatnoca}%
Entry: {entry}
SL: {sl}
TP: {tp}
Napomena: {napomena}"""

                print(msg)
                send_telegram_message(msg)
                last_status = datetime.now()
            else:
                if debug_mode:
                    print(f"⛔ Nema signala za {symbol} / {tf}")

    # Ping svakih 2 sata ako nema pozicije
    if datetime.now() - last_status >= timedelta(hours=2):
        ping_msg = "⏳ Matrix3M aktivan, ali još nema signala. Pratim BTC/ETH na 1m i 5m..."
        print(ping_msg)
        send_telegram_message(ping_msg)
        last_status = datetime.now()

    if debug_mode:
        print("🕒 Spavanje 30s...\n")
    time.sleep(30)
