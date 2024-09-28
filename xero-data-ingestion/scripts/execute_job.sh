#!/bin/bash
# scripts/execute_job.sh

set -e

# usage: ./execute_job.sh CLIENT_ID

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 CLIENT_ID"
    exit 1
fi

CLIENT_ID=$1

PROJECT_ID="semantc-dev"
REGION="us-central1"
JOB_NAME="data-ingestion-job"

BUCKET_NAME="client-${CLIENT_ID}-bucket-xero"

# execute the Cloud Run Job with environment variables
gcloud run jobs execute ${JOB_NAME} \
    --region=${REGION} \
    --set-env-vars CLIENT_ID=${CLIENT_ID},PROJECT_ID=${PROJECT_ID},BUCKET_NAME=${BUCKET_NAME}

echo "job executed for ${CLIENT_ID} successfully"