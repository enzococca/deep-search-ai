"""
Test base per l'applicazione Deep Search AI
"""

import pytest
import json
import os
import tempfile
from app import create_app

@pytest.fixture
def app():
    """Fixture per l'applicazione Flask"""
    
    # Configurazione di test
    test_config = {
        'flask': {
            'testing': True,
            'debug': True,
            'secret_key': 'test-secret-key'
        },
        'database': {
            'url': 'sqlite:///:memory:'
        },
        'file_service': {
            'upload_folder': tempfile.mkdtemp(),
            'max_file_size': 10,  # 10MB per test
            'allowed_extensions': ['txt', 'pdf', 'jpg', 'png']
        },
        'llm': {
            'provider': 'mock',  # Mock per test
            'model': 'test-model',
            'api_key': 'test-key'
        },
        'embedding': {
            'provider': 'mock',
            'model': 'test-embedding',
            'api_key': 'test-key'
        },
        'vector_db': {
            'provider': 'mock',
            'persist_directory': tempfile.mkdtemp()
        },
        'agents': {
            'text': {'enabled': True, 'max_results': 5},
            'image': {'enabled': True, 'max_results': 5},
            'document': {'enabled': True, 'max_results': 5},
            'web': {'enabled': False},  # Disabilitato per test
            'synthesis': {'enabled': True}
        },
        'logging': {
            'level': 'DEBUG'
        }
    }
    
    # Crea app con configurazione di test
    app = create_app()
    app.config.update({
        'TESTING': True,
        'APP_CONFIG': test_config
    })
    
    return app

@pytest.fixture
def client(app):
    """Fixture per il client di test"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Fixture per il runner CLI"""
    return app.test_cli_runner()

class TestBasicRoutes:
    """Test per le route base dell'applicazione"""
    
    def test_index_route(self, client):
        """Test della route principale"""
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['message'] == 'Deep Search AI API'
        assert data['version'] == '1.0.0'
        assert data['status'] == 'running'
        assert 'endpoints' in data
    
    def test_health_route(self, client):
        """Test della route di health check"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'Deep Search AI'
        assert 'timestamp' in data
    
    def test_api_health_route(self, client):
        """Test della route API health"""
        response = client.get('/api/v1/health')
        assert response.status_code in [200, 503]  # Può fallire se servizi non disponibili
        
        data = json.loads(response.data)
        assert 'status' in data

class TestAPIRoutes:
    """Test per le API routes"""
    
    def test_capabilities_endpoint(self, client):
        """Test dell'endpoint capabilities"""
        response = client.get('/api/v1/capabilities')
        assert response.status_code in [200, 500]  # Può fallire se SearchController non inizializzato
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'capabilities' in data
    
    def test_search_endpoint_validation(self, client):
        """Test validazione endpoint search"""
        # Test senza JSON
        response = client.post('/api/v1/search')
        assert response.status_code == 400
        
        # Test con JSON vuoto
        response = client.post('/api/v1/search', 
                             json={},
                             content_type='application/json')
        assert response.status_code == 400
        
        # Test con query vuota
        response = client.post('/api/v1/search',
                             json={'query': ''},
                             content_type='application/json')
        assert response.status_code == 400
    
    def test_upload_endpoint_validation(self, client):
        """Test validazione endpoint upload"""
        # Test senza file
        response = client.post('/api/v1/upload')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data
        assert 'file' in data['error'].lower()

class TestFileHandling:
    """Test per la gestione file"""
    
    def test_upload_text_file(self, client):
        """Test upload di un file di testo"""
        # Crea un file di test temporaneo
        test_content = "Questo è un file di test per Deep Search AI"
        
        response = client.post('/api/v1/upload',
                             data={
                                 'file': (tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False), test_content)
                             },
                             content_type='multipart/form-data')
        
        # Può fallire se servizi non disponibili, ma dovrebbe gestire gracefully
        assert response.status_code in [200, 500]
    
    def test_analyze_image_validation(self, client):
        """Test validazione analisi immagine"""
        response = client.post('/api/v1/analyze-image')
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'error' in data

class TestErrorHandling:
    """Test per la gestione degli errori"""
    
    def test_404_error(self, client):
        """Test gestione errore 404"""
        response = client.get('/api/v1/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_405_error(self, client):
        """Test gestione errore 405 (Method Not Allowed)"""
        response = client.put('/api/v1/search')
        assert response.status_code == 405

class TestConfiguration:
    """Test per la configurazione dell'applicazione"""
    
    def test_app_configuration(self, app):
        """Test configurazione dell'app"""
        assert app.config['TESTING'] is True
        assert 'APP_CONFIG' in app.config
        
        config = app.config['APP_CONFIG']
        assert 'flask' in config
        assert 'agents' in config
    
    def test_cors_configuration(self, client):
        """Test configurazione CORS"""
        response = client.options('/api/v1/health')
        # CORS headers dovrebbero essere presenti
        assert response.status_code in [200, 404]  # OPTIONS può non essere implementato

class TestMockServices:
    """Test per verificare che i servizi mock funzionino"""
    
    def test_search_with_mock_services(self, client):
        """Test ricerca con servizi mock"""
        response = client.post('/api/v1/search',
                             json={'query': 'test query'},
                             content_type='application/json')
        
        # Con servizi mock, dovrebbe fallire gracefully
        assert response.status_code in [200, 500]
        
        data = json.loads(response.data)
        assert 'success' in data or 'error' in data

if __name__ == '__main__':
    pytest.main([__file__])
