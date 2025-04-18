import requests
import statistics
import time

BINANCE_BASE_URL = "https://api.binance.com"

def get_klines(symbol, interval, limit=30, retries=2):
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    for _ in range(retries):
        response = requests.get(url, params=params)
        klines = response.json()
        if isinstance(klines, list) and len(klines) >= 12:
            return klines
        time.sleep(3)
    return []

def get_orderbook(symbol, limit=10):
    url = f"{BINANCE_BASE_URL}/api/v3/depth"
    params = {"symbol": symbol, "limit": limit}
    try:
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        if 'bids' in data and 'asks' in data:
            return data
        else:
            return None
    except:
        return None

def detect_spoofing(symbol):
    ob = get_orderbook(symbol)
    if not ob or 'bids' not in ob or 'asks' not in ob:
        return False
    bids = sum(float(b[1]) for b in ob['bids'])
    asks = sum(float(a[1]) for a in ob['asks'])
    ratio = bids / asks if asks > 0 else 0
    return ratio > 1.5 or ratio < 0.7

def detect_delta_flip(klines):
    if len(klines) < 12:
        return False
    volumes = [float(k[5]) for k in klines]
    recent = volumes[-10:]
    avg = statistics.mean(volumes[:-10]) if len(volumes) > 10 else 0
    return any(v > avg * 1.1 for v in recent)

def detect_imbalance(klines):
    if len(klines) < 15:
        return False
    for k in klines[-15:]:
        high = float(k[2])
        low = float(k[3])
        open_price = float(k[1])
        close_price = float(k[4])
        spread = high - low
        body = abs(close_price - open_price)
        if spread > 0 and body / spread < 0.5:
            return True
    return False

def detect_choc(klines):
    if len(klines) < 11:
        return False
    prev_high = float(klines[-11][2])
    curr_high = float(klines[-1][2])
    return curr_high > prev_high

def detect_trap_wick(klines):
    if len(klines) < 15:
        return False
    for k in klines[-15:]:
        high = float(k[2])
        low = float(k[3])
        open_price = float(k[1])
        close_price = float(k[4])
        wick_up = high - max(open_price, close_price)
        wick_down = min(open_price, close_price) - low
        if wick_up > wick_down * 1.4 or wick_down > wick_up * 1.4:
            return True
    return False

def detect_momentum_breakout(klines):
    if len(klines) < 12:
        return False
    last = klines[-1]
    prev = klines[-2]
    last_range = float(last[2]) - float(last[3])
    prev_range = float(prev[2]) - float(prev[3])
    if prev_range == 0:
        return False
    range_spike = last_range > prev_range * 2
    volume_spike = float(last[5]) > float(prev[5]) * 2
    price_change = abs(float(last[4]) - float(prev[4])) / float(prev[4]) > 0.005
    return range_spike and volume_spike and price_change

def analyze_market(symbol, timeframe):
    try:
        klines = get_klines(symbol, timeframe, limit=30)
        if not klines or len(klines) < 12:
            print("⚠️ Nedovoljno podataka iz klines za", symbol)
            return None

        spoof = detect_spoofing(symbol)
        delta = detect_delta_flip(klines)
        imbalance = detect_imbalance(klines)
        choc = detect_choc(klines)
        wick = detect_trap_wick(klines)
        momentum = detect_momentum_breakout(klines)

        # DEBUG ISPIS
        print(f"--- Detekcija ({symbol} / {timeframe}) ---")
        print(f"Spoofing: {spoof}")
        print(f"Delta Flip: {delta}")
        print(f"Imbalance Spike: {imbalance}")
        print(f"CHoCH Break: {choc}")
        print(f"Trap Wick: {wick}")
        print(f"Momentum Breakout: {momentum}")
        print("-----------------------------------------")

        setup = []
        if spoof: setup.append("Spoofing")
        if delta: setup.append("Delta Flip")
        if imbalance: setup.append("Imbalance Spike")
        if choc: setup.append("CHoCH Break")
        if wick: setup.append("Trap Wick")
        if momentum: setup.append("Momentum Breakout")

        if len(setup) > 0:
            last_close = float(klines[-1][4])
            entry = round(last_close, 2)
            sl = round(entry * 0.995, 2)
            tp = round(entry * 1.015, 2)
            return {
                "setup": " + ".join(setup),
                "verovatnoća": 50 + len(setup) * 10,
                "napomena": "DEBUG MODE: vidi terminal za sve detekcije",
                "entry": entry,
                "sl": sl,
                "tp": tp
            }

        return None

    except Exception as e:
        print("Greška u analizi (debug):", str(e))
        return None
