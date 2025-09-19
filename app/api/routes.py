"""
API Routes per Deep Search AI
"""

import logging
import asyncio
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from functools import wraps
import time

from .search_controller import SearchController

logger = logging.getLogger(__name__)

# Crea blueprint per le API
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def async_route(f):
    """Decorator per gestire route asincrone in Flask"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

def validate_json_request(required_fields=None):
    """Decorator per validare richieste JSON"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Content-Type deve essere application/json'
                }), 400
            
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Body JSON richiesto'
                }), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'error': f'Campi richiesti mancanti: {", ".join(missing_fields)}'
                    }), 400
            
            return f(data, *args, **kwargs)
        return wrapper
    return decorator

def get_search_controller():
    """Ottiene l'istanza del SearchController dall'app context"""
    return current_app.search_controller

@api_bp.route('/search', methods=['POST'])
@validate_json_request(['query'])
@async_route
async def search(data):
    """
    Endpoint principale per la ricerca
    
    Body JSON:
    {
        "query": "string",
        "options": {
            "agents": ["text", "web", "document", "image"],
            "exclude_agents": ["agent_name"],
            "max_results": 10,
            "scope": "all"
        }
    }
    """
    
    try:
        query = data['query'].strip()
        search_options = data.get('options', {})
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query non può essere vuota'
            }), 400
        
        # Validazione opzioni
        valid_agents = ['text', 'image', 'document', 'web']
        if 'agents' in search_options:
            invalid_agents = [a for a in search_options['agents'] if a not in valid_agents]
            if invalid_agents:
                return jsonify({
                    'success': False,
                    'error': f'Agenti non validi: {", ".join(invalid_agents)}'
                }), 400
        
        # Esegue ricerca
        controller = get_search_controller()
        result = await controller.search(query, search_options)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Errore nell'endpoint search: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore interno del server'
        }), 500

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    """
    Endpoint per caricare file nella knowledge base
    
    Form data:
    - file: File da caricare
    - user_id: ID utente (opzionale)
    """
    
    try:
        # Verifica presenza file
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nessun file fornito'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nessun file selezionato'
            }), 400
        
        # Ottiene parametri opzionali
        user_id = request.form.get('user_id')
        
        # Legge dati file
        filename = secure_filename(file.filename)
        file_data = file.read()
        
        # Elabora file
        controller = get_search_controller()
        result = controller.upload_file(file_data, filename, user_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Errore nell'upload file: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore nell\'elaborazione del file'
        }), 500

@api_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """
    Endpoint per analizzare un'immagine specifica
    
    Form data:
    - image: File immagine
    - query: Query di analisi (opzionale)
    """
    
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nessuna immagine fornita'
            }), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nessuna immagine selezionata'
            }), 400
        
        # Salva temporaneamente l'immagine
        controller = get_search_controller()
        filename = secure_filename(image_file.filename)
        file_data = image_file.read()
        
        # Salva file temporaneo
        file_info = controller.file_service.save_uploaded_file(file_data, filename)
        
        if not file_info.get('success'):
            return jsonify(file_info), 400
        
        # Analizza immagine
        query = request.form.get('query', 'Analizza questa immagine')
        context = {'image_path': file_info['file_path']}
        
        image_agent = controller.agents['image']
        result = image_agent.process_query(query, context)
        
        # Pulisce file temporaneo
        controller.file_service.delete_file(file_info['file_path'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Errore nell'analisi immagine: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore nell\'analisi dell\'immagine'
        }), 500

@api_bp.route('/analyze-document', methods=['POST'])
def analyze_document():
    """
    Endpoint per analizzare un documento specifico
    
    Form data:
    - document: File documento
    - query: Query di analisi (opzionale)
    """
    
    try:
        if 'document' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Nessun documento fornito'
            }), 400
        
        doc_file = request.files['document']
        if doc_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Nessun documento selezionato'
            }), 400
        
        # Salva temporaneamente il documento
        controller = get_search_controller()
        filename = secure_filename(doc_file.filename)
        file_data = doc_file.read()
        
        file_info = controller.file_service.save_uploaded_file(file_data, filename)
        
        if not file_info.get('success'):
            return jsonify(file_info), 400
        
        # Analizza documento
        query = request.form.get('query', 'Analizza questo documento')
        context = {'document_path': file_info['file_path']}
        
        document_agent = controller.agents['document']
        result = document_agent.process_query(query, context)
        
        # Pulisce file temporaneo
        controller.file_service.delete_file(file_info['file_path'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Errore nell'analisi documento: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore nell\'analisi del documento'
        }), 500

@api_bp.route('/web-search', methods=['POST'])
@validate_json_request(['query'])
@async_route
async def web_search(data):
    """
    Endpoint per ricerca web specifica
    
    Body JSON:
    {
        "query": "string",
        "urls": ["url1", "url2"],  // opzionale
        "max_pages": 10
    }
    """
    
    try:
        query = data['query'].strip()
        urls = data.get('urls', [])
        max_pages = data.get('max_pages', 10)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query non può essere vuota'
            }), 400
        
        # Prepara contesto per WebAgent
        context = {}
        if urls:
            context['urls'] = urls
        if max_pages:
            context['max_pages'] = max_pages
        
        # Esegue ricerca web
        controller = get_search_controller()
        web_agent = controller.agents['web']
        result = web_agent.process_query(query, context)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Errore nella ricerca web: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore nella ricerca web'
        }), 500

@api_bp.route('/agents/stats', methods=['GET'])
def get_agent_stats():
    """Endpoint per ottenere statistiche degli agenti"""
    
    try:
        controller = get_search_controller()
        stats = controller.get_agent_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Errore nel recupero statistiche: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore nel recupero delle statistiche'
        }), 500

@api_bp.route('/agents/stats/reset', methods=['POST'])
def reset_agent_stats():
    """Endpoint per resettare statistiche degli agenti"""
    
    try:
        controller = get_search_controller()
        results = controller.reset_agent_stats()
        
        return jsonify({
            'success': True,
            'reset_results': results,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Errore nel reset statistiche: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore nel reset delle statistiche'
        }), 500

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint per verificare lo stato di salute del sistema"""
    
    try:
        controller = get_search_controller()
        health = controller.health_check()
        
        status_code = 200
        if health['status'] == 'degraded':
            status_code = 206  # Partial Content
        elif health['status'] == 'unhealthy':
            status_code = 503  # Service Unavailable
        
        return jsonify(health), status_code
        
    except Exception as e:
        logger.error(f"Errore nel health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Errore nel controllo dello stato di salute'
        }), 503

@api_bp.route('/capabilities', methods=['GET'])
def get_capabilities():
    """Endpoint per ottenere le capacità del sistema"""
    
    try:
        controller = get_search_controller()
        
        capabilities = {
            'agents': {},
            'supported_file_types': {
                'documents': ['pdf', 'docx', 'txt', 'xlsx', 'pptx'],
                'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp']
            },
            'search_types': ['text', 'semantic', 'image', 'document', 'web', 'multimodal'],
            'features': [
                'multi_agent_search',
                'result_synthesis',
                'file_upload',
                'ocr_extraction',
                'web_crawling',
                'knowledge_base'
            ]
        }
        
        # Ottiene capacità di ogni agente
        for agent_name, agent in controller.agents.items():
            capabilities['agents'][agent_name] = {
                'enabled': agent.enabled,
                'capabilities': agent.get_capabilities()
            }
        
        return jsonify({
            'success': True,
            'capabilities': capabilities
        })
        
    except Exception as e:
        logger.error(f"Errore nel recupero capacità: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore nel recupero delle capacità'
        }), 500

@api_bp.route('/search/history', methods=['GET'])
def get_search_history():
    """Endpoint per ottenere cronologia ricerche (placeholder)"""
    
    # Implementazione futura: database per cronologia ricerche
    return jsonify({
        'success': True,
        'history': [],
        'message': 'Funzionalità cronologia in sviluppo'
    })

@api_bp.route('/knowledge-base/info', methods=['GET'])
def get_knowledge_base_info():
    """Endpoint per ottenere informazioni sulla knowledge base"""
    
    try:
        controller = get_search_controller()
        
        info = {
            'collections': {},
            'total_documents': 0,
            'total_images': 0,
            'total_text_chunks': 0
        }
        
        # Ottiene informazioni dalle collezioni vettoriali
        try:
            collections = controller.vector_service.list_collections()
            
            for collection_name in collections:
                try:
                    # Placeholder per statistiche collezione
                    # In implementazione reale, otterresti count reali
                    info['collections'][collection_name] = {
                        'document_count': 'N/A',
                        'last_updated': 'N/A'
                    }
                except Exception as e:
                    logger.error(f"Errore info collezione {collection_name}: {e}")
                    
        except Exception as e:
            logger.error(f"Errore nel recupero collezioni: {e}")
        
        return jsonify({
            'success': True,
            'knowledge_base': info
        })
        
    except Exception as e:
        logger.error(f"Errore info knowledge base: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore nel recupero informazioni knowledge base'
        }), 500

# Error handlers
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint non trovato'
    }), 404

@api_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Metodo HTTP non consentito'
    }), 405

@api_bp.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'success': False,
        'error': 'File troppo grande'
    }), 413

@api_bp.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        'success': False,
        'error': 'Errore interno del server'
    }), 500
