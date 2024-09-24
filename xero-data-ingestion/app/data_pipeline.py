import asyncio
from config import CONFIG
from api_client import fetch_data_from_endpoint
from data_storage import write_json_to_gcs
from utils import get_logger
import json
from datetime import datetime
from typing import Tuple

logger = get_logger()

async def process_endpoint(name_endpoint: Tuple[str, str]) -> None:
    """
    Processes a single endpoint by fetching and storing its data.

    Args:
        name_endpoint (Tuple[str, str]): A tuple containing the endpoint name and URL.
    """
    name, endpoint = name_endpoint
    all_data = []
    offset = 0
    batch_size = CONFIG['BATCH_SIZE']
    client_id = CONFIG['CLIENT_NAME']  # Assuming CLIENT_NAME is used as client_id

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
            await asyncio.to_thread(write_json_to_gcs, CONFIG['BUCKET_NAME'], f"{name}.json", json_lines)
            logger.info(f"Processed endpoint {name} for client {client_id}, total records: {len(all_data)}")
        else:
            logger.warning(f"No data found for endpoint {name} for client {client_id}")
    except Exception as e:
        logger.error(f"Error processing endpoint {name} for client {client_id}: {str(e)}")

async def run_pipeline() -> None:
    """
    Runs the data ingestion pipeline concurrently for all endpoints.
    """
    tasks = [process_endpoint(endpoint) for endpoint in CONFIG['ENDPOINTS'].items()]
    await asyncio.gather(*tasks, return_exceptions=True)