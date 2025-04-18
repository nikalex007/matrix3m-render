import requests
import time

# Globalni keš
cached_klines = {}

def get_klines(symbol, interval, limit=10, retries=5, delay=1):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if isinstance(data, list) and len(data) >= 3:
                cached_klines[(symbol, interval)] = data  # ažuriraj keš
                return data
            else:
                print(f"⚠️ Pokušaj {attempt+1}: stiglo samo {len(data)} sveća za {symbol}")
        except Exception as e:
            print(f"❌ Greška pri dohvatu klines (pokušaj {attempt+1}): {e}")
        time.sleep(delay)

    # Ako nismo uspeli, koristi fallback
    if (symbol, interval) in cached_klines:
        print("♻️ Koristim keširane sveće (fallback)")
        return cached_klines[(symbol, interval)]
    else:
        print("⛔ Nedovoljno podataka ni za fallback")
        return []

def analyze_market(symbol, interval):
    klines = get_klines(symbol, interval, limit=10)
    if not klines or len(klines) < 3:
        print(f"⛔ Nema dovoljno podataka za {symbol} / {interval}")
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
    before_prev = candles[-3]

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
        highs = [c['high'] for c in candles[-5:-1]]
        lows = [c['low'] for c in candles[-5:-1]]
        if last['close'] > max(highs):
            findings.append("CHoCH Break")
            print("✅ CHoCH Break (bullish)")
        elif last['close'] < min(lows):
            findings.append("CHoCH Break")
            print("✅ CHoCH Break (bearish)")

    wick = last['high'] - last['low']
    body = abs(last['close'] - last['open'])
    if wick > body * 3:
        findings.append("Trap Wick")
        print("✅ Trap Wick detektovan")

    if (last['close'] > last['open']) and (last['close'] > prev['high']) and (prev['close'] > before_prev['high']):
        findings.append("Momentum Breakout")
        print("✅ Momentum Breakout (bullish)")
    elif (last['close'] < last['open']) and (last['close'] < prev['low']) and (prev['close'] < before_prev['low']):
        findings.append("Momentum Breakout")
        print("✅ Momentum Breakout (bearish)")

    if findings:
        return {
            "setup": " + ".join(sorted(findings)),
            "verovatnoća": 90 if len(findings) >= 3 else 75 if len(findings) == 2 else 60,
            "napomena": "⚠️ Kombinovani fallback + greedy mod: analiza zadnje 3 sveće",
            "entry": round(last['close'], 2),
            "sl": round(last['low'] if last['close'] > last['open'] else last['high'], 2),
            "tp": round(last['close'] * 1.01 if last['close'] > last['open'] else last['close'] * 0.99, 2)
        }
    else:
        print(f"❌ Nema manipulacija u {symbol} / {interval}")
        return None
