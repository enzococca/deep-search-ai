"""
Servizio per l'integrazione con Large Language Models (GPT-5, etc.)
"""

import os
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from openai import OpenAI
import json

logger = logging.getLogger(__name__)

class LLMService:
    """Servizio per gestire le interazioni con i Large Language Models"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inizializza il servizio LLM
        
        Args:
            config: Configurazione del servizio LLM
        """
        self.config = config
        self.provider = config.get('provider', 'openai')
        self.model = config.get('model', 'gpt-4o')
        self.temperature = config.get('temperature', 0.1)
        self.max_tokens = config.get('max_tokens', 4000)
        
        # Inizializzazione client OpenAI
        if self.provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("OPENAI_API_KEY non configurata. Il servizio LLM potrebbe non funzionare.")
            
            self.client = OpenAI(api_key=api_key)
        
        logger.info(f"LLM Service inizializzato - Provider: {self.provider}, Model: {self.model}")
    
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Genera una risposta usando il modello LLM
        
        Args:
            prompt: Il prompt dell'utente
            system_prompt: Prompt di sistema opzionale
            **kwargs: Parametri aggiuntivi per il modello
            
        Returns:
            La risposta generata dal modello
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Parametri per la chiamata
            params = {
                "model": kwargs.get('model', self.model),
                "messages": messages,
                "temperature": kwargs.get('temperature', self.temperature),
                "max_tokens": kwargs.get('max_tokens', self.max_tokens)
            }
            
            # Chiamata all'API
            response = self.client.chat.completions.create(**params)
            
            result = response.choices[0].message.content
            
            logger.debug(f"LLM Response generata - Tokens: {response.usage.total_tokens}")
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nella generazione della risposta LLM: {e}")
            raise
    
    def generate_structured_response(self, prompt: str, schema: Dict[str, Any], 
                                   system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Genera una risposta strutturata seguendo uno schema JSON
        
        Args:
            prompt: Il prompt dell'utente
            schema: Schema JSON per la risposta strutturata
            system_prompt: Prompt di sistema opzionale
            
        Returns:
            Risposta strutturata come dizionario
        """
        try:
            # Costruzione del prompt per risposta strutturata
            structured_prompt = f"""
{prompt}

Rispondi SOLO con un JSON valido che segue questo schema:
{json.dumps(schema, indent=2)}

Non includere spiegazioni aggiuntive, solo il JSON.
"""
            
            response = self.generate_response(
                structured_prompt, 
                system_prompt,
                temperature=0.0  # Temperatura bassa per consistenza
            )
            
            # Parsing del JSON
            try:
                result = json.loads(response)
                return result
            except json.JSONDecodeError:
                # Tentativo di estrazione del JSON dalla risposta
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
                else:
                    raise ValueError("Impossibile estrarre JSON valido dalla risposta")
                    
        except Exception as e:
            logger.error(f"Errore nella generazione della risposta strutturata: {e}")
            raise
    
    def analyze_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Analizza l'intento di una query di ricerca
        
        Args:
            query: La query da analizzare
            
        Returns:
            Dizionario con l'analisi dell'intento
        """
        system_prompt = """Sei un esperto nell'analisi di query di ricerca. 
Analizza la query dell'utente e determina:
1. Il tipo di ricerca richiesta
2. Le entità chiave
3. Il livello di complessità
4. Gli agenti più appropriati da utilizzare"""
        
        schema = {
            "query_type": "string (text|image|document|multimodal|web)",
            "entities": ["lista di entità chiave"],
            "complexity": "string (simple|medium|complex)",
            "suggested_agents": ["lista di agenti consigliati"],
            "search_strategy": "string (semantic|keyword|hybrid)",
            "confidence": "number (0-1)"
        }
        
        prompt = f"Analizza questa query di ricerca: '{query}'"
        
        return self.generate_structured_response(prompt, schema, system_prompt)
    
    def generate_search_summary(self, query: str, results: List[Dict[str, Any]]) -> str:
        """
        Genera un riassunto dei risultati di ricerca
        
        Args:
            query: La query originale
            results: Lista dei risultati di ricerca
            
        Returns:
            Riassunto generato
        """
        system_prompt = """Sei un esperto nel sintetizzare informazioni da multiple fonti.
Crea un riassunto completo e accurato basato sui risultati di ricerca forniti.
Il riassunto deve essere informativo, ben strutturato e rispondere direttamente alla query dell'utente."""
        
        # Preparazione del contesto dai risultati
        context = ""
        for i, result in enumerate(results[:10], 1):  # Limita a 10 risultati
            context += f"\n--- Risultato {i} ---\n"
            context += f"Titolo: {result.get('title', 'N/A')}\n"
            context += f"Contenuto: {result.get('content', '')[:500]}...\n"
            context += f"Fonte: {result.get('source_type', 'N/A')}\n"
        
        prompt = f"""
Query dell'utente: "{query}"

Risultati di ricerca:
{context}

Genera un riassunto completo che risponda alla query dell'utente basandoti sui risultati forniti.
Includi le fonti più rilevanti e organizza le informazioni in modo logico.
"""
        
        return self.generate_response(prompt, system_prompt)
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Estrae parole chiave da un testo
        
        Args:
            text: Il testo da cui estrarre le parole chiave
            
        Returns:
            Lista di parole chiave
        """
        system_prompt = "Sei un esperto nell'estrazione di parole chiave. Estrai le parole chiave più rilevanti dal testo fornito."
        
        schema = {
            "keywords": ["lista di parole chiave rilevanti"],
            "entities": ["lista di entità nominate"],
            "topics": ["lista di argomenti principali"]
        }
        
        prompt = f"Estrai parole chiave, entità e argomenti da questo testo:\n\n{text[:2000]}"
        
        result = self.generate_structured_response(prompt, schema, system_prompt)
        return result.get('keywords', [])
    
    def generate_search_queries(self, original_query: str, num_queries: int = 3) -> List[str]:
        """
        Genera query di ricerca alternative per migliorare i risultati
        
        Args:
            original_query: La query originale
            num_queries: Numero di query alternative da generare
            
        Returns:
            Lista di query alternative
        """
        system_prompt = """Sei un esperto nella formulazione di query di ricerca.
Genera query alternative che possano aiutare a trovare informazioni rilevanti per la query originale.
Le query alternative devono essere diverse ma correlate, usando sinonimi, riformulazioni e approcci diversi."""
        
        schema = {
            "alternative_queries": [f"query alternativa {i+1}" for i in range(num_queries)]
        }
        
        prompt = f"""
Query originale: "{original_query}"

Genera {num_queries} query alternative che possano aiutare a trovare informazioni rilevanti.
Usa sinonimi, riformulazioni e approcci diversi.
"""
        
        result = self.generate_structured_response(prompt, schema, system_prompt)
        return result.get('alternative_queries', [])
    
    def evaluate_result_relevance(self, query: str, result: Dict[str, Any]) -> float:
        """
        Valuta la rilevanza di un risultato rispetto alla query
        
        Args:
            query: La query originale
            result: Il risultato da valutare
            
        Returns:
            Score di rilevanza (0-1)
        """
        system_prompt = """Sei un esperto nella valutazione della rilevanza dei risultati di ricerca.
Valuta quanto il risultato fornito è rilevante per rispondere alla query dell'utente.
Considera il contenuto, il titolo e il contesto."""
        
        schema = {
            "relevance_score": "number (0-1)",
            "reasoning": "string (spiegazione del punteggio)",
            "key_matches": ["lista di elementi che corrispondono alla query"]
        }
        
        prompt = f"""
Query: "{query}"

Risultato da valutare:
Titolo: {result.get('title', 'N/A')}
Contenuto: {result.get('content', '')[:1000]}
Fonte: {result.get('source_type', 'N/A')}

Valuta la rilevanza di questo risultato per la query (0 = non rilevante, 1 = perfettamente rilevante).
"""
        
        evaluation = self.generate_structured_response(prompt, schema, system_prompt)
        return evaluation.get('relevance_score', 0.5)
    
    async def generate_response_async(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        Versione asincrona della generazione di risposta
        
        Args:
            prompt: Il prompt dell'utente
            system_prompt: Prompt di sistema opzionale
            **kwargs: Parametri aggiuntivi
            
        Returns:
            La risposta generata
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.generate_response, 
            prompt, 
            system_prompt, 
            **kwargs
        )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Restituisce informazioni sul modello corrente
        
        Returns:
            Dizionario con informazioni sul modello
        """
        return {
            'provider': self.provider,
            'model': self.model,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'available': self.client is not None if self.provider == 'openai' else False
        }
