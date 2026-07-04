#!/bin/bash
set -e

DC="docker-compose"

DOMAINS=(app-calidad.duckdns.org api-calidad.duckdns.org)
EMAIL="nelsonchumacero755@gmail.com"
CERT_PATH="./certbot/conf/live/${DOMAINS[0]}"

# ── Check if certs already exist ──────────────────────────────────
if [ -d "$CERT_PATH" ]; then
  echo "✔ Certificates already exist at $CERT_PATH"
  echo "  Starting services with SSL profile..."
  $DC --profile ssl up -d --build
  echo "✔ Done! Site available at https://${DOMAINS[0]}"
  exit 0
fi

# ── Step 1: Create dummy certificate ──────────────────────────────
echo "Creating dummy certificate for nginx to start..."
mkdir -p "$CERT_PATH"
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
  -keyout "$CERT_PATH/privkey.pem" \
  -out "$CERT_PATH/fullchain.pem" \
  -subj "/CN=localhost" 2>/dev/null
echo "✔ Dummy certificate created"

# ── Step 2: Start services ────────────────────────────────────────
echo "Starting services..."
$DC up -d --build
echo "✔ Services started"

# Wait for nginx to be ready
echo "Waiting for nginx..."
sleep 5

# ── Step 3: Remove dummy certificate ─────────────────────────────
echo "Removing dummy certificate..."
rm -rf "$CERT_PATH"
echo "✔ Dummy certificate removed"

# ── Step 4: Request real certificate from Let's Encrypt ───────────
echo "Requesting Let's Encrypt certificate..."
$DC run --rm --entrypoint certbot certbot certonly \
  --webroot -w /var/www/certbot \
  -d "${DOMAINS[0]}" -d "${DOMAINS[1]}" \
  --agree-tos -m "$EMAIL" --no-eff-email

echo "✔ Certificate obtained"

# ── Step 5: Reload nginx with real certificate ────────────────────
echo "Reloading nginx..."
$DC exec nginx nginx -s reload
echo "✔ Nginx reloaded with real certificate"

# ── Step 6: Restart with certbot auto-renewal ─────────────────────
echo "Restarting with SSL profile (certbot auto-renewal)..."
$DC --profile ssl up -d
echo ""
echo "══════════════════════════════════════════════════"
echo "  ✔ Deployment complete!"
echo "  Frontend: https://${DOMAINS[0]}"
echo "  API:      https://${DOMAINS[1]}"
echo "══════════════════════════════════════════════════"
