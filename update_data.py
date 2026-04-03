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

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_analysis():
    all_data = {}
    for sym, name in SYMBOLS.items():
        try:
            url = f"https://www.sikafinance.com/api/charting/GetTicksEOD?symbol={sym}&length=365&period=0&guid={GUID}"
            r = requests.get(url)
            df = pd.DataFrame(r.json())
            df.columns = ['d', 'open', 'high', 'low', 'close', 'volume']
            
            # Calcul RSI maison
            df['RSI'] = calculate_rsi(df['close'])
            
            # Calcul Bollinger maison
            sma = df['close'].rolling(window=20).mean()
            std = df['close'].rolling(window=20).std()
            df['UB'] = sma + (std * 2)
            df['LB'] = sma - (std * 2)

            last = df.iloc[-1]
            rsi_val = last['RSI']
            
            # Signal simple
            signal = "Neutre"
            color = "#bdc3c7"
            if rsi_val < 30:
                signal = "ACHAT (Survente)"
                color = "#26a69a"
            elif rsi_val > 70:
                signal = "VENTE (Surachat)"
                color = "#ef5350"

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
                "rsi": round(float(rsi_val), 2) if pd.notnull(rsi_val) else "N/A",
                "signal": signal,
                "color": color
            }
            print(f"✓ {sym} OK")
        except Exception as e:
            print(f"Erreur {sym}: {e}")

    with open('data.json', 'w') as f:
        json.dump(all_data, f)

if __name__ == "__main__":
    get_analysis()
