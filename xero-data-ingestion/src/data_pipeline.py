import asyncio
import json
from datetime import datetime
from typing import Tuple

from config import CONFIG
from api_client import fetch_data_from_endpoint
from data_storage import write_json_to_gcs
from utils import get_logger

logger = get_logger()

async def process_endpoint(name_endpoint: Tuple[str, str]) -> None:
    """
    processes a single endpoint by fetching and storing its data

    Args:
        name_endpoint (Tuple[str, str]): a tuple containing the endpoint name and URL
    """
    name, endpoint = name_endpoint
    all_data = []
    offset = 0
    batch_size = CONFIG['BATCH_SIZE']
    client_id = CONFIG['CLIENT_ID']
    bucket_name = CONFIG['BUCKET_NAME']

    try:
        while True:
            # Fetch data in a separate thread to avoid blocking
            data = await asyncio.to_thread(fetch_data_from_endpoint, endpoint, client_id, offset, batch_size)
            if not data:
                break
            all_data.extend(data)
            if len(data) < batch_size:
                break  # Last batch
            offset += batch_size  # increment offset by batch_size

        if all_data:
            ingestion_time = datetime.utcnow().isoformat()
            json_lines = "\n".join(json.dumps({**item, "ingestion_time": ingestion_time}) for item in all_data)
            await asyncio.to_thread(write_json_to_gcs, bucket_name, f"{name}.json", json_lines)
            logger.info(f"processed endpoint {name} for client {client_id}, total records: {len(all_data)}")
        else:
            logger.warning(f"no data found for endpoint {name} for client {client_id}")
    except Exception as e:
        logger.error(f"error processing endpoint {name} for client {client_id}: {str(e)}")

async def run_pipeline() -> None:
    """
    runs the data ingestion pipeline concurrently for all endpoints
    """
    endpoints = CONFIG['ENDPOINTS']
    tasks = [process_endpoint(endpoint) for endpoint in endpoints.items()]
    await asyncio.gather(*tasks, return_exceptions=True)