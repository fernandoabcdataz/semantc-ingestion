import json
import time
from google.cloud import secretmanager
from requests_oauthlib import OAuth2Session
from threading import Lock
from typing import Tuple, Dict, Any

from config import CONFIG
from utils import get_logger

logger = get_logger()

# initialize Secret Manager client once
client = secretmanager.SecretManagerServiceClient()

# simple cache to store tokens without fixed TTL
_token_cache = {}
_token_lock = Lock()

class SecretManagerError(Exception):
    pass

class TokenRetrievalError(Exception):
    pass

def get_secret(secret_id: str) -> str:
    """
    retrieves a secret from Google Secret Manager
    """
    try:
        name = f"{CONFIG['PROJECT_NUMBER']}/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(name=name)
        secret_value = response.payload.data.decode('UTF-8')
        logger.debug(f"successfully retrieved secret {secret_id}")
        return secret_value
    except Exception as e:
        logger.error(f"error accessing secret {secret_id}: {str(e)}")
        raise SecretManagerError(f"failed to access secret {secret_id}") from e

def get_app_credentials() -> Tuple[str, str]:
    """
    retrieves the application's APP_ID and APP_SECRET from Secret Manager
    """
    APP_ID = get_secret("core-client-id-xero")
    APP_SECRET = get_secret("core-client-secret-xero")
    return APP_ID, APP_SECRET

def retrieve_tokens(client_id: str) -> Dict[str, Any]:
    """
    retrieves stored tokens for a client from Secret Manager
    """
    try:
        secret_id = f"client-{client_id}-token-xero"
        tokens_json = get_secret(secret_id)
        
        logger.debug(f"successfully retrieved tokens for client {client_id}")
        
        if not tokens_json:
            logger.error(f"empty token data retrieved for client {client_id}")
            raise TokenRetrievalError("Empty token data")
        
        try:
            tokens = json.loads(tokens_json)
        except json.JSONDecodeError as json_error:
            logger.error(f"invalid JSON data for client {client_id}")
            logger.error(f"JSON decode error: {str(json_error)}")
            raise TokenRetrievalError(f"Invalid JSON data: {str(json_error)}") from json_error
        
        if not isinstance(tokens, dict):
            logger.error(f"unexpected token format for client {client_id}: {tokens}")
            raise TokenRetrievalError("unexpected token format")
        
        required_fields = {'access_token', 'refresh_token', 'expires_in', 'token_type', 'scope'}
        if not required_fields.issubset(tokens.keys()):
            logger.error(f"missing required token fields for client {client_id}")
            raise TokenRetrievalError("incomplete token data")
        
        return tokens
    except Exception as e:
        logger.error(f"Error retrieving tokens for client {client_id}: {str(e)}")
        raise

def store_tokens(client_id: str, tokens: Dict[str, Any]) -> None:
    """
    stores tokens for a client in Secret Manager
    """
    try:
        secret_id = f"client-{client_id}-token-xero"
        parent = f"{CONFIG['PROJECT_NUMBER']}/secrets/{secret_id}"

        payload = json.dumps(tokens).encode("UTF-8")
        client.add_secret_version(
            parent=parent,
            payload={"data": payload}
        )
        logger.info(f"Stored tokens for client {client_id}")
    except Exception as e:
        logger.error(f"error storing tokens for client {client_id}: {str(e)}")
        raise SecretManagerError(f"failed to store tokens for client {client_id}") from e

def refresh_access_token(client_id: str, refresh_token: str) -> Dict[str, Any]:
    """
    refreshes the OAuth access token using the refresh token
    """
    if not refresh_token:
        logger.error(f"no refresh token available for client {client_id}")
        raise TokenRetrievalError("missing refresh token")

    APP_ID, APP_SECRET = get_app_credentials()
    try:
        oauth = OAuth2Session(APP_ID, token={'refresh_token': refresh_token, 'token_type': 'Bearer'})
        new_tokens = oauth.refresh_token(
            'https://identity.xero.com/connect/token',
            client_secret=APP_SECRET
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
    retrieves and refreshes the OAuth access token for a client if necessary
    """
    with _token_lock:
        cached = _token_cache.get(client_id)
        if cached and cached['expires_at'] > time.time():
            return cached

        tokens = retrieve_tokens(client_id)
        
        # Set 'expires_at' if not present
        if 'expires_at' not in tokens:
            tokens['expires_at'] = time.time() + tokens.get('expires_in', 3600)
            store_tokens(client_id, tokens)  # Persist the updated tokens

        # Refresh if expired
        if tokens.get('expires_at', 0) < time.time():
            tokens = refresh_access_token(client_id, tokens.get('refresh_token'))
        
        _token_cache[client_id] = tokens
        return tokens