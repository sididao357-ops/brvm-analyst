import requests
import pandas as pd
import json
from datetime import datetime, timedelta

SYMBOLS = {
    "SDSC.ci": "AFRICA GLOBAL LOGISTICS CI",
    "BOAB.ci": "BANK OF AFRICA BENIN",
    "BOABF.ci": "BANK OF AFRICA BURKINA FASO",
    "BOAC.ci": "BANK OF AFRICA CI",
    "ECOC.ci": "ECOBANK CI",
    "NTLC.ci": "NESTLE CI",
    "ORAC.ci": "ORANGE CI",
    "SNTS.ci": "SONATEL SENEGAL"
}

GUID = "Bs6Jz65CExmMWlmTp3L4YeEt9PmzGZISgr-bFJ1DIyA"

def fetch_and_analyze():
    all_results = {}
    for sym, name in SYMBOLS.items():
        try:
            # Connexion à Sika Finance
            url = f"https://www.sikafinance.com/api/charting/GetTicksEOD?symbol={sym}&length=365&period=0&guid={GUID}"
            response = requests.get(url, timeout=10)
            if response.status_code != 200: continue
            
            data = response.json()
            df = pd.DataFrame(data)
            df.columns = ['d', 'open', 'high', 'low', 'close', 'volume']
            
            # --- CALCUL RSI MANUEL ---
            delta = df['close'].diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            ema_up = up.ewm(com=13, adjust=False).mean()
            ema_down = down.ewm(com=13, adjust=False).mean()
            rs = ema_up / ema_down
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # --- CALCUL BOLLINGER MANUEL ---
            df['MA20'] = df['close'].rolling(window=20).mean()
            df['STD'] = df['close'].rolling(window=20).std()
            df['UB'] = df['MA20'] + (df['STD'] * 2)
            df['LB'] = df['MA20'] - (df['STD'] * 2)

            last = df.iloc[-1]
            
            # Formattage pour Lightweight Charts
            candles = []
            for i, r in df.iterrows():
                date_obj = datetime(1970, 1, 1) + timedelta(days=int(r['d']))
                candles.append({
                    "time": date_obj.strftime('%Y-%m-%d'),
                    "open": float(r['open']), "high": float(r['high']),
                    "low": float(r['low']), "close": float(r['close'])
                })

            all_results[sym] = {
                "name": name,
                "candles": candles,
                "rsi": round(float(last['RSI']), 2),
                "bb_up": round(float(last['UB']), 2),
                "bb_low": round(float(last['LB']), 2),
                "figure": "Analyse en cours...",
                "decision": "ACHAT" if last['RSI'] < 30 else "VENTE" if last['RSI'] > 70 else "NEUTRE",
                "color": "#26a69a" if last['RSI'] < 30 else "#ef5350" if last['RSI'] > 70 else "#6b7280"
            }
        except Exception as e:
            print(f"Erreur sur {sym}: {e}")
            
    with open('data.json', 'w') as f:
        json.dump(all_results, f)

if __name__ == "__main__":
    fetch_and_analyze()
