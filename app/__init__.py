"""
Deep Search AI - Applicazione Flask principale
"""

import os
import logging
import yaml
from datetime import datetime
from flask import Flask
from flask_cors import CORS

from app.api import api_bp, SearchController
from app.models.database import init_db

def create_app(config_path=None):
    """
    Factory per creare l'applicazione Flask
    
    Args:
        config_path: Percorso del file di configurazione
        
    Returns:
        Istanza dell'applicazione Flask configurata
    """
    
    app = Flask(__name__)
    
    # Caricamento configurazione
    config = load_config(config_path)
    configure_app(app, config)
    
    # Configurazione CORS per deployment web
    CORS(app, 
         origins=['*'],  # Permette tutti i domini per deployment
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         supports_credentials=True)
    
    # Configurazione logging
    setup_logging(config.get('logging', {}))
    
    # Inizializzazione database
    init_db(config.get('database', {}))
    
    # Inizializzazione SearchController
    try:
        app.search_controller = SearchController(config)
        logging.info("SearchController inizializzato con successo")
    except Exception as e:
        logging.error(f"Errore nell'inizializzazione SearchController: {e}")
        # Continua senza SearchController per permettere testing base
        app.search_controller = None
    
    # Registrazione blueprint API
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    
    # Registrazione blueprint per servire frontend statico
    try:
        from app.static_routes import static_bp
        app.register_blueprint(static_bp)
        logging.info("Static routes registrate per servire frontend")
    except Exception as e:
        logging.error(f"Errore registrazione static routes: {e}")
    
    # Route API di base (solo per /api endpoint)
    @app.route('/api')
    def api_info():
        return {
            'message': 'Deep Search AI API',
            'version': '1.0.0',
            'status': 'running',
            'timestamp': datetime.now().isoformat(),
            'endpoints': {
                'search': '/api/v1/search',
                'upload': '/api/v1/upload',
                'health': '/api/v1/health',
                'capabilities': '/api/v1/capabilities',
                'docs': '/api/v1'
            }
        }
    
    @app.route('/health')
    def health():
        """Health check semplificato"""
        return {
            'status': 'healthy', 
            'service': 'Deep Search AI',
            'timestamp': datetime.now().isoformat(),
            'search_controller': app.search_controller is not None
        }
    
    # Error handlers globali
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Endpoint non trovato', 'status': 404}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logging.error(f"Errore interno: {error}")
        return {'error': 'Errore interno del server', 'status': 500}, 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        return {'error': 'File troppo grande', 'status': 413}, 413
    
    logging.info("Deep Search AI application initialized successfully")
    
    return app

def configure_app(app, config):
    """Configura l'applicazione Flask per deployment cloud"""
    
    flask_config = config.get('flask', {})
    
    # Configurazioni Flask base con supporto variabili d'ambiente
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', flask_config.get('secret_key', 'dev-secret-key-change-in-production'))
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', str(flask_config.get('debug', False))).lower() == 'true'
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', flask_config.get('max_content_length', 50 * 1024 * 1024)))
    
    # Configurazioni per deployment cloud
    app.config['PORT'] = int(os.getenv('PORT', 5000))
    app.config['HOST'] = os.getenv('HOST', '0.0.0.0')
    app.config['FLASK_ENV'] = os.getenv('FLASK_ENV', 'production')
    
    # Database URL per deployment cloud
    app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', config.get('database', {}).get('url', 'sqlite:///./data/app.db'))
    
    # Configurazioni per upload
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', config.get('file_service', {}).get('upload_folder', './data/uploads'))
    
    # API Keys
    app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', config.get('llm', {}).get('api_key'))
    
    # Crea directory necessarie
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('./data/chroma', exist_ok=True)
    os.makedirs('./logs', exist_ok=True)
    
    # Salva configurazione completa per accesso globale
    app.config['APP_CONFIG'] = config

def load_config(config_path=None):
    """
    Carica la configurazione dall'file YAML
    
    Args:
        config_path: Percorso del file di configurazione
        
    Returns:
        Dizionario con la configurazione
    """
    
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Sostituisce variabili d'ambiente
        config = substitute_env_vars(config)
        
        logging.info(f"Configurazione caricata da: {config_path}")
        return config
        
    except FileNotFoundError:
        logging.warning(f"File di configurazione non trovato: {config_path}. Uso configurazione di default.")
        return get_default_config()
    except Exception as e:
        logging.error(f"Errore nel caricamento configurazione: {e}. Uso configurazione di default.")
        return get_default_config()

def substitute_env_vars(config):
    """Sostituisce variabili d'ambiente nella configurazione"""
    
    def replace_env_vars(obj):
        if isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            default_value = None
            
            if ':' in env_var:
                env_var, default_value = env_var.split(':', 1)
            
            return os.getenv(env_var, default_value)
        else:
            return obj
    
    return replace_env_vars(config)

def get_default_config():
    """Restituisce configurazione di default"""
    
    return {
        'flask': {
            'secret_key': os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
            'debug': os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            'max_content_length': 50 * 1024 * 1024  # 50MB
        },
        'llm': {
            'provider': 'openai',
            'model': os.getenv('LLM_MODEL', 'gpt-4'),  # Fallback a GPT-4 se GPT-5 non disponibile
            'api_key': os.getenv('OPENAI_API_KEY'),
            'max_tokens': 2000,
            'temperature': 0.7,
            'timeout': 60
        },
        'embedding': {
            'provider': 'openai',
            'model': 'text-embedding-3-large',
            'api_key': os.getenv('OPENAI_API_KEY'),
            'batch_size': 100,
            'timeout': 30
        },
        'vector_db': {
            'provider': 'chroma',
            'host': os.getenv('CHROMA_HOST', 'localhost'),
            'port': int(os.getenv('CHROMA_PORT', '8000')),
            'persist_directory': os.getenv('CHROMA_PERSIST_DIR', './data/chroma')
        },
        'file_service': {
            'upload_folder': os.getenv('UPLOAD_FOLDER', './data/uploads'),
            'max_file_size': int(os.getenv('MAX_FILE_SIZE', '50')),  # MB
            'allowed_extensions': ['pdf', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'xlsx', 'pptx']
        },
        'agents': {
            'text': {
                'enabled': True, 
                'max_results': 10,
                'similarity_threshold': 0.7
            },
            'image': {
                'enabled': True, 
                'max_results': 10, 
                'ocr_enabled': True,
                'similarity_threshold': 0.7
            },
            'document': {
                'enabled': True, 
                'max_results': 10,
                'chunk_size': 1000,
                'chunk_overlap': 200,
                'similarity_threshold': 0.7
            },
            'web': {
                'enabled': True, 
                'max_results': 10, 
                'max_pages': 5,
                'timeout': 30,
                'similarity_threshold': 0.7
            },
            'synthesis': {
                'enabled': True, 
                'synthesis_depth': 'comprehensive',
                'max_sources': 20,
                'min_confidence': 0.3
            }
        },
        'database': {
            'url': os.getenv('DATABASE_URL', 'sqlite:///./data/app.db'),
            'echo': False
        },
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': os.getenv('LOG_FILE', './logs/deep_search_ai.log')
        },
        'security': {
            'allowed_origins': ['http://localhost:3000', 'http://localhost:5173', 'http://127.0.0.1:3000', 'http://127.0.0.1:5173']
        },
        'performance': {
            'max_parallel_agents': int(os.getenv('MAX_PARALLEL_AGENTS', '3')),
            'agent_timeout': int(os.getenv('AGENT_TIMEOUT', '60')),
            'enable_synthesis': os.getenv('ENABLE_SYNTHESIS', 'True').lower() == 'true'
        }
    }

def setup_logging(logging_config):
    """Configura il sistema di logging"""
    
    level = getattr(logging, logging_config.get('level', 'INFO').upper())
    format_str = logging_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    log_file = logging_config.get('file', './logs/deep_search_ai.log')
    
    # Crea directory per log se non esiste
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configurazione handlers
    handlers = [logging.StreamHandler()]
    
    try:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    except Exception as e:
        print(f"Impossibile creare file di log {log_file}: {e}")
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=handlers,
        force=True  # Sovrascrive configurazione esistente
    )
    
    # Riduce verbosità di librerie esterne
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    logging.info("Sistema di logging configurato")
