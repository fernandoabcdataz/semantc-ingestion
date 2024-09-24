import pytest
from unittest.mock import patch, MagicMock
from app.table_loader import load_json_to_table
from google.cloud import bigquery

@pytest.fixture
def mock_bigquery_client():
    with patch('app.table_loader.bigquery.Client') as mock:
        yield mock

@pytest.fixture
def mock_storage_client():
    with patch('app.table_loader.storage.Client') as mock:
        yield mock

def test_load_json_to_table_success(mock_bigquery_client, mock_storage_client):
    # Arrange
    mock_bq_instance = mock_bigquery_client.return_value
    mock_storage_instance = mock_storage_client.return_value
    mock_dataset = MagicMock()
    mock_bq_instance.get_dataset.return_value = mock_dataset
    mock_bq_instance.create_dataset.return_value = mock_dataset

    mock_table = MagicMock()
    mock_bq_instance.create_table.return_value = mock_table

    mock_load_job = MagicMock()
    mock_load_job.result.return_value = None
    mock_bq_instance.load_table_from_uri.return_value = mock_load_job

    # Act
    load_json_to_table()

    # Assert
    mock_bq_instance.get_dataset.assert_called_once()
    mock_bq_instance.create_dataset.assert_not_called()  # Dataset exists
    mock_bq_instance.create_table.assert_called()
    mock_bq_instance.load_table_from_uri.assert_called()
    mock_load_job.result.assert_called_once()

def test_load_json_to_table_dataset_not_found(mock_bigquery_client, mock_storage_client):
    # Arrange
    mock_bq_instance = mock_bigquery_client.return_value
    mock_bq_instance.get_dataset.side_effect = bigquery.NotFound("Dataset not found")
    mock_bq_instance.create_dataset.return_value = MagicMock()

    mock_table = MagicMock()
    mock_bq_instance.create_table.return_value = mock_table

    mock_load_job = MagicMock()
    mock_load_job.result.return_value = None
    mock_bq_instance.load_table_from_uri.return_value = mock_load_job

    # Act
    load_json_to_table()

    # Assert
    mock_bq_instance.get_dataset.assert_called_once()
    mock_bq_instance.create_dataset.assert_called_once()
    mock_bq_instance.create_table.assert_called()
    mock_bq_instance.load_table_from_uri.assert_called()
    mock_load_job.result.assert_called_once()

def test_load_json_to_table_failure(mock_bigquery_client, mock_storage_client):
    # Arrange
    mock_bq_instance = mock_bigquery_client.return_value
    mock_bq_instance.get_dataset.return_value = MagicMock()

    mock_bq_instance.create_table.side_effect = Exception("Table creation failed")

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        load_json_to_table()
    assert "Table creation failed" in str(exc_info.value)