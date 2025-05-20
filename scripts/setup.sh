#!/bin/bash
# scripts/setup.sh

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p logs
mkdir -p ~/.grekko

# Set up pre-commit hooks
pip install pre-commit
pre-commit install

# Set up environment variables
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Grekko Environment Configuration
PYTHONPATH=$(pwd)
LOG_LEVEL=INFO
CONFIG_ENV=development

# API Keys (do not fill in - use credentials manager)
OPENAI_API_KEY=
TRADINGVIEW_API_KEY=

# Database
DATABASE_URL=postgresql://grekko:grekkopassword@localhost:5432/grekko

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF
fi

echo "Development environment setup complete."
echo "Run 'source venv/bin/activate' to activate the virtual environment."