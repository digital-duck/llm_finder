# OpenRouter LLM Model Explorer

A comprehensive Streamlit application for exploring and comparing 300+ LLM models available on OpenRouter.ai. This tool helps users discover, filter, and select the right language models for their specific needs.

## Features

- **🤖 Model Database**: Complete listing of 300+ LLM models from OpenRouter.ai
- **🔍 Advanced Search & Filter**: Search by name, description, provider, and pricing category
- **📊 Interactive Visualizations**: Pie charts and bar graphs showing model distribution
- **📋 Data Table**: Sortable, filterable table using AgGrid with advanced filtering capabilities
- **🆓 Free vs Paid Categorization**: Clear separation between free and paid models
- **📚 User Guide**: Comprehensive guide for exploring and selecting models
- **🎯 Model Details**: Detailed information about selected models
- **📱 Responsive Design**: Works on desktop and mobile devices

## Screenshots

The application includes:
- Interactive data table with search and filter capabilities
- Visual analytics showing model distribution
- Detailed model information panels
- User-friendly interface with comprehensive filtering options

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Step 1: Clone or Download the Project

```bash
# If you have the project in a git repository
git clone <repository-url>
cd openrouter-llm-explorer

# Or simply download the files and extract them
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```


```bash
conda activate zai
```
### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Scrape Model Data

Before running the app, you need to scrape the model data from OpenRouter.ai:

```bash
python scrape_models.py
```

This will:
- Fetch model information from https://openrouter.ai/models
- Parse and clean the data
- Categorize models into Free, Paid, and Unknown
- Save the data as `openrouter_models.csv`

**Note**: The scraping process may take a few minutes depending on your internet connection and the website structure.

### Step 5: Run the Streamlit App

```bash
streamlit run app.py
```

The application will automatically open in your default web browser at `http://localhost:8501`

## Usage Guide

### Getting Started

1. **Launch the Application**: After running `streamlit run app.py`, the app will open in your browser
2. **Explore the Dashboard**: The main dashboard shows:
   - Summary metrics (total models, free models, paid models)
   - Interactive visualizations
   - Comprehensive model data table

### Searching and Filtering

#### Sidebar Controls
- **Category Filter**: Filter models by Free, Paid, or Unknown pricing
- **Provider Filter**: Filter by specific model providers (OpenAI, Anthropic, etc.)
- **Search Bar**: Search models by name or description
- **Refresh Data**: Reload the dataset

#### Table Filters
- **Column Headers**: Click the filter icon (≡) on any column header
- **Text Filters**: Use contains, starts with, ends with options
- **Set Filters**: Multi-select filters for categorical data
- **Sort**: Click column headers to sort ascending/descending

### Understanding Model Categories

#### 🆓 Free Models
- No cost to use
- Great for testing and learning
- May have usage limitations
- Examples: Many open-source models

#### 💰 Paid Models
- Require payment or subscription
- Often higher performance
- Better for production use
- Examples: GPT-4, Claude, etc.

#### ❓ Unknown Pricing
- Pricing information not available
- May require checking provider website
- Could be free or paid

### Selecting the Right Model

#### For Testing/Learning
1. Start with **Free** models
2. Look for models with good documentation
3. Test multiple models to compare performance

#### For Production
1. Consider **Paid** models for reliability
2. Check context length for your use case
3. Evaluate provider reputation and support

#### Key Considerations
- **Context Length**: Larger is better for long documents
- **Provider**: Some specialize in specific model types
- **Capabilities**: Match to your specific use case
- **Cost**: Monitor usage costs for paid models

### Interactive Features

#### Visual Analytics
- **Pie Chart**: Shows distribution of Free vs Paid models
- **Bar Chart**: Top 10 providers by model count
- **Real-time Updates**: Charts update based on current filters

#### Model Details
- Click any row in the table to see detailed information
- View model specifications, pricing, and provider details
- Access direct links to model websites when available

## Data Structure

The application uses a CSV file with the following columns:

| Column | Description |
|--------|-------------|
| `name` | Model name |
| `id` | Unique identifier |
| `description` | Model description |
| `category` | Free/Paid/Unknown |
| `pricing` | Pricing information |
| `provider` | Model provider |
| `context_length` | Maximum context size |
| `architecture` | Model architecture |
| `capabilities` | Model capabilities |
| `website` | Official website URL |

## Troubleshooting

### Common Issues

#### "Model data file not found"
- Run `python scrape_models.py` first to generate the data file
- Ensure `openrouter_models.csv` exists in the same directory

#### "Error scraping models"
- Check your internet connection
- The website structure may have changed
- Try running the scraper again later

#### "Module not found" errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check you're using the correct Python environment

#### AgGrid not displaying properly
- Ensure you have a stable internet connection
- Try refreshing the page
- Check browser console for errors

### Performance Tips

- **Large Datasets**: The app handles 300+ models efficiently
- **Filtering**: Use filters to reduce dataset size for better performance
- **Browser**: Use modern browsers (Chrome, Firefox, Safari, Edge)
- **Memory**: Ensure sufficient system memory for large datasets

## Customization

### Adding New Features
- Modify `app.py` to add new visualizations or filters
- Update the scraping logic in `scrape_models.py` for additional data
- Customize the CSS styling in the app.py file

### Data Updates
- Run `python scrape_models.py` periodically to get the latest model data
- The scraper will overwrite the existing CSV file
- Consider scheduling regular updates

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational and research purposes. Please respect the terms of service of OpenRouter.ai when using scraped data.

## Support

For issues or questions:
- Check the troubleshooting section above
- Verify your Python environment and dependencies
- Ensure you have the latest versions of required packages

## Data Source

Model data is sourced from [OpenRouter.ai](https://openrouter.ai/models). Please respect their terms of service and robots.txt file when scraping data.

---

**Built with Streamlit, Pandas, Plotly, and AgGrid** 🚀