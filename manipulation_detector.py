
import requests
from datetime import datetime

def get_last_candles(symbol="BTCUSDT", interval="1m", limit=5):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    try:
        response = requests.get(url, params=params)
        return response.json()
    except Exception as e:
        print("Greška kod klines:", e)
        return []

def detect_delta_flip(symbol="BTCUSDT", interval="1m"):
    candles = get_last_candles(symbol, interval, 2)
    if not isinstance(candles, list) or len(candles) < 2:
        return False
    prev = candles[-2]
    curr = candles[-1]
    prev_buy = float(prev[10])
    curr_buy = float(curr[10])
    prev_total = float(prev[5])
    curr_total = float(curr[5])
    prev_sell = prev_total - prev_buy
    curr_sell = curr_total - curr_buy
    prev_dom = "buy" if prev_buy > prev_sell else "sell"
    curr_dom = "buy" if curr_buy > curr_sell else "sell"
    return prev_dom != curr_dom

def get_orderbook(symbol="BTCUSDT", limit=10):
    url = f"https://api.binance.com/api/v3/depth"
    try:
        res = requests.get(url, params={"symbol": symbol, "limit": limit})
        return res.json()
    except Exception as e:
        print("Greška kod order book-a:", e)
        return {}

def detect_spoofing_layer(symbol="BTCUSDT"):
    book = get_orderbook(symbol)
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    if not bids or not asks:
        return False
    bid_vol = sum(float(b[1]) for b in bids)
    ask_vol = sum(float(a[1]) for a in asks)
    ratio = bid_vol / ask_vol if ask_vol else 0
    return ratio > 3 or ratio < 1/3

def detect_imbalance_spike(symbol="BTCUSDT"):
    book = get_orderbook(symbol)
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    if not bids or not asks:
        return False
    bid_vol = sum(float(b[1]) for b in bids)
    ask_vol = sum(float(a[1]) for a in asks)
    total = bid_vol + ask_vol
    if total == 0:
        return False
    imbalance = (bid_vol - ask_vol) / total
    return abs(imbalance) > 0.6

def detect_choch_shift(symbol="BTCUSDT", interval="1m"):
    candles = get_last_candles(symbol, interval, 5)
    if not isinstance(candles, list) or len(candles) < 5:
        return False
    highs = [float(c[2]) for c in candles]
    lows = [float(c[3]) for c in candles]
    trend_h = "up" if highs[1] < highs[2] < highs[3] else "down" if highs[1] > highs[2] > highs[3] else None
    trend_l = "down" if lows[1] > lows[2] > lows[3] else "up" if lows[1] < lows[2] < lows[3] else None
    if trend_h == "up" and highs[4] < highs[3]:
        return True
    if trend_l == "down" and lows[4] > lows[3]:
        return True
    return False

def detect_trap_wick(symbol="BTCUSDT", interval="1m"):
    candles = get_last_candles(symbol, interval, 1)
    if not isinstance(candles, list) or len(candles) < 1:
        return False
    c = candles[-1]
    open_, high, low, close = float(c[1]), float(c[2]), float(c[3]), float(c[4])
    body = abs(close - open_)
    wick_top = high - max(open_, close)
    wick_bot = min(open_, close) - low
    wick_ratio = max(wick_top, wick_bot) / body if body else 0
    return wick_ratio > 2.5

def detect_breakout_pressure(symbol="BTCUSDT", interval="1m"):
    candles = get_last_candles(symbol, interval, 2)
    if not isinstance(candles, list) or len(candles) < 2:
        return None
    prev = candles[-2]
    curr = candles[-1]
    prev_buy = float(prev[10])
    curr_buy = float(curr[10])
    prev_total = float(prev[5])
    curr_total = float(curr[5])
    prev_sell = prev_total - prev_buy
    curr_sell = curr_total - curr_buy
    prev_dom = "buy" if prev_buy > prev_sell else "sell"
    curr_dom = "buy" if curr_buy > curr_sell else "sell"
    delta_dir = curr_dom
    book = get_orderbook(symbol)
    bids = book.get("bids", [])
    asks = book.get("asks", [])
    if not bids or not asks:
        return None
    bid_vol = sum(float(b[1]) for b in bids)
    ask_vol = sum(float(a[1]) for a in asks)
    total = bid_vol + ask_vol
    imbalance = (bid_vol - ask_vol) / total if total else 0
    imbalance_dir = "buy" if imbalance > 0.6 else "sell" if imbalance < -0.6 else None
    spoof_dir = None
    if bid_vol / ask_vol > 3:
        spoof_dir = "buy"
    elif ask_vol / bid_vol > 3:
        spoof_dir = "sell"
    if delta_dir == imbalance_dir and spoof_dir and spoof_dir != delta_dir:
        return delta_dir
    return None

def analyze_market(pair, timeframe):
    spoofing = detect_spoofing_layer(pair)
    delta = detect_delta_flip(pair, timeframe)
    imbalance = detect_imbalance_spike(pair)
    choch = detect_choch_shift(pair, timeframe)
    trap = detect_trap_wick(pair, timeframe)
    breakout = detect_breakout_pressure(pair, timeframe)

    manipulacije = {
        "Spoofing": spoofing,
        "Delta Flip": delta,
        "Imbalance Spike": imbalance,
        "CHoCH Break": choch,
        "Trap Wick": trap
    }

    ukupno = sum(manipulacije.values())
    if ukupno >= 3:
        aktivne = [k for k, v in manipulacije.items() if v]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "signal": True,
            "setup": f"Matrix3M: {' + '.join(aktivne)}",
            "entry": "75,800 – 76,100",
            "tp": "76,900",
            "sl": "75,500",
            "rrr": "2.5",
            "verovatnoća": str(70 + ukupno * 5),
            "napomena": f"🧠 {ukupno}/5 manipulacija detektovano ({', '.join(aktivne)}) [{now}] | Breakout bias: {breakout or 'N/A'}"
        }

    return None
