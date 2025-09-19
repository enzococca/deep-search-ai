# Multi-stage build per frontend React

# Stage 1: Build
FROM node:18-alpine AS builder

WORKDIR /app

# Copia package files
COPY package*.json pnpm-lock.yaml ./

# Installa pnpm e dipendenze
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile

# Copia codice sorgente
COPY . .

# Build per produzione
RUN pnpm run build

# Stage 2: Serve
FROM nginx:alpine

# Copia build files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copia configurazione nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Espone porta
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Avvia nginx
CMD ["nginx", "-g", "daemon off;"]
