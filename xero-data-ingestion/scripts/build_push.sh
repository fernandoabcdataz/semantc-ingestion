#!/bin/bash
# scripts/build_push.sh

set -e

# configuration
PROJECT_ID="semantc-dev"
REGION="us-central1"
REPO="gcr.io"
IMAGE_TAG="latest"
IMAGE_NAME="${REPO}/${PROJECT_ID}/xero-ingestion:${IMAGE_TAG}"

echo "${IMAGE_NAME}"

# authenticate with GCP
gcloud auth configure-docker gcr.io

# create Artifact Registry repository if it doesn't exist
if ! gcloud artifacts repositories list --filter="name:${REPO}" --format="value(name)" | grep -q ${REPO}; then
    gcloud artifacts repositories create ${REPO} \
        --repository-format=docker \
        --location=${REGION} \
        --description="Artifact repository for Xero Data Ingestion"
    echo "Artifact Registry repository '${REPO}' created"
else
    echo "Artifact Registry repository '${REPO}' already exists"
fi

# build Docker image
docker build -t ${IMAGE_NAME} .

# push Docker image to Artifact Registry
docker push ${IMAGE_NAME}

echo "docker image pushed to ${IMAGE_NAME} successfully"