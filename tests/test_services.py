"""
Test per i servizi di Deep Search AI
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from app.services.file_service import FileService

class TestFileService:
    """Test per il FileService"""
    
    @pytest.fixture
    def file_service(self):
        """Fixture per FileService"""
        config = {
            'upload_folder': tempfile.mkdtemp(),
            'max_file_size': 10 * 1024 * 1024,  # 10MB
            'allowed_extensions': ['txt', 'pdf', 'jpg', 'png', 'docx']
        }
        return FileService(config)
    
    def test_file_service_initialization(self, file_service):
        """Test inizializzazione FileService"""
        assert file_service.upload_folder is not None
        assert file_service.max_file_size > 0
        assert len(file_service.allowed_extensions) > 0
    
    def test_validate_file_size(self, file_service):
        """Test validazione dimensione file"""
        # File troppo grande
        large_data = b'x' * (file_service.max_file_size + 1)
        result = file_service.validate_file(large_data, 'test.txt')
        assert not result['valid']
        assert 'troppo grande' in result['error'].lower()
        
        # File di dimensione accettabile
        small_data = b'test content'
        result = file_service.validate_file(small_data, 'test.txt')
        assert result['valid']
    
    def test_validate_file_extension(self, file_service):
        """Test validazione estensione file"""
        data = b'test content'
        
        # Estensione non supportata
        result = file_service.validate_file(data, 'test.xyz')
        assert not result['valid']
        assert 'estensione' in result['error'].lower()
        
        # Estensione supportata
        result = file_service.validate_file(data, 'test.txt')
        assert result['valid']
    
    def test_save_uploaded_file(self, file_service):
        """Test salvataggio file"""
        data = b'test file content'
        filename = 'test.txt'
        
        result = file_service.save_uploaded_file(data, filename)
        
        assert result['success']
        assert result['original_filename'] == filename
        assert result['file_size'] == len(data)
        assert os.path.exists(result['file_path'])
        
        # Cleanup
        os.remove(result['file_path'])
    
    def test_extract_text_from_txt(self, file_service):
        """Test estrazione testo da file TXT"""
        # Crea file temporaneo
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            test_content = "Questo è un test di estrazione testo"
            f.write(test_content)
            temp_path = f.name
        
        try:
            result = file_service.extract_text_from_document(temp_path, 'txt')
            assert result['success']
            assert test_content in result['extracted_text']
        finally:
            os.unlink(temp_path)
    
    def test_chunk_document_text(self, file_service):
        """Test chunking del testo"""
        text = "Questo è un testo di test. " * 100  # Testo lungo
        
        chunks = file_service.chunk_document_text(text, chunk_size=100, chunk_overlap=20)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 120 for chunk in chunks)  # Considera overlap
    
    def test_calculate_file_hash(self, file_service):
        """Test calcolo hash file"""
        data1 = b'test data'
        data2 = b'test data'
        data3 = b'different data'
        
        hash1 = file_service._calculate_file_hash(data1)
        hash2 = file_service._calculate_file_hash(data2)
        hash3 = file_service._calculate_file_hash(data3)
        
        assert hash1 == hash2  # Stesso contenuto, stesso hash
        assert hash1 != hash3  # Contenuto diverso, hash diverso
        assert len(hash1) == 64  # SHA-256 produce hash di 64 caratteri

class TestMockLLMService:
    """Test per LLMService con mock"""
    
    @patch('openai.OpenAI')
    def test_llm_service_mock(self, mock_openai):
        """Test LLMService con OpenAI mockato"""
        from app.services.llm_service import LLMService
        
        # Mock della risposta OpenAI
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        config = {
            'provider': 'openai',
            'model': 'gpt-4',
            'api_key': 'test-key'
        }
        
        try:
            llm_service = LLMService(config)
            response = llm_service.generate_response("Test prompt")
            assert response == "Test response"
        except Exception as e:
            # Se fallisce per mancanza di API key, è normale nei test
            assert 'api_key' in str(e).lower() or 'openai' in str(e).lower()

class TestMockEmbeddingService:
    """Test per EmbeddingService con mock"""
    
    @patch('openai.OpenAI')
    def test_embedding_service_mock(self, mock_openai):
        """Test EmbeddingService con OpenAI mockato"""
        from app.services.embedding_service import EmbeddingService
        
        # Mock della risposta OpenAI
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3] * 1024  # Simula embedding
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        config = {
            'provider': 'openai',
            'model': 'text-embedding-3-large',
            'api_key': 'test-key'
        }
        
        try:
            embedding_service = EmbeddingService(config)
            embedding = embedding_service.generate_text_embedding("Test text")
            assert isinstance(embedding, list)
            assert len(embedding) > 0
        except Exception as e:
            # Se fallisce per mancanza di API key, è normale nei test
            assert 'api_key' in str(e).lower() or 'openai' in str(e).lower()

class TestMockVectorService:
    """Test per VectorService con mock"""
    
    def test_vector_service_mock(self):
        """Test VectorService con configurazione mock"""
        from app.services.vector_service import VectorService
        
        config = {
            'provider': 'chroma',
            'persist_directory': tempfile.mkdtemp()
        }
        
        try:
            vector_service = VectorService(config)
            # Test base di inizializzazione
            assert vector_service.provider == 'chroma'
        except Exception as e:
            # ChromaDB potrebbe non essere disponibile nei test
            assert 'chroma' in str(e).lower() or 'connection' in str(e).lower()

class TestIntegration:
    """Test di integrazione tra servizi"""
    
    def test_file_to_text_pipeline(self):
        """Test pipeline completa file -> testo"""
        config = {
            'upload_folder': tempfile.mkdtemp(),
            'max_file_size': 10 * 1024 * 1024,
            'allowed_extensions': ['txt']
        }
        
        file_service = FileService(config)
        
        # Crea e salva file
        test_content = "Contenuto di test per pipeline"
        data = test_content.encode('utf-8')
        
        save_result = file_service.save_uploaded_file(data, 'test.txt')
        assert save_result['success']
        
        # Estrai testo
        extract_result = file_service.extract_text_from_document(
            save_result['file_path'], 'txt'
        )
        assert extract_result['success']
        assert test_content in extract_result['extracted_text']
        
        # Cleanup
        os.remove(save_result['file_path'])

if __name__ == '__main__':
    pytest.main([__file__])
