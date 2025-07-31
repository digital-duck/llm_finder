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
            soup = BeautifulSoup(response.content, 'html.parser')
            
            models = []
            
            # Look for model containers (this will need to be adjusted based on actual HTML structure)
            model_sections = soup.find_all(['div', 'section'], class_=re.compile(r'model|card|item'))
            
            for section in model_sections:
                model_info = self.extract_model_from_section(section)
                if model_info:
                    models.append(model_info)
            
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
