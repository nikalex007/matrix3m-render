import requests
import statistics

BINANCE_BASE_URL = "https://api.binance.com"

def get_klines(symbol, interval, limit=20):
    url = f"{BINANCE_BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    response = requests.get(url, params=params)
    return response.json()

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
    return ratio > 1.8 or ratio < 0.6

def detect_delta_flip(klines):
    volumes = [float(k[5]) for k in klines]
    if len(volumes) < 8:
        return False
    recent = volumes[-5:]
    avg = statistics.mean(volumes[:-5]) if len(volumes) > 5 else 0
    return any(v > avg * 1.15 for v in recent)

def detect_imbalance(klines):
    for k in klines[-10:]:
        high = float(k[2])
        low = float(k[3])
        open_price = float(k[1])
        close_price = float(k[4])
        spread = high - low
        body = abs(close_price - open_price)
        if spread > 0 and body / spread < 0.35:
            return True
    return False

def detect_choc(klines):
    if len(klines) < 6:
        return False
    prev_high = float(klines[-6][2])
    curr_high = float(klines[-1][2])
    return curr_high > prev_high

def detect_trap_wick(klines):
    for k in klines[-10:]:
        high = float(k[2])
        low = float(k[3])
        open_price = float(k[1])
        close_price = float(k[4])
        wick_up = high - max(open_price, close_price)
        wick_down = min(open_price, close_price) - low
        if wick_up > wick_down * 1.8 or wick_down > wick_up * 1.8:
            return True
    return False

def analyze_market(symbol, timeframe):
    try:
        klines = get_klines(symbol, timeframe, limit=20)
        if not klines:
            return None

        spoof = detect_spoofing(symbol)
        delta = detect_delta_flip(klines)
        imbalance = detect_imbalance(klines)
        choc = detect_choc(klines)
        wick = detect_trap_wick(klines)

        setup = []
        if spoof: setup.append("Spoofing")
        if delta: setup.append("Delta Flip")
        if imbalance: setup.append("Imbalance Spike")
        if choc: setup.append("CHoCH Break")
        if wick: setup.append("Trap Wick")

        if len(setup) > 0:
            last_close = float(klines[-1][4])
            entry = round(last_close, 2)
            sl = round(entry * 0.995, 2)
            tp = round(entry * 1.015, 2)
            return {
                "setup": " + ".join(setup),
                "verovatnoća": 55 + len(setup) * 10,
                "napomena": "EMERGENCY MODE: signal baziran na 1+ manipulaciji",
                "entry": entry,
                "sl": sl,
                "tp": tp
            }

        return None

    except Exception as e:
        print("Greška u analizi (emergency):", str(e))
        return None
