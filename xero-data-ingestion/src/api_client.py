import requests
from requests.exceptions import RequestException
from ratelimit import limits, sleep_and_retry
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Any

from authentication import get_token
from utils import get_logger

logger = get_logger()

# configure retry strategy
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

# rate limit configuration
RATE_LIMIT_CALLS = 60
RATE_LIMIT_PERIOD = 50  # seconds

@sleep_and_retry
@limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
def fetch_data_from_endpoint(endpoint: str, client_id: str, offset: int = 0, batch_size: int = 100) -> List[Dict[str, Any]]:
    """
    fetches data from a specified Xero API endpoint with pagination

    Args:
        endpoint (str): the API endpoint URL
        client_id (str): the unique identifier for the client
        offset (int, optional): the pagination offset (defaults to 0)
        batch_size (int, optional): number of records to fetch per request (defaults to 100)

    Returns:
        List[Dict[str, Any]]: a list of data items
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
        logger.info(f"fetching data from {endpoint} for client {client_id} - offset {offset}")
        response = session.get(endpoint, headers=headers, params=params, timeout=30)
        if response.status_code == 429:
            logger.warning(f"rate limit exceeded when accessing {endpoint} for client {client_id}. retrying...")
            raise RequestException("rate limit exceeded")
        response.raise_for_status()
        data = response.json()

        # extract the actual data items from the response
        actual_data = next((value for key, value in data.items() if isinstance(value, list)), [])

        return actual_data
    except RequestException as e:
        logger.error(f"failed to fetch data from {endpoint} for client {client_id} - offset {offset}: {str(e)}")
        raise