#!/usr/bin/env python3
"""
Script per creare un package distribuibile di Deep Search AI
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

def create_package():
    """Crea un package completo per distribuzione locale"""
    
    print("🚀 Creazione package Deep Search AI...")
    
    # Directory di lavoro
    project_root = Path(__file__).parent.parent
    package_dir = project_root / "dist" / "deep-search-ai-package"
    
    # Pulisce directory esistente
    if package_dir.exists():
        shutil.rmtree(package_dir)
    
    package_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Directory package: {package_dir}")
    
    # File e directory da includere
    include_items = [
        "app/",
        "frontend/",
        "scripts/",
        "tests/",
        "config.yaml",
        "requirements.txt",
        "run.py",
        "setup.py",
        "README.md",
        "DEPLOYMENT.md",
        "LICENSE",
        ".gitignore"
    ]
    
    # Copia file nel package
    print("📋 Copia file nel package...")
    for item in include_items:
        src = project_root / item
        dst = package_dir / item
        
        if src.exists():
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '*.pyo', '.git', 'node_modules',
                    '.pytest_cache', '.coverage', '*.log'
                ))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            print(f"  ✓ {item}")
        else:
            print(f"  ⚠️ {item} non trovato")
    
    # Crea script di installazione semplificato
    create_install_script(package_dir)
    
    # Crea file di configurazione esempio
    create_example_config(package_dir)
    
    # Crea documentazione di avvio rapido
    create_quick_start(package_dir)
    
    # Crea archivio ZIP
    create_zip_archive(package_dir)
    
    print("✅ Package creato con successo!")
    print(f"📦 Percorso: {package_dir}")
    print(f"📦 Archivio: {package_dir.parent / 'deep-search-ai-package.zip'}")

def create_install_script(package_dir):
    """Crea script di installazione semplificato"""
    
    # Script Linux/macOS
    install_sh = package_dir / "install.sh"
    with open(install_sh, 'w') as f:
        f.write("""#!/bin/bash

# Script di installazione Deep Search AI

set -e

echo "🚀 Installazione Deep Search AI..."

# Controlla Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trovato. Installa Python 3.8+ da python.org"
    exit 1
fi

echo "✅ Python trovato"

# Crea ambiente virtuale
if [ ! -d "venv" ]; then
    echo "📦 Creazione ambiente virtuale..."
    python3 -m venv venv
fi

# Attiva ambiente virtuale
echo "🔧 Attivazione ambiente virtuale..."
source venv/bin/activate

# Installa dipendenze
echo "📥 Installazione dipendenze..."
pip install --upgrade pip
pip install -r requirements.txt

# Crea directory necessarie
mkdir -p data/uploads data/chroma logs

echo ""
echo "✅ Installazione completata!"
echo ""
echo "🚀 Per avviare l'applicazione:"
echo "   ./start.sh"
echo ""
echo "🔑 Non dimenticare di impostare OPENAI_API_KEY:"
echo "   export OPENAI_API_KEY='your-api-key'"
echo ""
""")
    
    os.chmod(install_sh, 0o755)
    
    # Script Windows
    install_bat = package_dir / "install.bat"
    with open(install_bat, 'w') as f:
        f.write("""@echo off

REM Script di installazione Deep Search AI

echo 🚀 Installazione Deep Search AI...

REM Controlla Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trovato. Installa Python 3.8+ da python.org
    pause
    exit /b 1
)

echo ✅ Python trovato

REM Crea ambiente virtuale
if not exist "venv" (
    echo 📦 Creazione ambiente virtuale...
    python -m venv venv
)

REM Attiva ambiente virtuale
echo 🔧 Attivazione ambiente virtuale...
call venv\\Scripts\\activate.bat

REM Installa dipendenze
echo 📥 Installazione dipendenze...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM Crea directory necessarie
if not exist "data" mkdir data
if not exist "data\\uploads" mkdir data\\uploads
if not exist "data\\chroma" mkdir data\\chroma
if not exist "logs" mkdir logs

echo.
echo ✅ Installazione completata!
echo.
echo 🚀 Per avviare l'applicazione:
echo    start.bat
echo.
echo 🔑 Non dimenticare di impostare OPENAI_API_KEY:
echo    set OPENAI_API_KEY=your-api-key
echo.
pause
""")

def create_example_config(package_dir):
    """Crea file di configurazione esempio"""
    
    config_example = package_dir / "config.example.yaml"
    with open(config_example, 'w') as f:
        f.write("""# Configurazione esempio per Deep Search AI
# Copia questo file in config.yaml e modifica i valori

flask:
  secret_key: "change-this-secret-key-in-production"
  debug: false
  max_content_length: 52428800  # 50MB

llm:
  provider: "openai"
  model: "gpt-4o"  # o "gpt-5" quando disponibile
  api_key: "${OPENAI_API_KEY}"
  max_tokens: 2000
  temperature: 0.7

embedding:
  provider: "openai"
  model: "text-embedding-3-large"
  api_key: "${OPENAI_API_KEY}"
  batch_size: 100

vector_db:
  provider: "chroma"
  persist_directory: "./data/chroma"

file_service:
  upload_folder: "./data/uploads"
  max_file_size: 50  # MB
  allowed_extensions: ["pdf", "docx", "txt", "jpg", "jpeg", "png", "gif", "xlsx", "pptx"]

agents:
  text:
    enabled: true
    max_results: 10
  image:
    enabled: true
    max_results: 10
    ocr_enabled: true
  document:
    enabled: true
    max_results: 10
  web:
    enabled: true
    max_results: 10
    max_pages: 5
  synthesis:
    enabled: true

database:
  url: "sqlite:///./data/app.db"

logging:
  level: "INFO"
  file: "./logs/deep_search_ai.log"
""")

def create_quick_start(package_dir):
    """Crea guida di avvio rapido"""
    
    quick_start = package_dir / "QUICK_START.md"
    with open(quick_start, 'w') as f:
        f.write("""# 🚀 Avvio Rapido - Deep Search AI

## 📋 Prerequisiti

- **Python 3.8+** installato sul sistema
- **OpenAI API Key** (ottieni da https://platform.openai.com/)
- **4GB RAM** minimo, 8GB raccomandato

## ⚡ Installazione in 3 Passi

### 1. Installa Dipendenze
```bash
# Linux/macOS
./install.sh

# Windows
install.bat
```

### 2. Configura API Key
```bash
# Linux/macOS
export OPENAI_API_KEY="your-openai-api-key-here"

# Windows
set OPENAI_API_KEY=your-openai-api-key-here
```

### 3. Avvia l'Applicazione
```bash
# Linux/macOS
./scripts/start.sh

# Windows
scripts\\start.bat
```

## 🌐 Accesso all'Applicazione

- **Backend API**: http://localhost:5000
- **Frontend Web**: http://localhost:3000 (se avviato separatamente)

## 🔧 Configurazione Avanzata

1. Copia `config.example.yaml` in `config.yaml`
2. Modifica i parametri secondo le tue esigenze
3. Riavvia l'applicazione

## 📚 Funzionalità Principali

### 🔍 Ricerca Intelligente
- Ricerca semantica avanzata
- Supporto multi-modale (testo, immagini, documenti)
- Agenti AI specializzati

### 📄 Elaborazione Documenti
- PDF, DOCX, Excel, PowerPoint
- Estrazione testo automatica
- Analisi contenuto con AI

### 🖼️ Analisi Immagini
- OCR (riconoscimento testo)
- Descrizione automatica
- Ricerca per similarità

### 🌐 Ricerca Web
- Crawling intelligente
- Analisi contenuti online
- Sintesi automatica

## 🆘 Risoluzione Problemi

### Errore "Module not found"
```bash
pip install -r requirements.txt
```

### Errore OpenAI API
- Verifica che la API key sia corretta
- Controlla il credito disponibile su OpenAI

### Errore di avvio
- Controlla i log in `logs/deep_search_ai.log`
- Verifica che la porta 5000 sia libera

## 📞 Supporto

- **Documentazione**: README.md
- **Deployment**: DEPLOYMENT.md
- **Issues**: https://github.com/enzococca/deep-search-ai/issues

## 🎯 Prossimi Passi

1. Carica alcuni documenti nella knowledge base
2. Prova diverse tipologie di ricerca
3. Esplora le API REST
4. Personalizza la configurazione

Buon utilizzo! 🚀
""")

def create_zip_archive(package_dir):
    """Crea archivio ZIP del package"""
    
    zip_path = package_dir.parent / "deep-search-ai-package.zip"
    
    print("📦 Creazione archivio ZIP...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            # Esclude directory non necessarie
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules']]
            
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(package_dir.parent)
                zipf.write(file_path, arc_path)
    
    print(f"✅ Archivio creato: {zip_path}")
    print(f"📊 Dimensione: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    try:
        create_package()
    except KeyboardInterrupt:
        print("\n❌ Operazione annullata dall'utente")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Errore durante la creazione del package: {e}")
        sys.exit(1)
