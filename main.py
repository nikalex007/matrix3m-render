from keep_alive import keep_alive
from manipulation_detector import analyze_market
from telegram_notifier import send_telegram_message
import time

keep_alive()
send_telegram_message("✅ Matrix3M TEST režim aktiviran – prati sve TF-ove sa 2/5 pragom.")

symbol = "BTCUSDT"
timeframes = ["1m", "5m", "15m", "1h", "4h"]
last_no_signal_sent = {tf: 0 for tf in timeframes}
no_signal_delay = 60 * 60  # 1 sat

while True:
    for tf in timeframes:
        print(f"🔍 Proveravam: {symbol} / {tf}")
        signal = analyze_market(symbol, tf)
        print(f"📊 Rezultat analize za {tf}: {signal}")

        if signal:
            setup = signal.get('setup', 'Nepoznat setup')
            verovatnoca = signal.get('verovatnoća', 'N/A')
            napomena = signal.get('napomena', '')
            entry = signal.get('entry')
            sl = signal.get('sl')
            tp = signal.get('tp')
            rrr = round((tp - entry) / (entry - sl), 2) if entry and sl and tp else "N/A"

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
                msg = (
                    f"TESTNI SIGNAL za {symbol} [{tf}]\n"
                    f"Manipulacije: {manip_summary}\n"
                    f"Ukupno: {len(active)}/5 - SIGNAL AKTIVAN (TEST režim)\n\n"
                    f"Setup: {setup}\n"
                    f"Entry: {entry}\n"
                    f"SL: {sl}\n"
                    f"TP: {tp}\n"
                    f"RRR: {rrr}\n"
                    f"Verovatnoća: {verovatnoca}%\n"
                    f"Napomena: {napomena}"
                )
                print(msg)
                send_telegram_message(msg)

            else:
                now = time.time()
                if now - last_no_signal_sent[tf] > no_signal_delay:
                    msg = (
                        f"TEST analiza za {symbol} [{tf}]\n"
                        f"Manipulacije: {manip_summary}\n"
                        f"Ukupno: {len(active)}/5 - Ispod praga (TEST režim)\n"
                        f"Signal NIJE poslat"
                    )
                    print(msg)
                    send_telegram_message(msg)
                    last_no_signal_sent[tf] = now
                else:
                    print(f"⏱ Skipped 'nema signal' poruka za {tf} (još u okviru 1h)")

        else:
            now = time.time()
            if now - last_no_signal_sent[tf] > no_signal_delay:
                msg = (
                    f"TEST analiza za {symbol} [{tf}]\n"
                    f"Manipulacije: 0/5 - Ispod praga (TEST režim)\n"
                    f"Signal NIJE poslat"
                )
                print(msg)
                send_telegram_message(msg)
                last_no_signal_sent[tf] = now
            else:
                print(f"⏱ Skipped 'nema signal' poruka za {tf} (još u okviru 1h)")

    print("🕒 Spavanje 60 sekundi...\n")
    time.sleep(60)
