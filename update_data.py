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

def get_analysis():
    all_data = {}
    for sym, name in SYMBOLS.items():
        try:
            url = f"https://www.sikafinance.com/api/charting/GetTicksEOD?symbol={sym}&length=365&period=0&guid={GUID}"
            r = requests.get(url)
            df = pd.DataFrame(r.json())
            df.columns = ['d', 'open', 'high', 'low', 'close', 'volume']
            
            # --- INDICATEURS ---
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            df['RSI'] = 100 - (100 / (1 + (gain / loss)))
            
            # Bollinger
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            df['UB'] = sma + (std * 2)
            df['LB'] = sma - (std * 2)

            # --- DETECTION DE FIGURES (BOUGIES) ---
            last = df.iloc[-1]
            prev = df.iloc[-2]
            body = abs(last['close'] - last['open'])
            prev_body = abs(prev['close'] - prev['open'])
            range_t = last['high'] - last['low']
            
            fig = "Standard"
            if range_t > 0 and body / range_t < 0.1: fig = "Doji"
            elif (last['high'] - max(last['open'], last['close'])) < body * 0.1 and (min(last['open'], last['close']) - last['low']) > body * 2: fig = "Marteau"
            elif last['close'] > prev['open'] and last['open'] < prev['close'] and body > prev_body: fig = "Englobante Haussière"

            # --- SIGNAL & DECISION ---
            rsi_v = last['RSI']
            decision = "ATTENTE"
            color = "#bdc3c7"
            
            if rsi_v < 35:
                decision = "ACHAT FORT (Survente + RSI bas)"
                color = "#26a69a"
            elif rsi_v > 65:
                decision = "VENTE FORTE (Surachat + RSI haut)"
                color = "#ef5350"
            elif last['close'] < last['LB']:
                decision = "ACHAT (Sortie Bollinger Basse)"
                color = "#2ecc71"

            chart_data = []
            for i, row in df.iterrows():
                chart_data.append({
                    "time": (datetime(1970, 1, 1) + timedelta(days=row['d'])).strftime('%Y-%m-%d'),
                    "open": float(row['open']), "high": float(row['high']),
                    "low": float(row['low']), "close": float(row['close'])
                })

            all_data[sym] = {
                "name": name,
                "candles": chart_data,
                "rsi": round(float(rsi_v), 2) if pd.notnull(rsi_v) else "N/A",
                "bb_up": round(float(last['UB']), 2),
                "bb_low": round(float(last['LB']), 2),
                "figure": fig,
                "decision": decision,
                "color": color
            }
        except: continue

    with open('data.json', 'w') as f:
        json.dump(all_data, f)

if __name__ == "__main__":
    get_analysis()
