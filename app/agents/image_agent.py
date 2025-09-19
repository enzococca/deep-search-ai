"""
Agente specializzato per la ricerca e analisi di immagini
"""

import logging
from typing import Dict, List, Any, Optional
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class ImageAgent(BaseAgent):
    """Agente specializzato per ricerca e analisi di contenuti visuali"""
    
    def __init__(self, config: Dict[str, Any], llm_service, embedding_service, vector_service, file_service):
        super().__init__("ImageAgent", config, llm_service, embedding_service, vector_service)
        
        self.file_service = file_service
        
        # Configurazioni specifiche per immagini
        self.collection_name = "image_embeddings"
        self.ocr_enabled = config.get('ocr_enabled', True)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.max_results = config.get('max_results', 10)
        
        # Inizializza collezione se non esiste
        self._ensure_collection_exists()
    
    def get_capabilities(self) -> List[str]:
        """Restituisce le capacità dell'agente immagini"""
        return [
            'image_search',
            'visual_analysis',
            'ocr_text_extraction',
            'image_description',
            'visual_similarity',
            'multimodal_search'
        ]
    
    def can_handle_query(self, query: str, query_type: str) -> bool:
        """Determina se può gestire la query"""
        if not self.enabled:
            return False
        
        # Gestisce query di tipo immagine e multimodali
        return query_type in ['image', 'visual', 'multimodal']
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Elabora una query relativa alle immagini
        
        Args:
            query: Query da elaborare
            context: Contesto aggiuntivo (può includere percorso immagine)
            
        Returns:
            Risultati della ricerca/analisi immagini
        """
        return self.execute_with_stats(self._process_image_query, query, context)
    
    def _process_image_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implementazione interna dell'elaborazione query immagini"""
        
        # Validazione query
        validation = self.validate_query(query)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        try:
            # Determina il tipo di operazione richiesta
            operation_type = self._determine_operation_type(query, context)
            
            if operation_type == 'analyze_image':
                return self._analyze_single_image(query, context)
            elif operation_type == 'search_by_description':
                return self._search_images_by_description(query)
            elif operation_type == 'search_by_image':
                return self._search_similar_images(context.get('image_path'))
            elif operation_type == 'extract_text':
                return self._extract_text_from_image(context.get('image_path'))
            else:
                return self._general_image_search(query)
                
        except Exception as e:
            logger.error(f"Errore nell'elaborazione query immagini: {e}")
            return {'success': False, 'error': str(e)}
    
    def _determine_operation_type(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Determina il tipo di operazione richiesta"""
        
        # Se c'è un'immagine nel contesto
        if context and context.get('image_path'):
            if any(keyword in query.lower() for keyword in ['analizza', 'descrivi', 'cosa vedi']):
                return 'analyze_image'
            elif any(keyword in query.lower() for keyword in ['simili', 'trova immagini come']):
                return 'search_by_image'
            elif any(keyword in query.lower() for keyword in ['testo', 'ocr', 'leggi']):
                return 'extract_text'
        
        # Ricerca per descrizione
        if any(keyword in query.lower() for keyword in ['trova immagini', 'cerca foto', 'immagini di']):
            return 'search_by_description'
        
        return 'general_image_search'
    
    def _analyze_single_image(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza una singola immagine"""
        try:
            image_path = context.get('image_path')
            if not image_path:
                return {'success': False, 'error': 'Percorso immagine non fornito'}
            
            # Analisi base dell'immagine
            image_analysis = self.file_service.analyze_image(image_path)
            if not image_analysis.get('success'):
                return image_analysis
            
            # Estrazione testo se OCR abilitato
            ocr_result = None
            if self.ocr_enabled:
                ocr_result = self.file_service.extract_text_from_image(image_path)
            
            # Generazione descrizione con GPT-5V (simulata con descrizione basata su analisi)
            description = self._generate_image_description(image_analysis, ocr_result)
            
            # Estrazione tag e categorie
            tags = self._extract_image_tags(description, ocr_result)
            
            result = {
                'title': 'Analisi Immagine',
                'content': description,
                'summary': description[:200] + '...' if len(description) > 200 else description,
                'source_type': 'image_analysis',
                'source_path': image_path,
                'relevance_score': 1.0,
                'metadata': {
                    'image_info': image_analysis,
                    'ocr_text': ocr_result.get('extracted_text') if ocr_result else None,
                    'tags': tags,
                    'analysis_type': 'single_image'
                }
            }
            
            return self.format_results([result], query)
            
        except Exception as e:
            logger.error(f"Errore nell'analisi immagine: {e}")
            return {'success': False, 'error': str(e)}
    
    def _search_images_by_description(self, query: str) -> Dict[str, Any]:
        """Cerca immagini basandosi su una descrizione testuale"""
        try:
            # Genera embedding per la descrizione
            query_embedding = self.embedding_service.generate_text_embedding(query)
            
            # Ricerca nel database vettoriale delle immagini
            search_results = self.vector_service.search_vectors(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                top_k=self.max_results,
                threshold=self.similarity_threshold
            )
            
            # Formattazione risultati
            formatted_results = []
            for result in search_results:
                metadata = result.get('metadata', {})
                formatted_result = {
                    'title': metadata.get('original_filename', 'Immagine'),
                    'content': result.get('text', ''),  # Descrizione o testo OCR
                    'summary': metadata.get('description', ''),
                    'source_type': 'image',
                    'source_path': metadata.get('file_path'),
                    'relevance_score': result.get('score', 0.0),
                    'metadata': metadata
                }
                formatted_results.append(formatted_result)
            
            return self.format_results(formatted_results, query)
            
        except Exception as e:
            logger.error(f"Errore nella ricerca immagini per descrizione: {e}")
            return {'success': False, 'error': str(e)}
    
    def _search_similar_images(self, image_path: str) -> Dict[str, Any]:
        """Cerca immagini simili a quella fornita"""
        try:
            if not image_path:
                return {'success': False, 'error': 'Percorso immagine non fornito'}
            
            # Analizza l'immagine di riferimento
            image_analysis = self.file_service.analyze_image(image_path)
            if not image_analysis.get('success'):
                return image_analysis
            
            # Genera descrizione per l'embedding
            description = self._generate_image_description(image_analysis)
            
            # Genera embedding
            image_embedding = self.embedding_service.generate_text_embedding(description)
            
            # Ricerca immagini simili
            search_results = self.vector_service.search_vectors(
                collection_name=self.collection_name,
                query_vector=image_embedding,
                top_k=self.max_results,
                threshold=self.similarity_threshold
            )
            
            # Filtra l'immagine originale dai risultati
            filtered_results = [
                result for result in search_results 
                if result.get('metadata', {}).get('file_path') != image_path
            ]
            
            # Formattazione risultati
            formatted_results = []
            for result in filtered_results:
                metadata = result.get('metadata', {})
                formatted_result = {
                    'title': f"Immagine simile: {metadata.get('original_filename', 'Sconosciuta')}",
                    'content': result.get('text', ''),
                    'summary': metadata.get('description', ''),
                    'source_type': 'similar_image',
                    'source_path': metadata.get('file_path'),
                    'relevance_score': result.get('score', 0.0),
                    'metadata': metadata
                }
                formatted_results.append(formatted_result)
            
            return self.format_results(formatted_results, f"Immagini simili a {image_path}")
            
        except Exception as e:
            logger.error(f"Errore nella ricerca immagini simili: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """Estrae testo da un'immagine usando OCR"""
        try:
            if not image_path:
                return {'success': False, 'error': 'Percorso immagine non fornito'}
            
            # Estrazione testo con OCR
            ocr_result = self.file_service.extract_text_from_image(image_path)
            
            if not ocr_result.get('success'):
                return ocr_result
            
            extracted_text = ocr_result.get('extracted_text', '')
            
            # Se il testo è significativo, analizzalo
            analysis = ""
            if len(extracted_text.strip()) > 10:
                analysis_prompt = f"""
Analizza questo testo estratto da un'immagine e fornisci:
1. Un riassunto del contenuto
2. Il tipo di documento/immagine (es. documento, cartello, schermata, etc.)
3. Informazioni chiave estratte

Testo estratto:
{extracted_text}
"""
                
                analysis = self.llm_service.generate_response(
                    analysis_prompt,
                    system_prompt="Sei un esperto nell'analisi di testi estratti da immagini."
                )
            
            result = {
                'title': 'Testo estratto da immagine',
                'content': extracted_text,
                'summary': analysis if analysis else extracted_text[:200],
                'source_type': 'ocr_extraction',
                'source_path': image_path,
                'relevance_score': 1.0 if extracted_text.strip() else 0.1,
                'metadata': {
                    'ocr_result': ocr_result,
                    'text_length': len(extracted_text),
                    'analysis': analysis
                }
            }
            
            return self.format_results([result], f"Estrazione testo da {image_path}")
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione testo da immagine: {e}")
            return {'success': False, 'error': str(e)}
    
    def _general_image_search(self, query: str) -> Dict[str, Any]:
        """Ricerca generale nelle immagini"""
        try:
            # Combina ricerca per descrizione e contenuto OCR
            results = self._search_images_by_description(query)
            
            # Se non ci sono risultati sufficienti, espandi la ricerca
            if results.get('total_results', 0) < 3:
                # Genera query alternative
                alternative_queries = self.llm_service.generate_search_queries(query, num_queries=2)
                
                for alt_query in alternative_queries:
                    alt_results = self._search_images_by_description(alt_query)
                    if alt_results.get('results'):
                        results['results'].extend(alt_results['results'])
                
                # Rimuovi duplicati e rilimita
                results['results'] = self._deduplicate_results(results['results'])[:self.max_results]
                results['total_results'] = len(results['results'])
            
            return results
            
        except Exception as e:
            logger.error(f"Errore nella ricerca generale immagini: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_image_description(self, image_analysis: Dict[str, Any], 
                                  ocr_result: Optional[Dict[str, Any]] = None) -> str:
        """Genera una descrizione dell'immagine basata sull'analisi"""
        
        # Informazioni base
        width = image_analysis.get('width', 0)
        height = image_analysis.get('height', 0)
        format_type = image_analysis.get('format', 'unknown')
        
        # Colori dominanti
        colors = image_analysis.get('dominant_colors', [])
        color_description = ""
        if colors:
            color_names = self._colors_to_names(colors[:3])  # Primi 3 colori
            color_description = f"Colori dominanti: {', '.join(color_names)}. "
        
        # Testo OCR se disponibile
        ocr_text = ""
        if ocr_result and ocr_result.get('extracted_text'):
            text = ocr_result['extracted_text'].strip()
            if text:
                ocr_text = f"Testo presente nell'immagine: {text[:200]}. "
        
        # Costruzione descrizione
        description = f"Immagine {format_type.lower()} di dimensioni {width}x{height} pixel. "
        description += color_description
        description += ocr_text
        
        # Determina il tipo di contenuto basandosi su dimensioni e testo
        if ocr_text:
            if any(keyword in ocr_text.lower() for keyword in ['documento', 'contratto', 'fattura']):
                description += "Sembra essere un documento di testo. "
            elif any(keyword in ocr_text.lower() for keyword in ['menu', 'prezzo', 'euro', '$']):
                description += "Potrebbe essere un menu o listino prezzi. "
            elif len(ocr_text.split()) > 20:
                description += "Contiene una quantità significativa di testo. "
        
        # Analisi dimensioni
        if width > height * 2:
            description += "Formato panoramico orizzontale. "
        elif height > width * 2:
            description += "Formato verticale allungato. "
        elif abs(width - height) < min(width, height) * 0.1:
            description += "Formato quadrato. "
        
        return description.strip()
    
    def _extract_image_tags(self, description: str, ocr_result: Optional[Dict[str, Any]] = None) -> List[str]:
        """Estrae tag dall'immagine basandosi su descrizione e OCR"""
        try:
            tag_prompt = f"""
Basandoti su questa descrizione di un'immagine, estrai tag rilevanti per la categorizzazione e ricerca.

Descrizione: {description}

Testo OCR: {ocr_result.get('extracted_text', 'Nessun testo') if ocr_result else 'Nessun testo'}

Fornisci una lista di tag separati da virgole (massimo 10 tag).
Includi: tipo di contenuto, colori principali, oggetti visibili, categoria generale.
"""
            
            tags_response = self.llm_service.generate_response(
                tag_prompt,
                system_prompt="Sei un esperto nel tagging di immagini per sistemi di ricerca."
            )
            
            # Estrai tag dalla risposta
            tags = [tag.strip() for tag in tags_response.split(',')]
            return tags[:10]  # Limita a 10 tag
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione tag: {e}")
            return ['immagine', 'contenuto_visuale']
    
    def _colors_to_names(self, colors: List[tuple]) -> List[str]:
        """Converte valori RGB in nomi di colori approssimativi"""
        color_names = []
        
        for r, g, b in colors:
            # Logica semplificata per determinare il nome del colore
            if r > 200 and g > 200 and b > 200:
                color_names.append("bianco")
            elif r < 50 and g < 50 and b < 50:
                color_names.append("nero")
            elif r > g and r > b:
                color_names.append("rosso")
            elif g > r and g > b:
                color_names.append("verde")
            elif b > r and b > g:
                color_names.append("blu")
            elif r > 150 and g > 150 and b < 100:
                color_names.append("giallo")
            elif r > 150 and g < 100 and b > 150:
                color_names.append("viola")
            elif r > 150 and g > 100 and b < 100:
                color_names.append("arancione")
            else:
                color_names.append("grigio")
        
        return color_names
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rimuove risultati duplicati"""
        seen_paths = set()
        unique_results = []
        
        for result in results:
            path = result.get('source_path')
            if path and path not in seen_paths:
                seen_paths.add(path)
                unique_results.append(result)
            elif not path:  # Risultati senza path
                unique_results.append(result)
        
        return unique_results
    
    def add_image_to_knowledge_base(self, image_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Aggiunge un'immagine alla knowledge base
        
        Args:
            image_path: Percorso dell'immagine
            metadata: Metadati associati
            
        Returns:
            True se aggiunta con successo
        """
        try:
            # Analisi dell'immagine
            image_analysis = self.file_service.analyze_image(image_path)
            if not image_analysis.get('success'):
                return False
            
            # Estrazione testo se OCR abilitato
            ocr_result = None
            if self.ocr_enabled:
                ocr_result = self.file_service.extract_text_from_image(image_path)
            
            # Generazione descrizione
            description = self._generate_image_description(image_analysis, ocr_result)
            
            # Estrazione tag
            tags = self._extract_image_tags(description, ocr_result)
            
            # Preparazione testo per embedding (descrizione + testo OCR)
            embedding_text = description
            if ocr_result and ocr_result.get('extracted_text'):
                embedding_text += " " + ocr_result['extracted_text']
            
            # Generazione embedding
            embedding = self.embedding_service.generate_text_embedding(embedding_text)
            
            # Preparazione metadati completi
            full_metadata = metadata.copy() if metadata else {}
            full_metadata.update({
                'file_path': image_path,
                'image_info': image_analysis,
                'description': description,
                'tags': tags,
                'ocr_text': ocr_result.get('extracted_text') if ocr_result else None,
                'has_text': bool(ocr_result and ocr_result.get('extracted_text'))
            })
            
            # Inserimento nel database vettoriale
            success = self.vector_service.insert_vectors(
                collection_name=self.collection_name,
                vectors=[embedding],
                texts=[embedding_text],
                metadatas=[full_metadata]
            )
            
            if success:
                logger.info(f"Immagine aggiunta alla knowledge base: {image_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Errore nell'aggiunta immagine alla knowledge base: {e}")
            return False
    
    def _ensure_collection_exists(self):
        """Assicura che la collezione per le immagini esista"""
        try:
            collections = self.vector_service.list_collections()
            
            if self.collection_name not in collections:
                success = self.vector_service.create_collection(
                    collection_name=self.collection_name,
                    dimension=3072,
                    description="Collezione per embeddings di immagini e contenuti visuali"
                )
                
                if success:
                    logger.info(f"Collezione {self.collection_name} creata con successo")
                else:
                    logger.error(f"Errore nella creazione della collezione {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Errore nella verifica/creazione collezione immagini: {e}")
