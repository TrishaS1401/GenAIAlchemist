#!/bin/bash

# Single Command Deployment Script for GenAIAlchemist
# This script sets up secrets and deploys using cloudbuild.yaml

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ID="${GCP_PROJECT_ID:-prod-prototype-27}"
REGION="${GCP_REGION:-us-central1}"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  GenAIAlchemist - Single YAML Deployment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"

# Check config.env
if [ ! -f "backend/config.env" ]; then
    echo -e "${RED}❌ backend/config.env not found!${NC}"
    exit 1
fi

# Load environment variables
source backend/config.env

echo -e "${YELLOW}📋 Project: $PROJECT_ID${NC}"
echo -e "${YELLOW}📍 Region: $REGION${NC}\n"

# Set project
gcloud config set project "$PROJECT_ID"

# Enable APIs
echo -e "${YELLOW}🔧 Enabling APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    secretmanager.googleapis.com \
    --quiet

# Create Artifact Registry
echo -e "\n${YELLOW}📦 Creating Artifact Registry...${NC}"
gcloud artifacts repositories create genaialchemist \
    --repository-format=docker \
    --location="$REGION" \
    --description="GenAIAlchemist Docker Repository" \
    2>/dev/null && echo "   ✅ Created" || echo "   ✅ Already exists"

# Store secrets
echo -e "\n${YELLOW}🔐 Setting up Secret Manager...${NC}"
store_secret() {
    local name=$1
    local value=$2
    
    if [ -z "$value" ]; then
        echo -e "   ${YELLOW}⚠️  $name is empty, skipping${NC}"
        return
    fi
    
    if gcloud secrets describe "$name" --project="$PROJECT_ID" &>/dev/null; then
        echo -n "$value" | gcloud secrets versions add "$name" --data-file=- --project="$PROJECT_ID" 2>/dev/null
        echo "   ✅ Updated $name"
    else
        echo -n "$value" | gcloud secrets create "$name" --data-file=- --project="$PROJECT_ID" 2>/dev/null
        echo "   ✅ Created $name"
    fi
}

store_secret "gemini-api-key" "$GEMINI_API_KEY"
store_secret "google-api-key" "$GOOGLE_API_KEY"
store_secret "amadeus-client-id" "$AMADEUS_CLIENT_ID"
store_secret "amadeus-client-secret" "$AMADEUS_CLIENT_SECRET"
store_secret "google-maps-key" "$GOOGLE_MAPS_KEY"
store_secret "rapid-api-key" "$RAPID_API_KEY"

# Grant Cloud Build access to secrets
echo -e "\n${YELLOW}🔑 Granting Cloud Build access to secrets...${NC}"
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

for secret in gemini-api-key google-api-key amadeus-client-id amadeus-client-secret google-maps-key rapid-api-key; do
    gcloud secrets add-iam-policy-binding "$secret" \
        --member="serviceAccount:${CLOUD_BUILD_SA}" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" \
        --quiet 2>/dev/null && echo "   ✅ Granted access to $secret" || echo "   ℹ️  Already has access to $secret"
done

# Grant Cloud Run access to Cloud Build service account
echo -e "\n${YELLOW}🔑 Granting deployment permissions...${NC}"
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/run.admin" \
    --quiet 2>/dev/null

gcloud iam service-accounts add-iam-policy-binding \
    "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --member="serviceAccount:${CLOUD_BUILD_SA}" \
    --role="roles/iam.serviceAccountUser" \
    --quiet 2>/dev/null

# Run Cloud Build
echo -e "\n${GREEN}🚀 Starting Cloud Build deployment...${NC}"
echo -e "${YELLOW}This will take 15-20 minutes. Go grab a coffee! ☕${NC}\n"

gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions="_REGION=$REGION,_GEMINI_MODEL=${GEMINI_MODEL:-gemini-2.0-flash-exp},_INDIAN_RAPID_HOST=${INDIAN_RAPID_HOST:-irctc-indian-railway-api.p.rapidapi.com}" \
    --timeout=60m

# Get URLs
BACKEND_URL=$(gcloud run services describe genaialchemist-backend --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "Not deployed")
FRONTEND_URL=$(gcloud run services describe genaialchemist-frontend --region="$REGION" --format='value(status.url)' 2>/dev/null || echo "Not deployed")

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "\n${YELLOW}🌐 Frontend:${NC} ${GREEN}$FRONTEND_URL${NC}"
echo -e "${YELLOW}🔗 Backend:${NC}  ${BLUE}$BACKEND_URL${NC}"
echo -e "\n${YELLOW}📊 Logs:${NC}"
echo -e "   gcloud run logs tail genaialchemist-backend --region $REGION"
echo -e "\n${YELLOW}🌐 Console:${NC}"
echo -e "   https://console.cloud.google.com/run?project=$PROJECT_ID"
echo -e "\n${GREEN}🎉 All done!${NC}\n"