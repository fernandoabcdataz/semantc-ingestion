#!/bin/bash

# scripts/deploy.sh

set -e

# usage: ./deploy.sh CLIENT_ID PROJECT_ID EXPECTED_API_KEY

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 CLIENT_ID PROJECT_ID EXPECTED_API_KEY"
    exit 1
fi

CLIENT_ID=$1
PROJECT_ID=$2
EXPECTED_API_KEY=$3

# set environment variables
export CLIENT_NAME=$CLIENT_ID
export GOOGLE_CLOUD_PROJECT=$PROJECT_ID

# variables
REGION=us-central1
REPO=xero-data-ingestion-repo
IMAGE_TAG=latest
BUCKET_NAME=${PROJECT_ID}-${CLIENT_ID}-xero-data

# authenticate with GCP
gcloud auth login
gcloud config set project $PROJECT_ID

# create Artifact Registry repository if it doesn't exist
if ! gcloud artifacts repositories list --filter="name:$REPO" --format="value(name)" | grep -q $REPO; then
    gcloud artifacts repositories create $REPO \
        --repository-format=docker \
        --location=$REGION \
        --description="Artifact repository for Xero Data Ingestion"
fi

# build Docker image
docker build -t $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/xero-data-ingestion:$IMAGE_TAG .

# push Docker image to Artifact Registry
docker push $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/xero-data-ingestion:$IMAGE_TAG

# create Cloud Storage bucket if it doesn't exist
if ! gsutil ls -b gs://$BUCKET_NAME >/dev/null 2>&1; then
    gsutil mb -l $REGION gs://$BUCKET_NAME
fi

# deploy to Cloud Run
gcloud run deploy xero-data-ingestion-service \
    --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/xero-data-ingestion:$IMAGE_TAG \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars CLIENT_NAME=$CLIENT_ID,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,EXPECTED_API_KEY=$EXPECTED_API_KEY \
    --memory 1Gi \
    --port 8080 \
    --service-account=your-service-account@${PROJECT_ID}.iam.gserviceaccount.com

echo "Deployment completed successfully."