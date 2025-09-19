"""
Agente specializzato per la sintesi e aggregazione di risultati da multiple fonti
"""

import logging
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class SynthesisAgent(BaseAgent):
    """Agente specializzato per sintetizzare e aggregare risultati da diversi agenti"""
    
    def __init__(self, config: Dict[str, Any], llm_service, embedding_service, vector_service):
        super().__init__("SynthesisAgent", config, llm_service, embedding_service, vector_service)
        
        # Configurazioni specifiche per sintesi
        self.max_sources = config.get('max_sources', 20)
        self.min_confidence = config.get('min_confidence', 0.3)
        self.synthesis_depth = config.get('synthesis_depth', 'comprehensive')  # basic, standard, comprehensive
        
    def get_capabilities(self) -> List[str]:
        """Restituisce le capacità dell'agente di sintesi"""
        return [
            'result_aggregation',
            'cross_source_synthesis',
            'information_consolidation',
            'conflict_resolution',
            'comprehensive_reporting',
            'source_attribution'
        ]
    
    def can_handle_query(self, query: str, query_type: str) -> bool:
        """L'agente di sintesi può gestire qualsiasi tipo di query per aggregazione"""
        return self.enabled
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Elabora e sintetizza risultati da multiple fonti
        
        Args:
            query: Query originale
            context: Contesto con risultati da altri agenti
            
        Returns:
            Risultati sintetizzati e aggregati
        """
        return self.execute_with_stats(self._process_synthesis_query, query, context)
    
    def _process_synthesis_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implementazione interna della sintesi"""
        
        # Validazione query
        validation = self.validate_query(query)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        try:
            # Estrae risultati dal contesto
            agent_results = context.get('agent_results', {}) if context else {}
            
            if not agent_results:
                return {'success': False, 'error': 'Nessun risultato da sintetizzare'}
            
            # Preprocessa e normalizza i risultati
            normalized_results = self._normalize_agent_results(agent_results)
            
            # Filtra risultati per qualità e rilevanza
            filtered_results = self._filter_results_by_quality(normalized_results, query)
            
            # Risolve conflitti tra fonti diverse
            resolved_results = self._resolve_conflicts(filtered_results, query)
            
            # Genera sintesi completa
            synthesis = self._generate_comprehensive_synthesis(query, resolved_results)
            
            # Crea report finale strutturato
            final_report = self._create_final_report(query, synthesis, resolved_results)
            
            return self.format_results([final_report], query)
            
        except Exception as e:
            logger.error(f"Errore nella sintesi risultati: {e}")
            return {'success': False, 'error': str(e)}
    
    def synthesize_multi_agent_results(self, query: str, agent_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Metodo pubblico per sintetizzare risultati da multiple agenti
        
        Args:
            query: Query originale
            agent_results: Dizionario con risultati per agente
            
        Returns:
            Sintesi completa
        """
        context = {'agent_results': agent_results}
        return self.process_query(query, context)
    
    def _normalize_agent_results(self, agent_results: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalizza risultati da diversi agenti in formato uniforme"""
        
        normalized = []
        
        for agent_name, agent_data in agent_results.items():
            if not agent_data.get('results'):
                continue
            
            for result in agent_data['results']:
                normalized_result = {
                    'agent_source': agent_name,
                    'title': result.get('title', 'Risultato senza titolo'),
                    'content': result.get('content', ''),
                    'summary': result.get('summary', ''),
                    'source_type': result.get('source_type', 'unknown'),
                    'source_url': result.get('source_url'),
                    'source_path': result.get('source_path'),
                    'relevance_score': result.get('relevance_score', 0.0),
                    'confidence_score': result.get('confidence_score', 0.5),
                    'metadata': result.get('metadata', {}),
                    'agent_processing_time': agent_data.get('processing_time', 0)
                }
                normalized.append(normalized_result)
        
        logger.info(f"Normalizzati {len(normalized)} risultati da {len(agent_results)} agenti")
        return normalized
    
    def _filter_results_by_quality(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filtra risultati basandosi su qualità e rilevanza"""
        
        filtered = []
        
        for result in results:
            # Filtri di qualità
            relevance_score = result.get('relevance_score', 0.0)
            confidence_score = result.get('confidence_score', 0.5)
            content_length = len(result.get('content', ''))
            
            # Criteri di filtro
            if (relevance_score >= self.min_confidence and 
                confidence_score >= self.min_confidence and 
                content_length > 50):  # Contenuto minimo
                
                # Calcola score combinato
                combined_score = (relevance_score + confidence_score) / 2
                result['combined_quality_score'] = combined_score
                
                filtered.append(result)
        
        # Ordina per qualità e limita numero
        filtered.sort(key=lambda x: x.get('combined_quality_score', 0), reverse=True)
        filtered = filtered[:self.max_sources]
        
        logger.info(f"Filtrati {len(filtered)} risultati di qualità da {len(results)} totali")
        return filtered
    
    def _resolve_conflicts(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Risolve conflitti e contraddizioni tra fonti diverse"""
        
        if len(results) <= 1:
            return results
        
        try:
            # Raggruppa risultati per argomento/contenuto simile
            content_groups = self._group_similar_content(results)
            
            resolved_results = []
            
            for group in content_groups:
                if len(group) == 1:
                    # Nessun conflitto, aggiunge direttamente
                    resolved_results.append(group[0])
                else:
                    # Risolve conflitti nel gruppo
                    resolved_result = self._resolve_group_conflicts(group, query)
                    if resolved_result:
                        resolved_results.append(resolved_result)
            
            return resolved_results
            
        except Exception as e:
            logger.error(f"Errore nella risoluzione conflitti: {e}")
            return results  # Fallback ai risultati originali
    
    def _group_similar_content(self, results: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Raggruppa risultati con contenuto simile"""
        
        groups = []
        used_indices = set()
        
        for i, result1 in enumerate(results):
            if i in used_indices:
                continue
            
            current_group = [result1]
            used_indices.add(i)
            
            # Trova risultati simili
            for j, result2 in enumerate(results[i+1:], i+1):
                if j in used_indices:
                    continue
                
                # Calcola similarità basata su contenuto
                similarity = self._calculate_content_similarity(
                    result1.get('content', ''), 
                    result2.get('content', '')
                )
                
                if similarity > 0.7:  # Soglia di similarità
                    current_group.append(result2)
                    used_indices.add(j)
            
            groups.append(current_group)
        
        return groups
    
    def _calculate_content_similarity(self, content1: str, content2: str) -> float:
        """Calcola similarità tra due contenuti (implementazione semplificata)"""
        
        if not content1 or not content2:
            return 0.0
        
        # Tokenizzazione semplice
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _resolve_group_conflicts(self, group: List[Dict[str, Any]], query: str) -> Optional[Dict[str, Any]]:
        """Risolve conflitti all'interno di un gruppo di risultati simili"""
        
        try:
            # Prepara contenuti per l'analisi
            contents = []
            for result in group:
                content_info = {
                    'agent': result.get('agent_source'),
                    'source': result.get('source_type'),
                    'content': result.get('content', ''),
                    'score': result.get('combined_quality_score', 0)
                }
                contents.append(content_info)
            
            # Prompt per risoluzione conflitti
            conflict_resolution_prompt = f"""
Analizza questi contenuti che trattano lo stesso argomento e risolvi eventuali conflitti o contraddizioni.

Query originale: "{query}"

Contenuti da analizzare:
"""
            
            for i, content in enumerate(contents, 1):
                conflict_resolution_prompt += f"""
--- Fonte {i} (Agente: {content['agent']}, Tipo: {content['source']}) ---
{content['content'][:1000]}

"""
            
            conflict_resolution_prompt += """
Fornisci una sintesi che:
1. Risolva eventuali contraddizioni
2. Integri le informazioni complementari
3. Indichi il livello di affidabilità
4. Citi le fonti più autorevoli

Mantieni un approccio obiettivo e bilanciato.
"""
            
            resolved_content = self.llm_service.generate_response(
                conflict_resolution_prompt,
                system_prompt="Sei un esperto nell'analisi critica e risoluzione di conflitti informativi."
            )
            
            # Crea risultato risolto
            best_result = max(group, key=lambda x: x.get('combined_quality_score', 0))
            
            resolved_result = {
                'agent_source': 'SynthesisAgent',
                'title': f"Sintesi: {best_result.get('title', 'Informazioni aggregate')}",
                'content': resolved_content,
                'summary': resolved_content[:300] + '...' if len(resolved_content) > 300 else resolved_content,
                'source_type': 'conflict_resolution',
                'relevance_score': max(r.get('relevance_score', 0) for r in group),
                'confidence_score': sum(r.get('confidence_score', 0) for r in group) / len(group),
                'metadata': {
                    'sources_count': len(group),
                    'source_agents': [r.get('agent_source') for r in group],
                    'resolution_type': 'conflict_resolution'
                }
            }
            
            return resolved_result
            
        except Exception as e:
            logger.error(f"Errore nella risoluzione conflitti gruppo: {e}")
            # Fallback: restituisce il risultato con score migliore
            return max(group, key=lambda x: x.get('combined_quality_score', 0))
    
    def _generate_comprehensive_synthesis(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Genera una sintesi completa di tutti i risultati"""
        
        if not results:
            return "Nessuna informazione disponibile per la query fornita."
        
        try:
            # Prepara contesto per la sintesi
            synthesis_context = f"Query: {query}\n\nInformazioni raccolte:\n\n"
            
            for i, result in enumerate(results, 1):
                synthesis_context += f"""
--- Fonte {i}: {result.get('agent_source')} ({result.get('source_type')}) ---
Titolo: {result.get('title')}
Contenuto: {result.get('content')[:1500]}
Rilevanza: {result.get('relevance_score', 0):.2f}

"""
            
            # Determina il tipo di sintesi basato sulla configurazione
            if self.synthesis_depth == 'basic':
                synthesis_prompt = self._get_basic_synthesis_prompt(query, synthesis_context)
            elif self.synthesis_depth == 'comprehensive':
                synthesis_prompt = self._get_comprehensive_synthesis_prompt(query, synthesis_context)
            else:  # standard
                synthesis_prompt = self._get_standard_synthesis_prompt(query, synthesis_context)
            
            synthesis = self.llm_service.generate_response(
                synthesis_prompt,
                system_prompt="Sei un esperto ricercatore che sintetizza informazioni da multiple fonti in modo accurato e completo."
            )
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Errore nella generazione sintesi: {e}")
            return "Errore nella generazione della sintesi completa."
    
    def _get_basic_synthesis_prompt(self, query: str, context: str) -> str:
        """Prompt per sintesi di base"""
        return f"""
Basandoti sulle informazioni raccolte, fornisci una risposta concisa alla query.

{context}

Fornisci una risposta diretta e sintetica (massimo 200 parole) che risponda alla query "{query}".
Includi solo le informazioni più rilevanti e cita le fonti principali.
"""
    
    def _get_standard_synthesis_prompt(self, query: str, context: str) -> str:
        """Prompt per sintesi standard"""
        return f"""
Analizza le informazioni raccolte e crea una sintesi strutturata per rispondere alla query.

{context}

Crea una sintesi che includa:
1. Risposta diretta alla query
2. Punti chiave dalle diverse fonti
3. Eventuali prospettive diverse o contraddizioni
4. Conclusioni basate sull'evidenza

Mantieni un approccio bilanciato e cita le fonti quando appropriato.
"""
    
    def _get_comprehensive_synthesis_prompt(self, query: str, context: str) -> str:
        """Prompt per sintesi completa"""
        return f"""
Crea un'analisi completa e approfondita basata su tutte le informazioni raccolte.

{context}

Fornisci una sintesi completa che includa:

1. **Risposta Principale**: Risposta diretta e dettagliata alla query
2. **Analisi delle Fonti**: Valutazione della qualità e affidabilità delle diverse fonti
3. **Punti di Convergenza**: Dove le fonti sono d'accordo
4. **Divergenze e Contraddizioni**: Eventuali discrepanze e loro possibili spiegazioni
5. **Contesto e Background**: Informazioni di contesto rilevanti
6. **Implicazioni**: Cosa significano queste informazioni nel contesto più ampio
7. **Limitazioni**: Eventuali lacune o limitazioni nelle informazioni disponibili
8. **Conclusioni**: Sintesi finale basata sull'evidenza

Usa un approccio accademico e rigoroso, citando specificamente le fonti per ogni affermazione.
"""
    
    def _create_final_report(self, query: str, synthesis: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Crea il report finale strutturato"""
        
        # Statistiche sui risultati
        agent_stats = {}
        source_types = {}
        
        for result in results:
            agent = result.get('agent_source', 'unknown')
            source_type = result.get('source_type', 'unknown')
            
            agent_stats[agent] = agent_stats.get(agent, 0) + 1
            source_types[source_type] = source_types.get(source_type, 0) + 1
        
        # Calcola score medio
        avg_relevance = sum(r.get('relevance_score', 0) for r in results) / len(results) if results else 0
        avg_confidence = sum(r.get('confidence_score', 0) for r in results) / len(results) if results else 0
        
        # Crea report finale
        final_report = {
            'title': f'Sintesi Completa: {query}',
            'content': synthesis,
            'summary': synthesis[:400] + '...' if len(synthesis) > 400 else synthesis,
            'source_type': 'comprehensive_synthesis',
            'relevance_score': avg_relevance,
            'confidence_score': avg_confidence,
            'metadata': {
                'query': query,
                'total_sources': len(results),
                'agents_used': list(agent_stats.keys()),
                'agent_statistics': agent_stats,
                'source_type_distribution': source_types,
                'synthesis_depth': self.synthesis_depth,
                'average_relevance': avg_relevance,
                'average_confidence': avg_confidence,
                'synthesis_timestamp': self.stats.get('last_used')
            }
        }
        
        return final_report
    
    def create_executive_summary(self, query: str, synthesis_result: Dict[str, Any]) -> str:
        """Crea un riassunto esecutivo della sintesi"""
        
        try:
            full_content = synthesis_result.get('content', '')
            metadata = synthesis_result.get('metadata', {})
            
            summary_prompt = f"""
Crea un riassunto esecutivo conciso basato su questa sintesi completa.

Query originale: {query}
Fonti utilizzate: {metadata.get('total_sources', 0)}
Agenti coinvolti: {', '.join(metadata.get('agents_used', []))}

Sintesi completa:
{full_content}

Fornisci un riassunto esecutivo (massimo 150 parole) che catturi:
1. La risposta principale alla query
2. I punti chiave più importanti
3. Il livello di affidabilità delle informazioni
"""
            
            executive_summary = self.llm_service.generate_response(
                summary_prompt,
                system_prompt="Crea riassunti esecutivi chiari e informativi per decision makers."
            )
            
            return executive_summary
            
        except Exception as e:
            logger.error(f"Errore nella creazione riassunto esecutivo: {e}")
            return synthesis_result.get('summary', 'Riassunto non disponibile')
