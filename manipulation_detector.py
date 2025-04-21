import aiohttp
import asyncio
import time
import statistics
from datetime import datetime

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}

async def fetch(session, url):
    try:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"\u274c HTTP {response.status} za {url}")
                return None
    except Exception as e:
        print(f"\u26a0\ufe0f Greska u fetch: {e}")
        return None

async def analyze_market(symbol: str, timeframe: str):
    base_url = "https://fapi.binance.com"
    klines_url = f"{base_url}/fapi/v1/klines?symbol={symbol}&interval={timeframe}&limit=50"
    depth_url = f"{base_url}/fapi/v1/depth?symbol={symbol}&limit=5"

    async with aiohttp.ClientSession() as session:
        candles, orderbook = await asyncio.gather(
            fetch(session, klines_url),
            fetch(session, depth_url)
        )

    if not candles or len(candles) < 30:
        print(f"\u26a0\ufe0f Nedovoljno podataka za {symbol} / {timeframe}")
        return None

    try:
        last = candles[-1]
        close = float(last[4])
        open_price = float(last[1])
        high = float(last[2])
        low = float(last[3])
        volume = float(last[5])

        bodies = [abs(float(c[4]) - float(c[1])) for c in candles[-10:]]
        avg_body = statistics.mean(bodies)
        big_candle = abs(close - open_price) > avg_body * 1.5

        delta = close - open_price
        imbalance = abs(high - low) > avg_body * 2

        # Spoofing check (fake order walls)
        if orderbook:
            bid_vol = sum(float(x[1]) for x in orderbook['bids'])
            ask_vol = sum(float(x[1]) for x in orderbook['asks'])
            spoof = bid_vol > ask_vol * 4 or ask_vol > bid_vol * 4
        else:
            spoof = False

        if big_candle or spoof or imbalance:
            print(f"\u2705 Detektovan potencijalni Matrix3M setup za {symbol} / {timeframe}")
            return {
                "setup": "Matrix3M Auto Trigger",
                "verovatnoća": "75%",
                "napomena": "Delta/Imbalance/Spoofing logika aktivirana",
                "entry": round(close, 2),
                "sl": round(close * 0.9975, 2),
                "tp": round(close * 1.005, 2)
            }

    except Exception as e:
        print(f"\u274c Greska u analizi: {e}")
        return None

    print(f"\u274c Nema signala za {symbol} / {timeframe}")
    return None
