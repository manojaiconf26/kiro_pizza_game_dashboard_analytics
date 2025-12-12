# Pizza Game Dashboard - Development Makefile

.PHONY: setup install test clean deploy package lint format

# Setup development environment
setup:
	python setup_dev.py

# Install dependencies
install:
	pip install -r requirements.txt

# Run tests
test:
	python -m pytest tests/ -v

# Run property-based tests specifically
test-properties:
	python -m pytest tests/ -v -k "property"

# Clean build artifacts
clean:
	rm -rf deploy/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	rm -rf src/__pycache__/
	rm -rf tests/__pycache__/
	rm -f pizza-game-dashboard.zip

# Create deployment package
package:
	python deploy.py

# Deploy with SAM
deploy:
	python deploy.py --sam

# Lint code
lint:
	flake8 src/ tests/ lambda_function.py

# Format code
format:
	black src/ tests/ lambda_function.py

# Run local Lambda function
run-local:
	python lambda_function.py

# Setup AWS CLI (reminder)
aws-setup:
	@echo "Configure AWS CLI with:"
	@echo "aws configure"
	@echo "Ensure you have:"
	@echo "- AWS Access Key ID"
	@echo "- AWS Secret Access Key" 
	@echo "- Default region (e.g., us-east-1)"

# Install SAM CLI (reminder)
sam-setup:
	@echo "Install SAM CLI:"
	@echo "https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html"

# Help
help:
	@echo "Available commands:"
	@echo "  setup        - Setup development environment"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run all tests"
	@echo "  test-properties - Run property-based tests only"
	@echo "  clean        - Clean build artifacts"
	@echo "  package      - Create Lambda deployment package"
	@echo "  deploy       - Deploy with SAM CLI"
	@echo "  lint         - Lint code with flake8"
	@echo "  format       - Format code with black"
	@echo "  run-local    - Run Lambda function locally"
	@echo "  aws-setup    - Show AWS CLI setup instructions"
	@echo "  sam-setup    - Show SAM CLI setup instructions"