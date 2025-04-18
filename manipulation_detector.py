import requests
import time

def get_klines(symbol, interval, limit=10, retries=5, delay=1):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            if isinstance(data, list) and len(data) >= 5:
                print(f"✅ Stiglo {len(data)} sveća za {symbol} ({interval}) [pokušaj {attempt+1}]")
                return data
            else:
                print(f"⚠️ Pokušaj {attempt+1}: stiglo {len(data) if isinstance(data, list) else 'nevalidno'} za {symbol}")
        except Exception as e:
            print(f"❌ Greška pri dohvatu klines (pokušaj {attempt+1}): {e}")
        time.sleep(delay)
    print(f"⛔ Nedovoljno podataka iz klines za {symbol} – nije stiglo dovoljno sveća")
    return []

def analyze_market(symbol, interval):
    klines = get_klines(symbol, interval, limit=10)
    if not klines or len(klines) < 5:
        print(f"⛔ Nema dovoljno sveća za {symbol} / {interval}, analiza preskočena.")
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

    # 1. Spoofing detekcija
    if last['volume'] > 3 * prev['volume']:
        findings.append("Spoofing")
        print("✅ Spoofing detektovan")

    # 2. Delta Flip
    if abs(last['close'] - last['open']) > abs(prev['close'] - prev['open']) * 2:
        findings.append("Delta Flip")
        print("✅ Delta Flip detektovan")

    # 3. Imbalance Spike
    if (last['high'] - last['low']) > 2 * (prev['high'] - prev['low']):
        findings.append("Imbalance Spike")
        print("✅ Imbalance Spike detektovan")

    # 4. CHoCH Break
    recent_highs = [c['high'] for c in candles[-5:-1]]
    recent_lows = [c['low'] for c in candles[-5:-1]]
    if last['close'] > max(recent_highs):
        findings.append("CHoCH Break")
        print("✅ CHoCH Break (bullish)")
    elif last['close'] < min(recent_lows):
        findings.append("CHoCH Break")
        print("✅ CHoCH Break (bearish)")

    # 5. Trap Wick
    wick = last['high'] - last['low']
    body = abs(last['close'] - last['open'])
    if wick > body * 3:
        findings.append("Trap Wick")
        print("✅ Trap Wick detektovan")

    # 6. Momentum Breakout
    if last['close'] > last['open'] and last['close'] > prev['high']:
        findings.append("Momentum Breakout")
        print("✅ Momentum Breakout (bullish)")
    elif last['close'] < last['open'] and last['close'] < prev['low']:
        findings.append("Momentum Breakout")
        print("✅ Momentum Breakout (bearish)")

    if findings:
        setup = " + ".join(findings)
        verovatnoca = 85 if len(findings) >= 3 else 65
        napomena = "⚠️ Signal baziran na agresivnoj sveći"
        entry = round(last['close'], 2)
        sl = round(last['low'] if last['close'] > last['open'] else last['high'], 2)
        tp = round(last['close'] * 1.01 if last['close'] > last['open'] else last['close'] * 0.99, 2)

        print(f"📍 Signal potvrđen: {setup} | Entry: {entry}, SL: {sl}, TP: {tp}")
        return {
            "setup": setup,
            "verovatnoća": verovatnoca,
            "napomena": napomena,
            "entry": entry,
            "sl": sl,
            "tp": tp
        }
    else:
        print(f"❌ Nema manipulacija u {symbol} / {interval}")
        return None
