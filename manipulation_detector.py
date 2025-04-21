import aiohttp
import asyncio
import statistics
import os
from dotenv import load_dotenv

load_dotenv()

BINANCE_BASE_URL = "https://fapi.binance.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

async def fetch(session, url, params):
    try:
        async with session.get(url, headers=HEADERS, params=params, timeout=10) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                print(f"⛔ HTTP {resp.status} za {url}")
                return None
    except Exception as e:
        print(f"⛔ Greška pri fetch-u {url}: {str(e)}")
        return None

async def get_klines(symbol, interval, limit=50):
    async with aiohttp.ClientSession() as session:
        url = f"{BINANCE_BASE_URL}/fapi/v1/klines"
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        return await fetch(session, url, params)

async def get_orderbook(symbol, limit=10):
    async with aiohttp.ClientSession() as session:
        url = f"{BINANCE_BASE_URL}/fapi/v1/depth"
        params = {"symbol": symbol.upper(), "limit": limit}
        return await fetch(session, url, params)

def detect_spoofing(orderbook):
    if not orderbook:
        return False
    bids = sum(float(b[1]) for b in orderbook['bids'])
    asks = sum(float(a[1]) for a in orderbook['asks'])
    ratio = bids / asks if asks > 0 else 0
    return ratio > 3 or ratio < 0.33

def detect_delta_flip(klines):
    volumes = [float(k[5]) for k in klines]
    if len(volumes) < 5:
        return False
    recent = volumes[-3:]
    avg = statistics.mean(volumes[:-3])
    return any(v > avg * 2 for v in recent)

def detect_imbalance(klines):
    imbalances = 0
    for k in klines[-10:]:
        open_price = float(k[1])
        close_price = float(k[4])
        high = float(k[2])
        low = float(k[3])
        spread = high - low
        body = abs(close_price - open_price)
        if spread > 0 and body / spread < 0.2:
            imbalances += 1
    return imbalances >= 3

def detect_choc(klines):
    if len(klines) < 5:
        return False
    prev_high = float(klines[-5][2])
    curr_high = float(klines[-1][2])
    return curr_high > prev_high

def detect_trap_wick(klines):
    traps = 0
    for k in klines[-10:]:
        high = float(k[2])
        low = float(k[3])
        open_price = float(k[1])
        close = float(k[4])
        wick_up = high - max(open_price, close)
        wick_down = min(open_price, close) - low
        if wick_up > wick_down * 2 or wick_down > wick_up * 2:
            traps += 1
    return traps >= 3

async def analyze_market(symbol, timeframe):
    klines = await get_klines(symbol, timeframe)
    orderbook = await get_orderbook(symbol)

    if not klines or len(klines) < 30:
        print(f"⚠️ Nedovoljno podataka za {symbol} / {timeframe}")
        return None

    spoof = detect_spoofing(orderbook)
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

    if len(setup) >= 1:
        last_close = float(klines[-1][4])
        entry = round(last_close, 2)
        sl = round(entry * 0.995, 2)
        tp = round(entry * 1.015, 2)

        return {
            "setup": " + ".join(setup),
            "verovatnoća": 70 + len(setup) * 5,
            "napomena": "Real-time manipulacije detektovane",
            "entry": entry,
            "sl": sl,
            "tp": tp
        }

    return None

# Za testiranje lokalno:
# asyncio.run(analyze_market("BTCUSDT", "1m"))
