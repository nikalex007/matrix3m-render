import requests
import time

def get_klines(symbol, interval, limit=10, retries=5, delay=1):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if isinstance(data, list) and len(data) == limit:
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
    if not klines or len(klines) < 5:
        print(f"⛔ Nema dovoljno podataka za {symbol} / {interval}")
        return None

    # Pretvaramo u float vrednosti poslednjih 10 sveća
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

    # 1. Spoofing detekcija (nagla promena volumena)
    if last['volume'] > 3 * prev['volume']:
        findings.append("Spoofing")
        print("✅ Spoofing detektovan")

    # 2. Delta Flip (open-close razlika i wick obrti)
    if abs(last['close'] - last['open']) > abs(prev['close'] - prev['open']) * 2:
        findings.append("Delta Flip")
        print("✅ Delta Flip detektovan")

    # 3. Imbalance Spike
    if (last['high'] - last['low']) > 2 * (prev['high'] - prev['low']):
        findings.append("Imbalance Spike")
        print("✅ Imbalance Spike detektovan")

    # 4. CHoCH Break (simple struktura)
    if last['close'] > max(c['high'] for c in candles[-5:-1]):
        findings.append("CHoCH Break")
        print("✅ CHoCH Break (bullish)")

    elif last['close'] < min(c['low'] for c in candles[-5:-1]):
        findings.append("CHoCH Break")
        print("✅ CHoCH Break (bearish)")

    # 5. Trap Wick (shadow manipulacija)
    wick = last['high'] - last['low']
    body = abs(last['close'] - last['open'])
    if wick > body * 3:
        findings.append("Trap Wick")
        print("✅ Trap Wick detektovan")

    # 6. Momentum Breakout
    if (last['close'] > last['open']) and (last['close'] > prev['high']):
        findings.append("Momentum Breakout")
        print("✅ Momentum Breakout (bullish)")

    elif (last['close'] < last['open']) and (last['close'] < prev['low']):
        findings.append("Momentum Breakout")
        print("✅ Momentum Breakout (bearish)")

    if findings:
        return {
            "setup": " + ".join(findings),
            "verovatnoća": 85 if len(findings) >= 3 else 65,
            "napomena": "⚠️ Signal baziran na agresivnoj sveći",
            "entry": round(last['close'], 2),
            "sl": round(last['low'] if last['close'] > last['open'] else last['high'], 2),
            "tp": round(last['close'] * 1.01 if last['close'] > last['open'] else last['close'] * 0.99, 2)
        }
    else:
        print(f"❌ Nema manipulacija u {symbol} / {interval}")
        return None
