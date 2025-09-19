"""
Controller principale per orchestrare la ricerca attraverso gli agenti AI
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import concurrent.futures

from app.agents import TextAgent, ImageAgent, DocumentAgent, WebAgent, SynthesisAgent
from app.services import LLMService, EmbeddingService, VectorService, FileService

logger = logging.getLogger(__name__)

class SearchController:
    """Controller principale per orchestrare ricerche multi-agente"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inizializza il controller di ricerca
        
        Args:
            config: Configurazione dell'applicazione
        """
        self.config = config
        
        # Inizializza servizi
        self.llm_service = LLMService(config.get('llm', {}))
        self.embedding_service = EmbeddingService(config.get('embedding', {}))
        self.vector_service = VectorService(config.get('vector_db', {}))
        self.file_service = FileService(config.get('file_service', {}))
        
        # Inizializza agenti
        self.agents = self._initialize_agents()
        
        # Configurazioni controller
        self.max_parallel_agents = config.get('max_parallel_agents', 3)
        self.enable_synthesis = config.get('enable_synthesis', True)
        self.timeout_seconds = config.get('agent_timeout', 60)
        
        logger.info(f"SearchController inizializzato con {len(self.agents)} agenti")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Inizializza tutti gli agenti AI"""
        
        agents = {}
        
        try:
            # TextAgent
            text_config = self.config.get('agents', {}).get('text', {})
            agents['text'] = TextAgent(
                text_config, 
                self.llm_service, 
                self.embedding_service, 
                self.vector_service
            )
            
            # ImageAgent
            image_config = self.config.get('agents', {}).get('image', {})
            agents['image'] = ImageAgent(
                image_config,
                self.llm_service,
                self.embedding_service, 
                self.vector_service,
                self.file_service
            )
            
            # DocumentAgent
            document_config = self.config.get('agents', {}).get('document', {})
            agents['document'] = DocumentAgent(
                document_config,
                self.llm_service,
                self.embedding_service,
                self.vector_service,
                self.file_service
            )
            
            # WebAgent
            web_config = self.config.get('agents', {}).get('web', {})
            agents['web'] = WebAgent(
                web_config,
                self.llm_service,
                self.embedding_service,
                self.vector_service
            )
            
            # SynthesisAgent
            synthesis_config = self.config.get('agents', {}).get('synthesis', {})
            agents['synthesis'] = SynthesisAgent(
                synthesis_config,
                self.llm_service,
                self.embedding_service,
                self.vector_service
            )
            
            logger.info("Tutti gli agenti inizializzati con successo")
            
        except Exception as e:
            logger.error(f"Errore nell'inizializzazione agenti: {e}")
            raise
        
        return agents
    
    async def search(self, query: str, search_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Esegue ricerca completa utilizzando agenti appropriati
        
        Args:
            query: Query di ricerca
            search_options: Opzioni di ricerca (agenti da usare, filtri, etc.)
            
        Returns:
            Risultati aggregati della ricerca
        """
        
        start_time = datetime.now()
        
        try:
            # Validazione input
            if not query or not query.strip():
                return {
                    'success': False,
                    'error': 'Query vuota o non valida',
                    'timestamp': start_time.isoformat()
                }
            
            # Analisi della query per determinare agenti appropriati
            query_analysis = await self._analyze_query(query, search_options)
            
            # Selezione agenti
            selected_agents = self._select_agents(query_analysis, search_options)
            
            if not selected_agents:
                return {
                    'success': False,
                    'error': 'Nessun agente disponibile per questa query',
                    'timestamp': start_time.isoformat()
                }
            
            # Esecuzione parallela degli agenti
            agent_results = await self._execute_agents_parallel(query, selected_agents, search_options)
            
            # Sintesi risultati se abilitata
            final_results = agent_results
            if self.enable_synthesis and len(agent_results) > 1:
                synthesis_result = await self._synthesize_results(query, agent_results)
                if synthesis_result.get('success'):
                    final_results['synthesis'] = synthesis_result
            
            # Calcola tempo totale
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Prepara risposta finale
            response = {
                'success': True,
                'query': query,
                'results': final_results,
                'query_analysis': query_analysis,
                'agents_used': list(selected_agents.keys()),
                'processing_time': processing_time,
                'timestamp': start_time.isoformat(),
                'total_results': sum(len(r.get('results', [])) for r in final_results.values() if isinstance(r, dict))
            }
            
            logger.info(f"Ricerca completata in {processing_time:.2f}s - Query: {query[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Errore nella ricerca: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'timestamp': start_time.isoformat(),
                'processing_time': (datetime.now() - start_time).total_seconds()
            }
    
    async def _analyze_query(self, query: str, search_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Analizza la query per determinare intenti e tipi di ricerca"""
        
        try:
            # Usa LLM per analizzare la query
            analysis = self.llm_service.analyze_query_intent(query)
            
            # Aggiunge informazioni dalle opzioni di ricerca
            if search_options:
                analysis.update({
                    'forced_agents': search_options.get('agents', []),
                    'exclude_agents': search_options.get('exclude_agents', []),
                    'search_scope': search_options.get('scope', 'all'),
                    'max_results': search_options.get('max_results', 10)
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Errore nell'analisi query: {e}")
            return {
                'query_type': 'general',
                'complexity': 'medium',
                'confidence': 0.5,
                'keywords': query.split()[:5]
            }
    
    def _select_agents(self, query_analysis: Dict[str, Any], search_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Seleziona gli agenti appropriati per la query"""
        
        selected = {}
        
        # Agenti forzati dalle opzioni
        forced_agents = query_analysis.get('forced_agents', [])
        if forced_agents:
            for agent_name in forced_agents:
                if agent_name in self.agents and self.agents[agent_name].enabled:
                    selected[agent_name] = self.agents[agent_name]
            return selected
        
        # Agenti da escludere
        excluded_agents = set(query_analysis.get('exclude_agents', []))
        
        # Selezione automatica basata su analisi query
        query_type = query_analysis.get('query_type', 'general')
        query = query_analysis.get('query', '')
        
        # TextAgent - sempre incluso per ricerche generali
        if 'text' not in excluded_agents and self.agents['text'].can_handle_query(query, query_type):
            selected['text'] = self.agents['text']
        
        # ImageAgent - per query visuali o multimodali
        if ('image' not in excluded_agents and 
            (query_type in ['image', 'visual', 'multimodal'] or
             any(keyword in query.lower() for keyword in ['immagine', 'foto', 'visual', 'grafico']))):
            selected['image'] = self.agents['image']
        
        # DocumentAgent - per ricerche in documenti
        if ('document' not in excluded_agents and
            (query_type in ['document', 'pdf', 'file'] or
             any(keyword in query.lower() for keyword in ['documento', 'pdf', 'file', 'report']))):
            selected['document'] = self.agents['document']
        
        # WebAgent - per informazioni attuali o web
        if ('web' not in excluded_agents and
            (query_type in ['web', 'news', 'current'] or
             any(keyword in query.lower() for keyword in ['web', 'online', 'notizie', 'attuale', 'recente']))):
            selected['web'] = self.agents['web']
        
        # Limita numero di agenti paralleli
        if len(selected) > self.max_parallel_agents:
            # Prioritizza agenti basandosi su rilevanza
            agent_priorities = {
                'text': 1,
                'web': 2, 
                'document': 3,
                'image': 4
            }
            
            sorted_agents = sorted(selected.items(), 
                                 key=lambda x: agent_priorities.get(x[0], 999))
            selected = dict(sorted_agents[:self.max_parallel_agents])
        
        logger.info(f"Agenti selezionati: {list(selected.keys())}")
        return selected
    
    async def _execute_agents_parallel(self, query: str, selected_agents: Dict[str, Any], 
                                     search_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Esegue gli agenti selezionati in parallelo"""
        
        results = {}
        
        # Prepara contesto per gli agenti
        context = search_options.copy() if search_options else {}
        
        # Usa ThreadPoolExecutor per esecuzione parallela
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_parallel_agents) as executor:
            
            # Sottomette task per ogni agente
            future_to_agent = {}
            for agent_name, agent in selected_agents.items():
                future = executor.submit(agent.process_query, query, context)
                future_to_agent[future] = agent_name
            
            # Raccoglie risultati con timeout
            for future in concurrent.futures.as_completed(future_to_agent, timeout=self.timeout_seconds):
                agent_name = future_to_agent[future]
                
                try:
                    result = future.result()
                    results[agent_name] = result
                    logger.info(f"Agente {agent_name} completato")
                    
                except Exception as e:
                    logger.error(f"Errore nell'agente {agent_name}: {e}")
                    results[agent_name] = {
                        'success': False,
                        'error': str(e),
                        'agent': agent_name
                    }
        
        return results
    
    async def _synthesize_results(self, query: str, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Sintetizza risultati da multiple agenti"""
        
        try:
            # Filtra risultati validi
            valid_results = {
                agent_name: result 
                for agent_name, result in agent_results.items()
                if result.get('success') and result.get('results')
            }
            
            if len(valid_results) < 2:
                return {'success': False, 'error': 'Risultati insufficienti per sintesi'}
            
            # Usa SynthesisAgent per aggregare
            synthesis_agent = self.agents['synthesis']
            synthesis_result = synthesis_agent.synthesize_multi_agent_results(query, valid_results)
            
            return synthesis_result
            
        except Exception as e:
            logger.error(f"Errore nella sintesi risultati: {e}")
            return {'success': False, 'error': str(e)}
    
    def upload_file(self, file_data: bytes, filename: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Carica e elabora un file per aggiungerlo alla knowledge base
        
        Args:
            file_data: Dati binari del file
            filename: Nome originale del file
            user_id: ID dell'utente (opzionale)
            
        Returns:
            Risultato dell'upload e elaborazione
        """
        
        try:
            # Salva il file
            file_info = self.file_service.save_uploaded_file(file_data, filename, user_id)
            
            if not file_info.get('success'):
                return file_info
            
            file_path = file_info['file_path']
            file_type = file_info['file_type']
            
            # Determina quale agente usare per l'elaborazione
            success_count = 0
            
            # Elaborazione con DocumentAgent per documenti
            if file_type in ['pdf', 'docx', 'txt', 'xlsx', 'pptx']:
                document_agent = self.agents['document']
                if document_agent.add_document_to_knowledge_base(file_path, file_info):
                    success_count += 1
                    logger.info(f"File aggiunto alla knowledge base documenti: {filename}")
            
            # Elaborazione con ImageAgent per immagini
            elif file_type in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                image_agent = self.agents['image']
                if image_agent.add_image_to_knowledge_base(file_path, file_info):
                    success_count += 1
                    logger.info(f"Immagine aggiunta alla knowledge base: {filename}")
            
            # Elaborazione con TextAgent per contenuto testuale estratto
            if file_type in ['pdf', 'docx', 'txt']:
                extraction_result = self.file_service.extract_text_from_document(file_path, file_type)
                if extraction_result.get('success'):
                    text_agent = self.agents['text']
                    if text_agent.add_text_to_knowledge_base(extraction_result['extracted_text'], file_info):
                        success_count += 1
                        logger.info(f"Testo estratto aggiunto alla knowledge base: {filename}")
            
            return {
                'success': success_count > 0,
                'file_info': file_info,
                'processed_by_agents': success_count,
                'message': f'File elaborato con successo da {success_count} agenti'
            }
            
        except Exception as e:
            logger.error(f"Errore nell'upload file: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche di tutti gli agenti"""
        
        stats = {}
        
        for agent_name, agent in self.agents.items():
            try:
                stats[agent_name] = agent.get_stats()
            except Exception as e:
                logger.error(f"Errore nel recupero statistiche {agent_name}: {e}")
                stats[agent_name] = {'error': str(e)}
        
        return stats
    
    def reset_agent_stats(self) -> Dict[str, bool]:
        """Resetta le statistiche di tutti gli agenti"""
        
        results = {}
        
        for agent_name, agent in self.agents.items():
            try:
                agent.reset_stats()
                results[agent_name] = True
            except Exception as e:
                logger.error(f"Errore nel reset statistiche {agent_name}: {e}")
                results[agent_name] = False
        
        return results
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica lo stato di salute del sistema"""
        
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'agents': {}
        }
        
        # Verifica servizi
        try:
            # Test LLM Service
            test_response = self.llm_service.generate_response("Test", max_tokens=10)
            health['services']['llm'] = {'status': 'ok' if test_response else 'error'}
        except Exception as e:
            health['services']['llm'] = {'status': 'error', 'error': str(e)}
        
        try:
            # Test Embedding Service
            test_embedding = self.embedding_service.generate_text_embedding("test")
            health['services']['embedding'] = {'status': 'ok' if test_embedding else 'error'}
        except Exception as e:
            health['services']['embedding'] = {'status': 'error', 'error': str(e)}
        
        try:
            # Test Vector Service
            collections = self.vector_service.list_collections()
            health['services']['vector_db'] = {'status': 'ok', 'collections': len(collections)}
        except Exception as e:
            health['services']['vector_db'] = {'status': 'error', 'error': str(e)}
        
        # Verifica agenti
        for agent_name, agent in self.agents.items():
            health['agents'][agent_name] = {
                'enabled': agent.enabled,
                'capabilities': agent.get_capabilities()
            }
        
        # Determina stato generale
        service_errors = [s for s in health['services'].values() if s.get('status') == 'error']
        if service_errors:
            health['status'] = 'degraded' if len(service_errors) < len(health['services']) else 'unhealthy'
        
        return health
