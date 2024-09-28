#!/bin/bash
# scripts/execute_job.sh

set -e

# usage: ./execute_job.sh CLIENT_NAME CLIENT_TOKEN

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 CLIENT_NAME CLIENT_TOKEN"
    exit 1
fi

CLIENT_NAME=$1
CLIENT_TOKEN=$2

PROJECT_ID="semantc-dev"
REGION="us-central1"
JOB_NAME="data-ingestion-job"

BUCKET_NAME="client-${CLIENT_NAME}-bucket"

# execute the Cloud Run Job with environment variables
gcloud run jobs execute ${JOB_NAME} \
    --region=${REGION} \
    --set-env-vars CLIENT_NAME=${CLIENT_NAME},GOOGLE_CLOUD_PROJECT=${PROJECT_ID},CLIENT_TOKEN=${CLIENT_TOKEN},BUCKET_NAME=${BUCKET_NAME}

echo "job executed for ${CLIENT_NAME} successfully"