"""
MT5 Data Downloader
Stahuje historická data z MetaTrader 5 pro zadané instrumenty a timeframy.
"""

import MetaTrader5 as mt5
import pandas as pd
import json
import os
from datetime import datetime, timedelta, timezone
import sys
import io

# Nastavení kódování pro Windows konzoli
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
    
    print("[OK] Uspesne pripojeno k MT5")
    account_info = mt5.account_info()
    if account_info:
        print(f"[OK] Prihlaseno jako: {account_info.login} ({account_info.server})")
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
    
    # Vypočítej datum začátku a konce
    # Použij UTC čas, protože MT5 pracuje s UTC
    to_date = datetime.now(timezone.utc)
    from_date = to_date - timedelta(days=days_back)
    
    # Vypočítej přibližný počet svíček podle timeframu
    if timeframe == mt5.TIMEFRAME_M5:
        # Pro M5 zkus použít copy_rates_range s plným rozsahem
        rates = mt5.copy_rates_range(symbol, timeframe, from_date, to_date)
        
        if rates is None or len(rates) == 0:
            # Pokud copy_rates_range nefunguje, zkus copy_rates_from s aktuálním časem
            max_count = 100000
            rates = mt5.copy_rates_from(symbol, timeframe, to_date, max_count)
        
        if rates is None or len(rates) == 0:
            # Zkus s from_date a menším počtem
            count = min(days_back * 24 * 12, 100000)
            rates = mt5.copy_rates_from(symbol, timeframe, from_date, count)
    elif timeframe == mt5.TIMEFRAME_M10:
        count = days_back * 24 * 6  # 6 svíček za hodinu
        # Pro ostatní timeframy zkus nejprve copy_rates_range
        rates = mt5.copy_rates_range(symbol, timeframe, from_date, to_date)
        # Pokud to nefunguje, použij copy_rates_from
        if rates is None or len(rates) == 0:
            rates = mt5.copy_rates_from(symbol, timeframe, from_date, count)
    elif timeframe == mt5.TIMEFRAME_M15:
        count = days_back * 24 * 4  # 4 svíčky za hodinu
        # Pro ostatní timeframy zkus nejprve copy_rates_range
        rates = mt5.copy_rates_range(symbol, timeframe, from_date, to_date)
        # Pokud to nefunguje, použij copy_rates_from
        if rates is None or len(rates) == 0:
            rates = mt5.copy_rates_from(symbol, timeframe, from_date, count)
    else:
        count = days_back * 24 * 12
        rates = mt5.copy_rates_range(symbol, timeframe, from_date, to_date)
        if rates is None or len(rates) == 0:
            rates = mt5.copy_rates_from(symbol, timeframe, from_date, count)
    
    if rates is None or len(rates) == 0:
        print(f"  [VAROVANI] Nepodarilo se stahnout data pro {symbol} ({timeframe_name})")
        print(f"  Chyba MT5: {mt5.last_error()}")
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
    
    print(f"  [OK] Stazeno {len(df)} svicek")
    print(f"  [OK] Datum od: {df['time'].min()}")
    print(f"  [OK] Datum do: {df['time'].max()}")
    
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
    print(f"  [OK] Data ulozena do: {filename}")
    
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
        print("\n[VAROVANI] Nezapomente vyplnit prihlasovaci udaje v mt5_credentials.json!")
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
                print(f"  [CHYBA] Chyba pri stahovani {instrument} ({timeframe_name}): {e}")
    
    # Ukonči připojení
    mt5.shutdown()
    
    # Shrnutí
    print("\n" + "=" * 60)
    print("Stahování dokončeno!")
    print("=" * 60)
    print(f"\nCelkem uloženo souborů: {len(all_files)}")
    for filename in all_files:
        print(f"  - {filename}")
    print("\n[OK] Hotovo!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStahování přerušeno uživatelem.")
        mt5.shutdown()
        sys.exit(0)
    except Exception as e:
        print(f"\n[CHYBA] Neocekavana chyba: {e}")
        mt5.shutdown()
        sys.exit(1)

