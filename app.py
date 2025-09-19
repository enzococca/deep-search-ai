#!/usr/bin/env python3
"""
Entry point per deployment cloud di Deep Search AI
Ottimizzato per servizi come Render, Railway, Heroku
"""

import os
import sys
from pathlib import Path

# Aggiungi la directory del progetto al path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app

# Crea l'applicazione Flask
app = create_app()

if __name__ == '__main__':
    # Configurazione per deployment cloud
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Avvio Deep Search AI su {host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'production')}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
