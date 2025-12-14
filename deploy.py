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
    if deploy_dir.exists():
        import shutil
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir(exist_ok=True)
    
    # Install minimal dependencies for Lambda with Linux platform targeting
    print("Installing minimal dependencies for Lambda...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", 
            "-r", "requirements-lambda.txt", 
            "-t", str(deploy_dir),
            "--platform", "linux_x86_64",
            "--implementation", "cp",
            "--python-version", "3.13",
            "--only-binary=:all:",
            "--upgrade"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error installing with Linux platform targeting: {e}")
        print("Trying fallback installation...")
        
        # Fallback: install without platform constraints
        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", 
                "-r", "requirements-lambda.txt", 
                "-t", str(deploy_dir),
                "--upgrade"
            ], check=True)
        except subprocess.CalledProcessError as e2:
            print(f"Error installing dependencies: {e2}")
            return None
    
    # Copy source code to deployment directory
    print("Copying source code...")
    
    # Copy main Lambda handler
    import shutil
    shutil.copy2("lambda_function.py", deploy_dir)
    
    # Copy source packages
    if Path("src").exists():
        shutil.copytree("src", deploy_dir / "src")
    if Path("config").exists():
        shutil.copytree("config", deploy_dir / "config")
    
    # Remove unnecessary files to reduce package size
    print("Cleaning up deployment package...")
    cleanup_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/.pytest_cache",
        "**/tests",
        "**/*.dist-info",
        "**/test_*"
    ]
    
    import glob
    for pattern in cleanup_patterns:
        for path in glob.glob(str(deploy_dir / pattern), recursive=True):
            path_obj = Path(path)
            if path_obj.is_file():
                path_obj.unlink()
            elif path_obj.is_dir():
                shutil.rmtree(path_obj)
    
    # Create ZIP file
    zip_path = "pizza-game-dashboard.zip"
    print(f"Creating ZIP file: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deploy_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deploy_dir)
                zipf.write(file_path, arcname)
    
    # Clean up deployment directory
    shutil.rmtree(deploy_dir)
    
    print(f"Deployment package created: {zip_path}")
    print(f"Package size: {os.path.getsize(zip_path) / 1024 / 1024:.2f} MB")
    
    if os.path.getsize(zip_path) > 50 * 1024 * 1024:  # 50MB limit
        print("WARNING: Package size exceeds 50MB. Consider using Lambda layers for large dependencies.")
    
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