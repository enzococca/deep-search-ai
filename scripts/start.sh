#!/bin/bash

# Script di avvio per Deep Search AI (Linux/macOS)

set -e

echo "🚀 Avvio Deep Search AI..."

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funzione per stampare messaggi colorati
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Controlla se Python è installato
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 non trovato. Installa Python 3.8 o superiore."
    exit 1
fi

# Controlla versione Python
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Python $PYTHON_VERSION trovato, ma è richiesto Python $REQUIRED_VERSION o superiore."
    exit 1
fi

print_success "Python $PYTHON_VERSION trovato"

# Controlla se siamo nella directory corretta
if [ ! -f "run.py" ]; then
    print_error "File run.py non trovato. Assicurati di essere nella directory del progetto."
    exit 1
fi

# Crea ambiente virtuale se non esiste
if [ ! -d "venv" ]; then
    print_status "Creazione ambiente virtuale..."
    python3 -m venv venv
    print_success "Ambiente virtuale creato"
fi

# Attiva ambiente virtuale
print_status "Attivazione ambiente virtuale..."
source venv/bin/activate

# Aggiorna pip
print_status "Aggiornamento pip..."
pip install --upgrade pip

# Installa dipendenze
print_status "Installazione dipendenze..."
pip install -r requirements.txt

# Controlla se esiste file di configurazione
if [ ! -f "config.yaml" ]; then
    print_warning "File config.yaml non trovato. Verrà usata la configurazione di default."
fi

# Controlla variabili d'ambiente
if [ -z "$OPENAI_API_KEY" ]; then
    print_warning "OPENAI_API_KEY non impostata. Alcune funzionalità potrebbero non funzionare."
    echo "Imposta la variabile con: export OPENAI_API_KEY='your-api-key'"
fi

# Crea directory necessarie
print_status "Creazione directory necessarie..."
mkdir -p data/uploads data/chroma logs

# Avvia l'applicazione
print_status "Avvio del server..."
echo ""
echo "🌟 Deep Search AI"
echo "📡 Server: http://localhost:5000"
echo "🎨 Frontend: http://localhost:3000 (se avviato separatamente)"
echo ""
echo "Premi Ctrl+C per fermare il server"
echo ""

# Avvia il server Flask
python run.py

print_success "Server arrestato"
