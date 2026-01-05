# MT5 Data Downloader

Script pro stahování historických dat z MetaTrader 5 pro instrumenty XAUUSD a EURUSD s timeframy M5, M10, M15.

## Požadavky

- Python 3.7 nebo novější
- MetaTrader 5 nainstalovaný na počítači
- Účet u brokera s přístupem k MT5

## Instalace

1. Nainstalujte závislosti:
```bash
py -m pip install -r requirements.txt
```

## Konfigurace

1. Otevřete soubor `mt5_credentials.json`
2. Vyplňte své přihlašovací údaje:
   - `login`: Vaše přihlašovací číslo
   - `password`: Vaše heslo
   - `server`: Název serveru vašeho brokera (např. "MetaQuotes-Demo", "YourBroker-Demo")
   - `path`: Cesta k MetaTrader 5 (výchozí: "C:\\Program Files\\MetaTrader 5\\terminal64.exe")

## Použití

### Spuštění pomocí batch souboru (doporučeno)

Jednoduše dvojklikněte na `run_downloader.bat` nebo spusťte z příkazové řádky:
```bash
run_downloader.bat
```

### Spuštění přímo pomocí Pythonu

```bash
py mt5_downloader.py
```

## Výstup

Data se ukládají do složky `data/` ve formátu CSV s následujícím názvem:
```
data/{SYMBOL}_{TIMEFRAME}_{DATUM}.csv
```

Například:
- `data/XAUUSD_M5_20241215.csv`
- `data/EURUSD_M15_20241215.csv`

## Obsah stažených dat

Každý CSV soubor obsahuje následující sloupce:

- **time**: Čas svíčky
- **symbol**: Název instrumentu
- **timeframe**: Timeframe (M5, M10, M15)
- **open**: Otevírací cena
- **high**: Nejvyšší cena
- **low**: Nejnižší cena
- **close**: Zavírací cena
- **tick_volume**: Tick volume
- **spread**: Spread v bodech
- **range**: Rozsah svíčky (high - low)
- **body**: Velikost těla svíčky
- **upper_wick**: Velikost horního knotu
- **lower_wick**: Velikost dolního knotu
- **is_bullish**: 1 pro býčí svíčku, 0 pro medvědí
- **point**: Hodnota jednoho pointu
- **digits**: Počet desetinných míst

## Poznámky

- Script stahuje data za posledních 365 dní
- Ujistěte se, že je MetaTrader 5 spuštěný nebo alespoň nainstalovaný
- Pokud máte problémy s připojením, zkontrolujte přihlašovací údaje a cestu k MT5

