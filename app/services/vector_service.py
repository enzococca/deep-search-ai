"""
Servizio per la gestione del database vettoriale (Milvus/ChromaDB)
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class VectorService:
    """Servizio per gestire operazioni su database vettoriali"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inizializza il servizio del database vettoriale
        
        Args:
            config: Configurazione del database vettoriale
        """
        self.config = config
        self.provider = config.get('provider', 'chromadb')
        self.client = None
        self.collections = {}
        
        # Inizializzazione del provider
        if self.provider == 'milvus':
            self._init_milvus()
        elif self.provider == 'chromadb':
            self._init_chromadb()
        else:
            raise ValueError(f"Provider non supportato: {self.provider}")
        
        logger.info(f"Vector Service inizializzato - Provider: {self.provider}")
    
    def _init_milvus(self):
        """Inizializza connessione Milvus"""
        try:
            from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType
            
            host = self.config.get('host', 'localhost')
            port = self.config.get('port', 19530)
            
            # Connessione a Milvus
            connections.connect("default", host=host, port=port)
            
            self.milvus_connections = connections
            self.milvus_Collection = Collection
            self.milvus_CollectionSchema = CollectionSchema
            self.milvus_FieldSchema = FieldSchema
            self.milvus_DataType = DataType
            
            logger.info(f"Connesso a Milvus su {host}:{port}")
            
        except ImportError:
            logger.error("pymilvus non installato. Installa con: pip install pymilvus")
            raise
        except Exception as e:
            logger.error(f"Errore nella connessione a Milvus: {e}")
            # Fallback a ChromaDB
            logger.info("Fallback a ChromaDB")
            self.provider = 'chromadb'
            self._init_chromadb()
    
    def _init_chromadb(self):
        """Inizializza ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            persist_directory = self.config.get('persist_directory', './data/chromadb')
            
            # Assicura che la directory esista
            os.makedirs(persist_directory, exist_ok=True)
            
            # Inizializzazione client ChromaDB
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            logger.info(f"ChromaDB inizializzato - Directory: {persist_directory}")
            
        except ImportError:
            logger.error("chromadb non installato. Installa con: pip install chromadb")
            raise
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione di ChromaDB: {e}")
            raise
    
    def create_collection(self, collection_name: str, dimension: int = 3072, 
                         description: str = "") -> bool:
        """
        Crea una nuova collezione nel database vettoriale
        
        Args:
            collection_name: Nome della collezione
            dimension: Dimensione dei vettori
            description: Descrizione della collezione
            
        Returns:
            True se creata con successo, False altrimenti
        """
        try:
            if self.provider == 'milvus':
                return self._create_milvus_collection(collection_name, dimension, description)
            elif self.provider == 'chromadb':
                return self._create_chromadb_collection(collection_name, description)
                
        except Exception as e:
            logger.error(f"Errore nella creazione della collezione {collection_name}: {e}")
            return False
    
    def _create_milvus_collection(self, collection_name: str, dimension: int, description: str) -> bool:
        """Crea collezione Milvus"""
        try:
            # Schema della collezione
            fields = [
                self.milvus_FieldSchema(name="id", dtype=self.milvus_DataType.INT64, is_primary=True, auto_id=True),
                self.milvus_FieldSchema(name="embedding", dtype=self.milvus_DataType.FLOAT_VECTOR, dim=dimension),
                self.milvus_FieldSchema(name="text", dtype=self.milvus_DataType.VARCHAR, max_length=65535),
                self.milvus_FieldSchema(name="metadata", dtype=self.milvus_DataType.JSON)
            ]
            
            schema = self.milvus_CollectionSchema(fields, description)
            collection = self.milvus_Collection(collection_name, schema)
            
            # Creazione indice
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index("embedding", index_params)
            
            self.collections[collection_name] = collection
            logger.info(f"Collezione Milvus '{collection_name}' creata")
            return True
            
        except Exception as e:
            logger.error(f"Errore nella creazione collezione Milvus: {e}")
            return False
    
    def _create_chromadb_collection(self, collection_name: str, description: str) -> bool:
        """Crea collezione ChromaDB"""
        try:
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": description}
            )
            
            self.collections[collection_name] = collection
            logger.info(f"Collezione ChromaDB '{collection_name}' creata/recuperata")
            return True
            
        except Exception as e:
            logger.error(f"Errore nella creazione collezione ChromaDB: {e}")
            return False
    
    def insert_vectors(self, collection_name: str, vectors: List[List[float]], 
                      texts: List[str], metadatas: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        Inserisce vettori nella collezione
        
        Args:
            collection_name: Nome della collezione
            vectors: Lista di vettori
            texts: Lista di testi corrispondenti
            metadatas: Lista di metadati (opzionale)
            
        Returns:
            True se inserimento riuscito, False altrimenti
        """
        try:
            if not vectors or not texts or len(vectors) != len(texts):
                logger.error("Vettori e testi devono avere la stessa lunghezza")
                return False
            
            # Assicura che la collezione esista
            if collection_name not in self.collections:
                self.create_collection(collection_name)
            
            if self.provider == 'milvus':
                return self._insert_milvus_vectors(collection_name, vectors, texts, metadatas)
            elif self.provider == 'chromadb':
                return self._insert_chromadb_vectors(collection_name, vectors, texts, metadatas)
                
        except Exception as e:
            logger.error(f"Errore nell'inserimento vettori: {e}")
            return False
    
    def _insert_milvus_vectors(self, collection_name: str, vectors: List[List[float]], 
                              texts: List[str], metadatas: Optional[List[Dict[str, Any]]]) -> bool:
        """Inserisce vettori in Milvus"""
        try:
            collection = self.collections[collection_name]
            
            # Preparazione dati
            data = [
                vectors,
                texts,
                metadatas or [{}] * len(vectors)
            ]
            
            # Inserimento
            collection.insert(data)
            collection.flush()
            
            logger.info(f"Inseriti {len(vectors)} vettori in Milvus collezione '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Errore inserimento Milvus: {e}")
            return False
    
    def _insert_chromadb_vectors(self, collection_name: str, vectors: List[List[float]], 
                                texts: List[str], metadatas: Optional[List[Dict[str, Any]]]) -> bool:
        """Inserisce vettori in ChromaDB"""
        try:
            collection = self.collections[collection_name]
            
            # Generazione IDs
            ids = [f"{collection_name}_{i}" for i in range(len(vectors))]
            
            # Inserimento
            collection.add(
                embeddings=vectors,
                documents=texts,
                metadatas=metadatas or [{}] * len(vectors),
                ids=ids
            )
            
            logger.info(f"Inseriti {len(vectors)} vettori in ChromaDB collezione '{collection_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Errore inserimento ChromaDB: {e}")
            return False
    
    def search_vectors(self, collection_name: str, query_vector: List[float], 
                      top_k: int = 10, threshold: float = 0.0) -> List[Dict[str, Any]]:
        """
        Cerca vettori simili nella collezione
        
        Args:
            collection_name: Nome della collezione
            query_vector: Vettore di query
            top_k: Numero di risultati da restituire
            threshold: Soglia di similarità minima
            
        Returns:
            Lista di risultati con score e metadati
        """
        try:
            if collection_name not in self.collections:
                logger.error(f"Collezione '{collection_name}' non trovata")
                return []
            
            if self.provider == 'milvus':
                return self._search_milvus_vectors(collection_name, query_vector, top_k, threshold)
            elif self.provider == 'chromadb':
                return self._search_chromadb_vectors(collection_name, query_vector, top_k, threshold)
                
        except Exception as e:
            logger.error(f"Errore nella ricerca vettori: {e}")
            return []
    
    def _search_milvus_vectors(self, collection_name: str, query_vector: List[float], 
                              top_k: int, threshold: float) -> List[Dict[str, Any]]:
        """Cerca vettori in Milvus"""
        try:
            collection = self.collections[collection_name]
            collection.load()
            
            search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
            
            results = collection.search(
                data=[query_vector],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["text", "metadata"]
            )
            
            formatted_results = []
            for hit in results[0]:
                if hit.score >= threshold:
                    formatted_results.append({
                        'id': hit.id,
                        'score': hit.score,
                        'text': hit.entity.get('text'),
                        'metadata': hit.entity.get('metadata', {})
                    })
            
            logger.debug(f"Trovati {len(formatted_results)} risultati in Milvus")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Errore ricerca Milvus: {e}")
            return []
    
    def _search_chromadb_vectors(self, collection_name: str, query_vector: List[float], 
                                top_k: int, threshold: float) -> List[Dict[str, Any]]:
        """Cerca vettori in ChromaDB"""
        try:
            collection = self.collections[collection_name]
            
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k
            )
            
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    # Converte distanza in similarità (assumendo distanza coseno)
                    similarity = 1 - distance
                    
                    if similarity >= threshold:
                        formatted_results.append({
                            'id': results['ids'][0][i],
                            'score': similarity,
                            'text': results['documents'][0][i] if results['documents'] else '',
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                        })
            
            logger.debug(f"Trovati {len(formatted_results)} risultati in ChromaDB")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Errore ricerca ChromaDB: {e}")
            return []
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Elimina una collezione
        
        Args:
            collection_name: Nome della collezione da eliminare
            
        Returns:
            True se eliminazione riuscita, False altrimenti
        """
        try:
            if self.provider == 'milvus':
                if collection_name in self.collections:
                    self.collections[collection_name].drop()
                    del self.collections[collection_name]
            elif self.provider == 'chromadb':
                self.client.delete_collection(collection_name)
                if collection_name in self.collections:
                    del self.collections[collection_name]
            
            logger.info(f"Collezione '{collection_name}' eliminata")
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'eliminazione collezione: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """
        Ottiene informazioni su una collezione
        
        Args:
            collection_name: Nome della collezione
            
        Returns:
            Dizionario con informazioni sulla collezione
        """
        try:
            if collection_name not in self.collections:
                return {}
            
            if self.provider == 'milvus':
                collection = self.collections[collection_name]
                return {
                    'name': collection_name,
                    'provider': self.provider,
                    'num_entities': collection.num_entities,
                    'schema': str(collection.schema)
                }
            elif self.provider == 'chromadb':
                collection = self.collections[collection_name]
                count = collection.count()
                return {
                    'name': collection_name,
                    'provider': self.provider,
                    'num_entities': count,
                    'metadata': collection.metadata
                }
                
        except Exception as e:
            logger.error(f"Errore nel recupero info collezione: {e}")
            return {}
    
    def list_collections(self) -> List[str]:
        """
        Lista tutte le collezioni disponibili
        
        Returns:
            Lista dei nomi delle collezioni
        """
        try:
            if self.provider == 'milvus':
                from pymilvus import utility
                return utility.list_collections()
            elif self.provider == 'chromadb':
                collections = self.client.list_collections()
                return [col.name for col in collections]
                
        except Exception as e:
            logger.error(f"Errore nel listing collezioni: {e}")
            return []
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Restituisce informazioni sul servizio
        
        Returns:
            Dizionario con informazioni sul servizio
        """
        return {
            'provider': self.provider,
            'config': self.config,
            'collections_loaded': list(self.collections.keys()),
            'available_collections': self.list_collections()
        }
