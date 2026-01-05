"""
MT5 Data Downloader
Stahuje historická data z MetaTrader 5 pro zadané instrumenty a timeframy.
"""

import MetaTrader5 as mt5
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import sys

# Konfigurace
INSTRUMENTS = ["XAUUSD", "EURUSD"]
TIMEFRAMES = {
    "M5": mt5.TIMEFRAME_M5,
    "M10": mt5.TIMEFRAME_M10,
    "M15": mt5.TIMEFRAME_M15
}
DAYS_BACK = 365  # Počet dní zpět pro stahování dat

def load_credentials():
    """Načte přihlašovací údaje ze souboru mt5_credentials.json"""
    try:
        with open("mt5_credentials.json", "r", encoding="utf-8") as f:
            creds = json.load(f)
        return creds
    except FileNotFoundError:
        print("CHYBA: Soubor mt5_credentials.json nebyl nalezen!")
        print("Vytvořte soubor mt5_credentials.json s přihlašovacími údaji.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("CHYBA: Soubor mt5_credentials.json obsahuje neplatný JSON!")
        sys.exit(1)

def initialize_mt5(credentials):
    """Inicializuje připojení k MT5"""
    # Zkontroluj, zda je cesta k MT5 nastavena
    if credentials.get("path") and os.path.exists(credentials["path"]):
        if not mt5.initialize(path=credentials["path"]):
            print(f"CHYBA: Nepodařilo se inicializovat MT5 z cesty: {credentials['path']}")
            print("Zkouším inicializovat bez cesty...")
            if not mt5.initialize():
                print("CHYBA: Nepodařilo se inicializovat MT5!")
                sys.exit(1)
    else:
        if not mt5.initialize():
            print("CHYBA: Nepodařilo se inicializovat MT5!")
            print("Ujistěte se, že je MetaTrader 5 nainstalován.")
            sys.exit(1)
    
    # Přihlášení
    if not mt5.login(
        login=int(credentials["login"]),
        password=credentials["password"],
        server=credentials["server"]
    ):
        print(f"CHYBA: Nepodařilo se přihlásit k MT5!")
        print(f"Kód chyby: {mt5.last_error()}")
        mt5.shutdown()
        sys.exit(1)
    
    print("✓ Úspěšně připojeno k MT5")
    account_info = mt5.account_info()
    if account_info:
        print(f"✓ Přihlášeno jako: {account_info.login} ({account_info.server})")
    return True

def get_symbol_info(symbol):
    """Získá informace o symbolu"""
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"CHYBA: Symbol {symbol} nebyl nalezen!")
        return None
    
    # Aktivuje symbol v Market Watch, pokud není aktivní
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print(f"CHYBA: Nepodařilo se aktivovat symbol {symbol}!")
            return None
    
    return symbol_info

def download_data(symbol, timeframe, timeframe_name, days_back=365):
    """Stáhne historická data pro daný symbol a timeframe"""
    print(f"\nStahuji data pro {symbol} ({timeframe_name})...")
    
    # Zkontroluj symbol
    symbol_info = get_symbol_info(symbol)
    if symbol_info is None:
        return None
    
    # Vypočítej datum začátku
    from_date = datetime.now() - timedelta(days=days_back)
    
    # Stáhni data
    rates = mt5.copy_rates_from(symbol, timeframe, from_date, days_back * 24 * 60 // 5)  # Odhad počtu svíček
    
    if rates is None or len(rates) == 0:
        print(f"  ⚠ Varování: Nepodařilo se stáhnout data pro {symbol} ({timeframe_name})")
        return None
    
    # Vytvoř DataFrame
    df = pd.DataFrame(rates)
    
    # Převod času na datetime
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Přidání dalších informací
    df['symbol'] = symbol
    df['timeframe'] = timeframe_name
    
    # Přidání technických informací
    df['spread'] = symbol_info.spread / 10  # Spread v bodech
    df['point'] = symbol_info.point
    df['digits'] = symbol_info.digits
    
    # Výpočet dalších metrik
    df['range'] = df['high'] - df['low']  # Rozsah svíčky
    df['body'] = abs(df['close'] - df['open'])  # Velikost těla
    df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)  # Horní knot
    df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']  # Dolní knot
    df['is_bullish'] = (df['close'] > df['open']).astype(int)  # Medvědí/býčí svíčka
    
    # Přesunutí sloupců pro lepší čitelnost
    columns_order = ['time', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 
                     'tick_volume', 'spread', 'range', 'body', 'upper_wick', 'lower_wick', 
                     'is_bullish', 'point', 'digits']
    df = df[columns_order]
    
    print(f"  ✓ Staženo {len(df)} svíček")
    print(f"  ✓ Datum od: {df['time'].min()}")
    print(f"  ✓ Datum do: {df['time'].max()}")
    
    return df

def save_data(df, symbol, timeframe_name):
    """Uloží data do CSV souboru"""
    if df is None or len(df) == 0:
        return
    
    # Vytvoř složku pro data, pokud neexistuje
    output_dir = "data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Název souboru
    filename = f"{output_dir}/{symbol}_{timeframe_name}_{datetime.now().strftime('%Y%m%d')}.csv"
    
    # Ulož do CSV
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"  ✓ Data uložena do: {filename}")
    
    return filename

def main():
    """Hlavní funkce"""
    print("=" * 60)
    print("MT5 Data Downloader")
    print("=" * 60)
    
    # Načti přihlašovací údaje
    print("\n1. Načítám přihlašovací údaje...")
    credentials = load_credentials()
    
    # Zkontroluj, zda jsou údaje vyplněné
    if credentials.get("login") == "YOUR_LOGIN_HERE" or \
       credentials.get("password") == "YOUR_PASSWORD_HERE" or \
       credentials.get("server") == "YOUR_SERVER_HERE":
        print("\n⚠ VAROVÁNÍ: Nezapomeňte vyplnit přihlašovací údaje v mt5_credentials.json!")
        print("Pokračuji s aktuálními údaji...")
    
    # Inicializuj MT5
    print("\n2. Připojuji se k MT5...")
    if not initialize_mt5(credentials):
        return
    
    # Stáhni data pro každý instrument a timeframe
    print("\n3. Stahuji data...")
    all_files = []
    
    for instrument in INSTRUMENTS:
        for timeframe_name, timeframe in TIMEFRAMES.items():
            try:
                df = download_data(instrument, timeframe, timeframe_name, DAYS_BACK)
                if df is not None:
                    filename = save_data(df, instrument, timeframe_name)
                    if filename:
                        all_files.append(filename)
            except Exception as e:
                print(f"  ✗ Chyba při stahování {instrument} ({timeframe_name}): {e}")
    
    # Ukonči připojení
    mt5.shutdown()
    
    # Shrnutí
    print("\n" + "=" * 60)
    print("Stahování dokončeno!")
    print("=" * 60)
    print(f"\nCelkem uloženo souborů: {len(all_files)}")
    for filename in all_files:
        print(f"  - {filename}")
    print("\n✓ Hotovo!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStahování přerušeno uživatelem.")
        mt5.shutdown()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Neočekávaná chyba: {e}")
        mt5.shutdown()
        sys.exit(1)

