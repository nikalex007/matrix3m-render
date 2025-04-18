import requests
import time

def get_klines(symbol, interval, limit=10, retries=5, delay=1):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if isinstance(data, list) and len(data) >= 3:
                return data
            else:
                print(f"⚠️ Pokušaj {attempt+1}: stiglo samo {len(data)} sveća za {symbol}")
        except Exception as e:
            print(f"❌ Greška pri dohvatu klines (pokušaj {attempt+1}): {e}")
        time.sleep(delay)
    print(f"⛔ Nedovoljno podataka iz klines za {symbol} – stiglo {len(data) if isinstance(data, list) else 'nevalidan odgovor'}")
    return []

def analyze_market(symbol, interval):
    klines = get_klines(symbol, interval, limit=10)
    if not klines or len(klines) < 3:
        print(f"⛔ Nema dovoljno podataka za {symbol} / {interval}")
        return None

    print(f"🔍 Broj sveća za analizu: {len(klines)}")

    candles = [{
        'open': float(k[1]),
        'high': float(k[2]),
        'low': float(k[3]),
        'close': float(k[4]),
        'volume': float(k[5])
    } for k in klines]

    last = candles[-1]
    prev = candles[-2] if len(candles) >= 2 else last

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
        napomena = "🧪 Partial Data Analysis" if len(candles) < 10 else "⚠️ Signal baziran na agresivnoj sveći"
        return {
            "setup": " + ".join(findings),
            "verovatnoća": 85 if len(findings) >= 3 else 65,
            "napomena": napomena,
            "entry": round(last['close'], 2),
            "sl": round(last['low'] if last['close'] > last['open'] else last['high'], 2),
            "tp": round(last['close'] * 1.01 if last['close'] > last['open'] else last['close'] * 0.99, 2)
        }
    else:
        print(f"❌ Nema manipulacija u {symbol} / {interval}")
        return None
