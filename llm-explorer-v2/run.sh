#!/bin/bash

# OpenRouter LLM Model Explorer - Run Script
# This script sets up and runs the Streamlit application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python() {
    print_status "Checking Python installation..."
    
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else:
        print_error "Python is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_status "Found Python $PYTHON_VERSION"
    
    # Extract major and minor version
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required. Found $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python version check passed"
}

# Function to check if pip exists
check_pip() {
    print_status "Checking pip installation..."
    
    if command_exists pip3; then
        PIP_CMD="pip3"
    elif command_exists pip; then
        PIP_CMD="pip"
    else
        print_error "pip is not installed. Please install pip."
        exit 1
    fi
    
    print_success "pip installation check passed"
}

# Function to install requirements
install_requirements() {
    print_status "Installing Python requirements..."
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt not found. Please ensure you're in the correct directory."
        exit 1
    fi
    
    $PIP_CMD install -r requirements.txt
    
    if [ $? -eq 0 ]; then
        print_success "Requirements installed successfully"
    else
        print_error "Failed to install requirements"
        exit 1
    fi
}

# Function to scrape data
scrape_data() {
    print_status "Scraping model data from OpenRouter.ai..."
    
    if [ ! -f "scrape_models.py" ]; then
        print_error "scrape_models.py not found. Please ensure you're in the correct directory."
        exit 1
    fi
    
    $PYTHON_CMD scrape_models.py
    
    if [ $? -eq 0 ]; then
        print_success "Data scraping completed"
    else
        print_error "Failed to scrape data"
        exit 1
    fi
}

# Function to check if data file exists
check_data_file() {
    print_status "Checking data file..."
    
    if [ -f "openrouter_models.csv" ]; then
        # Check if file is not empty
        if [ -s "openrouter_models.csv" ]; then
            print_success "Data file exists and is not empty"
            return 0
        else
            print_warning "Data file exists but is empty"
            return 1
        fi
    else
        print_warning "Data file does not exist"
        return 1
    fi
}

# Function to run the Streamlit app
run_app() {
    print_status "Starting Streamlit application..."
    
    if [ ! -f "app.py" ]; then
        print_error "app.py not found. Please ensure you're in the correct directory."
        exit 1
    fi
    
    print_success "Starting application..."
    print_status "The application will open in your default web browser"
    print_status "Press Ctrl+C to stop the application"
    
    streamlit run app.py
}

# Function to show help
show_help() {
    echo "OpenRouter LLM Model Explorer - Run Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -s, --setup         Full setup (install requirements + scrape data)"
    echo "  -i, --install       Install requirements only"
    echo "  -d, --data          Scrape data only"
    echo "  -r, --run           Run app only"
    echo "  -c, --check         Check dependencies and data"
    echo ""
    echo "Examples:"
    echo "  $0 -s    # Full setup and run"
    echo "  $0 -i    # Install requirements only"
    echo "  $0 -d    # Scrape data only"
    echo "  $0 -r    # Run app only"
    echo "  $0       # Check dependencies and run app"
}

# Main script logic
main() {
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        -s|--setup)
            print_status "Starting full setup..."
            check_python
            check_pip
            install_requirements
            scrape_data
            run_app
            ;;
        -i|--install)
            print_status "Installing requirements..."
            check_python
            check_pip
            install_requirements
            print_success "Installation completed"
            ;;
        -d|--data)
            print_status "Scraping data..."
            check_python
            scrape_data
            print_success "Data scraping completed"
            ;;
        -r|--run)
            print_status "Running application..."
            run_app
            ;;
        -c|--check)
            print_status "Checking dependencies and data..."
            check_python
            check_pip
            check_data_file
            print_success "Check completed"
            ;;
        "")
            print_status "Checking dependencies..."
            check_python
            check_pip
            
            if ! check_data_file; then
                print_warning "Data file not found or empty. Scraping data..."
                scrape_data
            fi
            
            run_app
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"