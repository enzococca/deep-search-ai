"""
Agente specializzato per la ricerca e analisi di documenti
"""

import logging
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class DocumentAgent(BaseAgent):
    """Agente specializzato per elaborazione e ricerca in documenti"""
    
    def __init__(self, config: Dict[str, Any], llm_service, embedding_service, vector_service, file_service):
        super().__init__("DocumentAgent", config, llm_service, embedding_service, vector_service)
        
        self.file_service = file_service
        
        # Configurazioni specifiche per documenti
        self.collection_name = "document_embeddings"
        self.chunk_size = config.get('chunk_size', 1000)
        self.chunk_overlap = config.get('chunk_overlap', 200)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.max_results = config.get('max_results', 10)
        
        # Tipi di documento supportati
        self.supported_types = ['pdf', 'docx', 'txt', 'xlsx', 'pptx']
        
        # Inizializza collezione se non esiste
        self._ensure_collection_exists()
    
    def get_capabilities(self) -> List[str]:
        """Restituisce le capacità dell'agente documenti"""
        return [
            'document_search',
            'document_analysis',
            'content_extraction',
            'document_summarization',
            'structured_data_extraction',
            'cross_document_search'
        ]
    
    def can_handle_query(self, query: str, query_type: str) -> bool:
        """Determina se può gestire la query"""
        if not self.enabled:
            return False
        
        # Gestisce query di tipo documento e ricerche in documenti
        return query_type in ['document', 'pdf', 'file', 'content']
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Elabora una query relativa ai documenti
        
        Args:
            query: Query da elaborare
            context: Contesto aggiuntivo (può includere percorso documento)
            
        Returns:
            Risultati della ricerca/analisi documenti
        """
        return self.execute_with_stats(self._process_document_query, query, context)
    
    def _process_document_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implementazione interna dell'elaborazione query documenti"""
        
        # Validazione query
        validation = self.validate_query(query)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        try:
            # Determina il tipo di operazione richiesta
            operation_type = self._determine_operation_type(query, context)
            
            if operation_type == 'analyze_document':
                return self._analyze_single_document(query, context)
            elif operation_type == 'search_in_document':
                return self._search_within_document(query, context)
            elif operation_type == 'extract_structured_data':
                return self._extract_structured_data(query, context)
            elif operation_type == 'summarize_document':
                return self._summarize_document(query, context)
            else:
                return self._search_across_documents(query)
                
        except Exception as e:
            logger.error(f"Errore nell'elaborazione query documenti: {e}")
            return {'success': False, 'error': str(e)}
    
    def _determine_operation_type(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Determina il tipo di operazione richiesta"""
        
        # Se c'è un documento specifico nel contesto
        if context and context.get('document_path'):
            if any(keyword in query.lower() for keyword in ['riassumi', 'sommario', 'sintesi']):
                return 'summarize_document'
            elif any(keyword in query.lower() for keyword in ['estrai', 'trova dati', 'tabella', 'numeri']):
                return 'extract_structured_data'
            elif any(keyword in query.lower() for keyword in ['cerca in', 'trova nel documento']):
                return 'search_in_document'
            else:
                return 'analyze_document'
        
        # Ricerca generale nei documenti
        return 'search_across_documents'
    
    def _analyze_single_document(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza un singolo documento"""
        try:
            document_path = context.get('document_path')
            if not document_path:
                return {'success': False, 'error': 'Percorso documento non fornito'}
            
            # Determina il tipo di file
            file_extension = document_path.split('.')[-1].lower()
            if file_extension not in self.supported_types:
                return {'success': False, 'error': f'Tipo file non supportato: {file_extension}'}
            
            # Estrazione contenuto
            extraction_result = self.file_service.extract_text_from_document(document_path, file_extension)
            if not extraction_result.get('success'):
                return extraction_result
            
            extracted_text = extraction_result.get('extracted_text', '')
            metadata = extraction_result.get('metadata', {})
            
            # Analisi del contenuto con LLM
            analysis = self._perform_document_analysis(extracted_text, query, metadata)
            
            result = {
                'title': f'Analisi documento: {document_path.split("/")[-1]}',
                'content': analysis,
                'summary': analysis[:300] + '...' if len(analysis) > 300 else analysis,
                'source_type': 'document_analysis',
                'source_path': document_path,
                'relevance_score': 1.0,
                'metadata': {
                    'document_metadata': metadata,
                    'file_type': file_extension,
                    'text_length': len(extracted_text),
                    'analysis_type': 'single_document'
                }
            }
            
            return self.format_results([result], query)
            
        except Exception as e:
            logger.error(f"Errore nell'analisi documento: {e}")
            return {'success': False, 'error': str(e)}
    
    def _search_within_document(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Cerca all'interno di un documento specifico"""
        try:
            document_path = context.get('document_path')
            if not document_path:
                return {'success': False, 'error': 'Percorso documento non fornito'}
            
            # Cerca chunks del documento nel database vettoriale
            # Filtra per documento specifico
            query_embedding = self.embedding_service.generate_text_embedding(query)
            
            search_results = self.vector_service.search_vectors(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                top_k=self.max_results * 2,  # Prende più risultati per filtrare
                threshold=self.similarity_threshold
            )
            
            # Filtra risultati per il documento specifico
            document_results = [
                result for result in search_results
                if result.get('metadata', {}).get('source_path') == document_path
            ]
            
            # Formattazione risultati
            formatted_results = []
            for result in document_results[:self.max_results]:
                metadata = result.get('metadata', {})
                formatted_result = {
                    'title': f"Sezione documento (Chunk {metadata.get('chunk_id', 'N/A')})",
                    'content': result.get('text', ''),
                    'summary': result.get('text', '')[:200] + '...',
                    'source_type': 'document_chunk',
                    'source_path': document_path,
                    'relevance_score': result.get('score', 0.0),
                    'metadata': metadata
                }
                formatted_results.append(formatted_result)
            
            return self.format_results(formatted_results, query)
            
        except Exception as e:
            logger.error(f"Errore nella ricerca nel documento: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_structured_data(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Estrae dati strutturati da un documento"""
        try:
            document_path = context.get('document_path')
            if not document_path:
                return {'success': False, 'error': 'Percorso documento non fornito'}
            
            # Estrazione contenuto
            file_extension = document_path.split('.')[-1].lower()
            extraction_result = self.file_service.extract_text_from_document(document_path, file_extension)
            
            if not extraction_result.get('success'):
                return extraction_result
            
            extracted_text = extraction_result.get('extracted_text', '')
            
            # Prompt per estrazione dati strutturati
            extraction_prompt = f"""
Analizza questo documento e estrai i dati strutturati richiesti nella query.

Query: {query}

Contenuto documento:
{extracted_text[:5000]}  # Limita per evitare token excess

Estrai e organizza i dati in formato strutturato (tabelle, liste, etc.) secondo la richiesta.
Se non trovi i dati richiesti, indica cosa hai trovato di simile.
"""
            
            structured_data = self.llm_service.generate_response(
                extraction_prompt,
                system_prompt="Sei un esperto nell'estrazione di dati strutturati da documenti. Organizza le informazioni in modo chiaro e preciso."
            )
            
            result = {
                'title': f'Dati estratti da: {document_path.split("/")[-1]}',
                'content': structured_data,
                'summary': structured_data[:200] + '...' if len(structured_data) > 200 else structured_data,
                'source_type': 'structured_extraction',
                'source_path': document_path,
                'relevance_score': 1.0,
                'metadata': {
                    'extraction_type': 'structured_data',
                    'file_type': file_extension,
                    'query': query
                }
            }
            
            return self.format_results([result], query)
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione dati strutturati: {e}")
            return {'success': False, 'error': str(e)}
    
    def _summarize_document(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Riassume un documento"""
        try:
            document_path = context.get('document_path')
            if not document_path:
                return {'success': False, 'error': 'Percorso documento non fornito'}
            
            # Estrazione contenuto
            file_extension = document_path.split('.')[-1].lower()
            extraction_result = self.file_service.extract_text_from_document(document_path, file_extension)
            
            if not extraction_result.get('success'):
                return extraction_result
            
            extracted_text = extraction_result.get('extracted_text', '')
            metadata = extraction_result.get('metadata', {})
            
            # Se il documento è molto lungo, riassumi per chunks
            if len(extracted_text) > 8000:
                summary = self._summarize_long_document(extracted_text, query)
            else:
                summary = self._summarize_short_document(extracted_text, query)
            
            result = {
                'title': f'Riassunto: {document_path.split("/")[-1]}',
                'content': summary,
                'summary': summary[:300] + '...' if len(summary) > 300 else summary,
                'source_type': 'document_summary',
                'source_path': document_path,
                'relevance_score': 1.0,
                'metadata': {
                    'document_metadata': metadata,
                    'file_type': file_extension,
                    'original_length': len(extracted_text),
                    'summary_length': len(summary)
                }
            }
            
            return self.format_results([result], query)
            
        except Exception as e:
            logger.error(f"Errore nel riassunto documento: {e}")
            return {'success': False, 'error': str(e)}
    
    def _search_across_documents(self, query: str) -> Dict[str, Any]:
        """Cerca attraverso tutti i documenti nella knowledge base"""
        try:
            # Genera embedding per la query
            query_embedding = self.embedding_service.generate_text_embedding(query)
            
            # Ricerca nel database vettoriale
            search_results = self.vector_service.search_vectors(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                top_k=self.max_results,
                threshold=self.similarity_threshold
            )
            
            # Raggruppa risultati per documento
            document_groups = {}
            for result in search_results:
                metadata = result.get('metadata', {})
                source_path = metadata.get('source_path', 'unknown')
                
                if source_path not in document_groups:
                    document_groups[source_path] = []
                document_groups[source_path].append(result)
            
            # Formatta risultati raggruppati
            formatted_results = []
            for source_path, chunks in document_groups.items():
                # Prende il chunk più rilevante per documento
                best_chunk = max(chunks, key=lambda x: x.get('score', 0))
                metadata = best_chunk.get('metadata', {})
                
                # Combina contenuto di chunks multipli se disponibili
                combined_content = ""
                for chunk in chunks[:3]:  # Massimo 3 chunks per documento
                    combined_content += chunk.get('text', '') + "\n\n"
                
                formatted_result = {
                    'title': metadata.get('title', source_path.split('/')[-1] if source_path != 'unknown' else 'Documento'),
                    'content': combined_content.strip(),
                    'summary': best_chunk.get('text', '')[:200] + '...',
                    'source_type': 'document',
                    'source_path': source_path,
                    'relevance_score': best_chunk.get('score', 0.0),
                    'metadata': {
                        **metadata,
                        'chunks_found': len(chunks),
                        'best_chunk_id': metadata.get('chunk_id')
                    }
                }
                formatted_results.append(formatted_result)
            
            # Ordina per rilevanza
            formatted_results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return self.format_results(formatted_results, query)
            
        except Exception as e:
            logger.error(f"Errore nella ricerca tra documenti: {e}")
            return {'success': False, 'error': str(e)}
    
    def _perform_document_analysis(self, text: str, query: str, metadata: Dict[str, Any]) -> str:
        """Esegue analisi approfondita di un documento"""
        
        analysis_prompt = f"""
Analizza questo documento in base alla seguente richiesta: {query}

Metadati documento:
- Titolo: {metadata.get('title', 'N/A')}
- Autore: {metadata.get('author', 'N/A')}
- Pagine: {metadata.get('page_count', 'N/A')}

Contenuto documento:
{text[:6000]}  # Primi 6000 caratteri

Fornisci un'analisi completa che includa:
1. Panoramica generale del documento
2. Argomenti principali trattati
3. Struttura e organizzazione
4. Punti chiave e informazioni rilevanti
5. Risposta specifica alla query se applicabile
"""
        
        return self.llm_service.generate_response(
            analysis_prompt,
            system_prompt="Sei un esperto analista di documenti. Fornisci analisi dettagliate e strutturate."
        )
    
    def _summarize_long_document(self, text: str, query: str) -> str:
        """Riassume un documento lungo usando chunking"""
        
        # Divide il documento in chunks
        chunks = self.file_service.chunk_document_text(text, self.chunk_size, self.chunk_overlap)
        
        # Riassume ogni chunk
        chunk_summaries = []
        for i, chunk in enumerate(chunks[:10]):  # Limita a 10 chunks per performance
            chunk_prompt = f"""
Riassumi questo segmento del documento (parte {i+1} di {len(chunks)}):

{chunk}

Fornisci un riassunto conciso dei punti principali.
"""
            
            chunk_summary = self.llm_service.generate_response(
                chunk_prompt,
                system_prompt="Riassumi in modo conciso mantenendo le informazioni chiave."
            )
            chunk_summaries.append(chunk_summary)
        
        # Combina i riassunti dei chunks
        combined_summaries = "\n\n".join(chunk_summaries)
        
        # Riassunto finale
        final_prompt = f"""
Basandoti su questi riassunti di sezioni del documento, crea un riassunto finale completo:

{combined_summaries}

Query originale: {query}

Fornisci un riassunto strutturato e coerente dell'intero documento.
"""
        
        return self.llm_service.generate_response(
            final_prompt,
            system_prompt="Crea riassunti finali coerenti e ben strutturati."
        )
    
    def _summarize_short_document(self, text: str, query: str) -> str:
        """Riassume un documento breve"""
        
        summary_prompt = f"""
Riassumi questo documento in base alla seguente richiesta: {query}

Contenuto documento:
{text}

Fornisci un riassunto strutturato che evidenzi:
1. Argomento principale
2. Punti chiave
3. Conclusioni o risultati
4. Informazioni rilevanti per la query
"""
        
        return self.llm_service.generate_response(
            summary_prompt,
            system_prompt="Crea riassunti accurati e informativi."
        )
    
    def add_document_to_knowledge_base(self, document_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Aggiunge un documento alla knowledge base
        
        Args:
            document_path: Percorso del documento
            metadata: Metadati associati
            
        Returns:
            True se aggiunto con successo
        """
        try:
            # Determina tipo file
            file_extension = document_path.split('.')[-1].lower()
            if file_extension not in self.supported_types:
                logger.error(f"Tipo file non supportato: {file_extension}")
                return False
            
            # Estrazione contenuto
            extraction_result = self.file_service.extract_text_from_document(document_path, file_extension)
            if not extraction_result.get('success'):
                logger.error(f"Errore nell'estrazione contenuto: {extraction_result.get('error')}")
                return False
            
            extracted_text = extraction_result.get('extracted_text', '')
            doc_metadata = extraction_result.get('metadata', {})
            
            # Chunking del testo
            chunks = self.file_service.chunk_document_text(extracted_text, self.chunk_size, self.chunk_overlap)
            
            # Generazione embeddings
            embeddings = self.embedding_service.generate_batch_embeddings(chunks)
            
            # Preparazione metadati per ogni chunk
            chunk_metadatas = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy() if metadata else {}
                chunk_metadata.update({
                    'source_path': document_path,
                    'file_type': file_extension,
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'chunk_text_length': len(chunk),
                    **doc_metadata  # Metadati del documento
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
                logger.info(f"Documento aggiunto alla knowledge base: {document_path} ({len(chunks)} chunks)")
            
            return success
            
        except Exception as e:
            logger.error(f"Errore nell'aggiunta documento alla knowledge base: {e}")
            return False
    
    def _ensure_collection_exists(self):
        """Assicura che la collezione per i documenti esista"""
        try:
            collections = self.vector_service.list_collections()
            
            if self.collection_name not in collections:
                success = self.vector_service.create_collection(
                    collection_name=self.collection_name,
                    dimension=3072,
                    description="Collezione per embeddings di documenti e contenuti testuali"
                )
                
                if success:
                    logger.info(f"Collezione {self.collection_name} creata con successo")
                else:
                    logger.error(f"Errore nella creazione della collezione {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Errore nella verifica/creazione collezione documenti: {e}")
