#!/usr/bin/env python3
"""
Deep Search AI - Applicazione principale
"""

import os
import sys
import logging
from app import create_app

def main():
    """Funzione principale per avviare l'applicazione"""
    
    # Configurazione logging di base
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Creazione dell'applicazione Flask
        app = create_app()
        
        # Recupero configurazione
        config = app.config.get('APP_CONFIG', {})
        app_config = config.get('app', {})
        
        # Parametri di avvio
        host = app_config.get('host', '0.0.0.0')
        port = app_config.get('port', 5000)
        debug = app_config.get('debug', False)
        
        logger.info(f"Avvio Deep Search AI su {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        
        # Verifica delle variabili d'ambiente necessarie
        check_environment()
        
        # Avvio dell'applicazione
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except Exception as e:
        logger.error(f"Errore nell'avvio dell'applicazione: {e}")
        sys.exit(1)

def check_environment():
    """Verifica che le variabili d'ambiente necessarie siano configurate"""
    
    logger = logging.getLogger(__name__)
    
    # Variabili d'ambiente opzionali ma consigliate
    env_vars = {
        'OPENAI_API_KEY': 'Chiave API OpenAI per GPT-5 e embeddings',
        'SECRET_KEY': 'Chiave segreta per Flask (usa quella di default in sviluppo)',
        'DATABASE_URL': 'URL del database (usa SQLite di default)',
    }
    
    missing_vars = []
    
    for var, description in env_vars.items():
        if not os.getenv(var):
            if var == 'OPENAI_API_KEY':
                missing_vars.append(f"  {var}: {description}")
            else:
                logger.info(f"Variabile d'ambiente {var} non configurata: {description}")
    
    if missing_vars:
        logger.warning("Variabili d'ambiente mancanti (necessarie per il funzionamento completo):")
        for var in missing_vars:
            logger.warning(var)
        logger.warning("L'applicazione potrebbe non funzionare correttamente senza queste variabili.")
    
    # Verifica directory necessarie
    directories = [
        './data',
        './data/uploads',
        './logs'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"Directory creata: {directory}")

if __name__ == '__main__':
    main()
