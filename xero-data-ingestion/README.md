# Xero Data Ingestion Service

## Overview

The **Xero Data Ingestion Service** is a cloud-agnostic application designed to fetch data from the Xero API using OAuth 2.0 authentication, store the data in Google Cloud Storage, and load it into BigQuery for analysis. The service leverages GCP resources such as Secret Manager for secure token storage, Cloud Storage for data responses, BigQuery for data warehousing, and Artifact Registry for Docker image management.

## Features

- **OAuth 2.0 Authentication:** Securely authenticate with the Xero API.
- **Data Fetching:** Retrieve data from various Xero API endpoints with pagination and rate limiting.
- **Data Storage:** Store fetched data in Google Cloud Storage.
- **Data Loading:** Load data from Cloud Storage into BigQuery tables.
- **Secure Token Management:** Utilize Secret Manager to store and manage OAuth tokens.
- **Dockerized Deployment:** Containerize the application for consistent deployments.
- **Unit Testing:** Ensure code reliability with comprehensive tests.
- **Automated Deployment Script:** Simplify the deployment process with a bash script.

## Project Structure

```
xero-data-ingestion/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api_client.py
│   ├── authentication.py
│   ├── data_pipeline.py
│   ├── data_storage.py
│   ├── table_loader.py
│   ├── config.py
│   ├── utils.py
│   ├── requirements.txt
│   └── Dockerfile
├── tests/
│   ├── __init__.py
│   ├── test_api_client.py
│   ├── test_authentication.py
│   ├── test_data_pipeline.py
│   └── test_table_loader.py
├── scripts/
│   └── deploy.sh
├── .gitignore
└── README.md
```

## Setup Instructions

### Prerequisites

- **Python 3.11** or higher
- **Docker** installed on your machine
- **Google Cloud SDK** (`gcloud`) installed and configured
- **Terraform** installed (if using for infrastructure as code)
- Access to a **Google Cloud Project** with the necessary APIs enabled:
  - Secret Manager
  - Cloud Storage
  - BigQuery
  - Artifact Registry

### Environment Variables

The application relies on the following environment variables:

- `CLIENT_NAME`: Unique identifier for the client.
- `GOOGLE_CLOUD_PROJECT`: Your GCP project ID.
- `EXPECTED_API_KEY`: API key required to access the `/run` endpoint.
- `BATCH_SIZE` (optional): Number of records to fetch per API call (default is 100).
- `PORT` (optional): Port on which the Flask app runs (default is 8080).

### Secret Management

Store sensitive information like `CLIENT_ID`, `CLIENT_SECRET`, and OAuth tokens in **Google Cloud Secret Manager**.

1. **Create Secrets:**

   ```bash
   # Replace placeholders with actual values
   gcloud secrets create "${PROJECT_ID}-${CLIENT_NAME}-xero-client-id" --data-file=path/to/client_id.txt
   gcloud secrets create "${PROJECT_ID}-${CLIENT_NAME}-xero-client-secret" --data-file=path/to/client_secret.txt
   gcloud secrets create "xero_token_${CLIENT_NAME}" --data-file=path/to/token.json
   ```

2. **Grant Access:**

   Ensure that the service account running the application has `Secret Manager Secret Accessor` role.

   ```bash
   gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
       --member="serviceAccount:your-service-account@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com" \
       --role="roles/secretmanager.secretAccessor"
   ```

### Building and Pushing the Docker Image

1. **Navigate to the `app/` Directory:**

   ```bash
   cd app/
   ```

2. **Build the Docker Image:**

   ```bash
   docker build -t gcr.io/semantc-dev/xero-ingestion:latest .
   ```

3. **Tag the Docker Image for Artifact Registry:**

   <!-- ```bash
   docker tag gcr.io/semantc-dev/xero-ingestion:latest REGION-docker.pkg.dev/PROJECT_ID/xero-data-ingestion-repo/gcr.io/semantc-dev/xero-ingestion:latest
   ```

   Replace `REGION` and `PROJECT_ID` with your GCP region and project ID. -->

4. **Push the Docker Image to Artifact Registry:**

   ```bash
   docker push gcr.io/semantc-dev/xero-ingestion:latest
   ```

### Deploying the Application

Use the provided `deploy.sh` script for automated deployment.

1. **Make the Script Executable:**

   ```bash
   chmod +x scripts/deploy.sh
   ```

2. **Run the Deployment Script:**

   ```bash
   ./scripts/deploy.sh CLIENT_ID PROJECT_ID
   ```

   Replace `CLIENT_ID` and `PROJECT_ID` with your actual client ID and GCP project ID.

### Running Tests

1. **Navigate to the Project Root:**

   ```bash
   cd xero-data-ingestion/
   ```

2. **Install Testing Dependencies:**

   *(Assuming you have a separate `requirements-test.txt`, else include test dependencies in `requirements.txt`)*

   ```bash
   pip install -r app/requirements.txt
   pip install pytest
   ```

3. **Run Tests:**

   ```bash
   pytest tests/
   ```

## Usage

### Triggering the Data Pipeline

1. **Send a POST Request to the `/run` Endpoint:**

   ```bash
   curl -X POST http://your-cloud-run-url/run \
        -H "X-API-KEY: your_expected_api_key"
   ```

   Replace `your-cloud-run-url` with the actual URL of your deployed service and `your_expected_api_key` with the API key you set during deployment.

### Accessing the Home Endpoint

1. **Send a GET Request to the Home Endpoint:**

   ```bash
   curl http://your-cloud-run-url/
   ```

   Expected response:

   ```
   Data Fetching Service is running
   ```

## Deployment Notes

- **Cloud Run:** The deployment script assumes usage of Cloud Run for hosting the Flask application. Adjust the `deploy.sh` script if deploying to a different service.
- **Artifact Registry:** Ensure that the Artifact Registry repository (`xero-data-ingestion-repo`) exists or is created by the deployment script.
- **Cloud Storage Bucket:** The deployment script creates the Cloud Storage bucket if it doesn't exist. Ensure proper IAM permissions for the service account to access the bucket.
- **BigQuery:** The application creates BigQuery datasets and tables as needed. Ensure the service account has the necessary BigQuery roles.

## Security Considerations

- **API Key Protection:** The `/run` endpoint is secured using an API key. Ensure that the `EXPECTED_API_KEY` is stored securely and rotated regularly.
- **Secret Management:** All sensitive information is stored in Secret Manager. Regularly audit and rotate secrets to maintain security.
- **Least Privilege:** Assign only the necessary IAM roles to service accounts to minimize security risks.

## Contributing

Contributions are welcome! Please open issues or submit pull requests for any improvements or bug fixes.

## License

[MIT License](LICENSE)