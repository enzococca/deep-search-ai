# Deep Search AI

Un'applicazione Python avanzata per ricerca intelligente multimodale con agenti AI specializzati, alimentata da GPT-5 e tecnologie di vector database.

## 🚀 Caratteristiche Principali

- **Ricerca Multimodale**: Supporta ricerca su testo, immagini e documenti
- **Agenti AI Specializzati**: Agenti dedicati per diversi tipi di contenuto
- **GPT-5 Integration**: Utilizza il modello più avanzato di OpenAI
- **Vector Database**: Ricerca semantica con Milvus/ChromaDB
- **Elaborazione Documenti**: Supporto per PDF, DOCX, immagini e più formati
- **API REST**: API completa per integrazione con altre applicazioni
- **Interfaccia Web**: Interfaccia utente moderna e intuitiva

## 🏗️ Architettura

L'applicazione è strutturata con un'architettura modulare che include:

- **Agenti Specializzati**: Text Agent, Image Agent, Document Agent, Web Agent, Synthesis Agent
- **Servizi Core**: LLM Service, Embedding Service, Vector Service, File Service
- **Database Layer**: SQLAlchemy per metadati, Vector DB per embeddings
- **API Layer**: Flask REST API con autenticazione JWT
- **Frontend**: Interfaccia web responsive

## 📋 Prerequisiti

- Python 3.10 o superiore
- OpenAI API Key (per GPT-5 e embeddings)
- Milvus (opzionale, usa ChromaDB come alternativa)
- Redis (opzionale, per caching)

## 🛠️ Installazione

### 1. Clona il Repository

```bash
git clone https://github.com/tuousername/deep-search-ai.git
cd deep-search-ai
```

### 2. Crea Ambiente Virtuale

```bash
python -m venv venv
source venv/bin/activate  # Su Windows: venv\Scripts\activate
```

### 3. Installa Dipendenze

```bash
pip install -r requirements.txt
```

### 4. Configura Variabili d'Ambiente

Crea un file `.env` nella directory root:

```env
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///./data/app.db
```

### 5. Configura l'Applicazione

Modifica il file `config.yaml` secondo le tue esigenze:

```yaml
ai:
  llm:
    provider: "openai"
    model: "gpt-4o"  # Sarà aggiornato a GPT-5 quando disponibile
    temperature: 0.1
```

## 🚀 Avvio Rapido

### Avvio dell'Applicazione

```bash
python run.py
```

L'applicazione sarà disponibile su `http://localhost:5000`

### Test dell'API

```bash
# Health check
curl http://localhost:5000/health

# Ricerca di base
curl -X POST http://localhost:5000/api/search/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Cosa è l'intelligenza artificiale?", "type": "text"}'
```

## 📚 Utilizzo

### Ricerca Testuale

```python
import requests

response = requests.post('http://localhost:5000/api/search/query', json={
    'query': 'Spiegami la teoria della relatività',
    'type': 'text',
    'max_results': 10
})

results = response.json()
```

### Upload e Ricerca Documenti

```python
# Upload documento
files = {'file': open('documento.pdf', 'rb')}
response = requests.post('http://localhost:5000/api/upload/document', files=files)

# Ricerca nel documento
response = requests.post('http://localhost:5000/api/search/query', json={
    'query': 'Trova informazioni sui risultati finanziari',
    'type': 'document'
})
```

### Ricerca per Immagini

```python
# Upload immagine
files = {'file': open('immagine.jpg', 'rb')}
response = requests.post('http://localhost:5000/api/upload/image', files=files)

# Ricerca basata su immagine
response = requests.post('http://localhost:5000/api/search/query', json={
    'query': 'Trova immagini simili a questa',
    'type': 'image'
})
```

## 🔧 Configurazione Avanzata

### Database Vettoriale

#### Milvus (Raccomandato per produzione)

```yaml
vector_db:
  provider: "milvus"
  host: "localhost"
  port: 19530
```

#### ChromaDB (Per sviluppo locale)

```yaml
vector_db:
  provider: "chromadb"
  persist_directory: "./data/chromadb"
```

### Agenti Personalizzati

Puoi configurare il comportamento degli agenti nel file `config.yaml`:

```yaml
agents:
  text_agent:
    enabled: true
    max_tokens: 2000
  image_agent:
    enabled: true
    ocr_enabled: true
  document_agent:
    chunk_size: 1000
    chunk_overlap: 200
```

## 🐳 Docker

### Build e Run con Docker

```bash
# Build dell'immagine
docker build -t deep-search-ai .

# Run del container
docker run -p 5000:5000 -e OPENAI_API_KEY=your_key deep-search-ai
```

### Docker Compose

```bash
docker-compose up -d
```

## 🧪 Testing

```bash
# Run dei test
pytest

# Test con coverage
pytest --cov=app tests/

# Test specifici
pytest tests/test_agents.py
```

## 📖 Documentazione API

La documentazione completa dell'API è disponibile su:
- Swagger UI: `http://localhost:5000/docs`
- Redoc: `http://localhost:5000/redoc`

### Endpoint Principali

- `POST /api/search/query` - Esegue una ricerca
- `POST /api/upload/document` - Upload documento
- `POST /api/upload/image` - Upload immagine
- `GET /api/search/history` - Cronologia ricerche
- `GET /api/admin/stats` - Statistiche sistema

## 🔒 Sicurezza

- Autenticazione JWT per API protette
- Validazione rigorosa degli input
- Rate limiting per prevenire abusi
- Sanitizzazione dei file upload

## 🚀 Performance

- Caching multi-livello con Redis
- Elaborazione asincrona per file grandi
- Ottimizzazioni per database vettoriali
- Load balancing per deployment scalabili

## 🤝 Contribuire

1. Fork del repository
2. Crea un branch per la feature (`git checkout -b feature/AmazingFeature`)
3. Commit delle modifiche (`git commit -m 'Add some AmazingFeature'`)
4. Push del branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📄 Licenza

Questo progetto è rilasciato sotto licenza MIT. Vedi il file `LICENSE` per i dettagli.

## 🆘 Supporto

- 📧 Email: support@deepsearch-ai.com
- 💬 Discord: [Deep Search AI Community](https://discord.gg/deepsearch-ai)
- 📖 Wiki: [GitHub Wiki](https://github.com/tuousername/deep-search-ai/wiki)

## 🗺️ Roadmap

- [ ] Supporto GPT-5 completo
- [ ] Agenti personalizzabili dall'utente
- [ ] Integrazione con più provider AI
- [ ] Supporto per video e audio
- [ ] Dashboard analytics avanzata
- [ ] Plugin system
- [ ] Mobile app

## 🙏 Ringraziamenti

- OpenAI per GPT-5 e le API
- Milvus team per il database vettoriale
- La community open source per le librerie utilizzate

---

**Deep Search AI** - Portare l'intelligenza artificiale avanzata alla ricerca di informazioni 🔍✨
