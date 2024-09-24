import requests
from app.authentication import get_token
from app.utils import get_logger
from requests.exceptions import RequestException
from ratelimit import limits, sleep_and_retry
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Any

logger = get_logger()

# Configure retry strategy
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"],
    raise_on_status=False
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

# Rate limit configuration
RATE_LIMIT_CALLS = 60
RATE_LIMIT_PERIOD = 60  # seconds

@sleep_and_retry
@limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
def fetch_data_from_endpoint(endpoint: str, client_id: str, offset: int = 0, batch_size: int = 100) -> List[Dict[str, Any]]:
    """
    Fetches data from a specified Xero API endpoint with pagination.

    Args:
        endpoint (str): The API endpoint URL.
        client_id (str): The unique identifier for the client.
        offset (int, optional): The pagination offset. Defaults to 0.
        batch_size (int, optional): Number of records to fetch per request. Defaults to 100.

    Returns:
        List[Dict[str, Any]]: A list of data items.
    """
    token = get_token(client_id)
    headers = {
        'Authorization': f'Bearer {token["access_token"]}',
        'Accept': 'application/json'
    }
    params = {
        'offset': offset,
        'pageSize': batch_size
    }

    try:
        logger.info(f"Fetching data from {endpoint} for client {client_id} - Offset {offset}")
        response = session.get(endpoint, headers=headers, params=params, timeout=30)
        if response.status_code == 429:
            logger.warning(f"Rate limit exceeded when accessing {endpoint} for client {client_id}. Retrying...")
            raise RequestException("Rate limit exceeded")
        response.raise_for_status()
        data = response.json()

        # Extract the actual data items from the response
        actual_data = next((value for key, value in data.items() if isinstance(value, list)), [])

        return actual_data
    except RequestException as e:
        logger.error(f"Failed to fetch data from {endpoint} for client {client_id} - offset {offset}: {str(e)}")
        raise