import pytest
from unittest.mock import patch
from app.authentication import get_token, refresh_token, store_tokens, retrieve_tokens
from requests_oauthlib import OAuth2Session

@pytest.fixture
def mock_get_secret():
    with patch('app.authentication.get_secret') as mock:
        mock.return_value = '{"access_token": "test_access_token", "refresh_token": "test_refresh_token", "expires_at": 9999999999}'
        yield mock

@pytest.fixture
def mock_store_tokens():
    with patch('app.authentication.store_tokens') as mock:
        yield mock

@pytest.fixture
def mock_refresh_token():
    with patch('app.authentication.OAuth2Session') as mock:
        instance = mock.return_value
        instance.refresh_token.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600
        }
        yield mock

def test_get_token_valid(mock_get_secret, mock_store_tokens):
    # Arrange
    client_id = "test_client"

    # Act
    token = get_token(client_id)

    # Assert
    assert token['access_token'] == "test_access_token"
    assert token['refresh_token'] == "test_refresh_token"

def test_get_token_expired(mock_get_secret, mock_refresh_token, mock_store_tokens):
    # Arrange
    client_id = "test_client"
    # Set expires_at to past
    mock_get_secret.return_value = '{"access_token": "expired_access_token", "refresh_token": "test_refresh_token", "expires_at": 0}'

    # Act
    token = get_token(client_id)

    # Assert
    assert token['access_token'] == "new_access_token"
    assert token['refresh_token'] == "new_refresh_token"
    mock_refresh_token.assert_called_once()

def test_refresh_token_success(mock_refresh_token):
    # Arrange
    client_id = "test_client"
    refresh_token_str = "test_refresh_token"

    # Act
    new_tokens = refresh_token(client_id, refresh_token_str)

    # Assert
    assert new_tokens['access_token'] == "new_access_token"
    assert new_tokens['refresh_token'] == "new_refresh_token"
    assert 'expires_at' in new_tokens

def test_refresh_token_failure(mock_refresh_token):
    # Arrange
    client_id = "test_client"
    refresh_token_str = "test_refresh_token"
    mock_refresh_token.return_value.refresh_token.side_effect = Exception("Failed to refresh token")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        refresh_token(client_id, refresh_token_str)
    assert "Failed to refresh token" in str(exc_info.value)