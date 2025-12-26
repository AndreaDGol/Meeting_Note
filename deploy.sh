#!/bin/bash

# Azure Deployment Script for Notes Processing App
# This script deploys the application to Azure Container Apps with PostgreSQL

set -e  # Exit on error

# Configuration
RESOURCE_GROUP="notes-app-rg"
ACR_NAME="golcondaregistry"
APP_NAME="notes-processing-app"
ENV_NAME="notes-app-env"
IMAGE_NAME="notes-app:latest"
LOCATION="eastus"
DB_SERVER_NAME="notes-db-server"
DB_NAME="notesdb"
DB_ADMIN_USER="notesadmin"
DB_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)  # Generate secure password

echo "🚀 Starting Azure Deployment..."
echo "================================"

# Step 1: Login to Azure (if not already logged in)
echo "📋 Step 1: Checking Azure login..."
if ! az account show &>/dev/null; then
    echo "Please login to Azure..."
    az login
fi

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo "✅ Using subscription: $SUBSCRIPTION_ID"

# Step 2: Create Resource Group
echo ""
echo "📋 Step 2: Creating Resource Group..."
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --output none
echo "✅ Resource Group created: $RESOURCE_GROUP"

# Step 3: Create PostgreSQL Database
echo ""
echo "📋 Step 3: Creating PostgreSQL Database..."
echo "This may take 5-10 minutes..."

# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --location $LOCATION \
  --admin-user $DB_ADMIN_USER \
  --admin-password $DB_ADMIN_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 14 \
  --storage-size 32 \
  --public-access 0.0.0.0 \
  --output none

echo "✅ PostgreSQL server created: $DB_SERVER_NAME"

# Create database
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_SERVER_NAME \
  --database-name $DB_NAME \
  --output none

echo "✅ Database created: $DB_NAME"

# Get database connection string
DB_FQDN="$DB_SERVER_NAME.postgres.database.azure.com"
DATABASE_URL="postgresql://$DB_ADMIN_USER:$DB_ADMIN_PASSWORD@$DB_FQDN:5432/$DB_NAME"

echo ""
echo "📝 Database credentials saved:"
echo "   Server: $DB_FQDN"
echo "   Database: $DB_NAME"
echo "   Username: $DB_ADMIN_USER"
echo "   Password: $DB_ADMIN_PASSWORD"

# Step 4: Build and Push Docker Image
echo ""
echo "📋 Step 4: Building and pushing Docker image..."

# Login to ACR
echo "Logging into Azure Container Registry..."
echo "$ACR_PASSWORD" | docker login $ACR_NAME.azurecr.io -u $ACR_USERNAME --password-stdin

# Build image
echo "Building Docker image..."
docker build -t $ACR_NAME.azurecr.io/$IMAGE_NAME .

# Push image
echo "Pushing image to ACR..."
docker push $ACR_NAME.azurecr.io/$IMAGE_NAME

echo "✅ Image pushed successfully"

# Step 5: Create Container Apps Environment
echo ""
echo "📋 Step 5: Creating Container Apps Environment..."
az containerapp env create \
  --name $ENV_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --output none

echo "✅ Container Apps Environment created"

# Step 6: Create Container App
echo ""
echo "📋 Step 6: Creating Container App..."
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment $ENV_NAME \
  --image $ACR_NAME.azurecr.io/$IMAGE_NAME \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password "$ACR_PASSWORD" \
  --target-port 8000 \
  --ingress external \
  --env-vars \
    "DATABASE_URL=$DATABASE_URL" \
    "DEBUG=False" \
  --secrets \
    "openai-key=$OPENAI_API_KEY" \
  --secret-env-vars \
    "OPENAI_API_KEY=openai-key" \
  --cpu 1.0 \
  --memory 2.0Gi \
  --min-replicas 1 \
  --max-replicas 3 \
  --output none

echo "✅ Container App created"

# Step 7: Get Public URL
echo ""
echo "📋 Step 7: Getting public URL..."
APP_URL=$(az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn \
  -o tsv)

echo ""
echo "================================"
echo "✅ Deployment Complete!"
echo "================================"
echo ""
echo "🌐 Your web URL: https://$APP_URL"
echo ""
echo "📝 Database Info:"
echo "   Server: $DB_FQDN"
echo "   Database: $DB_NAME"
echo "   Username: $DB_ADMIN_USER"
echo "   Password: $DB_ADMIN_PASSWORD"
echo ""
echo "💡 Save the database password securely!"
echo ""



