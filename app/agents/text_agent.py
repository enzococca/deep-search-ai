"""
Agente specializzato per la ricerca e analisi di contenuti testuali
"""

import logging
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class TextAgent(BaseAgent):
    """Agente specializzato per ricerca semantica su contenuti testuali"""
    
    def __init__(self, config: Dict[str, Any], llm_service, embedding_service, vector_service):
        super().__init__("TextAgent", config, llm_service, embedding_service, vector_service)
        
        # Configurazioni specifiche per testo
        self.collection_name = "text_embeddings"
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.max_results = config.get('max_results', 10)
        
        # Inizializza collezione se non esiste
        self._ensure_collection_exists()
    
    def get_capabilities(self) -> List[str]:
        """Restituisce le capacità dell'agente testuale"""
        return [
            'text_search',
            'semantic_search', 
            'keyword_extraction',
            'text_analysis',
            'content_summarization',
            'question_answering'
        ]
    
    def can_handle_query(self, query: str, query_type: str) -> bool:
        """Determina se può gestire la query"""
        if not self.enabled:
            return False
        
        # Gestisce query di tipo testo e ricerche generiche
        return query_type in ['text', 'general', 'semantic']
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Elabora una query testuale
        
        Args:
            query: Query testuale da elaborare
            context: Contesto aggiuntivo
            
        Returns:
            Risultati della ricerca testuale
        """
        return self.execute_with_stats(self._process_text_query, query, context)
    
    def _process_text_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implementazione interna dell'elaborazione query"""
        
        # Validazione query
        validation = self.validate_query(query)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        try:
            # Analisi della query
            query_analysis = self._analyze_query(query)
            
            # Generazione embedding per la query
            query_embedding = self.embedding_service.generate_text_embedding(query)
            
            # Ricerca semantica nel database vettoriale
            semantic_results = self._semantic_search(query_embedding, query_analysis)
            
            # Generazione di query alternative per migliorare i risultati
            alternative_queries = self._generate_alternative_queries(query)
            
            # Ricerca con query alternative
            alternative_results = []
            for alt_query in alternative_queries:
                alt_embedding = self.embedding_service.generate_text_embedding(alt_query)
                alt_results = self._semantic_search(alt_embedding, query_analysis, max_results=5)
                alternative_results.extend(alt_results)
            
            # Combinazione e ranking dei risultati
            all_results = semantic_results + alternative_results
            ranked_results = self._rank_and_deduplicate_results(all_results, query)
            
            # Generazione di riassunti per i risultati migliori
            enhanced_results = self._enhance_results_with_summaries(ranked_results[:self.max_results], query)
            
            return self.format_results(enhanced_results, query)
            
        except Exception as e:
            logger.error(f"Errore nell'elaborazione query testuale: {e}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analizza la query per estrarre intenti e entità"""
        try:
            analysis = self.llm_service.analyze_query_intent(query)
            
            # Estrazione parole chiave aggiuntive
            keywords = self.llm_service.extract_keywords(query)
            analysis['keywords'] = keywords
            
            return analysis
            
        except Exception as e:
            logger.error(f"Errore nell'analisi della query: {e}")
            return {
                'query_type': 'text',
                'complexity': 'medium',
                'keywords': [],
                'confidence': 0.5
            }
    
    def _semantic_search(self, query_embedding: List[float], query_analysis: Dict[str, Any], 
                        max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Esegue ricerca semantica nel database vettoriale"""
        try:
            max_results = max_results or self.max_results
            
            # Ricerca nel database vettoriale
            search_results = self.vector_service.search_vectors(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                top_k=max_results * 2,  # Prende più risultati per poi filtrare
                threshold=self.similarity_threshold
            )
            
            # Conversione in formato standard
            formatted_results = []
            for result in search_results:
                formatted_result = {
                    'title': self._extract_title_from_text(result.get('text', '')),
                    'content': result.get('text', ''),
                    'source_type': 'database',
                    'relevance_score': result.get('score', 0.0),
                    'metadata': result.get('metadata', {})
                }
                formatted_results.append(formatted_result)
            
            return formatted_results[:max_results]
            
        except Exception as e:
            logger.error(f"Errore nella ricerca semantica: {e}")
            return []
    
    def _generate_alternative_queries(self, original_query: str) -> List[str]:
        """Genera query alternative per migliorare la ricerca"""
        try:
            alternatives = self.llm_service.generate_search_queries(original_query, num_queries=3)
            return alternatives
            
        except Exception as e:
            logger.error(f"Errore nella generazione query alternative: {e}")
            return []
    
    def _rank_and_deduplicate_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Ordina e rimuove duplicati dai risultati"""
        if not results:
            return []
        
        # Rimozione duplicati basata sul contenuto
        seen_content = set()
        unique_results = []
        
        for result in results:
            content_hash = hash(result.get('content', '')[:200])  # Usa primi 200 caratteri
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        # Ri-valutazione della rilevanza con LLM
        for result in unique_results:
            try:
                relevance_score = self.llm_service.evaluate_result_relevance(query, result)
                result['llm_relevance_score'] = relevance_score
                # Combina score semantico e LLM
                result['combined_score'] = (result.get('relevance_score', 0) + relevance_score) / 2
            except:
                result['combined_score'] = result.get('relevance_score', 0)
        
        # Ordinamento per score combinato
        unique_results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        return unique_results
    
    def _enhance_results_with_summaries(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Aggiunge riassunti ai risultati migliori"""
        enhanced_results = []
        
        for result in results:
            try:
                # Genera riassunto se il contenuto è lungo
                content = result.get('content', '')
                if len(content) > 500:
                    summary_prompt = f"""
Riassumi questo contenuto in relazione alla query: "{query}"

Contenuto:
{content[:2000]}

Fornisci un riassunto conciso (massimo 200 parole) che evidenzi le informazioni più rilevanti per la query.
"""
                    
                    summary = self.llm_service.generate_response(
                        summary_prompt,
                        system_prompt="Sei un esperto nel riassumere contenuti in modo accurato e conciso."
                    )
                    
                    result['summary'] = summary
                else:
                    result['summary'] = content
                
                enhanced_results.append(result)
                
            except Exception as e:
                logger.error(f"Errore nella generazione riassunto: {e}")
                result['summary'] = result.get('content', '')[:200] + '...'
                enhanced_results.append(result)
        
        return enhanced_results
    
    def _extract_title_from_text(self, text: str) -> str:
        """Estrae o genera un titolo dal testo"""
        if not text:
            return "Contenuto senza titolo"
        
        # Prende la prima frase o i primi 50 caratteri
        first_sentence = text.split('.')[0].strip()
        if len(first_sentence) > 10 and len(first_sentence) < 100:
            return first_sentence
        
        # Fallback: primi 50 caratteri
        return text[:50].strip() + ('...' if len(text) > 50 else '')
    
    def add_text_to_knowledge_base(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Aggiunge testo alla knowledge base
        
        Args:
            text: Testo da aggiungere
            metadata: Metadati associati
            
        Returns:
            True se aggiunto con successo
        """
        try:
            # Chunking del testo se necessario
            if len(text) > 1000:
                from app.services.file_service import FileService
                file_service = FileService({})
                chunks = file_service.chunk_document_text(text)
            else:
                chunks = [text]
            
            # Generazione embeddings
            embeddings = self.embedding_service.generate_batch_embeddings(chunks)
            
            # Preparazione metadati
            chunk_metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'text_length': len(chunk)
                })
                chunk_metadatas.append(chunk_metadata)
            
            # Inserimento nel database vettoriale
            success = self.vector_service.insert_vectors(
                collection_name=self.collection_name,
                vectors=embeddings,
                texts=chunks,
                metadatas=chunk_metadatas
            )
            
            if success:
                logger.info(f"Aggiunto testo alla knowledge base - Chunks: {len(chunks)}")
            
            return success
            
        except Exception as e:
            logger.error(f"Errore nell'aggiunta testo alla knowledge base: {e}")
            return False
    
    def search_knowledge_base(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Cerca nella knowledge base testuale
        
        Args:
            query: Query di ricerca
            max_results: Numero massimo di risultati
            
        Returns:
            Lista di risultati
        """
        try:
            # Genera embedding per la query
            query_embedding = self.embedding_service.generate_text_embedding(query)
            
            # Ricerca nel database vettoriale
            results = self.vector_service.search_vectors(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                top_k=max_results,
                threshold=self.similarity_threshold
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Errore nella ricerca knowledge base: {e}")
            return []
    
    def _ensure_collection_exists(self):
        """Assicura che la collezione per i testi esista"""
        try:
            # Verifica se la collezione esiste
            collections = self.vector_service.list_collections()
            
            if self.collection_name not in collections:
                # Crea la collezione
                success = self.vector_service.create_collection(
                    collection_name=self.collection_name,
                    dimension=3072,  # Dimensione per text-embedding-3-large
                    description="Collezione per embeddings testuali"
                )
                
                if success:
                    logger.info(f"Collezione {self.collection_name} creata con successo")
                else:
                    logger.error(f"Errore nella creazione della collezione {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Errore nella verifica/creazione collezione: {e}")
