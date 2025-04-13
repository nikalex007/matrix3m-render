from keep_alive import keep_alive
from manipulation_detector import analyze_market
from telegram_notifier import send_telegram_message
import time

# Aktiviraj web server da bi Render držao bot živim
keep_alive()

# Pošalji start poruku
send_telegram_message("🤖 Matrix3M bot je aktiviran! Počinjem analizu za BTCUSDT...")

symbol = "BTCUSDT"
timeframes = ["1m", "5m", "15m"]

while True:
    for tf in timeframes:
        signal = analyze_market(symbol, tf)
        if signal:
            msg = f"✅ SIGNAL [{tf}]: {signal}"
            print(msg)
            send_telegram_message(msg)

    time.sleep(60)
