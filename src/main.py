#!/usr/bin/env python3
"""
Entry point principale per Deep Search AI
Ottimizzato per deployment su servizi cloud
"""

import os
import sys
from pathlib import Path

# Aggiungi la directory root al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importa l'applicazione
from app import create_app

# Crea l'istanza dell'app
app = create_app()

if __name__ == '__main__':
    # Configurazione per deployment
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Avvio Deep Search AI")
    print(f"🌐 Host: {host}:{port}")
    print(f"🔧 Debug: {debug}")
    print(f"🌍 Environment: {os.environ.get('FLASK_ENV', 'production')}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )
