"""
Classe base per tutti gli agenti AI specializzati
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Classe base astratta per tutti gli agenti AI"""
    
    def __init__(self, name: str, config: Dict[str, Any], llm_service, embedding_service, vector_service):
        """
        Inizializza l'agente base
        
        Args:
            name: Nome dell'agente
            config: Configurazione dell'agente
            llm_service: Servizio LLM
            embedding_service: Servizio embedding
            vector_service: Servizio database vettoriale
        """
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.max_tokens = config.get('max_tokens', 2000)
        
        # Servizi condivisi
        self.llm_service = llm_service
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        
        # Statistiche dell'agente
        self.stats = {
            'queries_processed': 0,
            'total_processing_time': 0.0,
            'last_used': None,
            'errors': 0
        }
        
        logger.info(f"Agente {self.name} inizializzato - Enabled: {self.enabled}")
    
    @abstractmethod
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Elabora una query e restituisce risultati
        
        Args:
            query: La query da elaborare
            context: Contesto aggiuntivo (opzionale)
            
        Returns:
            Dizionario con i risultati dell'elaborazione
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Restituisce le capacità dell'agente
        
        Returns:
            Lista delle capacità supportate
        """
        pass
    
    def can_handle_query(self, query: str, query_type: str) -> bool:
        """
        Determina se l'agente può gestire una specifica query
        
        Args:
            query: La query da valutare
            query_type: Tipo della query
            
        Returns:
            True se l'agente può gestire la query, False altrimenti
        """
        if not self.enabled:
            return False
        
        # Implementazione base - gli agenti specializzati dovrebbero sovrascrivere
        return query_type in self.get_capabilities()
    
    def execute_with_stats(self, func, *args, **kwargs):
        """
        Esegue una funzione tracciando le statistiche
        
        Args:
            func: Funzione da eseguire
            *args: Argomenti posizionali
            **kwargs: Argomenti nominali
            
        Returns:
            Risultato della funzione
        """
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            
            # Aggiorna statistiche di successo
            self.stats['queries_processed'] += 1
            self.stats['last_used'] = start_time
            
            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats['total_processing_time'] += processing_time
            
            logger.debug(f"Agente {self.name} - Query processata in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            # Aggiorna statistiche di errore
            self.stats['errors'] += 1
            logger.error(f"Errore nell'agente {self.name}: {e}")
            raise
    
    def format_results(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """
        Formatta i risultati in un formato standard
        
        Args:
            results: Lista di risultati grezzi
            query: Query originale
            
        Returns:
            Risultati formattati
        """
        formatted_results = []
        
        for result in results:
            formatted_result = {
                'title': result.get('title', 'Risultato senza titolo'),
                'content': result.get('content', ''),
                'summary': result.get('summary', ''),
                'source_type': result.get('source_type', 'unknown'),
                'source_url': result.get('source_url'),
                'relevance_score': result.get('relevance_score', 0.0),
                'confidence_score': result.get('confidence_score'),
                'agent_source': self.name,
                'metadata': result.get('metadata', {})
            }
            formatted_results.append(formatted_result)
        
        return {
            'agent': self.name,
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results),
            'processing_time': self.stats.get('total_processing_time', 0),
            'timestamp': datetime.now().isoformat()
        }
    
    def generate_system_prompt(self) -> str:
        """
        Genera il prompt di sistema per l'agente
        
        Returns:
            Prompt di sistema
        """
        return f"""Sei un agente AI specializzato chiamato {self.name}.
Le tue capacità includono: {', '.join(self.get_capabilities())}.

Linee guida:
1. Fornisci risposte accurate e pertinenti
2. Usa le tue capacità specializzate per analizzare la query
3. Includi fonti e riferimenti quando possibile
4. Mantieni un tono professionale e informativo
5. Se non sei sicuro, indica il livello di confidenza

Rispondi sempre in italiano a meno che non sia specificato diversamente."""
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Valida una query prima dell'elaborazione
        
        Args:
            query: Query da validare
            
        Returns:
            Risultato della validazione
        """
        if not query or not query.strip():
            return {
                'valid': False,
                'error': 'Query vuota o non valida'
            }
        
        if len(query) > 10000:  # Limite ragionevole
            return {
                'valid': False,
                'error': 'Query troppo lunga (massimo 10000 caratteri)'
            }
        
        return {'valid': True}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Restituisce le statistiche dell'agente
        
        Returns:
            Dizionario con le statistiche
        """
        avg_processing_time = 0.0
        if self.stats['queries_processed'] > 0:
            avg_processing_time = self.stats['total_processing_time'] / self.stats['queries_processed']
        
        return {
            'name': self.name,
            'enabled': self.enabled,
            'capabilities': self.get_capabilities(),
            'queries_processed': self.stats['queries_processed'],
            'total_processing_time': self.stats['total_processing_time'],
            'average_processing_time': avg_processing_time,
            'last_used': self.stats['last_used'].isoformat() if self.stats['last_used'] else None,
            'errors': self.stats['errors'],
            'config': self.config
        }
    
    def reset_stats(self):
        """Resetta le statistiche dell'agente"""
        self.stats = {
            'queries_processed': 0,
            'total_processing_time': 0.0,
            'last_used': None,
            'errors': 0
        }
        logger.info(f"Statistiche dell'agente {self.name} resettate")
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Aggiorna la configurazione dell'agente
        
        Args:
            new_config: Nuova configurazione
        """
        self.config.update(new_config)
        self.enabled = self.config.get('enabled', True)
        self.max_tokens = self.config.get('max_tokens', 2000)
        
        logger.info(f"Configurazione dell'agente {self.name} aggiornata")
    
    def __str__(self):
        return f"Agent({self.name}, enabled={self.enabled}, capabilities={self.get_capabilities()})"
    
    def __repr__(self):
        return self.__str__()
