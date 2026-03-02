# ── Stage: runtime ────────────────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

# Install deps first so this layer is cached on code changes
COPY package*.json ./
RUN npm ci

# Copy application source
COPY . .

EXPOSE 3000

# Bind to 0.0.0.0 so the port is reachable outside the container.
# NEXT_PUBLIC_API_URL is read at dev-server startup from the environment,
# so docker-compose can inject it without a rebuild.
CMD ["node_modules/.bin/next", "dev", "-H", "0.0.0.0", "-p", "3000"]
