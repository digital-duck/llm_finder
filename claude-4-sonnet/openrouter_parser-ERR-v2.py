#!/usr/bin/env python3
"""
OpenRouter Model Information Parser

This script parses LLM model information from OpenRouter using both web scraping
and API approaches. It extracts model details including names, URLs, pricing,
context windows, descriptions, and provider information.

Requirements:
    pip install requests beautifulsoup4 lxml pandas

Usage:
    python openrouter_parser.py
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re
from urllib.parse import urljoin, urlparse
from typing import Dict, List, Optional, Tuple
import time


class OpenRouterParser:
    def __init__(self):
        self.base_url = "https://openrouter.ai"
        self.models_url = "https://openrouter.ai/models"
        self.api_url = "https://openrouter.ai/api/v1/models"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_models_via_api(self) -> List[Dict]:
        """
        Fetch model information using OpenRouter's public API.
        This is the most reliable method as it provides structured data.
        """
        try:
            print("Fetching models via API...")
            response = self.session.get(self.api_url)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            print(f"Error fetching via API: {e}")
            return []

    def parse_web_interface(self) -> List[Dict]:
        """
        Parse model information from the web interface.
        This method scrapes the HTML page to extract model details.
        """
        try:
            print("Fetching models via web scraping...")
            response = self.session.get(self.models_url)
            response.raise_for_status()
            
            # Save HTML for debugging
            with open('openrouter_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved HTML page to openrouter_page.html for inspection")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            models = []
            
            # Try multiple strategies to find model containers
            strategies = [
                # Strategy 1: Look for common model container patterns
                lambda s: s.find_all(['div', 'article', 'section'], class_=re.compile(r'model|card|item|row')),
                # Strategy 2: Look for elements containing model names and pricing
                lambda s: s.find_all('div', string=re.compile(r'tokens|context|\

    def extract_model_from_element(self, element) -> Optional[Dict]:
        """
        Extract model information from a web page element.
        Enhanced version with better pattern matching.
        """
        try:
            model_info = {}
            
            # Get all text content for analysis
            text_content = element.get_text(strip=True)
            if not text_content or len(text_content) < 10:
                return None
            
            # Look for the parent container that might contain all model info
            container = element
            for _ in range(3):  # Search up to 3 levels up
                if container.parent:
                    container = container.parent
                    container_text = container.get_text()
                    if ('tokens' in container_text and 
                        ('

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """
        Format API data to match the structure expected from web scraping.
        """
        formatted_models = []
        
        for model in api_models:
            provider_name = self.extract_provider_from_id(model.get('id', ''))
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': provider_name,
                'provider_url': f"https://openrouter.ai/providers/{provider_name}" if provider_name else '',
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt'), "input"),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion'), "output"),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image'), "image"),
                'created': model.get('created'),
                'updated': model.get('updated'),
                'owned_by': model.get('owned_by', ''),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}),
                'per_request_limits': model.get('per_request_limits')
            }
            formatted_models.append(formatted_model)
        
        return formatted_models

    def extract_provider_from_id(self, model_id: str) -> str:
        """Extract provider name from model ID."""
        if '/' in model_id:
            return model_id.split('/')[0]
        return ''

    def format_pricing(self, pricing: Optional[str], pricing_type: str = "tokens") -> str:
        """Format pricing information for display."""
        if not pricing or pricing == "0":
            # Only return "Free" for input/output tokens, empty string for images
            return "Free" if pricing_type in ["input", "output"] else ""
        
        try:
            price_float = float(pricing)
            if price_float == 0:
                return "Free" if pricing_type in ["input", "output"] else ""
            elif price_float < 0.001:
                return f"${price_float * 1000000:.2f}/M tokens"
            elif price_float < 1:
                return f"${price_float * 1000:.2f}/K tokens"
            else:
                return f"${price_float:.2f}/token"
        except (ValueError, TypeError):
            return str(pricing) if pricing else ""

    def save_to_csv(self, models: List[Dict], filename: str = "openrouter_models.csv"):
        """Save model data to CSV file."""
        if not models:
            print("No models to save.")
            return
        
        df = pd.DataFrame(models)
        df.to_csv(filename, index=False)
        print(f"Saved {len(models)} models to {filename}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file."""
        if not models:
            print("No models to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(models)} models to {filename}")

    def display_summary(self, models: List[Dict]):
        """Display a summary of parsed models."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n=== OpenRouter Models Summary ===")
        print(f"Total models found: {len(models)}")
        
        # Count by provider
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"\nTop providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider}: {count} models")
        
        # Show sample models
        print(f"\nSample models:")
        for i, model in enumerate(models[:5]):
            print(f"  {i+1}. {model.get('name', 'N/A')} - {model.get('input_pricing', 'N/A')} input")

    def run(self, use_api: bool = True, save_csv: bool = True, save_json: bool = True, compare_methods: bool = False):
        """
        Main execution method.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
            compare_methods: If True, run both methods and compare results
        """
        print("Starting OpenRouter model parsing...")
        
        api_models = []
        web_models = []
        
        if use_api or compare_methods:
            print("\n--- Using API Method ---")
            api_models = self.fetch_models_via_api()
            if api_models:
                api_models = self.format_api_data(api_models)
                print(f"API method found: {len(api_models)} models")
        
        if not use_api or compare_methods:
            print("\n--- Using Web Scraping Method ---")
            web_models = self.parse_web_interface()
            print(f"Web scraping found: {len(web_models)} models")
        
        # Choose primary dataset
        if use_api and api_models:
            models = api_models
            method_used = "API"
        elif web_models:
            models = web_models
            method_used = "Web Scraping"
        else:
            models = api_models if api_models else web_models
            method_used = "Fallback"
        
        print(f"\nUsing {method_used} results as primary dataset")
        
        # Compare methods if requested
        if compare_methods and api_models and web_models:
            self.compare_methods(api_models, web_models)
        
        if not models:
            print("No models found with any method!")
            return []
        
        self.display_summary(models)
        
        if save_csv:
            filename = f"openrouter_models_{method_used.lower().replace(' ', '_')}.csv"
            self.save_to_csv(models, filename)
        
        if save_json:
            filename = f"openrouter_models_{method_used.lower().replace(' ', '_')}.json"
            self.save_to_json(models, filename)
        
        return models

    def compare_methods(self, api_models: List[Dict], web_models: List[Dict]):
        """Compare results from API and web scraping methods."""
        print(f"\n=== Method Comparison ===")
        print(f"API models: {len(api_models)}")
        print(f"Web scraping models: {len(web_models)}")
        
        # Get model IDs/names for comparison
        api_ids = set()
        for model in api_models:
            if 'id' in model:
                api_ids.add(model['id'])
            elif 'name' in model:
                api_ids.add(model['name'])
        
        web_ids = set()
        for model in web_models:
            if 'id' in model:
                web_ids.add(model['id'])
            elif 'name' in model:
                web_ids.add(model['name'])
        
        common = api_ids.intersection(web_ids)
        api_only = api_ids - web_ids
        web_only = web_ids - api_ids
        
        print(f"Models in both: {len(common)}")
        print(f"API only: {len(api_only)}")
        print(f"Web scraping only: {len(web_only)}")
        
        if api_only:
            print(f"\nSample API-only models: {list(api_only)[:5]}")
        if web_only:
            print(f"Sample web-only models: {list(web_only)[:5]}")
        
        # Save comparison results
        comparison = {
            'api_count': len(api_models),
            'web_count': len(web_models),
            'common_count': len(common),
            'api_only': list(api_only),
            'web_only': list(web_only),
            'common': list(common)
        }
        
        with open('method_comparison.json', 'w') as f:
            json.dump(comparison, f, indent=2)
        print("Saved comparison to method_comparison.json")


def main():
    """Main function to run the parser."""
    parser = OpenRouterParser()
    
    print("Choose parsing method:")
    print("1. API only (recommended)")
    print("2. Web scraping only") 
    print("3. Both methods with comparison")
    
    choice = input("Enter choice (1-3) or press Enter for default (3): ").strip()
    
    if choice == "1":
        models = parser.run(use_api=True, compare_methods=False)
    elif choice == "2":
        models = parser.run(use_api=False, compare_methods=False)
    else:  # Default to comparison
        models = parser.run(use_api=True, compare_methods=True)
    
    print(f"\nParsing complete! Found {len(models)} models.")
    
    if models:
        print("\nFiles generated:")
        print("- CSV file with model data")
        print("- JSON file with model data")
        if choice == "3" or choice == "":
            print("- method_comparison.json with comparison analysis")
            print("- openrouter_page.html (saved HTML for debugging)")
    
    return models


if __name__ == "__main__":
    main()
)),
                # Strategy 3: Look for link elements that might be model links
                lambda s: s.find_all('a', href=re.compile(r'/models/')),
                # Strategy 4: Look for any div containing "by" (provider info)
                lambda s: s.find_all('div', string=re.compile(r'by\s+\w+')),
            ]
            
            for i, strategy in enumerate(strategies):
                print(f"Trying strategy {i+1}...")
                elements = strategy(soup)
                print(f"Found {len(elements)} potential elements")
                
                if elements:
                    for element in elements[:10]:  # Limit to first 10 for debugging
                        model_info = self.extract_model_from_element(element)
                        if model_info:
                            models.append(model_info)
                    
                    if models:
                        print(f"Strategy {i+1} found {len(models)} models")
                        break
            
            # If no models found, try a more generic approach
            if not models:
                print("No models found with standard strategies, trying generic text extraction...")
                models = self.extract_models_from_text(soup)
            
            return models
            
        except Exception as e:
            print(f"Error parsing web interface: {e}")
            return []

    def extract_model_from_section(self, section) -> Optional[Dict]:
        """
        Extract model information from a web page section.
        Based on your observations about the display format.
        """
        try:
            model_info = {}
            
            # Extract model name and URL (item 1)
            model_link = section.find('a', href=True)
            if model_link:
                model_info['name'] = model_link.get_text(strip=True)
                model_info['model_url'] = urljoin(self.base_url, model_link['href'])
            
            # Extract token counts (right-aligned text in item 1)
            token_text = section.find(text=re.compile(r'\d+[KM]?\s*context'))
            if token_text:
                model_info['context_window'] = token_text.strip()
            
            # Extract categories (item 2, optional)
            category_elements = section.find_all(text=re.compile(r'#\d+'))
            if category_elements:
                model_info['categories'] = [cat.strip() for cat in category_elements]
            
            # Extract description (item 3, wrapped text)
            desc_elem = section.find(['p', 'div'], class_=re.compile(r'desc|description'))
            if desc_elem:
                model_info['description'] = desc_elem.get_text(strip=True)
            
            # Extract provider, context, pricing info (items 4-8, delimited by "|")
            pipe_delimited = section.find(text=re.compile(r'.*\|.*\|.*'))
            if pipe_delimited:
                parts = [part.strip() for part in pipe_delimited.split('|')]
                if len(parts) >= 5:
                    # Item 4: Provider (with URL)
                    provider_link = section.find('a', href=True, text=re.compile(r'by\s+'))
                    if provider_link:
                        model_info['provider'] = provider_link.get_text(strip=True).replace('by ', '')
                        model_info['provider_url'] = urljoin(self.base_url, provider_link['href'])
                    
                    # Items 5-8: Context, input pricing, output pricing, image pricing
                    for i, part in enumerate(parts[1:5], 5):
                        if 'context' in part.lower():
                            model_info['context_window'] = part
                        elif 'input' in part.lower():
                            model_info['input_pricing'] = part
                        elif 'output' in part.lower():
                            model_info['output_pricing'] = part
                        elif 'img' in part.lower():
                            model_info['image_pricing'] = part
            
            return model_info if model_info else None
            
        except Exception as e:
            print(f"Error extracting model info: {e}")
            return None

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """
        Format API data to match the structure expected from web scraping.
        """
        formatted_models = []
        
        for model in api_models:
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': self.extract_provider_from_id(model.get('id', '')),
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt')),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion')),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image')),
                'created': model.get('created'),
                'updated': model.get('updated'),
                'owned_by': model.get('owned_by', ''),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}),
                'per_request_limits': model.get('per_request_limits')
            }
            formatted_models.append(formatted_model)
        
        return formatted_models

    def extract_provider_from_id(self, model_id: str) -> str:
        """Extract provider name from model ID."""
        if '/' in model_id:
            return model_id.split('/')[0]
        return ''

    def format_pricing(self, pricing: Optional[str]) -> str:
        """Format pricing information for display."""
        if not pricing or pricing == "0":
            return "Free"
        
        try:
            price_float = float(pricing)
            if price_float < 0.001:
                return f"${price_float * 1000000:.2f}/M tokens"
            elif price_float < 1:
                return f"${price_float * 1000:.2f}/K tokens"
            else:
                return f"${price_float:.2f}/token"
        except (ValueError, TypeError):
            return str(pricing) if pricing else ""

    def save_to_csv(self, models: List[Dict], filename: str = "openrouter_models.csv"):
        """Save model data to CSV file."""
        if not models:
            print("No models to save.")
            return
        
        df = pd.DataFrame(models)
        df.to_csv(filename, index=False)
        print(f"Saved {len(models)} models to {filename}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file."""
        if not models:
            print("No models to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(models)} models to {filename}")

    def display_summary(self, models: List[Dict]):
        """Display a summary of parsed models."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n=== OpenRouter Models Summary ===")
        print(f"Total models found: {len(models)}")
        
        # Count by provider
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"\nTop providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider}: {count} models")
        
        # Show sample models
        print(f"\nSample models:")
        for i, model in enumerate(models[:5]):
            print(f"  {i+1}. {model.get('name', 'N/A')} - {model.get('input_pricing', 'N/A')} input")

    def run(self, use_api: bool = True, save_csv: bool = True, save_json: bool = True):
        """
        Main execution method.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
        """
        print("Starting OpenRouter model parsing...")
        
        if use_api:
            models = self.fetch_models_via_api()
            if models:
                models = self.format_api_data(models)
        else:
            models = self.parse_web_interface()
        
        if not models:
            print("No models found. Trying alternative method...")
            if use_api:
                models = self.parse_web_interface()
            else:
                models = self.fetch_models_via_api()
                if models:
                    models = self.format_api_data(models)
        
        self.display_summary(models)
        
        if save_csv:
            self.save_to_csv(models)
        
        if save_json:
            self.save_to_json(models)
        
        return models


def main():
    """Main function to run the parser."""
    parser = OpenRouterParser()
    
    # Run with API first (more reliable)
    models = parser.run(use_api=True, save_csv=True, save_json=True)
    
    # Optionally, you can also try web scraping:
    # models = parser.run(use_api=False, save_csv=True, save_json=True)
    
    print("\nParsing complete!")
    return models


if __name__ == "__main__":
    main()
 in container_text or 'free' in container_text.lower()) and
                        'by ' in container_text):
                        break
            
            # Extract model name and URL
            model_links = container.find_all('a', href=re.compile(r'/models/'))
            if model_links:
                link = model_links[0]
                model_info['name'] = link.get_text(strip=True)
                model_info['model_url'] = urljoin(self.base_url, link['href'])
                model_info['id'] = link['href'].replace('/models/', '')
            
            # Extract token count (right-aligned)
            token_match = re.search(r'(\d+(?:\.\d+)?[KM]?)\s*tokens?', container.get_text())
            if token_match:
                model_info['context_window'] = token_match.group(1) + ' tokens'
            
            # Extract description (usually longer text block)
            paragraphs = container.find_all(['p', 'div'], recursive=True)
            for p in paragraphs:
                p_text = p.get_text(strip=True)
                if len(p_text) > 50 and 'tokens' not in p_text and '

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """
        Format API data to match the structure expected from web scraping.
        """
        formatted_models = []
        
        for model in api_models:
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': self.extract_provider_from_id(model.get('id', '')),
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt')),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion')),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image')),
                'created': model.get('created'),
                'updated': model.get('updated'),
                'owned_by': model.get('owned_by', ''),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}),
                'per_request_limits': model.get('per_request_limits')
            }
            formatted_models.append(formatted_model)
        
        return formatted_models

    def extract_provider_from_id(self, model_id: str) -> str:
        """Extract provider name from model ID."""
        if '/' in model_id:
            return model_id.split('/')[0]
        return ''

    def format_pricing(self, pricing: Optional[str]) -> str:
        """Format pricing information for display."""
        if not pricing or pricing == "0":
            return "Free"
        
        try:
            price_float = float(pricing)
            if price_float < 0.001:
                return f"${price_float * 1000000:.2f}/M tokens"
            elif price_float < 1:
                return f"${price_float * 1000:.2f}/K tokens"
            else:
                return f"${price_float:.2f}/token"
        except (ValueError, TypeError):
            return str(pricing) if pricing else ""

    def save_to_csv(self, models: List[Dict], filename: str = "openrouter_models.csv"):
        """Save model data to CSV file."""
        if not models:
            print("No models to save.")
            return
        
        df = pd.DataFrame(models)
        df.to_csv(filename, index=False)
        print(f"Saved {len(models)} models to {filename}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file."""
        if not models:
            print("No models to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(models)} models to {filename}")

    def display_summary(self, models: List[Dict]):
        """Display a summary of parsed models."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n=== OpenRouter Models Summary ===")
        print(f"Total models found: {len(models)}")
        
        # Count by provider
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"\nTop providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider}: {count} models")
        
        # Show sample models
        print(f"\nSample models:")
        for i, model in enumerate(models[:5]):
            print(f"  {i+1}. {model.get('name', 'N/A')} - {model.get('input_pricing', 'N/A')} input")

    def run(self, use_api: bool = True, save_csv: bool = True, save_json: bool = True):
        """
        Main execution method.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
        """
        print("Starting OpenRouter model parsing...")
        
        if use_api:
            models = self.fetch_models_via_api()
            if models:
                models = self.format_api_data(models)
        else:
            models = self.parse_web_interface()
        
        if not models:
            print("No models found. Trying alternative method...")
            if use_api:
                models = self.parse_web_interface()
            else:
                models = self.fetch_models_via_api()
                if models:
                    models = self.format_api_data(models)
        
        self.display_summary(models)
        
        if save_csv:
            self.save_to_csv(models)
        
        if save_json:
            self.save_to_json(models)
        
        return models


def main():
    """Main function to run the parser."""
    parser = OpenRouterParser()
    
    # Run with API first (more reliable)
    models = parser.run(use_api=True, save_csv=True, save_json=True)
    
    # Optionally, you can also try web scraping:
    # models = parser.run(use_api=False, save_csv=True, save_json=True)
    
    print("\nParsing complete!")
    return models


if __name__ == "__main__":
    main()
)),
                # Strategy 3: Look for link elements that might be model links
                lambda s: s.find_all('a', href=re.compile(r'/models/')),
                # Strategy 4: Look for any div containing "by" (provider info)
                lambda s: s.find_all('div', string=re.compile(r'by\s+\w+')),
            ]
            
            for i, strategy in enumerate(strategies):
                print(f"Trying strategy {i+1}...")
                elements = strategy(soup)
                print(f"Found {len(elements)} potential elements")
                
                if elements:
                    for element in elements[:10]:  # Limit to first 10 for debugging
                        model_info = self.extract_model_from_element(element)
                        if model_info:
                            models.append(model_info)
                    
                    if models:
                        print(f"Strategy {i+1} found {len(models)} models")
                        break
            
            # If no models found, try a more generic approach
            if not models:
                print("No models found with standard strategies, trying generic text extraction...")
                models = self.extract_models_from_text(soup)
            
            return models
            
        except Exception as e:
            print(f"Error parsing web interface: {e}")
            return []

    def extract_model_from_section(self, section) -> Optional[Dict]:
        """
        Extract model information from a web page section.
        Based on your observations about the display format.
        """
        try:
            model_info = {}
            
            # Extract model name and URL (item 1)
            model_link = section.find('a', href=True)
            if model_link:
                model_info['name'] = model_link.get_text(strip=True)
                model_info['model_url'] = urljoin(self.base_url, model_link['href'])
            
            # Extract token counts (right-aligned text in item 1)
            token_text = section.find(text=re.compile(r'\d+[KM]?\s*context'))
            if token_text:
                model_info['context_window'] = token_text.strip()
            
            # Extract categories (item 2, optional)
            category_elements = section.find_all(text=re.compile(r'#\d+'))
            if category_elements:
                model_info['categories'] = [cat.strip() for cat in category_elements]
            
            # Extract description (item 3, wrapped text)
            desc_elem = section.find(['p', 'div'], class_=re.compile(r'desc|description'))
            if desc_elem:
                model_info['description'] = desc_elem.get_text(strip=True)
            
            # Extract provider, context, pricing info (items 4-8, delimited by "|")
            pipe_delimited = section.find(text=re.compile(r'.*\|.*\|.*'))
            if pipe_delimited:
                parts = [part.strip() for part in pipe_delimited.split('|')]
                if len(parts) >= 5:
                    # Item 4: Provider (with URL)
                    provider_link = section.find('a', href=True, text=re.compile(r'by\s+'))
                    if provider_link:
                        model_info['provider'] = provider_link.get_text(strip=True).replace('by ', '')
                        model_info['provider_url'] = urljoin(self.base_url, provider_link['href'])
                    
                    # Items 5-8: Context, input pricing, output pricing, image pricing
                    for i, part in enumerate(parts[1:5], 5):
                        if 'context' in part.lower():
                            model_info['context_window'] = part
                        elif 'input' in part.lower():
                            model_info['input_pricing'] = part
                        elif 'output' in part.lower():
                            model_info['output_pricing'] = part
                        elif 'img' in part.lower():
                            model_info['image_pricing'] = part
            
            return model_info if model_info else None
            
        except Exception as e:
            print(f"Error extracting model info: {e}")
            return None

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """
        Format API data to match the structure expected from web scraping.
        """
        formatted_models = []
        
        for model in api_models:
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': self.extract_provider_from_id(model.get('id', '')),
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt')),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion')),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image')),
                'created': model.get('created'),
                'updated': model.get('updated'),
                'owned_by': model.get('owned_by', ''),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}),
                'per_request_limits': model.get('per_request_limits')
            }
            formatted_models.append(formatted_model)
        
        return formatted_models

    def extract_provider_from_id(self, model_id: str) -> str:
        """Extract provider name from model ID."""
        if '/' in model_id:
            return model_id.split('/')[0]
        return ''

    def format_pricing(self, pricing: Optional[str]) -> str:
        """Format pricing information for display."""
        if not pricing or pricing == "0":
            return "Free"
        
        try:
            price_float = float(pricing)
            if price_float < 0.001:
                return f"${price_float * 1000000:.2f}/M tokens"
            elif price_float < 1:
                return f"${price_float * 1000:.2f}/K tokens"
            else:
                return f"${price_float:.2f}/token"
        except (ValueError, TypeError):
            return str(pricing) if pricing else ""

    def save_to_csv(self, models: List[Dict], filename: str = "openrouter_models.csv"):
        """Save model data to CSV file."""
        if not models:
            print("No models to save.")
            return
        
        df = pd.DataFrame(models)
        df.to_csv(filename, index=False)
        print(f"Saved {len(models)} models to {filename}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file."""
        if not models:
            print("No models to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(models)} models to {filename}")

    def display_summary(self, models: List[Dict]):
        """Display a summary of parsed models."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n=== OpenRouter Models Summary ===")
        print(f"Total models found: {len(models)}")
        
        # Count by provider
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"\nTop providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider}: {count} models")
        
        # Show sample models
        print(f"\nSample models:")
        for i, model in enumerate(models[:5]):
            print(f"  {i+1}. {model.get('name', 'N/A')} - {model.get('input_pricing', 'N/A')} input")

    def run(self, use_api: bool = True, save_csv: bool = True, save_json: bool = True):
        """
        Main execution method.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
        """
        print("Starting OpenRouter model parsing...")
        
        if use_api:
            models = self.fetch_models_via_api()
            if models:
                models = self.format_api_data(models)
        else:
            models = self.parse_web_interface()
        
        if not models:
            print("No models found. Trying alternative method...")
            if use_api:
                models = self.parse_web_interface()
            else:
                models = self.fetch_models_via_api()
                if models:
                    models = self.format_api_data(models)
        
        self.display_summary(models)
        
        if save_csv:
            self.save_to_csv(models)
        
        if save_json:
            self.save_to_json(models)
        
        return models


def main():
    """Main function to run the parser."""
    parser = OpenRouterParser()
    
    # Run with API first (more reliable)
    models = parser.run(use_api=True, save_csv=True, save_json=True)
    
    # Optionally, you can also try web scraping:
    # models = parser.run(use_api=False, save_csv=True, save_json=True)
    
    print("\nParsing complete!")
    return models


if __name__ == "__main__":
    main()
 not in p_text:
                    model_info['description'] = p_text[:200] + '...' if len(p_text) > 200 else p_text
                    break
            
            # Extract provider info and URL
            provider_match = re.search(r'by\s+([^|]+)', container.get_text())
            if provider_match:
                provider_name = provider_match.group(1).strip()
                model_info['provider'] = provider_name
                # Try to find provider link
                provider_links = container.find_all('a', href=re.compile(r'/providers/'))
                if provider_links:
                    model_info['provider_url'] = urljoin(self.base_url, provider_links[0]['href'])
                else:
                    # Generate provider URL based on name
                    provider_slug = provider_name.lower().replace(' ', '-').replace('.', '')
                    model_info['provider_url'] = f"https://openrouter.ai/providers/{provider_slug}"
            
            # Extract pricing information
            pricing_text = container.get_text()
            
            # Input pricing
            input_match = re.search(r'\$([0-9.]+)/M\s+input', pricing_text)
            if input_match:
                model_info['input_pricing'] = f"${input_match.group(1)}/M tokens"
            elif 'free' in pricing_text.lower() or '$0' in pricing_text:
                model_info['input_pricing'] = 'Free'
            else:
                model_info['input_pricing'] = ''
            
            # Output pricing
            output_match = re.search(r'\$([0-9.]+)/M\s+output', pricing_text)
            if output_match:
                model_info['output_pricing'] = f"${output_match.group(1)}/M tokens"
            else:
                model_info['output_pricing'] = ''
            
            # Image pricing - only set if explicitly found, otherwise empty
            image_match = re.search(r'\$([0-9.]+)/K.*img', pricing_text)
            if image_match:
                model_info['image_pricing'] = f"${image_match.group(1)}/K images"
            else:
                model_info['image_pricing'] = ''
            
            return model_info if len(model_info) > 2 else None
            
        except Exception as e:
            print(f"Error extracting model info from element: {e}")
            return None

    def extract_models_from_text(self, soup) -> List[Dict]:
        """
        Fallback method to extract models from raw text patterns.
        """
        models = []
        try:
            # Get all text and look for patterns
            page_text = soup.get_text()
            
            # Split by horizontal dividers or double newlines
            sections = re.split(r'\n\s*\n', page_text)
            
            for section in sections:
                if ('tokens' in section and 
                    ('

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """
        Format API data to match the structure expected from web scraping.
        """
        formatted_models = []
        
        for model in api_models:
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': self.extract_provider_from_id(model.get('id', '')),
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt')),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion')),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image')),
                'created': model.get('created'),
                'updated': model.get('updated'),
                'owned_by': model.get('owned_by', ''),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}),
                'per_request_limits': model.get('per_request_limits')
            }
            formatted_models.append(formatted_model)
        
        return formatted_models

    def extract_provider_from_id(self, model_id: str) -> str:
        """Extract provider name from model ID."""
        if '/' in model_id:
            return model_id.split('/')[0]
        return ''

    def format_pricing(self, pricing: Optional[str]) -> str:
        """Format pricing information for display."""
        if not pricing or pricing == "0":
            return "Free"
        
        try:
            price_float = float(pricing)
            if price_float < 0.001:
                return f"${price_float * 1000000:.2f}/M tokens"
            elif price_float < 1:
                return f"${price_float * 1000:.2f}/K tokens"
            else:
                return f"${price_float:.2f}/token"
        except (ValueError, TypeError):
            return str(pricing) if pricing else ""

    def save_to_csv(self, models: List[Dict], filename: str = "openrouter_models.csv"):
        """Save model data to CSV file."""
        if not models:
            print("No models to save.")
            return
        
        df = pd.DataFrame(models)
        df.to_csv(filename, index=False)
        print(f"Saved {len(models)} models to {filename}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file."""
        if not models:
            print("No models to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(models)} models to {filename}")

    def display_summary(self, models: List[Dict]):
        """Display a summary of parsed models."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n=== OpenRouter Models Summary ===")
        print(f"Total models found: {len(models)}")
        
        # Count by provider
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"\nTop providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider}: {count} models")
        
        # Show sample models
        print(f"\nSample models:")
        for i, model in enumerate(models[:5]):
            print(f"  {i+1}. {model.get('name', 'N/A')} - {model.get('input_pricing', 'N/A')} input")

    def run(self, use_api: bool = True, save_csv: bool = True, save_json: bool = True):
        """
        Main execution method.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
        """
        print("Starting OpenRouter model parsing...")
        
        if use_api:
            models = self.fetch_models_via_api()
            if models:
                models = self.format_api_data(models)
        else:
            models = self.parse_web_interface()
        
        if not models:
            print("No models found. Trying alternative method...")
            if use_api:
                models = self.parse_web_interface()
            else:
                models = self.fetch_models_via_api()
                if models:
                    models = self.format_api_data(models)
        
        self.display_summary(models)
        
        if save_csv:
            self.save_to_csv(models)
        
        if save_json:
            self.save_to_json(models)
        
        return models


def main():
    """Main function to run the parser."""
    parser = OpenRouterParser()
    
    # Run with API first (more reliable)
    models = parser.run(use_api=True, save_csv=True, save_json=True)
    
    # Optionally, you can also try web scraping:
    # models = parser.run(use_api=False, save_csv=True, save_json=True)
    
    print("\nParsing complete!")
    return models


if __name__ == "__main__":
    main()
)),
                # Strategy 3: Look for link elements that might be model links
                lambda s: s.find_all('a', href=re.compile(r'/models/')),
                # Strategy 4: Look for any div containing "by" (provider info)
                lambda s: s.find_all('div', string=re.compile(r'by\s+\w+')),
            ]
            
            for i, strategy in enumerate(strategies):
                print(f"Trying strategy {i+1}...")
                elements = strategy(soup)
                print(f"Found {len(elements)} potential elements")
                
                if elements:
                    for element in elements[:10]:  # Limit to first 10 for debugging
                        model_info = self.extract_model_from_element(element)
                        if model_info:
                            models.append(model_info)
                    
                    if models:
                        print(f"Strategy {i+1} found {len(models)} models")
                        break
            
            # If no models found, try a more generic approach
            if not models:
                print("No models found with standard strategies, trying generic text extraction...")
                models = self.extract_models_from_text(soup)
            
            return models
            
        except Exception as e:
            print(f"Error parsing web interface: {e}")
            return []

    def extract_model_from_section(self, section) -> Optional[Dict]:
        """
        Extract model information from a web page section.
        Based on your observations about the display format.
        """
        try:
            model_info = {}
            
            # Extract model name and URL (item 1)
            model_link = section.find('a', href=True)
            if model_link:
                model_info['name'] = model_link.get_text(strip=True)
                model_info['model_url'] = urljoin(self.base_url, model_link['href'])
            
            # Extract token counts (right-aligned text in item 1)
            token_text = section.find(text=re.compile(r'\d+[KM]?\s*context'))
            if token_text:
                model_info['context_window'] = token_text.strip()
            
            # Extract categories (item 2, optional)
            category_elements = section.find_all(text=re.compile(r'#\d+'))
            if category_elements:
                model_info['categories'] = [cat.strip() for cat in category_elements]
            
            # Extract description (item 3, wrapped text)
            desc_elem = section.find(['p', 'div'], class_=re.compile(r'desc|description'))
            if desc_elem:
                model_info['description'] = desc_elem.get_text(strip=True)
            
            # Extract provider, context, pricing info (items 4-8, delimited by "|")
            pipe_delimited = section.find(text=re.compile(r'.*\|.*\|.*'))
            if pipe_delimited:
                parts = [part.strip() for part in pipe_delimited.split('|')]
                if len(parts) >= 5:
                    # Item 4: Provider (with URL)
                    provider_link = section.find('a', href=True, text=re.compile(r'by\s+'))
                    if provider_link:
                        model_info['provider'] = provider_link.get_text(strip=True).replace('by ', '')
                        model_info['provider_url'] = urljoin(self.base_url, provider_link['href'])
                    
                    # Items 5-8: Context, input pricing, output pricing, image pricing
                    for i, part in enumerate(parts[1:5], 5):
                        if 'context' in part.lower():
                            model_info['context_window'] = part
                        elif 'input' in part.lower():
                            model_info['input_pricing'] = part
                        elif 'output' in part.lower():
                            model_info['output_pricing'] = part
                        elif 'img' in part.lower():
                            model_info['image_pricing'] = part
            
            return model_info if model_info else None
            
        except Exception as e:
            print(f"Error extracting model info: {e}")
            return None

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """
        Format API data to match the structure expected from web scraping.
        """
        formatted_models = []
        
        for model in api_models:
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': self.extract_provider_from_id(model.get('id', '')),
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt')),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion')),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image')),
                'created': model.get('created'),
                'updated': model.get('updated'),
                'owned_by': model.get('owned_by', ''),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}),
                'per_request_limits': model.get('per_request_limits')
            }
            formatted_models.append(formatted_model)
        
        return formatted_models

    def extract_provider_from_id(self, model_id: str) -> str:
        """Extract provider name from model ID."""
        if '/' in model_id:
            return model_id.split('/')[0]
        return ''

    def format_pricing(self, pricing: Optional[str]) -> str:
        """Format pricing information for display."""
        if not pricing or pricing == "0":
            return "Free"
        
        try:
            price_float = float(pricing)
            if price_float < 0.001:
                return f"${price_float * 1000000:.2f}/M tokens"
            elif price_float < 1:
                return f"${price_float * 1000:.2f}/K tokens"
            else:
                return f"${price_float:.2f}/token"
        except (ValueError, TypeError):
            return str(pricing) if pricing else ""

    def save_to_csv(self, models: List[Dict], filename: str = "openrouter_models.csv"):
        """Save model data to CSV file."""
        if not models:
            print("No models to save.")
            return
        
        df = pd.DataFrame(models)
        df.to_csv(filename, index=False)
        print(f"Saved {len(models)} models to {filename}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file."""
        if not models:
            print("No models to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(models)} models to {filename}")

    def display_summary(self, models: List[Dict]):
        """Display a summary of parsed models."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n=== OpenRouter Models Summary ===")
        print(f"Total models found: {len(models)}")
        
        # Count by provider
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"\nTop providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider}: {count} models")
        
        # Show sample models
        print(f"\nSample models:")
        for i, model in enumerate(models[:5]):
            print(f"  {i+1}. {model.get('name', 'N/A')} - {model.get('input_pricing', 'N/A')} input")

    def run(self, use_api: bool = True, save_csv: bool = True, save_json: bool = True):
        """
        Main execution method.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
        """
        print("Starting OpenRouter model parsing...")
        
        if use_api:
            models = self.fetch_models_via_api()
            if models:
                models = self.format_api_data(models)
        else:
            models = self.parse_web_interface()
        
        if not models:
            print("No models found. Trying alternative method...")
            if use_api:
                models = self.parse_web_interface()
            else:
                models = self.fetch_models_via_api()
                if models:
                    models = self.format_api_data(models)
        
        self.display_summary(models)
        
        if save_csv:
            self.save_to_csv(models)
        
        if save_json:
            self.save_to_json(models)
        
        return models


def main():
    """Main function to run the parser."""
    parser = OpenRouterParser()
    
    # Run with API first (more reliable)
    models = parser.run(use_api=True, save_csv=True, save_json=True)
    
    # Optionally, you can also try web scraping:
    # models = parser.run(use_api=False, save_csv=True, save_json=True)
    
    print("\nParsing complete!")
    return models


if __name__ == "__main__":
    main()
 in section or 'free' in section.lower()) and
                    'by ' in section):
                    
                    lines = [line.strip() for line in section.split('\n') if line.strip()]
                    if len(lines) >= 3:
                        model_info = {
                            'name': lines[0],
                            'description': lines[1] if len(lines) > 1 else '',
                            'raw_text': section
                        }
                        
                        # Extract other info from the section text
                        token_match = re.search(r'(\d+(?:\.\d+)?[KM]?)\s*tokens?', section)
                        if token_match:
                            model_info['context_window'] = token_match.group(1) + ' tokens'
                        
                        provider_match = re.search(r'by\s+([^|]+)', section)
                        if provider_match:
                            model_info['provider'] = provider_match.group(1).strip()
                        
                        models.append(model_info)
            
            return models[:50]  # Limit to prevent too many false positives
            
        except Exception as e:
            print(f"Error in text extraction: {e}")
            return []

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """
        Format API data to match the structure expected from web scraping.
        """
        formatted_models = []
        
        for model in api_models:
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': self.extract_provider_from_id(model.get('id', '')),
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt')),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion')),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image')),
                'created': model.get('created'),
                'updated': model.get('updated'),
                'owned_by': model.get('owned_by', ''),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}),
                'per_request_limits': model.get('per_request_limits')
            }
            formatted_models.append(formatted_model)
        
        return formatted_models

    def extract_provider_from_id(self, model_id: str) -> str:
        """Extract provider name from model ID."""
        if '/' in model_id:
            return model_id.split('/')[0]
        return ''

    def format_pricing(self, pricing: Optional[str]) -> str:
        """Format pricing information for display."""
        if not pricing or pricing == "0":
            return "Free"
        
        try:
            price_float = float(pricing)
            if price_float < 0.001:
                return f"${price_float * 1000000:.2f}/M tokens"
            elif price_float < 1:
                return f"${price_float * 1000:.2f}/K tokens"
            else:
                return f"${price_float:.2f}/token"
        except (ValueError, TypeError):
            return str(pricing) if pricing else ""

    def save_to_csv(self, models: List[Dict], filename: str = "openrouter_models.csv"):
        """Save model data to CSV file."""
        if not models:
            print("No models to save.")
            return
        
        df = pd.DataFrame(models)
        df.to_csv(filename, index=False)
        print(f"Saved {len(models)} models to {filename}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file."""
        if not models:
            print("No models to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(models)} models to {filename}")

    def display_summary(self, models: List[Dict]):
        """Display a summary of parsed models."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n=== OpenRouter Models Summary ===")
        print(f"Total models found: {len(models)}")
        
        # Count by provider
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"\nTop providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider}: {count} models")
        
        # Show sample models
        print(f"\nSample models:")
        for i, model in enumerate(models[:5]):
            print(f"  {i+1}. {model.get('name', 'N/A')} - {model.get('input_pricing', 'N/A')} input")

    def run(self, use_api: bool = True, save_csv: bool = True, save_json: bool = True):
        """
        Main execution method.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
        """
        print("Starting OpenRouter model parsing...")
        
        if use_api:
            models = self.fetch_models_via_api()
            if models:
                models = self.format_api_data(models)
        else:
            models = self.parse_web_interface()
        
        if not models:
            print("No models found. Trying alternative method...")
            if use_api:
                models = self.parse_web_interface()
            else:
                models = self.fetch_models_via_api()
                if models:
                    models = self.format_api_data(models)
        
        self.display_summary(models)
        
        if save_csv:
            self.save_to_csv(models)
        
        if save_json:
            self.save_to_json(models)
        
        return models


def main():
    """Main function to run the parser."""
    parser = OpenRouterParser()
    
    # Run with API first (more reliable)
    models = parser.run(use_api=True, save_csv=True, save_json=True)
    
    # Optionally, you can also try web scraping:
    # models = parser.run(use_api=False, save_csv=True, save_json=True)
    
    print("\nParsing complete!")
    return models


if __name__ == "__main__":
    main()
)),
                # Strategy 3: Look for link elements that might be model links
                lambda s: s.find_all('a', href=re.compile(r'/models/')),
                # Strategy 4: Look for any div containing "by" (provider info)
                lambda s: s.find_all('div', string=re.compile(r'by\s+\w+')),
            ]
            
            for i, strategy in enumerate(strategies):
                print(f"Trying strategy {i+1}...")
                elements = strategy(soup)
                print(f"Found {len(elements)} potential elements")
                
                if elements:
                    for element in elements[:10]:  # Limit to first 10 for debugging
                        model_info = self.extract_model_from_element(element)
                        if model_info:
                            models.append(model_info)
                    
                    if models:
                        print(f"Strategy {i+1} found {len(models)} models")
                        break
            
            # If no models found, try a more generic approach
            if not models:
                print("No models found with standard strategies, trying generic text extraction...")
                models = self.extract_models_from_text(soup)
            
            return models
            
        except Exception as e:
            print(f"Error parsing web interface: {e}")
            return []

    def extract_model_from_section(self, section) -> Optional[Dict]:
        """
        Extract model information from a web page section.
        Based on your observations about the display format.
        """
        try:
            model_info = {}
            
            # Extract model name and URL (item 1)
            model_link = section.find('a', href=True)
            if model_link:
                model_info['name'] = model_link.get_text(strip=True)
                model_info['model_url'] = urljoin(self.base_url, model_link['href'])
            
            # Extract token counts (right-aligned text in item 1)
            token_text = section.find(text=re.compile(r'\d+[KM]?\s*context'))
            if token_text:
                model_info['context_window'] = token_text.strip()
            
            # Extract categories (item 2, optional)
            category_elements = section.find_all(text=re.compile(r'#\d+'))
            if category_elements:
                model_info['categories'] = [cat.strip() for cat in category_elements]
            
            # Extract description (item 3, wrapped text)
            desc_elem = section.find(['p', 'div'], class_=re.compile(r'desc|description'))
            if desc_elem:
                model_info['description'] = desc_elem.get_text(strip=True)
            
            # Extract provider, context, pricing info (items 4-8, delimited by "|")
            pipe_delimited = section.find(text=re.compile(r'.*\|.*\|.*'))
            if pipe_delimited:
                parts = [part.strip() for part in pipe_delimited.split('|')]
                if len(parts) >= 5:
                    # Item 4: Provider (with URL)
                    provider_link = section.find('a', href=True, text=re.compile(r'by\s+'))
                    if provider_link:
                        model_info['provider'] = provider_link.get_text(strip=True).replace('by ', '')
                        model_info['provider_url'] = urljoin(self.base_url, provider_link['href'])
                    
                    # Items 5-8: Context, input pricing, output pricing, image pricing
                    for i, part in enumerate(parts[1:5], 5):
                        if 'context' in part.lower():
                            model_info['context_window'] = part
                        elif 'input' in part.lower():
                            model_info['input_pricing'] = part
                        elif 'output' in part.lower():
                            model_info['output_pricing'] = part
                        elif 'img' in part.lower():
                            model_info['image_pricing'] = part
            
            return model_info if model_info else None
            
        except Exception as e:
            print(f"Error extracting model info: {e}")
            return None

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """
        Format API data to match the structure expected from web scraping.
        """
        formatted_models = []
        
        for model in api_models:
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': self.extract_provider_from_id(model.get('id', '')),
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt')),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion')),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image')),
                'created': model.get('created'),
                'updated': model.get('updated'),
                'owned_by': model.get('owned_by', ''),
                'architecture': model.get('architecture', {}),
                'top_provider': model.get('top_provider', {}),
                'per_request_limits': model.get('per_request_limits')
            }
            formatted_models.append(formatted_model)
        
        return formatted_models

    def extract_provider_from_id(self, model_id: str) -> str:
        """Extract provider name from model ID."""
        if '/' in model_id:
            return model_id.split('/')[0]
        return ''

    def format_pricing(self, pricing: Optional[str]) -> str:
        """Format pricing information for display."""
        if not pricing or pricing == "0":
            return "Free"
        
        try:
            price_float = float(pricing)
            if price_float < 0.001:
                return f"${price_float * 1000000:.2f}/M tokens"
            elif price_float < 1:
                return f"${price_float * 1000:.2f}/K tokens"
            else:
                return f"${price_float:.2f}/token"
        except (ValueError, TypeError):
            return str(pricing) if pricing else ""

    def save_to_csv(self, models: List[Dict], filename: str = "openrouter_models.csv"):
        """Save model data to CSV file."""
        if not models:
            print("No models to save.")
            return
        
        df = pd.DataFrame(models)
        df.to_csv(filename, index=False)
        print(f"Saved {len(models)} models to {filename}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file."""
        if not models:
            print("No models to save.")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(models, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(models)} models to {filename}")

    def display_summary(self, models: List[Dict]):
        """Display a summary of parsed models."""
        if not models:
            print("No models found.")
            return
        
        print(f"\n=== OpenRouter Models Summary ===")
        print(f"Total models found: {len(models)}")
        
        # Count by provider
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"\nTop providers:")
        for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {provider}: {count} models")
        
        # Show sample models
        print(f"\nSample models:")
        for i, model in enumerate(models[:5]):
            print(f"  {i+1}. {model.get('name', 'N/A')} - {model.get('input_pricing', 'N/A')} input")

    def run(self, use_api: bool = True, save_csv: bool = True, save_json: bool = True):
        """
        Main execution method.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
        """
        print("Starting OpenRouter model parsing...")
        
        if use_api:
            models = self.fetch_models_via_api()
            if models:
                models = self.format_api_data(models)
        else:
            models = self.parse_web_interface()
        
        if not models:
            print("No models found. Trying alternative method...")
            if use_api:
                models = self.parse_web_interface()
            else:
                models = self.fetch_models_via_api()
                if models:
                    models = self.format_api_data(models)
        
        self.display_summary(models)
        
        if save_csv:
            self.save_to_csv(models)
        
        if save_json:
            self.save_to_json(models)
        
        return models


def main():
    """Main function to run the parser."""
    parser = OpenRouterParser()
    
    # Run with API first (more reliable)
    models = parser.run(use_api=True, save_csv=True, save_json=True)
    
    # Optionally, you can also try web scraping:
    # models = parser.run(use_api=False, save_csv=True, save_json=True)
    
    print("\nParsing complete!")
    return models


if __name__ == "__main__":
    main()
