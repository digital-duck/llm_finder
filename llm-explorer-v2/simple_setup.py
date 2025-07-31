#!/usr/bin/env python3
"""
Simple setup script that creates sample data and provides instructions
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def create_sample_data():
    """Create sample model data"""
    print("📊 Creating sample model data...")
    
    try:
        # Import and run the sample data creation
        import create_sample_data
        success = create_sample_data.main()
        
        if success:
            print("✅ Sample data created successfully")
            return True
        else:
            print("❌ Failed to create sample data")
            return False
            
    except ImportError:
        print("❌ create_sample_data.py not found")
        return False
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'streamlit',
        'pandas',
        'plotly'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Missing packages: {', '.join(missing_packages)}")
        print("Install them with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required dependencies are available")
    return True

def test_app():
    """Test if the app can be imported"""
    print("🧪 Testing app import...")
    
    try:
        # Try to import the app
        import app
        print("✅ App can be imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Cannot import app: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing app: {e}")
        return False

def show_instructions():
    """Show setup and usage instructions"""
    print("\n" + "="*60)
    print("🚀 OpenRouter LLM Model Explorer - Setup Complete!")
    print("="*60)
    
    print("\n📋 What's been created:")
    print("✅ Sample model data (20 models)")
    print("✅ CSV file for the app to use")
    print("✅ Ready-to-run Streamlit application")
    
    print("\n🎯 Next steps:")
    print("1. Install missing dependencies (if any):")
    print("   pip install streamlit pandas plotly")
    print("\n2. Run the application:")
    print("   streamlit run app.py")
    print("\n3. Open your browser when prompted")
    
    print("\n📊 Sample data includes:")
    print("• 20 popular LLM models")
    print("• 13 different providers")
    print("• 15 free models, 5 paid models")
    print("• Detailed model information")
    
    print("\n🔧 If you want to scrape real data:")
    print("1. Install scraping dependencies:")
    print("   pip install requests beautifulsoup4 lxml")
    print("\n2. Run the scraper:")
    print("   python scrape_models.py")
    
    print("\n📚 For more information:")
    print("• Read README.md for detailed instructions")
    print("• Check QUICKSTART.md for fast setup")
    print("• View app.py for source code")
    
    print("\n" + "="*60)

def main():
    """Main setup function"""
    print("🚀 OpenRouter LLM Model Explorer - Simple Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create sample data
    if not create_sample_data():
        print("\n❌ Setup failed at sample data creation")
        sys.exit(1)
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Test app import
    app_ok = test_app()
    
    # Show instructions
    show_instructions()
    
    # Final status
    if deps_ok and app_ok:
        print("\n🎉 Setup completed successfully!")
        print("   You can now run: streamlit run app.py")
    else:
        print("\n⚠️  Setup completed with warnings")
        print("   You may need to install missing dependencies")
        print("   But the sample data is ready for testing")

if __name__ == "__main__":
    main()