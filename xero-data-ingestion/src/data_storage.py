from google.cloud import storage
from typing import Any

from .utils import get_logger

logger = get_logger()

# initialize storage client once
storage_client = storage.Client()

def write_json_to_gcs(bucket_name: str, file_name: str, content: str) -> None:
    """
    writes JSON content to a specified GCS bucket

    Args:
        bucket_name (str): The name of the GCS bucket
        file_name (str): The destination file name
        content (str): The JSON content to write
    """
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_name)
        blob.upload_from_string(content, content_type='application/json')
        logger.info(f"Saved {file_name} to gs://{bucket_name}/{file_name}")
    except Exception as e:
        logger.error(f"Failed to upload {file_name} to {bucket_name}: {str(e)}")
        raise