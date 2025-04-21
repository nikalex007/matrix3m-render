import aiohttp
import asyncio
import datetime
import numpy as np

BINANCE_BASE = "https://fapi.binance.com"

async def fetch_klines(session, symbol, interval, limit=50):
    url = f"{BINANCE_BASE}/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
    }
    try:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"❌ HTTP {response.status} za {url}")
                return None
            return await response.json()
    except Exception as e:
        print(f"⚠️ Greška pri fetch klines: {e}")
        return None

def analiziraj_svece(klines):
    cene = [float(k[4]) for k in klines]
    if len(cene) < 3:
        return None
    if cene[-1] > cene[-2] < cene[-3]:
        return "Long setup (mogući bounce)"
    if cene[-1] < cene[-2] > cene[-3]:
        return "Short setup (mogući rejection)"
    return None

async def analyze_market(symbol, interval):
    async with aiohttp.ClientSession() as session:
        klines = await fetch_klines(session, symbol, interval)
        if not klines or len(klines) < 10:
            print(f"⚠️ Nedovoljno podataka za {symbol} / {interval}")
            return None

        rezultat = analiziraj_svece(klines)
        if rezultat:
            return {
                "setup": rezultat,
                "verovatnoća": "⚡ 60-70%",
                "napomena": "Testna verzija – detekcija po kretanju cene",
                "entry": klines[-1][1],
                "sl": klines[-1][3],
                "tp": klines[-1][2]
            }

        return None

# Test mod za lokalnu proveru
if __name__ == "__main__":
    symbol = "BTCUSDT"
    interval = "1m"
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(analyze_market(symbol, interval))
    if result:
        print("✅ SIGNAL:", result)
    else:
        print("🚫 Nema signala")
