# Quick Start Guide

## 🚀 Fast Setup (5 minutes)

### Method 1: Automated Setup (Recommended)

```bash
# Navigate to the project directory
cd openrouter-llm-explorer

# Run the automated setup
python setup.py
```

### Method 2: Manual Setup

```bash
# 1. Install requirements
pip install -r requirements.txt

# 2. Scrape data
python scrape_models.py

# 3. Run the app
streamlit run app.py
```

### Method 3: Using the Run Script

```bash
# Make the script executable (Linux/macOS)
chmod +x run.sh

# Full setup
./run.sh -s

# Or just run the app
./run.sh -r
```

## 📋 What's Included

- ✅ **Data Scraper** (`scrape_models.py`) - Fetches model data from OpenRouter.ai
- ✅ **Streamlit App** (`app.py`) - Interactive web interface
- ✅ **Dependencies** (`requirements.txt`) - All required Python packages
- ✅ **Documentation** (`README.md`) - Complete installation and usage guide
- ✅ **Configuration** (`config.py`) - Customizable settings
- ✅ **Setup Scripts** - Automated installation and setup

## 🎯 Key Features

- **300+ LLM Models**: Complete database from OpenRouter.ai
- **Smart Filtering**: Search by name, description, provider, category
- **Visual Analytics**: Interactive charts and graphs
- **Free vs Paid**: Clear categorization of model pricing
- **Responsive Design**: Works on desktop and mobile
- **User Guide**: Built-in help and selection tips

## 🔧 System Requirements

- **Python**: 3.8 or higher
- **Memory**: 4GB RAM minimum
- **Storage**: 100MB free space
- **Internet**: Required for data scraping

## 🚨 Troubleshooting

### Common Issues

1. **"Module not found"**
   ```bash
   pip install -r requirements.txt
   ```

2. **"Data file not found"**
   ```bash
   python scrape_models.py
   ```

3. **"Python version too old"**
   - Install Python 3.8+ from python.org

4. **Scraping fails**
   - Check internet connection
   - Try again later (website may be temporarily unavailable)

### Getting Help

1. Check the full `README.md` for detailed instructions
2. Review the troubleshooting section
3. Ensure all dependencies are properly installed

## 🎉 Next Steps

After setup:

1. **Open the App**: Your browser will open automatically
2. **Explore Models**: Use filters and search to find models
3. **Compare Options**: Look at free vs paid categories
4. **Select Models**: Click on models for detailed information
5. **Make Decisions**: Use the user guide to choose the right model

## 📊 Expected Results

- **Total Models**: 300+ LLM models
- **Free Models**: ~50-100 models
- **Paid Models**: ~200+ models
- **Providers**: 20+ different providers
- **Load Time**: < 30 seconds for initial setup

---

**Ready to explore LLM models? Run the setup now!** 🤖