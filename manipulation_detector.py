import aiohttp
import asyncio
import datetime
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

BINANCE_BASE = "https://fapi.binance.com"

async def fetch_json(session, url):
    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            print(f"HTTP {response.status} za {url}")
            return None
        return await response.json()

async def fetch_klines(session, symbol, interval, limit=50):
    url = f"{BINANCE_BASE}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    return await fetch_json(session, url)

async def fetch_orderbook(session, symbol, limit=5):
    url = f"{BINANCE_BASE}/fapi/v1/depth?symbol={symbol}&limit={limit}"
    return await fetch_json(session, url)

def calculate_delta(candles):
    return float(candles[-1][5]) - float(candles[-2][5])

async def analyze_market(symbol, interval):
    async with aiohttp.ClientSession() as session:
        candles = await fetch_klines(session, symbol, interval)
        orderbook = await fetch_orderbook(session, symbol)

        if not candles or not orderbook:
            print(f"⚠️ Nedovoljno podataka za {symbol} / {interval}")
            return None

        delta = calculate_delta(candles)
        top_bid = float(orderbook['bids'][0][0])
        top_ask = float(orderbook['asks'][0][0])
        spread = top_ask - top_bid

        now = datetime.datetime.now().strftime("%H:%M:%S")

        if spread < 1 and abs(delta) > 500:
            direction = "BUY" if delta > 0 else "SELL"
            return {
                "setup": f"Delta spike + low spread [{direction}]",
                "verovatnoća": "85%",
                "napomena": f"Delta: {delta:.2f}, Spread: {spread:.2f} @ {now}",
                "entry": top_ask if delta > 0 else top_bid,
                "sl": top_ask + 50 if delta < 0 else top_bid - 50,
                "tp": top_ask - 100 if delta < 0 else top_bid + 100
            }

        print(f"🟡 Nema signala za {symbol} / {interval}")
        return None
