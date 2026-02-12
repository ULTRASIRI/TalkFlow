#!/bin/bash
# TalkFlow Installation Script for macOS/Linux

set -e

echo "========================================"
echo "TalkFlow Installation Script"
echo "========================================"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found: Python $PYTHON_VERSION"

# Check if version is sufficient (3.9+)
MAJOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR_VERSION=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR_VERSION" -lt 3 ] || ([ "$MAJOR_VERSION" -eq 3 ] && [ "$MINOR_VERSION" -lt 9 ]); then
    echo "Error: Python 3.9 or higher required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version is compatible"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv
echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
echo "(This may take 5-10 minutes...)"
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ All dependencies installed successfully"
else
    echo "✗ Error installing dependencies"
    echo "Try running manually: pip install -r requirements.txt"
    exit 1
fi

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Download models: python download_models.py"
echo "  2. Activate environment: source venv/bin/activate"
echo "  3. Start TalkFlow: python run.py"
echo "  4. Open browser: http://localhost:8000"
echo ""
echo "For detailed instructions, see QUICKSTART.md"
echo ""
