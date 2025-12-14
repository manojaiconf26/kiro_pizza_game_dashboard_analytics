"""
S3 Storage Service for Pizza Game Dashboard

This module provides S3 storage operations with proper authentication,
error handling, and data organization according to the bucket structure
defined in the design document.
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from botocore.exceptions import ClientError, NoCredentialsError, BotoCoreError
from dataclasses import asdict
from io import StringIO, BytesIO

from config.settings import S3_BUCKET_NAME, AWS_REGION, S3_FOLDERS


class S3StorageError(Exception):
    """Custom exception for S3 storage operations"""
    pass


class S3Service:
    """
    S3 Storage Service for managing pizza order and football match data.
    
    Provides methods for uploading, downloading, and organizing data in S3
    with proper error handling and metadata preservation.
    """
    
    def __init__(self, bucket_name: str = None, region: str = None):
        """
        Initialize S3 service with proper authentication.
        
        Args:
            bucket_name: S3 bucket name (defaults to config setting)
            region: AWS region (defaults to config setting)
        """
        self.bucket_name = bucket_name or S3_BUCKET_NAME
        self.region = region or AWS_REGION
        self.logger = logging.getLogger(__name__)
        
        try:
            # Initialize S3 client with proper error handling
            self.s3_client = boto3.client('s3', region_name=self.region)
            self.s3_resource = boto3.resource('s3', region_name=self.region)
            
            # Verify bucket access
            self._verify_bucket_access()
            
        except NoCredentialsError:
            raise S3StorageError(
                "AWS credentials not found. Please configure AWS credentials."
            )
        except Exception as e:
            raise S3StorageError(f"Failed to initialize S3 client: {str(e)}")
    
    def _verify_bucket_access(self) -> None:
        """
        Verify that the S3 bucket exists and is accessible.
        
        Raises:
            S3StorageError: If bucket is not accessible
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            self.logger.info(f"Successfully connected to S3 bucket: {self.bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise S3StorageError(f"S3 bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                raise S3StorageError(f"Access denied to S3 bucket '{self.bucket_name}'")
            else:
                raise S3StorageError(f"Error accessing S3 bucket: {str(e)}")
    
    def _generate_file_key(self, data_type: str, data_source: str, 
                          filename: str, timestamp: datetime = None) -> str:
        """
        Generate S3 object key with proper naming conventions.
        
        Args:
            data_type: Type of data ('dominos-orders' or 'football-data')
            data_source: Source of data ('real' or 'mock')
            filename: Base filename
            timestamp: Optional timestamp for file organization
            
        Returns:
            Properly formatted S3 object key
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Determine folder based on data type and source
        if data_type == 'dominos-orders':
            if data_source == 'real':
                folder = S3_FOLDERS['raw_dominos_real']
            else:
                folder = S3_FOLDERS['raw_dominos_mock']
        elif data_type == 'football-data':
            if data_source == 'real':
                folder = S3_FOLDERS['raw_football_real']
            else:
                folder = S3_FOLDERS['raw_football_mock']
        elif data_type == 'merged-datasets':
            folder = S3_FOLDERS['processed_merged']
        elif data_type == 'correlation-analysis':
            folder = S3_FOLDERS['processed_correlation']
        elif data_type == 'dashboard-data':
            folder = S3_FOLDERS['quicksight_data']
        elif data_type == 'metadata':
            folder = S3_FOLDERS['quicksight_metadata']
        else:
            raise S3StorageError(f"Unknown data type: {data_type}")
        
        # Create timestamped filename
        date_str = timestamp.strftime('%Y/%m/%d')
        timestamp_str = timestamp.strftime('%Y%m%d_%H%M%S')
        
        # Ensure filename has proper extension
        if not any(filename.endswith(ext) for ext in ['.json', '.csv', '.parquet']):
            filename = f"{filename}.json"
        
        return f"{folder}{date_str}/{timestamp_str}_{filename}"
    
    def _create_metadata(self, data_source: str, data_type: str, 
                        record_count: int = None, **kwargs) -> Dict[str, str]:
        """
        Create metadata for S3 object with data source labeling.
        
        Args:
            data_source: Source of data ('real' or 'mock')
            data_type: Type of data
            record_count: Number of records in the file
            **kwargs: Additional metadata fields
            
        Returns:
            Dictionary of metadata for S3 object
        """
        metadata = {
            'data-source': data_source,
            'data-type': data_type,
            'upload-timestamp': datetime.utcnow().isoformat(),
            'system': 'pizza-game-dashboard'
        }
        
        if record_count is not None:
            metadata['record-count'] = str(record_count)
        
        # Add any additional metadata
        for key, value in kwargs.items():
            metadata[key.replace('_', '-')] = str(value)
        
        return metadata
    
    def upload_json_data(self, data: Union[List[Dict], Dict], data_type: str, 
                        data_source: str, filename: str = None, 
                        timestamp: datetime = None, **metadata_kwargs) -> str:
        """
        Upload JSON data to S3 with proper organization and metadata.
        
        Args:
            data: Data to upload (list of dicts or single dict)
            data_type: Type of data ('dominos-orders', 'football-data', etc.)
            data_source: Source of data ('real' or 'mock')
            filename: Optional custom filename
            timestamp: Optional timestamp for organization
            **metadata_kwargs: Additional metadata fields
            
        Returns:
            S3 object key of uploaded file
            
        Raises:
            S3StorageError: If upload fails
        """
        try:
            # Generate filename if not provided
            if filename is None:
                filename = f"{data_type}_{data_source}_data"
            
            # Generate S3 key with proper naming convention
            s3_key = self._generate_file_key(data_type, data_source, filename, timestamp)
            
            # Convert data to JSON string
            json_data = json.dumps(data, indent=2, default=str)
            
            # Determine record count
            record_count = len(data) if isinstance(data, list) else 1
            
            # Create metadata with data source labeling
            metadata = self._create_metadata(
                data_source, data_type, record_count, **metadata_kwargs
            )
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json_data,
                ContentType='application/json',
                Metadata=metadata
            )
            
            self.logger.info(f"Successfully uploaded JSON data to s3://{self.bucket_name}/{s3_key}")
            return s3_key
            
        except Exception as e:
            raise S3StorageError(f"Failed to upload JSON data: {str(e)}")
    
    # CSV methods disabled to avoid pandas dependency
    # def upload_csv_data(self, data: Union[pd.DataFrame, List[Dict]], data_type: str,
    #                    data_source: str, filename: str = None,
    #                    timestamp: datetime = None, **metadata_kwargs) -> str:
    #     """
    #     Upload CSV data to S3 with proper organization and metadata.
    #     
    #     Args:
    #         data: Data to upload (DataFrame or list of dicts)
    #         data_type: Type of data
    #         data_source: Source of data ('real' or 'mock')
    #         filename: Optional custom filename
    #         timestamp: Optional timestamp for organization
    #         **metadata_kwargs: Additional metadata fields
    #         
    #     Returns:
    #         S3 object key of uploaded file
    #     """
    #     try:
    #         # Convert to DataFrame if needed
    #         if isinstance(data, list):
    #             df = pd.DataFrame(data)
    #         else:
    #             df = data
    #         
    #         # Generate filename if not provided
    #         if filename is None:
    #             filename = f"{data_type}_{data_source}_data.csv"
    #         elif not filename.endswith('.csv'):
    #             filename = f"{filename}.csv"
    #         
    #         # Generate S3 key
    #         s3_key = self._generate_file_key(data_type, data_source, filename, timestamp)
    #         
    #         # Convert DataFrame to CSV string
    #         csv_buffer = StringIO()
    #         df.to_csv(csv_buffer, index=False)
    #         csv_data = csv_buffer.getvalue()
    #         
    #         # Create metadata
    #         metadata = self._create_metadata(
    #             data_source, data_type, len(df), **metadata_kwargs
    #         )
    #         
    #         # Upload to S3
    #         self.s3_client.put_object(
    #             Bucket=self.bucket_name,
    #             Key=s3_key,
    #             Body=csv_data,
    #             ContentType='text/csv',
    #             Metadata=metadata
    #         )
    #         
    #         self.logger.info(f"Successfully uploaded CSV data to s3://{self.bucket_name}/{s3_key}")
    #         return s3_key
    #         
    #     except Exception as e:
    #         raise S3StorageError(f"Failed to upload CSV data: {str(e)}")
    
    def download_json_data(self, s3_key: str) -> Union[List[Dict], Dict]:
        """
        Download and parse JSON data from S3.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Parsed JSON data
            
        Raises:
            S3StorageError: If download or parsing fails
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            json_data = response['Body'].read().decode('utf-8')
            
            self.logger.info(f"Successfully downloaded JSON data from s3://{self.bucket_name}/{s3_key}")
            return json.loads(json_data)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise S3StorageError(f"File not found: {s3_key}")
            else:
                raise S3StorageError(f"Failed to download file: {str(e)}")
        except json.JSONDecodeError as e:
            raise S3StorageError(f"Failed to parse JSON data: {str(e)}")
        except Exception as e:
            raise S3StorageError(f"Unexpected error downloading JSON data: {str(e)}")
    
    # def download_csv_data(self, s3_key: str) -> pd.DataFrame:
    #     """
    #     Download and parse CSV data from S3.
    #     
    #     Args:
    #         s3_key: S3 object key
    #         
    #     Returns:
    #         DataFrame with CSV data
    #         
    #     Raises:
    #         S3StorageError: If download or parsing fails
    #     """
    #     try:
    #         response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
    #         csv_data = response['Body'].read().decode('utf-8')
    #         
    #         # Parse CSV data
    #         csv_buffer = StringIO(csv_data)
    #         df = pd.read_csv(csv_buffer)
    #         
    #         self.logger.info(f"Successfully downloaded CSV data from s3://{self.bucket_name}/{s3_key}")
    #         return df
    #         
    #     except ClientError as e:
    #         if e.response['Error']['Code'] == 'NoSuchKey':
    #             raise S3StorageError(f"File not found: {s3_key}")
    #         else:
    #             raise S3StorageError(f"Failed to download file: {str(e)}")
        except Exception as e:
            raise S3StorageError(f"Unexpected error downloading CSV data: {str(e)}")
    
    def list_files(self, data_type: str = None, data_source: str = None, 
                   prefix: str = None) -> List[Dict[str, Any]]:
        """
        List files in S3 bucket with optional filtering.
        
        Args:
            data_type: Filter by data type
            data_source: Filter by data source ('real' or 'mock')
            prefix: Custom prefix to filter by
            
        Returns:
            List of file information dictionaries
        """
        try:
            # Determine prefix based on filters
            if prefix is None and data_type and data_source:
                if data_type == 'dominos-orders':
                    prefix = S3_FOLDERS['raw_dominos_real'] if data_source == 'real' else S3_FOLDERS['raw_dominos_mock']
                elif data_type == 'football-data':
                    prefix = S3_FOLDERS['raw_football_real'] if data_source == 'real' else S3_FOLDERS['raw_football_mock']
            elif prefix is None:
                prefix = ''
            
            # List objects
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Get object metadata
                    try:
                        head_response = self.s3_client.head_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        metadata = head_response.get('Metadata', {})
                    except:
                        metadata = {}
                    
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'metadata': metadata
                    })
            
            self.logger.info(f"Listed {len(files)} files with prefix '{prefix}'")
            return files
            
        except Exception as e:
            raise S3StorageError(f"Failed to list files: {str(e)}")
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Delete a file from S3.
        
        Args:
            s3_key: S3 object key to delete
            
        Returns:
            True if deletion was successful
            
        Raises:
            S3StorageError: If deletion fails
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            self.logger.info(f"Successfully deleted file: s3://{self.bucket_name}/{s3_key}")
            return True
            
        except Exception as e:
            raise S3StorageError(f"Failed to delete file {s3_key}: {str(e)}")
    
    def get_file_metadata(self, s3_key: str) -> Dict[str, Any]:
        """
        Get metadata for a specific S3 object.
        
        Args:
            s3_key: S3 object key
            
        Returns:
            Dictionary containing file metadata
            
        Raises:
            S3StorageError: If metadata retrieval fails
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType', ''),
                'metadata': response.get('Metadata', {}),
                'etag': response['ETag']
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise S3StorageError(f"File not found: {s3_key}")
            else:
                raise S3StorageError(f"Failed to get metadata: {str(e)}")
        except Exception as e:
            raise S3StorageError(f"Unexpected error getting metadata: {str(e)}")
    
    def upload_dataclass_objects(self, objects: List[Any], data_type: str,
                                data_source: str, filename: str = None,
                                timestamp: datetime = None, **metadata_kwargs) -> str:
        """
        Upload dataclass objects (like DominosOrder, FootballMatch) to S3 as JSON.
        
        Args:
            objects: List of dataclass objects
            data_type: Type of data
            data_source: Source of data ('real' or 'mock')
            filename: Optional custom filename
            timestamp: Optional timestamp for organization
            **metadata_kwargs: Additional metadata fields
            
        Returns:
            S3 object key of uploaded file
        """
        try:
            # Convert dataclass objects to dictionaries
            data = [asdict(obj) for obj in objects]
            
            return self.upload_json_data(
                data, data_type, data_source, filename, timestamp, **metadata_kwargs
            )
            
        except Exception as e:
            raise S3StorageError(f"Failed to upload dataclass objects: {str(e)}")