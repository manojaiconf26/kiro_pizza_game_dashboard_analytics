"""
Tests for S3 Storage Service

These tests verify the S3 service functionality including proper error handling,
data organization, and metadata preservation.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from dataclasses import dataclass

from src.storage.s3_service import S3Service, S3StorageError
from src.models.pizza_order import DominosOrder
from src.models.football_match import FootballMatch


@dataclass
class MockDataclass:
    """Mock dataclass for testing"""
    id: str
    value: int
    timestamp: datetime


class TestS3Service:
    """Test cases for S3Service"""
    
    @patch('src.storage.s3_service.boto3')
    def test_s3_service_initialization_success(self, mock_boto3):
        """Test successful S3 service initialization"""
        # Mock successful boto3 client creation
        mock_client = Mock()
        mock_resource = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = mock_resource
        
        # Mock successful bucket access verification
        mock_client.head_bucket.return_value = {}
        
        # Initialize service
        service = S3Service(bucket_name='test-bucket', region='us-east-1')
        
        # Verify initialization
        assert service.bucket_name == 'test-bucket'
        assert service.region == 'us-east-1'
        assert service.s3_client == mock_client
        assert service.s3_resource == mock_resource
        
        # Verify bucket access was checked
        mock_client.head_bucket.assert_called_once_with(Bucket='test-bucket')
    
    @patch('src.storage.s3_service.boto3')
    def test_s3_service_initialization_no_credentials(self, mock_boto3):
        """Test S3 service initialization with no credentials"""
        from botocore.exceptions import NoCredentialsError
        
        # Mock NoCredentialsError
        mock_boto3.client.side_effect = NoCredentialsError()
        
        # Verify exception is raised
        with pytest.raises(S3StorageError, match="AWS credentials not found"):
            S3Service()
    
    @patch('src.storage.s3_service.boto3')
    def test_s3_service_bucket_not_found(self, mock_boto3):
        """Test S3 service initialization with non-existent bucket"""
        from botocore.exceptions import ClientError
        
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        
        # Mock bucket not found error
        error_response = {'Error': {'Code': '404'}}
        mock_client.head_bucket.side_effect = ClientError(error_response, 'HeadBucket')
        
        # Verify exception is raised
        with pytest.raises(S3StorageError, match="S3 bucket .* not found"):
            S3Service(bucket_name='non-existent-bucket')
    
    @patch('src.storage.s3_service.boto3')
    def test_generate_file_key_dominos_real(self, mock_boto3):
        """Test file key generation for real Domino's data"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        timestamp = datetime(2024, 1, 15, 14, 30, 0)
        
        key = service._generate_file_key(
            'dominos-orders', 'real', 'orders_data', timestamp
        )
        
        expected = 'raw-data/dominos-orders/real/2024/01/15/20240115_143000_orders_data.json'
        assert key == expected
    
    @patch('src.storage.s3_service.boto3')
    def test_generate_file_key_football_mock(self, mock_boto3):
        """Test file key generation for mock football data"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        timestamp = datetime(2024, 1, 15, 14, 30, 0)
        
        key = service._generate_file_key(
            'football-data', 'mock', 'match_data.csv', timestamp
        )
        
        expected = 'raw-data/football-data/mock/2024/01/15/20240115_143000_match_data.csv'
        assert key == expected
    
    @patch('src.storage.s3_service.boto3')
    def test_create_metadata(self, mock_boto3):
        """Test metadata creation with data source labeling"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        metadata = service._create_metadata(
            'real', 'dominos-orders', 100, 
            collection_method='api', store_id='12345'
        )
        
        # Verify required metadata fields
        assert metadata['data-source'] == 'real'
        assert metadata['data-type'] == 'dominos-orders'
        assert metadata['record-count'] == '100'
        assert metadata['system'] == 'pizza-game-dashboard'
        assert metadata['collection-method'] == 'api'
        assert metadata['store-id'] == '12345'
        assert 'upload-timestamp' in metadata
    
    @patch('src.storage.s3_service.boto3')
    def test_upload_json_data_success(self, mock_boto3):
        """Test successful JSON data upload"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        test_data = [{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'test2'}]
        timestamp = datetime(2024, 1, 15, 14, 30, 0)
        
        s3_key = service.upload_json_data(
            test_data, 'dominos-orders', 'mock', 'test_data', timestamp
        )
        
        # Verify S3 put_object was called correctly
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        
        assert call_args[1]['Bucket'] == service.bucket_name
        assert 'raw-data/dominos-orders/mock' in call_args[1]['Key']
        assert call_args[1]['ContentType'] == 'application/json'
        
        # Verify metadata includes data source labeling
        metadata = call_args[1]['Metadata']
        assert metadata['data-source'] == 'mock'
        assert metadata['data-type'] == 'dominos-orders'
        assert metadata['record-count'] == '2'
        
        # Verify JSON data is properly formatted
        uploaded_data = json.loads(call_args[1]['Body'])
        assert uploaded_data == test_data
    
    @patch('src.storage.s3_service.boto3')
    def test_upload_csv_data_success(self, mock_boto3):
        """Test successful CSV data upload"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        # Test with DataFrame
        df = pd.DataFrame([{'id': 1, 'name': 'test'}, {'id': 2, 'name': 'test2'}])
        timestamp = datetime(2024, 1, 15, 14, 30, 0)
        
        s3_key = service.upload_csv_data(
            df, 'football-data', 'real', 'match_data', timestamp
        )
        
        # Verify S3 put_object was called correctly
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        
        assert call_args[1]['Bucket'] == service.bucket_name
        assert 'raw-data/football-data/real' in call_args[1]['Key']
        assert call_args[1]['ContentType'] == 'text/csv'
        
        # Verify metadata
        metadata = call_args[1]['Metadata']
        assert metadata['data-source'] == 'real'
        assert metadata['data-type'] == 'football-data'
        assert metadata['record-count'] == '2'
    
    @patch('src.storage.s3_service.boto3')
    def test_download_json_data_success(self, mock_boto3):
        """Test successful JSON data download"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        # Mock S3 response
        test_data = [{'id': 1, 'name': 'test'}]
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = json.dumps(test_data).encode('utf-8')
        mock_client.get_object.return_value = mock_response
        
        # Download data
        result = service.download_json_data('test/key.json')
        
        # Verify result
        assert result == test_data
        mock_client.get_object.assert_called_once_with(
            Bucket=service.bucket_name, Key='test/key.json'
        )
    
    @patch('src.storage.s3_service.boto3')
    def test_download_json_data_file_not_found(self, mock_boto3):
        """Test JSON data download with file not found"""
        from botocore.exceptions import ClientError
        
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        # Mock file not found error
        error_response = {'Error': {'Code': 'NoSuchKey'}}
        mock_client.get_object.side_effect = ClientError(error_response, 'GetObject')
        
        # Verify exception is raised
        with pytest.raises(S3StorageError, match="File not found"):
            service.download_json_data('nonexistent/key.json')
    
    @patch('src.storage.s3_service.boto3')
    def test_upload_dataclass_objects(self, mock_boto3):
        """Test uploading dataclass objects"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        # Create test dataclass objects
        objects = [
            MockDataclass('1', 100, datetime(2024, 1, 15)),
            MockDataclass('2', 200, datetime(2024, 1, 16))
        ]
        
        timestamp = datetime(2024, 1, 15, 14, 30, 0)
        
        s3_key = service.upload_dataclass_objects(
            objects, 'dominos-orders', 'mock', 'test_objects', timestamp
        )
        
        # Verify S3 put_object was called
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        
        # Verify the data was converted to dictionaries
        uploaded_data = json.loads(call_args[1]['Body'])
        assert len(uploaded_data) == 2
        assert uploaded_data[0]['id'] == '1'
        assert uploaded_data[0]['value'] == 100
        assert uploaded_data[1]['id'] == '2'
        assert uploaded_data[1]['value'] == 200
    
    @patch('src.storage.s3_service.boto3')
    def test_list_files_with_filters(self, mock_boto3):
        """Test listing files with data type and source filters"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        # Mock S3 list response
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'raw-data/dominos-orders/real/2024/01/15/test1.json',
                    'Size': 1024,
                    'LastModified': datetime(2024, 1, 15)
                },
                {
                    'Key': 'raw-data/dominos-orders/real/2024/01/16/test2.json',
                    'Size': 2048,
                    'LastModified': datetime(2024, 1, 16)
                }
            ]
        }
        
        # Mock head_object for metadata
        mock_client.head_object.return_value = {
            'Metadata': {'data-source': 'real', 'data-type': 'dominos-orders'}
        }
        
        # List files
        files = service.list_files('dominos-orders', 'real')
        
        # Verify results
        assert len(files) == 2
        assert files[0]['key'] == 'raw-data/dominos-orders/real/2024/01/15/test1.json'
        assert files[0]['size'] == 1024
        assert files[0]['metadata']['data-source'] == 'real'
        
        # Verify correct prefix was used
        mock_client.list_objects_v2.assert_called_once_with(
            Bucket=service.bucket_name,
            Prefix='raw-data/dominos-orders/real/'
        )
    
    @patch('src.storage.s3_service.boto3')
    def test_get_file_metadata(self, mock_boto3):
        """Test getting file metadata"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        # Mock head_object response
        mock_client.head_object.return_value = {
            'ContentLength': 1024,
            'LastModified': datetime(2024, 1, 15),
            'ContentType': 'application/json',
            'Metadata': {'data-source': 'real', 'data-type': 'dominos-orders'},
            'ETag': '"abc123"'
        }
        
        # Get metadata
        metadata = service.get_file_metadata('test/key.json')
        
        # Verify metadata
        assert metadata['size'] == 1024
        assert metadata['content_type'] == 'application/json'
        assert metadata['metadata']['data-source'] == 'real'
        assert metadata['etag'] == '"abc123"'
    
    @patch('src.storage.s3_service.boto3')
    def test_delete_file_success(self, mock_boto3):
        """Test successful file deletion"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        mock_boto3.resource.return_value = Mock()
        mock_client.head_bucket.return_value = {}
        
        service = S3Service()
        
        # Delete file
        result = service.delete_file('test/key.json')
        
        # Verify deletion
        assert result is True
        mock_client.delete_object.assert_called_once_with(
            Bucket=service.bucket_name, Key='test/key.json'
        )


if __name__ == '__main__':
    pytest.main([__file__])