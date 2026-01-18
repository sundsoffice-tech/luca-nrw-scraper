#!/bin/bash
# LUCA Command Center Installation Script for Linux/Mac
# This script sets up the Django CRM application

set -e  # Exit on error

echo "=================================="
echo "LUCA Command Center Installation"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    echo "Please install Python 3.9 or higher and try again."
    exit 1
fi

# Get Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Found Python $PYTHON_VERSION${NC}"

# Step 1: Create virtual environment
echo ""
echo "Step 1: Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists. Skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Step 2: Activate virtual environment and install dependencies
echo ""
echo "Step 2: Installing dependencies..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip > /dev/null 2>&1

# Install root requirements
if [ -f "requirements.txt" ]; then
    echo "Installing root requirements.txt..."
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Root requirements installed${NC}"
fi

# Install Django app requirements
if [ -f "telis_recruitment/requirements.txt" ]; then
    echo "Installing telis_recruitment/requirements.txt..."
    pip install -r telis_recruitment/requirements.txt
    echo -e "${GREEN}✓ Django app requirements installed${NC}"
fi

# Step 3: Setup environment variables
echo ""
echo "Step 3: Setting up environment configuration..."
if [ -f ".env" ]; then
    echo -e "${YELLOW}.env file already exists. Skipping...${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from .env.example${NC}"
    echo -e "${YELLOW}⚠ Please edit .env file and set your SECRET_KEY and other settings!${NC}"
fi

# Also copy to telis_recruitment if needed
if [ ! -f "telis_recruitment/.env" ]; then
    cp .env.example telis_recruitment/.env 2>/dev/null && echo -e "${GREEN}✓ Also copied .env to telis_recruitment/${NC}" || echo -e "${YELLOW}⚠ Note: Couldn't copy .env to telis_recruitment/ (may not be needed)${NC}"
fi

# Step 4: Run database migrations
echo ""
echo "Step 4: Running database migrations..."
cd telis_recruitment
python manage.py migrate
echo -e "${GREEN}✓ Database migrations completed${NC}"

# Step 4.5: Setup user groups
echo ""
echo "Step 4.5: Setting up user groups..."
python manage.py setup_groups
echo -e "${GREEN}✓ User groups setup completed${NC}"

# Step 5: Collect static files
echo ""
echo "Step 5: Collecting static files..."
python manage.py collectstatic --noinput > /dev/null 2>&1
echo -e "${GREEN}✓ Static files collected${NC}"

# Step 6: Create superuser (optional)
echo ""
echo "Step 6: Create admin superuser..."
read -p "Do you want to create a superuser now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
    echo -e "${GREEN}✓ Superuser created${NC}"
else
    echo -e "${YELLOW}Skipped. You can create a superuser later with: python manage.py createsuperuser${NC}"
fi

cd ..

# Installation complete
echo ""
echo "=================================="
echo -e "${GREEN}Installation Complete!${NC}"
echo "=================================="
echo ""
echo "To start the LUCA Command Center:"
echo ""
echo "  1. Activate virtual environment:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Navigate to Django app:"
echo "     cd telis_recruitment"
echo ""
echo "  3. Start the development server:"
echo "     python manage.py runserver"
echo ""
echo "  4. Open your browser and visit:"
echo "     http://127.0.0.1:8000/crm/"
echo ""
echo "For production deployment, see docs/DEPLOYMENT.md"
echo ""
echo -e "${YELLOW}Important: Don't forget to edit .env with your SECRET_KEY and API keys!${NC}"
echo ""
