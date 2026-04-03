import requests
import pandas as pd
import json
from datetime import datetime, timedelta

SYMBOLS = ["SDSC.ci", "BOAB.ci", "BOABF.ci", "BOAC.ci", "ECOC.ci", "NTLC.ci", "ORAC.ci", "SNTS.ci"]
GUID = "Bs6Jz65CExmMWlmTp3L4YeEt9PmzGZISgr-bFJ1DIyA"

def analyze():
    results = {}
    for sym in SYMBOLS:
        try:
            url = f"https://www.sikafinance.com/api/charting/GetTicksEOD?symbol={sym}&length=365&period=0&guid={GUID}"
            r = requests.get(url, timeout=15)
            if r.status_code != 200: continue
            
            df = pd.DataFrame(r.json(), columns=['d', 'open', 'high', 'low', 'close', 'volume'])
            
            # --- RSI MANUEL ---
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # --- BOLLINGER MANUEL ---
            df['ma'] = df['close'].rolling(window=20).mean()
            df['std'] = df['close'].rolling(window=20).std()
            df['u'] = df['ma'] + (df['std'] * 2)
            df['l'] = df['ma'] - (df['std'] * 2)

            last = df.iloc[-1]
            candles = []
            for _, row in df.iterrows():
                date = datetime(1970, 1, 1) + timedelta(days=int(row['d']))
                candles.append({"time": date.strftime('%Y-%m-%d'), "open": row['open'], "high": row['high'], "low": row['low'], "close": row['close']})

            results[sym] = {
                "name": sym, "candles": candles, "rsi": round(last['rsi'], 2),
                "bb_up": round(last['u'], 2), "bb_low": round(last['l'], 2),
                "decision": "ACHAT" if last['rsi'] < 30 else "VENTE" if last['rsi'] > 70 else "NEUTRE",
                "color": "#26a69a" if last['rsi'] < 30 else "#ef5350" if last['rsi'] > 70 else "#6b7280"
            }
        except: continue
            
    with open('data.json', 'w') as f:
        json.dump(results, f)

if __name__ == "__main__":
    analyze()
