#!/bin/bash

# Quick Deploy Script - No Local Docker Required!
# Uses Google Cloud Build to build images in the cloud

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ID="${GCP_PROJECT_ID:-prod-prototype-27}"
REGION="${GCP_REGION:-us-central1}"
BACKEND_SERVICE="genaialchemist-backend"
FRONTEND_SERVICE="genaialchemist-frontend"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  GenAIAlchemist Quick Deploy (No Docker)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Check prerequisites
if [ ! -f "backend/config.env" ]; then
    echo -e "${RED}❌ backend/config.env not found!${NC}"
    exit 1
fi

# Load environment variables
source backend/config.env

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   Project: $PROJECT_ID"
echo "   Region: $REGION"
echo ""

# Set project
gcloud config set project "$PROJECT_ID"

# Enable APIs
echo -e "${YELLOW}🔧 Enabling APIs...${NC}"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com --quiet

# Create Artifact Registry
echo -e "\n${YELLOW}📦 Setting up Artifact Registry...${NC}"
gcloud artifacts repositories create genaialchemist \
    --repository-format=docker \
    --location="$REGION" \
    --description="GenAIAlchemist" \
    2>/dev/null && echo "   ✅ Created" || echo "   ✅ Already exists"

# Create secrets
echo -e "\n${YELLOW}🔐 Storing secrets...${NC}"
store_secret() {
    local name=$1
    local value=$2
    [ -z "$value" ] && return
    
    if gcloud secrets describe "$name" &>/dev/null; then
        echo -n "$value" | gcloud secrets versions add "$name" --data-file=- 2>/dev/null
        echo "   ✅ Updated $name"
    else
        echo -n "$value" | gcloud secrets create "$name" --data-file=- 2>/dev/null
        echo "   ✅ Created $name"
    fi
}

store_secret "gemini-api-key" "$GEMINI_API_KEY"
store_secret "google-api-key" "$GOOGLE_API_KEY"
store_secret "amadeus-client-id" "$AMADEUS_CLIENT_ID"
store_secret "amadeus-client-secret" "$AMADEUS_CLIENT_SECRET"
store_secret "google-maps-key" "$GOOGLE_MAPS_KEY"
store_secret "rapid-api-key" "$RAPID_API_KEY"

# Build & Deploy Backend
echo -e "\n${GREEN}🔨 Building Backend (Cloud Build)...${NC}"
gcloud builds submit \
    --tag="${REGION}-docker.pkg.dev/$PROJECT_ID/genaialchemist/$BACKEND_SERVICE" \
    --dockerfile=Dockerfile.backend \
    --timeout=20m \
    .

echo -e "\n${GREEN}🚀 Deploying Backend to Cloud Run...${NC}"
gcloud run deploy "$BACKEND_SERVICE" \
    --image="${REGION}-docker.pkg.dev/$PROJECT_ID/genaialchemist/$BACKEND_SERVICE" \
    --region="$REGION" \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=2 \
    --timeout=300 \
    --max-instances=10 \
    --set-env-vars="GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.0-flash-exp},INDIAN_RAPID_HOST=${INDIAN_RAPID_HOST:-irctc-indian-railway-api.p.rapidapi.com}" \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,GOOGLE_API_KEY=google-api-key:latest,AMADEUS_CLIENT_ID=amadeus-client-id:latest,AMADEUS_CLIENT_SECRET=amadeus-client-secret:latest,GOOGLE_MAPS_KEY=google-maps-key:latest,RAPID_API_KEY=rapid-api-key:latest" \
    --quiet

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" --region="$REGION" --format='value(status.url)')
echo -e "${GREEN}✅ Backend: $BACKEND_URL${NC}"

# Build & Deploy Frontend
echo -e "\n${GREEN}🔨 Building Frontend (Cloud Build)...${NC}"

# Create temporary cloudbuild.yaml for frontend with build arg
cat > cloudbuild-frontend.yaml << EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '--build-arg'
      - 'VITE_API_URL=$BACKEND_URL'
      - '-t'
      - '${REGION}-docker.pkg.dev/$PROJECT_ID/genaialchemist/$FRONTEND_SERVICE'
      - '-f'
      - 'Dockerfile.frontend'
      - '.'
images:
  - '${REGION}-docker.pkg.dev/$PROJECT_ID/genaialchemist/$FRONTEND_SERVICE'
timeout: 1200s
EOF

gcloud builds submit --config=cloudbuild-frontend.yaml --timeout=20m .
rm cloudbuild-frontend.yaml

echo -e "\n${GREEN}🚀 Deploying Frontend to Cloud Run...${NC}"
gcloud run deploy "$FRONTEND_SERVICE" \
    --image="${REGION}-docker.pkg.dev/$PROJECT_ID/genaialchemist/$FRONTEND_SERVICE" \
    --region="$REGION" \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --max-instances=5 \
    --quiet

FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE" --region="$REGION" --format='value(status.url)')

# Success!
echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n${YELLOW}🌐 Your Application:${NC}"
echo -e "   ${GREEN}$FRONTEND_URL${NC}"
echo -e "\n${YELLOW}🔗 Backend API:${NC}"
echo -e "   ${BLUE}$BACKEND_URL${NC}"
echo -e "\n${YELLOW}📊 View Logs:${NC}"
echo -e "   gcloud run logs tail $BACKEND_SERVICE --region $REGION"
echo -e "\n${YELLOW}🎯 Quick Actions:${NC}"
echo -e "   Test frontend: curl $FRONTEND_URL"
echo -e "   Test backend: curl $BACKEND_URL/health"
echo -e "\n${GREEN}🎉 Done! Open $FRONTEND_URL in your browser${NC}\n"