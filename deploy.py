#!/usr/bin/env python3
"""
Deployment script for Pizza Game Dashboard Lambda function
Creates deployment package and uploads to AWS Lambda
"""
import os
import sys
import zipfile
import subprocess
from pathlib import Path

def create_deployment_package():
    """
    Create a deployment package for Lambda function
    """
    print("Creating Lambda deployment package...")
    
    # Create deployment directory
    deploy_dir = Path("deploy")
    deploy_dir.mkdir(exist_ok=True)
    
    # Install dependencies to deployment directory
    print("Installing dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install", 
        "-r", "requirements.txt", 
        "-t", str(deploy_dir)
    ], check=True)
    
    # Copy source code to deployment directory
    print("Copying source code...")
    
    # Copy main Lambda handler
    subprocess.run(["cp", "lambda_function.py", str(deploy_dir)], check=True)
    
    # Copy source packages
    subprocess.run(["cp", "-r", "src", str(deploy_dir)], check=True)
    subprocess.run(["cp", "-r", "config", str(deploy_dir)], check=True)
    
    # Create ZIP file
    zip_path = "pizza-game-dashboard.zip"
    print(f"Creating ZIP file: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
    
    print(f"Deployment package created: {zip_path}")
    print(f"Package size: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")
    
    return zip_path

def deploy_with_sam():
    """
    Deploy using SAM CLI
    """
    print("Deploying with SAM CLI...")
    
    # Build the application
    subprocess.run(["sam", "build"], check=True)
    
    # Deploy the application
    subprocess.run([
        "sam", "deploy", 
        "--guided",  # Interactive deployment
        "--stack-name", "pizza-game-dashboard",
        "--capabilities", "CAPABILITY_IAM"
    ], check=True)

def main():
    """
    Main deployment function
    """
    if len(sys.argv) > 1 and sys.argv[1] == "--sam":
        deploy_with_sam()
    else:
        create_deployment_package()
        print("\nDeployment package created successfully!")
        print("To deploy:")
        print("1. Upload pizza-game-dashboard.zip to AWS Lambda console")
        print("2. Or use: python deploy.py --sam (requires SAM CLI)")

if __name__ == "__main__":
    main()