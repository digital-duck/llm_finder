#!/usr/bin/env python3
"""
Script to test the enhanced OpenRouter model scraper and compare with API results.
"""

import asyncio
import json
import logging
from scrape_models import scrape_openrouter_models
from openrouter_api import get_openrouter_models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_and_compare():
    """Test both scraping and API methods and compare results."""
    
    print("=== Testing OpenRouter Model Data Collection ===\n")
    
    # Test API method
    print("1. Fetching models from OpenRouter API...")
    try:
        api_models = await get_openrouter_models()
        print(f"   API returned {len(api_models)} models")
        
        # Show first few models as sample
        print("\n   Sample API models:")
        for i, model in enumerate(api_models[:3]):
            print(f"   {i+1}. {model.get('id', 'Unknown ID')} - {model.get('name', 'Unknown name')}")
    except Exception as e:
        print(f"   Error fetching from API: {e}")
        api_models = []
    
    # Test scraping method
    print("\n2. Scraping models from OpenRouter website...")
    try:
        scraped_models = scrape_openrouter_models()
        print(f"   Scraping returned {len(scraped_models)} models")
        
        # Show first few models as sample
        print("\n   Sample scraped models:")
        for i, model in enumerate(scraped_models[:3]):
            print(f"   {i+1}. {model.get('name', 'Unknown name')} by {model.get('provider', 'Unknown provider')}")
            print(f"      Model URL: {model.get('model_url', 'N/A')}")
            print(f"      Provider URL: {model.get('provider_url', 'N/A')}")
    except Exception as e:
        print(f"   Error during scraping: {e}")
        scraped_models = []
    
    # Compare results
    print("\n=== Comparison Results ===")
    print(f"API models: {len(api_models)}")
    print(f"Scraped models: {len(scraped_models)}")
    print(f"Difference: {len(scraped_models) - len(api_models)} more models from scraping")
    
    # Find models in scraping but not in API
    if api_models and scraped_models:
        api_ids = {model.get('id') for model in api_models}
        scraped_names = {model.get('name') for model in scraped_models}
        
        # Try to match by name normalization
        common_models = 0
        for scraped_model in scraped_models:
            scraped_name = scraped_model.get('name', '').lower()
            for api_model in api_models:
                api_name = api_model.get('name', '').lower()
                api_id = api_model.get('id', '').lower()
                
                # Check if names match or if scraped name contains API id/name
                if (scraped_name == api_name or 
                    scraped_name in api_id or 
                    api_id in scraped_name or
                    scraped_name.replace(' ', '') == api_name.replace(' ', '')):
                    common_models += 1
                    break
        
        print(f"Estimated common models: {common_models}")
        print(f"Models only in scraping: ~{len(scraped_models) - common_models}")
        print(f"Models only in API: ~{len(api_models) - common_models}")
    
    # Save results to files for further analysis
    with open('api_models.json', 'w') as f:
        json.dump(api_models, f, indent=2)
    print(f"\nSaved API models to api_models.json")
    
    with open('scraped_models.json', 'w') as f:
        json.dump(scraped_models, f, indent=2)
    print(f"Saved scraped models to scraped_models.json")
    
    # Check URL coverage
    if scraped_models:
        models_with_urls = sum(1 for model in scraped_models if model.get('model_url'))
        providers_with_urls = sum(1 for model in scraped_models if model.get('provider_url'))
        
        print(f"\nURL Coverage in scraped data:")
        print(f"Models with URLs: {models_with_urls}/{len(scraped_models)} ({models_with_urls/len(scraped_models)*100:.1f}%)")
        print(f"Providers with URLs: {providers_with_urls}/{len(scraped_models)} ({providers_with_urls/len(scraped_models)*100:.1f}%)")
        
        # Show models without URLs
        models_without_urls = [model for model in scraped_models if not model.get('model_url')]
        if models_without_urls:
            print(f"\nFirst 5 models without URLs (for debugging):")
            for model in models_without_urls[:5]:
                print(f"  - {model.get('name', 'Unknown')} by {model.get('provider', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test_and_compare())