# Dockerfile per Deep Search AI Backend
FROM python:3.11-slim

# Imposta directory di lavoro
WORKDIR /app

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copia codice sorgente
COPY . .

# Crea directory necessarie
RUN mkdir -p data/uploads data/chroma logs
RUN chmod -R 755 data logs

# Crea utente non-root per sicurezza
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Espone porta
EXPOSE 5000

# Variabili d'ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando di avvio
CMD ["python", "app.py"]
