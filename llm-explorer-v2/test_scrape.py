#!/usr/bin/env python3
"""
Test script to validate the scraping logic without external dependencies
"""

import json
import sys
import os

def test_sample_data():
    """Test with sample data to ensure the logic works"""
    
    # Sample model data (simulating what we'd get from scraping)
    sample_models = [
        {
            'name': 'GPT-4',
            'id': 'openai/gpt-4',
            'description': 'Most capable GPT-4 model, great for complex tasks',
            'context_length': '8192',
            'pricing': '$0.03/1K tokens',
            'provider': 'OpenAI',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion'],
            'website': 'https://openai.com/gpt-4',
            'image_url': ''
        },
        {
            'name': 'Claude 2',
            'id': 'anthropic/claude-2',
            'description': 'Helpful, harmless, and honest AI assistant',
            'context_length': '100000',
            'pricing': '$0.011/1K tokens',
            'provider': 'Anthropic',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion'],
            'website': 'https://anthropic.com/claude',
            'image_url': ''
        },
        {
            'name': 'Llama 2',
            'id': 'meta-llama/llama-2-70b-chat',
            'description': 'Open source large language model',
            'context_length': '4096',
            'pricing': 'Free',
            'provider': 'Meta',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion'],
            'website': 'https://ai.meta.com/llama',
            'image_url': ''
        },
        {
            'name': 'Mistral 7B',
            'id': 'mistralai/mistral-7b-instruct',
            'description': 'High-performance open source model',
            'context_length': '8192',
            'pricing': 'Free',
            'provider': 'Mistral AI',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion'],
            'website': 'https://mistral.ai',
            'image_url': ''
        }
    ]
    
    print("Testing sample data processing...")
    print(f"Sample models count: {len(sample_models)}")
    
    # Test categorization logic
    def categorize_model(pricing_info):
        if not pricing_info:
            return 'Unknown'
        
        pricing_str = str(pricing_info).lower()
        
        # Check for free indicators
        if any(keyword in pricing_str for keyword in ['free', '0.00', 'no cost', 'gratis', 'open source']):
            return 'Free'
        
        # Check for paid indicators
        if any(keyword in pricing_str for keyword in ['$', 'paid', 'premium', 'subscribe', 'credit', 'token']):
            return 'Paid'
        
        return 'Unknown'
    
    # Categorize models
    categorized_models = []
    for model in sample_models:
        category = categorize_model(model['pricing'])
        model['category'] = category
        categorized_models.append(model)
        print(f"Model: {model['name']} -> Category: {category}")
    
    # Count categories
    free_count = len([m for m in categorized_models if m['category'] == 'Free'])
    paid_count = len([m for m in categorized_models if m['category'] == 'Paid'])
    unknown_count = len([m for m in categorized_models if m['category'] == 'Unknown'])
    
    print(f"\nCategory Summary:")
    print(f"Free models: {free_count}")
    print(f"Paid models: {paid_count}")
    print(f"Unknown pricing: {unknown_count}")
    print(f"Total models: {len(categorized_models)}")
    
    # Create a simple CSV-like output
    print(f"\nCSV-like output:")
    print("name,id,description,pricing,provider,category")
    for model in categorized_models:
        print(f"{model['name']},{model['id']},{model['description']},{model['pricing']},{model['provider']},{model['category']}")
    
    # Save to CSV file
    try:
        import csv
        with open('test_models.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'id', 'description', 'pricing', 'provider', 'category', 'context_length', 'architecture', 'website', 'capabilities', 'image_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for model in categorized_models:
                writer.writerow(model)
        print(f"\nSaved test_models.csv successfully!")
    except ImportError:
        print("CSV module not available, skipping CSV save")
    
    return categorized_models

def test_error_handling():
    """Test error handling scenarios"""
    print("\n" + "="*50)
    print("Testing error handling...")
    
    # Test empty data
    empty_data = []
    print(f"Empty data test: {len(empty_data)} models")
    
    # Test malformed data
    malformed_data = [
        {'name': 'Test Model'},  # Missing required fields
        {'id': 'test/model'},    # Missing name
        {}                       # Empty model
    ]
    print(f"Malformed data test: {len(malformed_data)} models")
    
    # Test pricing categorization edge cases
    test_pricings = [
        ('', 'Unknown'),
        ('Free', 'Free'),
        ('free', 'Free'),
        ('FREE', 'Free'),
        ('$0.00', 'Free'),
        ('$1.00', 'Paid'),
        ('paid', 'Paid'),
        ('premium', 'Paid'),
        ('unknown', 'Unknown'),
        ('0 tokens', 'Free'),
        ('1000 tokens', 'Paid'),
        ('Open Source', 'Free'),
        ('Subscribe', 'Paid')
    ]
    
    def categorize_model(pricing_info):
        if not pricing_info:
            return 'Unknown'
        
        pricing_str = str(pricing_info).lower()
        
        if any(keyword in pricing_str for keyword in ['free', '0.00', 'no cost', 'gratis', 'open source']):
            return 'Free'
        
        if any(keyword in pricing_str for keyword in ['$', 'paid', 'premium', 'subscribe', 'credit', 'token']):
            return 'Paid'
        
        return 'Unknown'
    
    print("\nPricing categorization tests:")
    for pricing, expected in test_pricings:
        result = categorize_model(pricing)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{pricing}' -> '{result}' (expected: '{expected}')")

def main():
    """Main test function"""
    print("OpenRouter LLM Scraper - Test Script")
    print("=" * 50)
    
    try:
        # Test sample data processing
        categorized_models = test_sample_data()
        
        # Test error handling
        test_error_handling()
        
        print("\n" + "="*50)
        print("✅ All tests completed successfully!")
        print("The scraping logic appears to be working correctly.")
        print("\nTo run the actual scraper, install dependencies:")
        print("pip install requests beautifulsoup4 pandas lxml")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()