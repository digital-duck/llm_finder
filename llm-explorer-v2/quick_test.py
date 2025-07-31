#!/usr/bin/env python3
"""
Quick test script to run the enhanced scraper and display URL results.
"""

import json
from scrape_models import scrape_openrouter_models

def main():
    print("=== Enhanced OpenRouter Model Scraper Test ===\n")
    
    # Run the scraper
    print("Scraping models from https://openrouter.ai/models...")
    models = scrape_openrouter_models()
    
    print(f"\nSuccessfully scraped {len(models)} models!\n")
    
    # Display URL statistics
    models_with_urls = sum(1 for model in models if model.get('model_url'))
    providers_with_urls = sum(1 for model in models if model.get('provider_url'))
    
    print("=== URL Coverage Statistics ===")
    print(f"Total models: {len(models)}")
    print(f"Models with URLs: {models_with_urls} ({models_with_urls/len(models)*100:.1f}%)")
    print(f"Providers with URLs: {providers_with_urls} ({providers_with_urls/len(models)*100:.1f}%)")
    
    # Show sample results with URLs
    print("\n=== Sample Models with URLs ===")
    for i, model in enumerate(models[:5]):
        print(f"\n{i+1}. {model.get('name', 'Unknown name')}")
        print(f"   Provider: {model.get('provider', 'Unknown provider')}")
        print(f"   Model URL: {model.get('model_url', 'N/A')}")
        print(f"   Provider URL: {model.get('provider_url', 'N/A')}")
        if model.get('description'):
            print(f"   Description: {model.get('description', '')[:100]}...")
    
    # Show models without URLs for debugging
    models_without_urls = [model for model in models if not model.get('model_url')]
    if models_without_urls:
        print(f"\n=== Models Without URLs (first 3 for debugging) ===")
        for i, model in enumerate(models_without_urls[:3]):
            print(f"\n{i+1}. {model.get('name', 'Unknown name')}")
            print(f"   Provider: {model.get('provider', 'Unknown provider')}")
            print(f"   Raw text section: {model.get('raw_text_section', '')[:200]}...")
    
    # Save results
    with open('enhanced_scraped_models.json', 'w') as f:
        json.dump(models, f, indent=2)
    
    print(f"\nResults saved to enhanced_scraped_models.json")
    print("\nTest completed! You can now drill down into model details using the provided URLs.")

if __name__ == "__main__":
    main()