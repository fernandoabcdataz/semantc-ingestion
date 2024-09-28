import json
import time
from google.cloud import secretmanager
from requests_oauthlib import OAuth2Session
from cachetools import TTLCache, cached
from config import CONFIG
from threading import Lock
from utils import get_logger
from typing import Tuple, Dict, Any

logger = get_logger()

# Cache to store tokens with a TTL of 1 hour
_token_cache = TTLCache(maxsize=1000, ttl=3600)
_token_lock = Lock()

def get_secret(secret_id: str) -> str:
    """
    retrieves a secret from Google Secret Manager

    Args:
        secret_id (str): the ID of the secret

    Returns:
        str: the secret value
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"{CONFIG['SECRETS_PATH']}/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {str(e)}")
        raise

def get_client_credentials() -> Tuple[str, str]:
    """
    Retrieves client ID and client secret from Secret Manager.

    Returns:
        Tuple[str, str]: A tuple containing CLIENT_ID and CLIENT_SECRET.
    """
    client_id_secret_name = f"{CONFIG['PROJECT_ID']}-{CONFIG['CLIENT_NAME']}-xero-client-id"
    client_secret_secret_name = f"{CONFIG['PROJECT_ID']}-{CONFIG['CLIENT_NAME']}-xero-client-secret"

    CLIENT_ID = get_secret(client_id_secret_name)
    CLIENT_SECRET = get_secret(client_secret_secret_name)

    return CLIENT_ID, CLIENT_SECRET

def retrieve_tokens(client_id: str) -> Dict[str, Any]:
    """
    Retrieves stored tokens for a client from Secret Manager.

    Args:
        client_id (str): The unique identifier for the client.

    Returns:
        Dict[str, Any]: The token dictionary.
    """
    try:
        secret_name = f"{CONFIG['SECRETS_PATH']}/xero_token_{client_id}"
        tokens_json = get_secret(secret_name)
        return json.loads(tokens_json)
    except Exception as e:
        logger.error(f"Error retrieving tokens for client {client_id}: {str(e)}")
        raise

def store_tokens(client_id: str, tokens: Dict[str, Any]) -> None:
    """
    Stores tokens for a client in Secret Manager.

    Args:
        client_id (str): The unique identifier for the client.
        tokens (Dict[str, Any]): The token dictionary.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        secret_name = f"{CONFIG['SECRETS_PATH']}/xero_token_{client_id}"
        payload = json.dumps(tokens)
        client.add_secret_version(
            parent=secret_name,
            payload={"data": payload.encode("UTF-8")}
        )
        logger.info(f"Stored tokens for client {client_id}")
    except Exception as e:
        logger.error(f"Error storing tokens for client {client_id}: {str(e)}")
        raise

def current_time() -> float:
    """
    Returns the current time in seconds since the epoch.

    Returns:
        float: Current time.
    """
    return time.time()

@cached(_token_cache)
def get_token(client_id: str) -> Dict[str, Any]:
    """
    Retrieves and refreshes the OAuth token for a client if necessary.

    Args:
        client_id (str): The unique identifier for the client.

    Returns:
        Dict[str, Any]: The valid token dictionary.
    """
    with _token_lock:
        tokens = retrieve_tokens(client_id)
        if tokens.get('expires_at', 0) < current_time():
            tokens = refresh_token(client_id, tokens.get('refresh_token'))
            store_tokens(client_id, tokens)
        return tokens

def refresh_token(client_id: str, refresh_token: str) -> Dict[str, Any]:
    """
    Refreshes the OAuth token using the refresh token.

    Args:
        client_id (str): The unique identifier for the client.
        refresh_token (str): The refresh token.

    Returns:
        Dict[str, Any]: The new token dictionary.
    """
    CLIENT_ID, CLIENT_SECRET = get_client_credentials()
    try:
        oauth = OAuth2Session(CLIENT_ID, token={'refresh_token': refresh_token, 'token_type': 'Bearer'})
        new_tokens = oauth.refresh_token(
            'https://identity.xero.com/connect/token',
            client_secret=CLIENT_SECRET
        )
        new_tokens['expires_at'] = current_time() + new_tokens.get('expires_in', 3600)
        logger.info(f"Refreshed token for client {client_id}")
        return new_tokens
    except Exception as e:
        logger.error(f"Error refreshing token for client {client_id}: {str(e)}")
        raise