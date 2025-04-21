import aiohttp
import asyncio
import datetime
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ NOVI FUNKCIONALNI BINANCE ENDPOINT
BINANCE_BASE = "https://api-gateway.binance.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9"
}

async def fetch_klines(session, symbol, interval, limit=50):
    url = f"{BINANCE_BASE}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        async with session.get(url, headers=HEADERS) as response:
            if response.status != 200:
                print(f"HTTP {response.status} za {url}")
                return None
            return await response.json()
    except Exception as e:
        print(f"Greška pri fetch_klines: {e}")
        return None

async def fetch_orderbook(session, symbol, limit=5):
    url = f"{BINANCE_BASE}/fapi/v1/depth?symbol={symbol}&limit={limit}"
    try:
        async with session.get(url, headers=HEADERS) as response:
            if response.status != 200:
                print(f"HTTP {response.status} za {url}")
                return None
            return await response.json()
    except Exception as e:
        print(f"Greška pri fetch_orderbook: {e}")
        return None

def analyze_klines(klines):
    if klines is None or len(klines) < 2:
        return False, "Nedovoljno podataka"

    body_sizes = [abs(float(k[4]) - float(k[1])) for k in klines[-5:]]
    avg_body = np.mean(body_sizes)
    if avg_body > 30:
        return True, "Agresivan pokret"
    return False, ""

def detect_spoofing(orderbook):
    if orderbook is None:
        return False

    bids = orderbook.get("bids", [])
    asks = orderbook.get("asks", [])

    if not bids or not asks:
        return False

    top_bid_volume = float(bids[0][1])
    top_ask_volume = float(asks[0][1])
    spoof_ratio = top_bid_volume / top_ask_volume if top_ask_volume else 0

    return spoof_ratio > 10 or spoof_ratio < 0.1

async def analyze_market(symbol, interval):
    async with aiohttp.ClientSession() as session:
        klines = await fetch_klines(session, symbol, interval)
        orderbook = await fetch_orderbook(session, symbol)

        if klines is None:
            print("❌ Nema klines podataka – fallback mod aktiviran.")
            return None

        pokret, poruka = analyze_klines(klines)
        spoofing = detect_spoofing(orderbook)

        if pokret or spoofing:
            setup = []
            if pokret:
                setup.append(poruka)
            if spoofing:
                setup.append("SPOOFING detektovan")

            return {
                "setup": ", ".join(setup),
                "verovatnoća": "SREDNJA",
                "napomena": "Korišćenje api-gateway + fake headers",
                "entry": float(klines[-1][4]) if klines else None,
                "sl": None,
                "tp": None
            }
        return None
