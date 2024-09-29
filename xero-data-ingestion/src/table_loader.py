from google.cloud import bigquery
from google.cloud import storage
import json
import io
import datetime
from typing import List, Dict, Any

from .config import CONFIG
from .utils import get_logger

logger = get_logger()

# initialize clients once
bigquery_client = bigquery.Client(project=CONFIG['PROJECT_ID'])
storage_client = storage.Client()

def load_json_to_table() -> None:
    """
    loads JSON data from GCS into BigQuery tables for each endpoint
    """
    endpoints = CONFIG['ENDPOINTS']
    project_id = CONFIG['PROJECT_ID']
    client_id = CONFIG['CLIENT_ID']
    bucket_name = CONFIG['BUCKET_NAME']

    
    dataset_id = f"{project_id}.{client_id}_raw"

    # ensure dataset exists
    try:
        bigquery_client.get_dataset(dataset_id)
        logger.info(f"dataset {dataset_id} already exists")
    # except bigquery.NotFound:
    #     dataset = bigquery.Dataset(dataset_id)
    #     dataset.location = 'US'  # Adjust location as needed
    #     bigquery_client.create_dataset(dataset)
    #     logger.info(f"Created dataset {dataset_id}")
    except Exception as e:
        logger.error(f"error accessing dataset {dataset_id}: {str(e)}")
        raise

    for endpoint in endpoints.keys():
        table_id = f"{dataset_id}.xero_{endpoint}"

        # define table schema
        schema = [
            bigquery.SchemaField("ingestion_time", "TIMESTAMP", mode="REQUIRED")
        ]

        table_ref = bigquery_client.dataset(dataset_id).table(f"xero_{endpoint}")

        # create or ensure table exists
        try:
            table = bigquery.Table(table_ref, schema=schema)
            table = bigquery_client.create_table(table, exists_ok=True)
            logger.info(f"ensured table {table_id} exists.")
        except Exception as e:
            logger.error(f"error creating table {table_id}: {str(e)}")
            continue

        # Load data from GCS to BigQuery
        try:
            uri = f"gs://{bucket_name}/{endpoint}.json"
            job_config = bigquery.LoadJobConfig(
                schema=schema,
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            load_job = bigquery_client.load_table_from_uri(
                uri,
                table_ref,
                job_config=job_config
            )
            load_job.result()  # Wait for the job to complete
            logger.info(f"loaded data into {table_id} from {uri}")
        except Exception as e:
            logger.error(f"error loading data into {table_id} from {uri}: {str(e)}")