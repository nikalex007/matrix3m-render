import requests
import time

# Globalna keš memorija za fallback
cached_klines = []

def get_klines(symbol, interval, limit=10, retries=5, delay=1):
    global cached_klines
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if isinstance(data, list) and len(data) >= 3:
                cached_klines = data  # update keš
                return data
            else:
                print(f"⚠️ Pokušaj {attempt+1}: stiglo {len(data)} sveća")
        except Exception as e:
            print(f"❌ Greška pri dohvatu klines: {e}")
        time.sleep(delay)

    print("🔁 Koristim keširane sveće (fallback)")
    return cached_klines if len(cached_klines) >= 3 else []

def is_trigger_candle(kline):
    open_price = float(kline[1])
    close_price = float(kline[4])
    high = float(kline[2])
    low = float(kline[3])
    volume = float(kline[5])

    spread = high - low
    body = abs(close_price - open_price)

    if spread > 30 and body > 15 and volume > 100:
        print("🚨 Trigger sveća detektovana (Momentum pokret)")
        return True
    return False

def analyze_market(symbol, interval):
    klines = get_klines(symbol, interval, limit=10)
    if not klines or len(klines) < 3:
        print("⛔ Nedovoljno podataka ni za fallback")
        return None

    if not is_trigger_candle(klines[-1]):
        print("⏸ Nema trigger sveće, preskačem analizu.")
        return None

    candles = [{
        'open': float(k[1]),
        'high': float(k[2]),
        'low': float(k[3]),
        'close': float(k[4]),
        'volume': float(k[5])
    } for k in klines]

    last = candles[-1]
    prev = candles[-2]

    findings = []

    if last['volume'] > 3 * prev['volume']:
        findings.append("Spoofing")
        print("✅ Spoofing detektovan")

    if abs(last['close'] - last['open']) > abs(prev['close'] - prev['open']) * 2:
        findings.append("Delta Flip")
        print("✅ Delta Flip detektovan")

    if (last['high'] - last['low']) > 2 * (prev['high'] - prev['low']):
        findings.append("Imbalance Spike")
        print("✅ Imbalance Spike detektovan")

    if len(candles) >= 5:
        recent_highs = [c['high'] for c in candles[-5:-1]]
        recent_lows = [c['low'] for c in candles[-5:-1]]
        if last['close'] > max(recent_highs):
            findings.append("CHoCH Break")
            print("✅ CHoCH Break (bullish)")
        elif last['close'] < min(recent_lows):
            findings.append("CHoCH Break")
            print("✅ CHoCH Break (bearish)")

    wick = last['high'] - last['low']
    body = abs(last['close'] - last['open'])
    if wick > body * 3:
        findings.append("Trap Wick")
        print("✅ Trap Wick detektovan")

    if (last['close'] > last['open']) and (last['close'] > prev['high']):
        findings.append("Momentum Breakout")
        print("✅ Momentum Breakout (bullish)")
    elif (last['close'] < last['open']) and (last['close'] < prev['low']):
        findings.append("Momentum Breakout")
        print("✅ Momentum Breakout (bearish)")

    if findings:
        verovatnoca = 90 if len(findings) >= 3 else 75 if len(findings) == 2 else 60
        print(f"🎯 Signal potvrđen | Manipulacije: {', '.join(findings)}")
        return {
            "setup": " + ".join(findings),
            "verovatnoća": verovatnoca,
            "napomena": "💡 Trigger + Greedy + Fallback mod",
            "entry": round(last['close'], 2),
            "sl": round(last['low'] if last['close'] > last['open'] else last['high'], 2),
            "tp": round(last['close'] * 1.01 if last['close'] > last['open'] else last['close'] * 0.99, 2)
        }
    else:
        print("❌ Nema manipulacija u sveći – iako je trigger postojao.")
        return None
