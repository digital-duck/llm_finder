#!/usr/bin/env python3
"""
Setup script for OpenRouter LLM Model Explorer
Automates installation and data scraping
"""

import subprocess
import sys
import os
import time

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_requirements():
    """Install required packages"""
    return run_command(
        "pip install -r requirements.txt",
        "Installing required packages"
    )

def scrape_data():
    """Scrape model data from OpenRouter"""
    return run_command(
        "python scrape_models.py",
        "Scraping model data from OpenRouter.ai"
    )

def verify_data_file():
    """Check if data file exists and has content"""
    print("\n🔍 Verifying data file...")
    if os.path.exists('openrouter_models.csv'):
        try:
            import pandas as pd
            df = pd.read_csv('openrouter_models.csv')
            if len(df) > 0:
                print(f"✅ Data file contains {len(df)} models")
                return True
            else:
                print("❌ Data file is empty")
                return False
        except Exception as e:
            print(f"❌ Error reading data file: {e}")
            return False
    else:
        print("❌ Data file not found")
        return False

def main():
    """Main setup function"""
    print("🚀 OpenRouter LLM Model Explorer Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Failed to install requirements. Please check the error messages above.")
        sys.exit(1)
    
    # Scrape data
    if not scrape_data():
        print("\n❌ Failed to scrape data. This could be due to:")
        print("   - Internet connection issues")
        print("   - Website structure changes")
        print("   - Temporary server issues")
        print("\nPlease try again later or check the website manually.")
        sys.exit(1)
    
    # Verify data
    if not verify_data_file():
        print("\n❌ Data verification failed")
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run the app: streamlit run app.py")
    print("2. Open your browser to the provided URL")
    print("3. Start exploring LLM models!")
    
    # Ask if user wants to start the app now
    try:
        response = input("\nWould you like to start the app now? (y/n): ").lower().strip()
        if response == 'y' or response == 'yes':
            print("\n🚀 Starting Streamlit app...")
            time.sleep(2)
            subprocess.run("streamlit run app.py", shell=True)
    except KeyboardInterrupt:
        print("\nSetup completed. You can start the app later with: streamlit run app.py")

if __name__ == "__main__":
    main()