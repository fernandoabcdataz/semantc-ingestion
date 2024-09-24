#!/bin/bash

# scripts/deploy.sh

set -e

# Usage: ./deploy.sh CLIENT_ID PROJECT_ID

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 CLIENT_ID PROJECT_ID"
    exit 1
fi

CLIENT_ID=$1
PROJECT_ID=$2

# Set environment variables
export CLIENT_NAME=$CLIENT_ID
export GOOGLE_CLOUD_PROJECT=$PROJECT_ID

# Variables
REGION=us-central1
REPO=xero-data-ingestion-repo
IMAGE_TAG=latest
BUCKET_NAME=${PROJECT_ID}-${CLIENT_ID}-xero-data

# Authenticate with GCP
gcloud auth login
gcloud config set project $PROJECT_ID

# Create Artifact Registry repository if it doesn't exist
gcloud artifacts repositories list --filter="name:$REPO" --format="value(name)" | grep $REPO || \
gcloud artifacts repositories create $REPO --repository-format=docker --location=$REGION --description="Artifact repository for Xero Data Ingestion"

# Build Docker image
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/xero-data-ingestion:$IMAGE_TAG .

# Push Docker image to Artifact Registry
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/xero-data-ingestion:$IMAGE_TAG

# Create Cloud Storage bucket if it doesn't exist
gsutil ls -b gs://$BUCKET_NAME || gsutil mb -l $REGION gs://$BUCKET_NAME

# Deploy to Cloud Run
gcloud run deploy xero-data-ingestion-service \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/xero-data-ingestion:$IMAGE_TAG \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars CLIENT_NAME=$CLIENT_ID,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,EXPECTED_API_KEY=$EXPECTED_API_KEY \
    --memory 512Mi \
    --port 8080

echo "Deployment completed successfully."