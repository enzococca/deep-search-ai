@echo off
REM Script di avvio per Deep Search AI (Windows)

echo 🚀 Avvio Deep Search AI...

REM Controlla se Python è installato
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python non trovato. Installa Python 3.8 o superiore da python.org
    pause
    exit /b 1
)

echo [SUCCESS] Python trovato

REM Controlla se siamo nella directory corretta
if not exist "run.py" (
    echo [ERROR] File run.py non trovato. Assicurati di essere nella directory del progetto.
    pause
    exit /b 1
)

REM Crea ambiente virtuale se non esiste
if not exist "venv" (
    echo [INFO] Creazione ambiente virtuale...
    python -m venv venv
    echo [SUCCESS] Ambiente virtuale creato
)

REM Attiva ambiente virtuale
echo [INFO] Attivazione ambiente virtuale...
call venv\Scripts\activate.bat

REM Aggiorna pip
echo [INFO] Aggiornamento pip...
python -m pip install --upgrade pip

REM Installa dipendenze
echo [INFO] Installazione dipendenze...
pip install -r requirements.txt

REM Controlla file di configurazione
if not exist "config.yaml" (
    echo [WARNING] File config.yaml non trovato. Verrà usata la configurazione di default.
)

REM Controlla variabili d'ambiente
if "%OPENAI_API_KEY%"=="" (
    echo [WARNING] OPENAI_API_KEY non impostata. Alcune funzionalità potrebbero non funzionare.
    echo Imposta la variabile con: set OPENAI_API_KEY=your-api-key
)

REM Crea directory necessarie
echo [INFO] Creazione directory necessarie...
if not exist "data" mkdir data
if not exist "data\uploads" mkdir data\uploads
if not exist "data\chroma" mkdir data\chroma
if not exist "logs" mkdir logs

REM Avvia l'applicazione
echo [INFO] Avvio del server...
echo.
echo 🌟 Deep Search AI
echo 📡 Server: http://localhost:5000
echo 🎨 Frontend: http://localhost:3000 (se avviato separatamente)
echo.
echo Premi Ctrl+C per fermare il server
echo.

REM Avvia il server Flask
python run.py

echo [SUCCESS] Server arrestato
pause
