# 🚀 Guida al Deployment - Deep Search AI

Questa guida fornisce istruzioni dettagliate per il deployment dell'applicazione Deep Search AI in diversi ambienti.

## 📋 Prerequisiti

### Sistema Operativo
- **Linux/macOS**: Ubuntu 20.04+, macOS 10.15+
- **Windows**: Windows 10/11 con WSL2 (raccomandato) o Windows nativo

### Software Richiesto
- **Python**: 3.8 o superiore
- **Node.js**: 18.0 o superiore (per il frontend)
- **Git**: Per clonare il repository
- **OpenAI API Key**: Per le funzionalità AI

### Hardware Raccomandato
- **RAM**: Minimo 4GB, raccomandato 8GB+
- **Storage**: Minimo 2GB di spazio libero
- **CPU**: Processore multi-core raccomandato

## 🔧 Installazione Rapida

### 1. Clona il Repository
```bash
git clone https://github.com/enzococca/deep-search-ai.git
cd deep-search-ai
```

### 2. Configurazione Variabili d'Ambiente
```bash
# Linux/macOS
export OPENAI_API_KEY="your-openai-api-key-here"

# Windows
set OPENAI_API_KEY=your-openai-api-key-here
```

### 3. Avvio Automatico

#### Linux/macOS
```bash
./scripts/start.sh
```

#### Windows
```cmd
scripts\start.bat
```

## 🐳 Deployment con Docker

### Dockerfile Backend
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "run.py"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

### Comandi Docker
```bash
# Build e avvio
docker-compose up --build

# Avvio in background
docker-compose up -d

# Stop
docker-compose down
```

## ☁️ Deployment Cloud

### Heroku
```bash
# Installa Heroku CLI
# Crea app
heroku create deep-search-ai-app

# Configura variabili
heroku config:set OPENAI_API_KEY=your-key

# Deploy
git push heroku main
```

### AWS EC2
```bash
# Connetti all'istanza
ssh -i your-key.pem ubuntu@your-ec2-ip

# Installa dipendenze
sudo apt update
sudo apt install python3 python3-pip nodejs npm git

# Clona e configura
git clone https://github.com/enzococca/deep-search-ai.git
cd deep-search-ai
./scripts/start.sh
```

### Google Cloud Platform
```bash
# Usa Cloud Run
gcloud run deploy deep-search-ai \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🔒 Configurazione Sicurezza

### Variabili d'Ambiente di Produzione
```bash
# File .env
FLASK_ENV=production
SECRET_KEY=your-super-secret-key
OPENAI_API_KEY=your-openai-api-key
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://localhost:6379
```

### Reverse Proxy (Nginx)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 Monitoraggio e Logging

### Configurazione Logging
```yaml
# config.yaml
logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file: './logs/deep_search_ai.log'
  max_size: 10MB
  backup_count: 5
```

### Health Check
```bash
# Verifica stato applicazione
curl http://localhost:5000/health

# Verifica API
curl http://localhost:5000/api/v1/health
```

## 🔧 Troubleshooting

### Problemi Comuni

#### 1. Errore "Module not found"
```bash
# Reinstalla dipendenze
pip install -r requirements.txt
```

#### 2. Errore Database
```bash
# Ricrea database
rm -f data/app.db
python -c "from app import create_app; app = create_app(); app.app_context().push()"
```

#### 3. Errore OpenAI API
```bash
# Verifica API key
python -c "import openai; print('API Key OK' if openai.api_key else 'API Key Missing')"
```

#### 4. Errore Frontend
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Log Files
- **Backend**: `logs/deep_search_ai.log`
- **Frontend**: Console del browser
- **Sistema**: `/var/log/syslog` (Linux)

## 📈 Ottimizzazione Performance

### Database
```python
# Configurazione SQLite per produzione
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
```

### Caching
```python
# Redis per caching
CACHE_TYPE = "redis"
CACHE_REDIS_URL = "redis://localhost:6379"
```

### Load Balancing
```nginx
upstream backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}
```

## 🔄 Aggiornamenti

### Aggiornamento Automatico
```bash
#!/bin/bash
# update.sh
git pull origin main
pip install -r requirements.txt
sudo systemctl restart deep-search-ai
```

### Backup Database
```bash
# Backup automatico
cp data/app.db backups/app_$(date +%Y%m%d_%H%M%S).db
```

## 📞 Supporto

Per problemi di deployment:
1. Controlla i log dell'applicazione
2. Verifica le variabili d'ambiente
3. Consulta la documentazione GitHub
4. Apri un issue su GitHub

## 🔗 Link Utili

- **Repository**: https://github.com/enzococca/deep-search-ai
- **Documentazione**: [README.md](README.md)
- **Issues**: https://github.com/enzococca/deep-search-ai/issues
- **OpenAI API**: https://platform.openai.com/
