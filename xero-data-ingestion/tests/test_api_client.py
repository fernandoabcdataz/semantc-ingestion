import pytest
from unittest.mock import patch
from app.api_client import fetch_data_from_endpoint

@pytest.fixture
def mock_get_token():
    with patch('app.authentication.get_token') as mock:
        mock.return_value = {"access_token": "test_access_token"}
        yield mock

@pytest.fixture
def mock_requests_get():
    with patch('app.api_client.requests.Session.get') as mock:
        yield mock

def test_fetch_data_from_endpoint_success(mock_requests_get, mock_get_token):
    # Arrange
    endpoint = "https://api.xero.com/api.xro/2.0/Invoices"
    client_id = "test_client"
    mock_response = mock_requests_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Invoices": [{"InvoiceID": "1"}, {"InvoiceID": "2"}]
    }

    # Act
    data = fetch_data_from_endpoint(endpoint, client_id)

    # Assert
    assert len(data) == 2
    assert data[0]['InvoiceID'] == "1"

def test_fetch_data_from_endpoint_rate_limit(mock_requests_get, mock_get_token):
    # Arrange
    endpoint = "https://api.xero.com/api.xro/2.0/Invoices"
    client_id = "test_client"
    mock_response = mock_requests_get.return_value
    mock_response.status_code = 429  # Rate limit exceeded
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        fetch_data_from_endpoint(endpoint, client_id)
    assert "Rate limit exceeded" in str(exc_info.value)

def test_fetch_data_from_endpoint_no_data(mock_requests_get, mock_get_token):
    # Arrange
    endpoint = "https://api.xero.com/api.xro/2.0/Invoices"
    client_id = "test_client"
    mock_response = mock_requests_get.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = {}

    # Act
    data = fetch_data_from_endpoint(endpoint, client_id)

    # Assert
    assert data == []