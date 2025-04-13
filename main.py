
from keep_alive import keep_alive
from manipulation_detector import analyze_market
import time

# Aktiviraj web server da bi Render držao bot živim
keep_alive()

symbol = "BTCUSDT"
timeframes = ["1m", "5m", "15m"]

while True:
    for tf in timeframes:
        signal = analyze_market(symbol, tf)
        if signal:
            print(f"✅ SIGNAL {tf}: {signal}")
    time.sleep(60)
