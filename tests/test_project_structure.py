"""
Test project structure and basic imports
"""
import pytest
import sys
from pathlib import Path

def test_project_structure():
    """Test that all required directories exist"""
    required_dirs = [
        "src",
        "src/data_collection", 
        "src/data_processing",
        "src/storage",
        "src/models",
        "tests",
        "config"
    ]
    
    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Directory {dir_path} should exist"
        assert Path(dir_path, "__init__.py").exists(), f"__init__.py should exist in {dir_path}"

def test_config_import():
    """Test that configuration can be imported"""
    sys.path.insert(0, str(Path.cwd()))
    
    try:
        from config.settings import S3_BUCKET_NAME, S3_FOLDERS
        assert isinstance(S3_BUCKET_NAME, str)
        assert isinstance(S3_FOLDERS, dict)
        assert len(S3_FOLDERS) > 0
    except ImportError as e:
        pytest.fail(f"Could not import config: {e}")

def test_lambda_handler_import():
    """Test that Lambda handler can be imported"""
    sys.path.insert(0, str(Path.cwd()))
    
    try:
        from lambda_function import lambda_handler
        assert callable(lambda_handler)
    except ImportError as e:
        pytest.fail(f"Could not import lambda_handler: {e}")

def test_requirements_file():
    """Test that requirements.txt exists and has required packages"""
    requirements_file = Path("requirements.txt")
    assert requirements_file.exists(), "requirements.txt should exist"
    
    content = requirements_file.read_text()
    required_packages = ["boto3", "pandas", "requests", "pytest", "hypothesis"]
    
    for package in required_packages:
        assert package in content, f"Package {package} should be in requirements.txt"