FROM node:20-alpine

WORKDIR /app

ENV CI=true \
    npm_config_audit=false \
    npm_config_fund=false \
    npm_config_progress=false \
    npm_config_fetch_retries=5 \
    npm_config_fetch_retry_factor=2 \
    npm_config_fetch_retry_mintimeout=20000 \
    npm_config_fetch_retry_maxtimeout=120000 \
    npm_config_fetch_timeout=1200000

COPY package*.json ./
RUN npm install --legacy-peer-deps --no-audit --no-fund --progress=false

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]
