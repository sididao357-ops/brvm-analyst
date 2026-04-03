import requests
import pandas as pd
import pandas_ta as ta
import json
from datetime import datetime, timedelta

# Ta liste de sociétés (On peut en ajouter plus tard)
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

def convert_sika_date(n):
    return (datetime(1970, 1, 1) + timedelta(days=n)).strftime('%Y-%m-%d')

def get_analysis():
    all_data = {}

    for sym, name in SYMBOLS.items():
        try:
            url = f"https://www.sikafinance.com/api/charting/GetTicksEOD?symbol={sym}&length=365&period=0&guid={GUID}"
            r = requests.get(url)
            raw = r.json()
            
            df = pd.DataFrame(raw)
            df.columns = ['d', 'open', 'high', 'low', 'close', 'volume']
            
            # --- CALCULS TECHNIQUES ---
            df['RSI'] = ta.rsi(df['close'], length=14)
            # Bandes de Bollinger
            bbands = ta.bbands(df['close'], length=20, std=2)
            df = pd.concat([df, bbands], axis=1)
            
            # Détection de bougies (Doji et Marteau)
            # On calcule manuellement pour éviter les bugs de librairie
            last = df.iloc[-1]
            body = abs(last['close'] - last['open'])
            range_total = last['high'] - last['low']
            
            candle_name = "Standard"
            if range_total > 0 and body / range_total < 0.1:
                candle_name = "Doji"
            elif (last['high'] - max(last['open'], last['close'])) < body * 0.1 and (min(last['open'], last['close']) - last['low']) > body * 2:
                candle_name = "Marteau"

            # --- LOGIQUE DE SIGNAL ---
            signal = "Neutre"
            color = "#bdc3c7" # Gris
            
            rsi_val = last['RSI']
            if pd.notnull(rsi_val):
                if rsi_val < 30:
                    signal = "ACHAT (Survente)"
                    color = "#26a69a" # Vert
                elif rsi_val > 70:
                    signal = "VENTE (Surachat)"
                    color = "#ef5350" # Rouge

            # Formatage pour le graphique
            chart_data = []
            for i, row in df.iterrows():
                chart_data.append({
                    "time": convert_sika_date(row['d']),
                    "open": float(row['open']), "high": float(row['high']),
                    "low": float(row['low']), "close": float(row['close'])
                })

            all_data[sym] = {
                "name": name,
                "candles": chart_data,
                "rsi": round(float(rsi_val), 2) if pd.notnull(rsi_val) else "N/A",
                "signal": f"{signal} | Bougie: {candle_name}",
                "color": color
            }
            print(f"✓ {sym} analysé")
        except Exception as e:
            print(f"Erreur sur {sym}: {e}")

    # Sauvegarde finale
    with open('data.json', 'w') as f:
        json.dump(all_data, f)

if __name__ == "__main__":
    get_analysis()
