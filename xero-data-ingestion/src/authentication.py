import json
import time
from google.cloud import secretmanager
from requests_oauthlib import OAuth2Session
from cachetools import TTLCache
from threading import Lock
from typing import Tuple, Dict, Any

from config import CONFIG
from utils import get_logger

logger = get_logger()

# Cache to store tokens with a TTL matching token expiry
_token_cache = TTLCache(maxsize=1000, ttl=3600)
_token_lock = Lock()

def get_secret(secret_id: str) -> str:
    """
    Retrieves a secret from Google Secret Manager.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{CONFIG['PROJECT_NUMBER']}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        logger.error(f"Error accessing secret {secret_id}: {str(e)}")
        raise

def get_client_credentials() -> Tuple[str, str]:
    """
    Retrieves CLIENT_ID and CLIENT_SECRET from Secret Manager.
    """
    CLIENT_ID = CONFIG['CLIENT_ID']
    CLIENT_SECRET = get_secret("client-secret")
    return CLIENT_ID, CLIENT_SECRET

def retrieve_tokens(client_id: str) -> Dict[str, Any]:
    """
    Retrieves stored tokens for a client from Secret Manager.
    """
    try:
        secret_id = f"xero_token_{client_id}"
        tokens_json = get_secret(secret_id)
        tokens = json.loads(tokens_json)
        return tokens
    except Exception as e:
        logger.error(f"Error retrieving tokens for client {client_id}: {str(e)}")
        raise

def store_tokens(client_id: str, tokens: Dict[str, Any]) -> None:
    """
    Stores tokens for a client in Secret Manager.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{CONFIG['PROJECT_NUMBER']}/secrets/xero_token_{client_id}"
        payload = json.dumps(tokens).encode("UTF-8")
        client.add_secret_version(
            parent=parent,
            payload={"data": payload}
        )
        logger.info(f"Stored tokens for client {client_id}")
    except Exception as e:
        logger.error(f"Error storing tokens for client {client_id}: {str(e)}")
        raise

def refresh_token(client_id: str, refresh_token: str) -> Dict[str, Any]:
    """
    Refreshes the OAuth token using the refresh token.
    """
    CLIENT_ID, CLIENT_SECRET = get_client_credentials()
    try:
        oauth = OAuth2Session(CLIENT_ID, token={'refresh_token': refresh_token, 'token_type': 'Bearer'})
        new_tokens = oauth.refresh_token(
            'https://identity.xero.com/connect/token',
            client_secret=CLIENT_SECRET
        )
        new_tokens['expires_at'] = time.time() + new_tokens.get('expires_in', 3600)
        store_tokens(client_id, new_tokens)
        logger.info(f"Refreshed token for client {client_id}")
        return new_tokens
    except Exception as e:
        logger.error(f"Error refreshing token for client {client_id}: {str(e)}")
        raise

def get_token(client_id: str) -> Dict[str, Any]:
    """
    Retrieves and refreshes the OAuth token for a client if necessary.
    """
    with _token_lock:
        if client_id in _token_cache:
            return _token_cache[client_id]

        tokens = retrieve_tokens(client_id)
        if tokens.get('expires_at', 0) < time.time():
            tokens = refresh_token(client_id, tokens.get('refresh_token'))
        _token_cache[client_id] = tokens
        return tokens