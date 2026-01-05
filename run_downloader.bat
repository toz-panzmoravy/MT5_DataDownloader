@echo off
chcp 65001 >nul
echo ============================================================
echo MT5 Data Downloader
echo ============================================================
echo.

REM Zkontroluj, zda existuje Python
where py >nul 2>&1
if %errorlevel% neq 0 (
    echo CHYBA: Python nebyl nalezen!
    echo Ujistěte se, že je Python nainstalován a přidán do PATH.
    pause
    exit /b 1
)

REM Zkontroluj, zda existuje soubor s přihlašovacími údaji
if not exist "mt5_credentials.json" (
    echo CHYBA: Soubor mt5_credentials.json nebyl nalezen!
    echo Vytvořte soubor mt5_credentials.json s přihlašovacími údaji.
    pause
    exit /b 1
)

REM Zkontroluj, zda jsou nainstalované závislosti
echo Kontroluji závislosti...
py -m pip show MetaTrader5 >nul 2>&1
if %errorlevel% neq 0 (
    echo Instaluji závislosti...
    py -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo CHYBA: Nepodařilo se nainstalovat závislosti!
        pause
        exit /b 1
    )
)

echo.
echo Spouštím stahování dat...
echo.

REM Spusť Python script
py mt5_downloader.py

REM Zkontroluj návratový kód
if %errorlevel% neq 0 (
    echo.
    echo CHYBA: Stahování selhalo!
    pause
    exit /b %errorlevel%
)

echo.
echo ============================================================
echo Stahování dokončeno!
echo ============================================================
pause

