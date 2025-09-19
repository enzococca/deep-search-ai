#!/bin/bash

# Script per avviare il frontend React

set -e

echo "🎨 Avvio Frontend Deep Search AI..."

# Colori per output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

# Controlla se Node.js è installato
if ! command -v node &> /dev/null; then
    print_error "Node.js non trovato. Installa Node.js 18 o superiore."
    exit 1
fi

# Controlla versione Node.js
NODE_VERSION=$(node -v | sed 's/v//')
REQUIRED_VERSION="18.0.0"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    print_error "Node.js $NODE_VERSION trovato, ma è richiesto Node.js $REQUIRED_VERSION o superiore."
    exit 1
fi

print_success "Node.js $NODE_VERSION trovato"

# Controlla se pnpm è installato
if ! command -v pnpm &> /dev/null; then
    print_warning "pnpm non trovato. Installazione in corso..."
    npm install -g pnpm
fi

# Vai nella directory frontend
if [ ! -d "frontend" ]; then
    print_error "Directory frontend non trovata. Assicurati di essere nella directory del progetto."
    exit 1
fi

cd frontend

print_status "Installazione dipendenze frontend..."
pnpm install

print_status "Avvio server di sviluppo..."
echo ""
echo "🎨 Frontend Deep Search AI"
echo "🌐 URL: http://localhost:3000"
echo "🔗 API Backend: http://localhost:5000"
echo ""
echo "Premi Ctrl+C per fermare il server"
echo ""

# Avvia il server di sviluppo
pnpm run dev --host

print_success "Server frontend arrestato"
