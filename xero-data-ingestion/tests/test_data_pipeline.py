import pytest
from unittest.mock import patch, MagicMock
from app.data_pipeline import run_pipeline, process_endpoint

@pytest.fixture
def mock_fetch_data():
    with patch('app.data_pipeline.fetch_data_from_endpoint') as mock:
        mock.return_value = [{"InvoiceID": "1"}, {"InvoiceID": "2"}]
        yield mock

@pytest.fixture
def mock_write_gcs():
    with patch('app.data_pipeline.write_json_to_gcs') as mock:
        yield mock

def test_process_endpoint_success(mock_fetch_data, mock_write_gcs):
    # Arrange
    name_endpoint = ("invoices", "https://api.xero.com/api.xro/2.0/Invoices")
    client_id = "test_client"

    # Act
    asyncio.run(process_endpoint(name_endpoint))

    # Assert
    mock_fetch_data.assert_called_with("https://api.xero.com/api.xro/2.0/Invoices", "test_client", 0, 100)
    mock_write_gcs.assert_called_once()
    args, kwargs = mock_write_gcs.call_args
    assert args[0] == "test_project-test_client-xero-data"
    assert args[1] == "invoices.json"
    assert '"InvoiceID": "1"' in args[2]

def test_process_endpoint_no_data(mock_fetch_data, mock_write_gcs):
    # Arrange
    name_endpoint = ("invoices", "https://api.xero.com/api.xro/2.0/Invoices")
    mock_fetch_data.return_value = []

    # Act
    asyncio.run(process_endpoint(name_endpoint))

    # Assert
    mock_fetch_data.assert_called_once()
    mock_write_gcs.assert_not_called()

def test_process_endpoint_failure(mock_fetch_data, mock_write_gcs):
    # Arrange
    name_endpoint = ("invoices", "https://api.xero.com/api.xro/2.0/Invoices")
    mock_fetch_data.side_effect = Exception("API failure")

    # Act
    asyncio.run(process_endpoint(name_endpoint))

    # Assert
    mock_write_gcs.assert_not_called()