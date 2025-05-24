#!/bin/bash
# Grekko Environment Setup Script
# This script sets up the Python environment and fixes import issues

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Export PYTHONPATH to include the project root and src directory
export PYTHONPATH="${SCRIPT_DIR}:${SCRIPT_DIR}/src:${PYTHONPATH}"

# Create necessary directories
mkdir -p logs
mkdir -p data
mkdir -p ~/.grekko

echo "Environment setup complete!"
echo "PYTHONPATH set to: ${PYTHONPATH}"
echo ""
echo "To make these changes permanent, add the following to your ~/.bashrc or ~/.zshrc:"
echo "export PYTHONPATH=\"${SCRIPT_DIR}:${SCRIPT_DIR}/src:\${PYTHONPATH}\""