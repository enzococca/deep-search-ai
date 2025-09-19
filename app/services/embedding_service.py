"""
Servizio per la generazione di embeddings testuali e multimodali
"""

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union
from openai import OpenAI
import hashlib
import pickle

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Servizio per generare embeddings per testo e contenuti multimodali"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inizializza il servizio di embedding
        
        Args:
            config: Configurazione del servizio embedding
        """
        self.config = config
        self.text_config = config.get('text', {})
        self.multimodal_config = config.get('multimodal', {})
        
        # Configurazione embedding testuali
        self.text_provider = self.text_config.get('provider', 'openai')
        self.text_model = self.text_config.get('model', 'text-embedding-3-large')
        self.text_dimensions = self.text_config.get('dimensions', 3072)
        
        # Inizializzazione client OpenAI
        if self.text_provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY non configurata. Gli embeddings potrebbero non funzionare.")
            
            self.openai_client = OpenAI(api_key=api_key)
        
        # Cache per embeddings (opzionale)
        self.cache_enabled = config.get('cache_enabled', True)
        self.cache = {}
        
        logger.info(f"Embedding Service inizializzato - Text Model: {self.text_model}")
    
    def generate_text_embedding(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Genera embedding per un testo
        
        Args:
            text: Il testo da convertire in embedding
            model: Modello specifico da usare (opzionale)
            
        Returns:
            Lista di float rappresentanti l'embedding
        """
        if not text or not text.strip():
            logger.warning("Testo vuoto fornito per embedding")
            return [0.0] * self.text_dimensions
        
        # Usa cache se abilitata
        if self.cache_enabled:
            cache_key = self._get_cache_key(text, model or self.text_model)
            if cache_key in self.cache:
                logger.debug("Embedding recuperato dalla cache")
                return self.cache[cache_key]
        
        try:
            # Preprocessing del testo
            processed_text = self._preprocess_text(text)
            
            if self.text_provider == 'openai':
                response = self.openai_client.embeddings.create(
                    model=model or self.text_model,
                    input=processed_text,
                    encoding_format="float"
                )
                
                embedding = response.data[0].embedding
                
                # Salva in cache
                if self.cache_enabled:
                    self.cache[cache_key] = embedding
                
                logger.debug(f"Embedding generato - Dimensioni: {len(embedding)}")
                return embedding
            
            else:
                raise ValueError(f"Provider di embedding non supportato: {self.text_provider}")
                
        except Exception as e:
            logger.error(f"Errore nella generazione dell'embedding: {e}")
            # Restituisce embedding zero in caso di errore
            return [0.0] * self.text_dimensions
    
    def generate_batch_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """
        Genera embeddings per una lista di testi in batch
        
        Args:
            texts: Lista di testi
            model: Modello specifico da usare (opzionale)
            
        Returns:
            Lista di embeddings
        """
        if not texts:
            return []
        
        try:
            # Filtra testi vuoti
            valid_texts = [text for text in texts if text and text.strip()]
            if not valid_texts:
                logger.warning("Nessun testo valido fornito per batch embedding")
                return [[0.0] * self.text_dimensions] * len(texts)
            
            # Preprocessing
            processed_texts = [self._preprocess_text(text) for text in valid_texts]
            
            if self.text_provider == 'openai':
                response = self.openai_client.embeddings.create(
                    model=model or self.text_model,
                    input=processed_texts,
                    encoding_format="float"
                )
                
                embeddings = [item.embedding for item in response.data]
                
                logger.debug(f"Batch embeddings generati - Count: {len(embeddings)}")
                return embeddings
            
            else:
                # Fallback: genera embeddings uno per uno
                return [self.generate_text_embedding(text, model) for text in valid_texts]
                
        except Exception as e:
            logger.error(f"Errore nella generazione batch embeddings: {e}")
            return [[0.0] * self.text_dimensions] * len(texts)
    
    def generate_document_embeddings(self, document_chunks: List[str], 
                                   metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Genera embeddings per chunks di un documento
        
        Args:
            document_chunks: Lista di chunks del documento
            metadata: Metadati del documento
            
        Returns:
            Lista di dizionari con embedding e metadati
        """
        try:
            embeddings = self.generate_batch_embeddings(document_chunks)
            
            results = []
            for i, (chunk, embedding) in enumerate(zip(document_chunks, embeddings)):
                result = {
                    'chunk_id': i,
                    'text': chunk,
                    'embedding': embedding,
                    'metadata': metadata or {}
                }
                results.append(result)
            
            logger.info(f"Embeddings documento generati - Chunks: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Errore nella generazione embeddings documento: {e}")
            return []
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calcola la similarità coseno tra due embeddings
        
        Args:
            embedding1: Primo embedding
            embedding2: Secondo embedding
            
        Returns:
            Similarità coseno (0-1)
        """
        try:
            # Conversione a numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calcolo similarità coseno
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Normalizza tra 0 e 1
            return (similarity + 1) / 2
            
        except Exception as e:
            logger.error(f"Errore nel calcolo della similarità: {e}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Trova gli embeddings più simili a quello di query
        
        Args:
            query_embedding: Embedding della query
            candidate_embeddings: Lista di embeddings candidati
            top_k: Numero di risultati da restituire
            
        Returns:
            Lista di risultati ordinati per similarità
        """
        try:
            similarities = []
            
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append({
                    'index': i,
                    'similarity': similarity
                })
            
            # Ordina per similarità decrescente
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Restituisce top_k risultati
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Errore nella ricerca di similarità: {e}")
            return []
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocessa il testo prima della generazione dell'embedding
        
        Args:
            text: Testo da preprocessare
            
        Returns:
            Testo preprocessato
        """
        # Rimuove spazi extra e caratteri di controllo
        processed = ' '.join(text.split())
        
        # Limita la lunghezza (OpenAI ha limiti sui token)
        max_length = 8000  # Circa 8000 caratteri per essere sicuri
        if len(processed) > max_length:
            processed = processed[:max_length]
            logger.debug(f"Testo troncato a {max_length} caratteri")
        
        return processed
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """
        Genera una chiave di cache per il testo e modello
        
        Args:
            text: Il testo
            model: Il modello
            
        Returns:
            Chiave di cache
        """
        content = f"{model}:{text}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_embedding_info(self) -> Dict[str, Any]:
        """
        Restituisce informazioni sui modelli di embedding
        
        Returns:
            Dizionario con informazioni sui modelli
        """
        return {
            'text_provider': self.text_provider,
            'text_model': self.text_model,
            'text_dimensions': self.text_dimensions,
            'cache_enabled': self.cache_enabled,
            'cache_size': len(self.cache) if self.cache_enabled else 0
        }
    
    def clear_cache(self):
        """Pulisce la cache degli embeddings"""
        if self.cache_enabled:
            self.cache.clear()
            logger.info("Cache embeddings pulita")
    
    def save_cache(self, filepath: str):
        """
        Salva la cache su file
        
        Args:
            filepath: Percorso del file dove salvare la cache
        """
        if self.cache_enabled and self.cache:
            try:
                with open(filepath, 'wb') as f:
                    pickle.dump(self.cache, f)
                logger.info(f"Cache salvata in {filepath}")
            except Exception as e:
                logger.error(f"Errore nel salvataggio della cache: {e}")
    
    def load_cache(self, filepath: str):
        """
        Carica la cache da file
        
        Args:
            filepath: Percorso del file da cui caricare la cache
        """
        if self.cache_enabled:
            try:
                with open(filepath, 'rb') as f:
                    self.cache = pickle.load(f)
                logger.info(f"Cache caricata da {filepath} - Entries: {len(self.cache)}")
            except FileNotFoundError:
                logger.info("File cache non trovato, inizializzazione cache vuota")
            except Exception as e:
                logger.error(f"Errore nel caricamento della cache: {e}")
                self.cache = {}
