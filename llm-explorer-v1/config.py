"""
Configuration settings for OpenRouter LLM Model Explorer
"""

# Data source configuration
DATA_SOURCE_URL = "https://openrouter.ai/models"
DATA_FILE = "openrouter_models.csv"

# Scraping configuration
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
REQUEST_TIMEOUT = 30  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # seconds

# App configuration
APP_TITLE = "OpenRouter LLM Model Explorer"
APP_ICON = "🤖"
PAGE_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Table configuration
DEFAULT_PAGE_SIZE = 50
MAX_TABLE_HEIGHT = 600
ENABLE_ROW_SELECTION = True

# Category colors and styling
CATEGORY_COLORS = {
    'Free': '#10b981',
    'Paid': '#f59e0b',
    'Unknown': '#6b7280'
}

# Visualization settings
CHART_THEME = "plotly_white"
CHART_HEIGHT = 400
TOP_PROVIDERS_COUNT = 10

# Search and filtering
ENABLE_FUZZY_SEARCH = False
SEARCH_MIN_CHARS = 2
MAX_SEARCH_RESULTS = 1000

# Performance settings
CACHE_TTL = 3600  # 1 hour in seconds
ENABLE_DATA_CACHING = True
MAX_DATA_SIZE_MB = 100

# Export settings
ENABLE_EXPORT = True
EXPORT_FORMATS = ['csv', 'json']
MAX_EXPORT_ROWS = 10000

# Debug settings
DEBUG_MODE = False
LOG_LEVEL = "INFO"
ENABLE_PERFORMANCE_METRICS = False

# Update settings
AUTO_UPDATE_INTERVAL = 24  # hours
CHECK_FOR_UPDATES = True

# API rate limiting
REQUESTS_PER_MINUTE = 60
RESPECT_ROBOTS_TXT = True

# Feature flags
ENABLE_ADVANCED_FILTERS = True
ENABLE_MODEL_COMPARISON = False
ENABLE_FAVORITES = False
ENABLE_NOTES = False