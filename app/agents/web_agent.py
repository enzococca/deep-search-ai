"""
Agente specializzato per la ricerca web e crawling
"""

import logging
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
from .base_agent import BaseAgent

logger = logging.getLogger(__name__)

class WebAgent(BaseAgent):
    """Agente specializzato per ricerca web e crawling di contenuti online"""
    
    def __init__(self, config: Dict[str, Any], llm_service, embedding_service, vector_service):
        super().__init__("WebAgent", config, llm_service, embedding_service, vector_service)
        
        # Configurazioni specifiche per web
        self.collection_name = "web_embeddings"
        self.max_pages = config.get('max_pages', 10)
        self.timeout = config.get('timeout', 30)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.max_results = config.get('max_results', 10)
        
        # Headers per le richieste HTTP
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Inizializza collezione se non esiste
        self._ensure_collection_exists()
    
    def get_capabilities(self) -> List[str]:
        """Restituisce le capacità dell'agente web"""
        return [
            'web_search',
            'content_crawling',
            'real_time_information',
            'news_search',
            'website_analysis',
            'link_extraction'
        ]
    
    def can_handle_query(self, query: str, query_type: str) -> bool:
        """Determina se può gestire la query"""
        if not self.enabled:
            return False
        
        # Gestisce query web e ricerche in tempo reale
        web_keywords = ['web', 'online', 'internet', 'sito', 'notizie', 'attuale', 'recente']
        return (query_type in ['web', 'online', 'news'] or 
                any(keyword in query.lower() for keyword in web_keywords))
    
    def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Elabora una query web
        
        Args:
            query: Query da elaborare
            context: Contesto aggiuntivo (può includere URLs specifici)
            
        Returns:
            Risultati della ricerca web
        """
        return self.execute_with_stats(self._process_web_query, query, context)
    
    def _process_web_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Implementazione interna dell'elaborazione query web"""
        
        # Validazione query
        validation = self.validate_query(query)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        try:
            # Determina il tipo di operazione richiesta
            operation_type = self._determine_operation_type(query, context)
            
            if operation_type == 'crawl_specific_urls':
                return self._crawl_specific_urls(query, context)
            elif operation_type == 'analyze_website':
                return self._analyze_website(query, context)
            elif operation_type == 'news_search':
                return self._search_news(query)
            else:
                return self._general_web_search(query)
                
        except Exception as e:
            logger.error(f"Errore nell'elaborazione query web: {e}")
            return {'success': False, 'error': str(e)}
    
    def _determine_operation_type(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Determina il tipo di operazione web richiesta"""
        
        # Se ci sono URL specifici nel contesto
        if context and context.get('urls'):
            if any(keyword in query.lower() for keyword in ['analizza', 'esamina', 'studia']):
                return 'analyze_website'
            else:
                return 'crawl_specific_urls'
        
        # Ricerca notizie
        if any(keyword in query.lower() for keyword in ['notizie', 'news', 'attualità', 'recenti']):
            return 'news_search'
        
        return 'general_web_search'
    
    def _general_web_search(self, query: str) -> Dict[str, Any]:
        """Esegue una ricerca web generale"""
        try:
            # Genera query di ricerca ottimizzate
            search_queries = self._generate_search_queries(query)
            
            all_results = []
            
            # Esegue ricerca per ogni query
            for search_query in search_queries[:3]:  # Limita a 3 query
                try:
                    # Simula ricerca web (in un'implementazione reale useresti API come Google Custom Search)
                    search_results = self._simulate_web_search(search_query)
                    
                    # Crawl delle pagine trovate
                    for result in search_results[:self.max_pages // len(search_queries)]:
                        crawled_content = self._crawl_page(result['url'])
                        if crawled_content:
                            result.update(crawled_content)
                            all_results.append(result)
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Errore nella ricerca per '{search_query}': {e}")
                    continue
            
            # Filtra e ranking dei risultati
            filtered_results = self._filter_and_rank_results(all_results, query)
            
            # Genera riassunti per i risultati migliori
            enhanced_results = self._enhance_web_results(filtered_results[:self.max_results], query)
            
            return self.format_results(enhanced_results, query)
            
        except Exception as e:
            logger.error(f"Errore nella ricerca web generale: {e}")
            return {'success': False, 'error': str(e)}
    
    def _crawl_specific_urls(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crawl di URL specifici forniti nel contesto"""
        try:
            urls = context.get('urls', [])
            if not urls:
                return {'success': False, 'error': 'Nessun URL fornito'}
            
            results = []
            
            for url in urls[:self.max_pages]:
                try:
                    crawled_content = self._crawl_page(url)
                    if crawled_content:
                        # Analizza il contenuto in relazione alla query
                        analysis = self._analyze_content_for_query(crawled_content['content'], query)
                        
                        result = {
                            'title': crawled_content.get('title', url),
                            'content': crawled_content.get('content', ''),
                            'summary': analysis,
                            'source_type': 'web_crawl',
                            'source_url': url,
                            'relevance_score': self._calculate_relevance_score(crawled_content['content'], query),
                            'metadata': {
                                'url': url,
                                'crawl_timestamp': time.time(),
                                'content_length': len(crawled_content.get('content', ''))
                            }
                        }
                        results.append(result)
                    
                    time.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Errore nel crawling di {url}: {e}")
                    continue
            
            return self.format_results(results, query)
            
        except Exception as e:
            logger.error(f"Errore nel crawling URL specifici: {e}")
            return {'success': False, 'error': str(e)}
    
    def _analyze_website(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analizza un sito web specifico"""
        try:
            urls = context.get('urls', [])
            if not urls:
                return {'success': False, 'error': 'Nessun URL fornito per l\'analisi'}
            
            url = urls[0]  # Analizza il primo URL
            
            # Crawl della pagina principale
            main_content = self._crawl_page(url)
            if not main_content:
                return {'success': False, 'error': f'Impossibile accedere a {url}'}
            
            # Estrazione link interni
            internal_links = self._extract_internal_links(url, main_content.get('raw_html', ''))
            
            # Analisi strutturale del sito
            site_analysis = self._perform_site_analysis(url, main_content, internal_links[:5])
            
            result = {
                'title': f'Analisi sito web: {urlparse(url).netloc}',
                'content': site_analysis,
                'summary': site_analysis[:300] + '...' if len(site_analysis) > 300 else site_analysis,
                'source_type': 'website_analysis',
                'source_url': url,
                'relevance_score': 1.0,
                'metadata': {
                    'main_url': url,
                    'internal_links_found': len(internal_links),
                    'analysis_timestamp': time.time()
                }
            }
            
            return self.format_results([result], query)
            
        except Exception as e:
            logger.error(f"Errore nell'analisi sito web: {e}")
            return {'success': False, 'error': str(e)}
    
    def _search_news(self, query: str) -> Dict[str, Any]:
        """Cerca notizie recenti"""
        try:
            # Genera query specifiche per notizie
            news_queries = [
                f"{query} notizie",
                f"{query} news",
                f"{query} attualità"
            ]
            
            all_results = []
            
            # Simula ricerca notizie (in implementazione reale useresti News API)
            for news_query in news_queries[:2]:
                try:
                    news_results = self._simulate_news_search(news_query)
                    
                    for result in news_results[:5]:
                        crawled_content = self._crawl_page(result['url'])
                        if crawled_content:
                            result.update(crawled_content)
                            result['source_type'] = 'news'
                            all_results.append(result)
                    
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Errore nella ricerca notizie per '{news_query}': {e}")
                    continue
            
            # Ordina per rilevanza e data
            sorted_results = sorted(all_results, key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            return self.format_results(sorted_results[:self.max_results], query)
            
        except Exception as e:
            logger.error(f"Errore nella ricerca notizie: {e}")
            return {'success': False, 'error': str(e)}
    
    def _crawl_page(self, url: str) -> Optional[Dict[str, Any]]:
        """Crawl di una singola pagina web"""
        try:
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parsing HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Rimozione script e style
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Estrazione titolo
            title = soup.find('title')
            title_text = title.get_text().strip() if title else urlparse(url).netloc
            
            # Estrazione contenuto principale
            content = self._extract_main_content(soup)
            
            # Estrazione metadati
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description.get('content', '') if meta_description else ''
            
            return {
                'title': title_text,
                'content': content,
                'description': description,
                'url': url,
                'raw_html': str(soup)
            }
            
        except requests.RequestException as e:
            logger.error(f"Errore HTTP nel crawling di {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Errore nel parsing di {url}: {e}")
            return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Estrae il contenuto principale da una pagina"""
        
        # Prova a trovare contenuto in tag semantici
        main_content = soup.find('main')
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        
        article = soup.find('article')
        if article:
            return article.get_text(separator=' ', strip=True)
        
        # Fallback: cerca div con classi comuni per contenuto
        content_selectors = [
            'div.content',
            'div.main-content',
            'div.post-content',
            'div.entry-content',
            'div.article-content'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                return content_div.get_text(separator=' ', strip=True)
        
        # Ultimo fallback: tutto il body
        body = soup.find('body')
        if body:
            return body.get_text(separator=' ', strip=True)
        
        return soup.get_text(separator=' ', strip=True)
    
    def _generate_search_queries(self, original_query: str) -> List[str]:
        """Genera query di ricerca ottimizzate"""
        try:
            # Usa LLM per generare query alternative
            search_queries = self.llm_service.generate_search_queries(original_query, num_queries=3)
            
            # Aggiunge la query originale
            all_queries = [original_query] + search_queries
            
            return all_queries
            
        except Exception as e:
            logger.error(f"Errore nella generazione query di ricerca: {e}")
            return [original_query]
    
    def _simulate_web_search(self, query: str) -> List[Dict[str, Any]]:
        """Simula risultati di ricerca web (da sostituire con API reale)"""
        
        # In un'implementazione reale, qui useresti Google Custom Search API, Bing API, etc.
        # Per ora, restituisce risultati simulati
        
        simulated_results = [
            {
                'title': f'Risultato per: {query}',
                'url': f'https://example.com/search/{query.replace(" ", "-")}',
                'snippet': f'Informazioni rilevanti su {query}...'
            },
            {
                'title': f'Approfondimento su {query}',
                'url': f'https://wikipedia.org/wiki/{query.replace(" ", "_")}',
                'snippet': f'Articolo enciclopedico su {query}...'
            }
        ]
        
        return simulated_results
    
    def _simulate_news_search(self, query: str) -> List[Dict[str, Any]]:
        """Simula ricerca notizie (da sostituire con News API)"""
        
        simulated_news = [
            {
                'title': f'Ultime notizie su {query}',
                'url': f'https://news.example.com/{query.replace(" ", "-")}',
                'snippet': f'Notizie recenti riguardanti {query}...',
                'published_date': time.time() - 3600  # 1 ora fa
            }
        ]
        
        return simulated_news
    
    def _filter_and_rank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filtra e ordina i risultati per rilevanza"""
        
        # Rimuove duplicati basati su URL
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Calcola score di rilevanza per ogni risultato
        for result in unique_results:
            content = result.get('content', '')
            title = result.get('title', '')
            
            # Score basato su presenza di parole chiave
            relevance_score = self._calculate_relevance_score(content + ' ' + title, query)
            result['relevance_score'] = relevance_score
        
        # Ordina per rilevanza
        unique_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return unique_results
    
    def _calculate_relevance_score(self, content: str, query: str) -> float:
        """Calcola un score di rilevanza semplice"""
        if not content or not query:
            return 0.0
        
        content_lower = content.lower()
        query_words = query.lower().split()
        
        # Conta occorrenze delle parole della query
        total_matches = 0
        for word in query_words:
            if len(word) > 2:  # Ignora parole troppo corte
                total_matches += content_lower.count(word)
        
        # Normalizza per lunghezza del contenuto
        content_length = len(content.split())
        if content_length == 0:
            return 0.0
        
        relevance_score = min(total_matches / content_length * 10, 1.0)
        return relevance_score
    
    def _enhance_web_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Migliora i risultati web con riassunti e analisi"""
        
        enhanced_results = []
        
        for result in results:
            try:
                content = result.get('content', '')
                
                # Genera riassunto se il contenuto è lungo
                if len(content) > 500:
                    summary_prompt = f"""
Riassumi questo contenuto web in relazione alla query: "{query}"

Contenuto:
{content[:2000]}

Fornisci un riassunto conciso (massimo 150 parole) che evidenzi le informazioni più rilevanti.
"""
                    
                    summary = self.llm_service.generate_response(
                        summary_prompt,
                        system_prompt="Riassumi contenuti web in modo accurato e conciso."
                    )
                    
                    result['summary'] = summary
                else:
                    result['summary'] = content
                
                enhanced_results.append(result)
                
            except Exception as e:
                logger.error(f"Errore nel miglioramento risultato web: {e}")
                result['summary'] = result.get('content', '')[:200] + '...'
                enhanced_results.append(result)
        
        return enhanced_results
    
    def _analyze_content_for_query(self, content: str, query: str) -> str:
        """Analizza contenuto web in relazione a una query specifica"""
        
        analysis_prompt = f"""
Analizza questo contenuto web in relazione alla query: "{query}"

Contenuto:
{content[:3000]}

Fornisci un'analisi che evidenzi:
1. Come il contenuto risponde alla query
2. Informazioni chiave rilevanti
3. Punti salienti e conclusioni
"""
        
        try:
            return self.llm_service.generate_response(
                analysis_prompt,
                system_prompt="Analizza contenuti web in modo preciso e pertinente."
            )
        except Exception as e:
            logger.error(f"Errore nell'analisi contenuto: {e}")
            return content[:300] + '...'
    
    def _extract_internal_links(self, base_url: str, html_content: str) -> List[str]:
        """Estrae link interni da una pagina"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            base_domain = urlparse(base_url).netloc
            
            internal_links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Converte link relativi in assoluti
                full_url = urljoin(base_url, href)
                parsed_url = urlparse(full_url)
                
                # Verifica se è un link interno
                if parsed_url.netloc == base_domain:
                    internal_links.append(full_url)
            
            # Rimuove duplicati
            return list(set(internal_links))
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione link interni: {e}")
            return []
    
    def _perform_site_analysis(self, url: str, main_content: Dict[str, Any], internal_links: List[str]) -> str:
        """Esegue analisi strutturale di un sito web"""
        
        analysis_prompt = f"""
Analizza questo sito web e fornisci un report strutturato:

URL principale: {url}
Titolo: {main_content.get('title', 'N/A')}
Descrizione: {main_content.get('description', 'N/A')}

Contenuto principale:
{main_content.get('content', '')[:2000]}

Link interni trovati: {len(internal_links)}

Fornisci un'analisi che includa:
1. Scopo e argomento principale del sito
2. Struttura e organizzazione
3. Qualità e tipo di contenuto
4. Navigazione e usabilità
5. Informazioni chiave disponibili
"""
        
        try:
            return self.llm_service.generate_response(
                analysis_prompt,
                system_prompt="Sei un esperto nell'analisi di siti web. Fornisci analisi dettagliate e strutturate."
            )
        except Exception as e:
            logger.error(f"Errore nell'analisi sito: {e}")
            return f"Analisi del sito {url}: {main_content.get('title', 'Sito web')}"
    
    def _ensure_collection_exists(self):
        """Assicura che la collezione per contenuti web esista"""
        try:
            collections = self.vector_service.list_collections()
            
            if self.collection_name not in collections:
                success = self.vector_service.create_collection(
                    collection_name=self.collection_name,
                    dimension=3072,
                    description="Collezione per embeddings di contenuti web"
                )
                
                if success:
                    logger.info(f"Collezione {self.collection_name} creata con successo")
                else:
                    logger.error(f"Errore nella creazione della collezione {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Errore nella verifica/creazione collezione web: {e}")
