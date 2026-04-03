#!/usr/bin/env bash
# =============================================================================
# deploy.sh — CareerWeave One-Click Deploy Script
#
# Run this from Google Cloud Shell or any machine with gcloud installed.
# It handles EVERYTHING: enabling APIs, creating the Artifact Registry repo,
# building the image, and deploying to Cloud Run.
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Or with custom values:
#   PROJECT_ID=my-project REGION=asia-south1 ./deploy.sh
# =============================================================================

set -euo pipefail   # exit on error, undefined vars, pipe failures

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }

# ── Configuration — override via env vars ─────────────────────────────────────
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-asia-south1}"           # Mumbai: best for India
SERVICE_NAME="${SERVICE_NAME:-careerweave}"
REPO_NAME="${REPO_NAME:-careerweave-repo}"
IMAGE_TAG="latest"

# ── Validate project ID ───────────────────────────────────────────────────────
if [[ -z "$PROJECT_ID" ]]; then
    error "No GCP project set. Run: gcloud config set project YOUR_PROJECT_ID"
fi

IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${SERVICE_NAME}:${IMAGE_TAG}"

echo ""
echo -e "${BOLD}🕸️  CareerWeave — Google Cloud Run Deployment${RESET}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Project  : ${CYAN}${PROJECT_ID}${RESET}"
echo -e "  Region   : ${CYAN}${REGION}${RESET}"
echo -e "  Service  : ${CYAN}${SERVICE_NAME}${RESET}"
echo -e "  Image    : ${CYAN}${IMAGE_URI}${RESET}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Step 1: Enable required Google Cloud APIs ─────────────────────────────────
info "Enabling required Google Cloud APIs…"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --project="${PROJECT_ID}" \
    --quiet
success "APIs enabled."

# ── Step 2: Create Artifact Registry repository (idempotent) ─────────────────
info "Creating Artifact Registry repository '${REPO_NAME}' (if not exists)…"
if ! gcloud artifacts repositories describe "${REPO_NAME}" \
        --location="${REGION}" \
        --project="${PROJECT_ID}" \
        --quiet 2>/dev/null; then
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="CareerWeave Docker images" \
        --project="${PROJECT_ID}" \
        --quiet
    success "Repository created."
else
    success "Repository already exists — skipping."
fi

# ── Step 3: Configure Docker auth for Artifact Registry ──────────────────────
info "Configuring Docker auth for Artifact Registry…"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
success "Docker auth configured."

# ── Step 4: Build & push Docker image ────────────────────────────────────────
info "Building Docker image (this takes ~2–3 minutes on first run)…"
docker build \
    --tag "${IMAGE_URI}" \
    --cache-from "${IMAGE_URI}" \
    . 2>&1 | sed 's/^/  /'
success "Image built: ${IMAGE_URI}"

info "Pushing image to Artifact Registry…"
docker push "${IMAGE_URI}" 2>&1 | sed 's/^/  /'
success "Image pushed."

# ── Step 5: Deploy to Cloud Run ───────────────────────────────────────────────
info "Deploying to Cloud Run in ${REGION}…"
gcloud run deploy "${SERVICE_NAME}" \
    --image="${IMAGE_URI}" \
    --region="${REGION}" \
    --platform=managed \
    --allow-unauthenticated \
    --port=8080 \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=3 \
    --timeout=300 \
    --set-env-vars="PYTHONUNBUFFERED=1" \
    --project="${PROJECT_ID}" \
    --quiet

# ── Grab the live URL ─────────────────────────────────────────────────────────
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region="${REGION}" \
    --project="${PROJECT_ID}" \
    --format="value(status.url)")

echo ""
echo -e "${BOLD}${GREEN}🎉 CareerWeave deployed successfully!${RESET}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  🌐 Live URL : ${CYAN}${SERVICE_URL}${RESET}"
echo -e "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
warn "Remember: Your API keys (Gemini + SerpApi) are entered in the app sidebar."
warn "They are NOT stored — users must provide them each session."
echo ""
