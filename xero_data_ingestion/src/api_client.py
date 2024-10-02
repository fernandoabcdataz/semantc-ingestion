import requests
from requests.exceptions import RequestException
from ratelimit import limits, sleep_and_retry
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Any

from authentication import get_token
from utils import get_logger

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
RATE_LIMIT_PERIOD = 50  # seconds

@sleep_and_retry
@limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)
def fetch_data_from_endpoint(endpoint: str, client_id: str, page_size: int = 100) -> List[Dict[str, Any]]:
    """
    fetches all data from a specified Xero API endpoint using pagination
    """
    all_data = []
    page = 1

    while True:
        token = get_token(client_id)
        headers = {
            'Authorization': f'Bearer {token["access_token"]}',
            'xero-tenant-id': client_id,
            'Accept': 'application/json'
        }
        params = {
            'page': page,
            'pageSize': page_size
        }

        try:
            logger.info(f"fetching page {page} from {endpoint} for client {client_id}")
            # response = session.get(endpoint, headers=headers, params=params, timeout=30)
            response = session.get(endpoint, headers=headers)
            # print(headers)
            if response.status_code == 429:
                logger.warning(f"rate limit exceeded when accessing {endpoint} for client {client_id}. retrying...")
                raise RequestException("rate limit exceeded")

            response.raise_for_status()
            data = response.json()

            # extract pagination info and data items
            pagination = data.get('pagination', {})
            items_key = endpoint.rstrip('/').split('/')[-1]  # e.g., 'BankTransactions'
            actual_data = data.get(items_key, [])

            logger.debug(f"page {page} fetched with {len(actual_data)} items.")

            if not actual_data:
                logger.info(f"no more data found on page {page}. Ending pagination.")
                break

            all_data.extend(actual_data)

            # check if we've reached the last page
            if page >= pagination.get('pageCount', page):
                logger.info(f"all pages fetched for {endpoint} for client {client_id}.")
                break

            page += 1

        except RequestException as e:
            logger.error(f"failed to fetch data from {endpoint} for client {client_id} on page {page}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"an unexpected error occurred while fetching data from {endpoint} for client {client_id}: {str(e)}")
            raise

    return all_data