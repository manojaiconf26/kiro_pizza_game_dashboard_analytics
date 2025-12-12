#!/usr/bin/env python3
"""
Local development environment setup for Pizza Game Dashboard
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_virtual_environment():
    """
    Set up Python virtual environment
    """
    print("Setting up virtual environment...")
    
    venv_path = Path("venv")
    if not venv_path.exists():
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("Virtual environment created: venv/")
    else:
        print("Virtual environment already exists: venv/")
    
    # Determine activation script path based on OS
    if os.name == 'nt':  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        pip_path = venv_path / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        activate_script = venv_path / "bin" / "activate"
        pip_path = venv_path / "bin" / "pip"
    
    print(f"To activate: {activate_script}")
    return pip_path

def install_dependencies(pip_path):
    """
    Install project dependencies
    """
    print("Installing dependencies...")
    
    subprocess.run([
        str(pip_path), "install", "-r", "requirements.txt"
    ], check=True)
    
    print("Dependencies installed successfully!")

def create_env_file():
    """
    Create .env file template for local development
    """
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# Pizza Game Dashboard - Local Development Environment Variables

# S3 Configuration
S3_BUCKET_NAME=pizza-game-analytics-dev
AWS_REGION=us-east-1

# API Keys (replace with actual keys)
DOMINOS_API_KEY=your_dominos_api_key_here
FOOTBALL_API_KEY=your_football_api_key_here

# QuickSight Configuration
QUICKSIGHT_ACCOUNT_ID=your_aws_account_id_here

# Development Settings
ENVIRONMENT=development
LOG_LEVEL=DEBUG
"""
        env_file.write_text(env_content)
        print("Created .env file template")
    else:
        print(".env file already exists")

def setup_local_s3_structure():
    """
    Create local folder structure that mirrors S3 for development
    """
    print("Creating local S3 folder structure...")
    
    folders = [
        "local_data/raw-data/dominos-orders/real",
        "local_data/raw-data/dominos-orders/mock",
        "local_data/raw-data/football-data/real", 
        "local_data/raw-data/football-data/mock",
        "local_data/processed-data/merged-datasets",
        "local_data/processed-data/correlation-analysis",
        "local_data/quicksight-ready/dashboard-data",
        "local_data/quicksight-ready/metadata"
    ]
    
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    print("Local data folders created in: local_data/")

def main():
    """
    Main setup function
    """
    print("Setting up Pizza Game Dashboard development environment...")
    
    # Setup virtual environment
    pip_path = setup_virtual_environment()
    
    # Install dependencies
    install_dependencies(pip_path)
    
    # Create environment file
    create_env_file()
    
    # Setup local folder structure
    setup_local_s3_structure()
    
    print("\n" + "="*50)
    print("Development environment setup complete!")
    print("="*50)
    print("Next steps:")
    print("1. Activate virtual environment:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("2. Update .env file with your API keys")
    print("3. Run tests: python -m pytest tests/")
    print("4. Run locally: python lambda_function.py")

if __name__ == "__main__":
    main()