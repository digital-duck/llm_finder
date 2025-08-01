#!/usr/bin/env python3
"""
OpenRouter Model Parser - Clean Working Version

Requirements:
    pip install requests beautifulsoup4 pandas

Usage:
    python openrouter_parser.py
"""

import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import re
from urllib.parse import urljoin
from typing import Dict, List, Optional
from datetime import datetime


class OpenRouterParser:
    def __init__(self):
        self.base_url = "https://openrouter.ai"
        self.models_url = "https://openrouter.ai/models"
        self.api_url = "https://openrouter.ai/api/v1/models"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_api_models(self) -> List[Dict]:
        """Fetch models from OpenRouter API."""
        try:
            print("📡 Fetching models from API...")
            response = self.session.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('data', [])
            
            print(f"✅ API returned {len(models)} models")
            return models
            
        except Exception as e:
            print(f"❌ API failed: {e}")
            return []

    def format_api_models(self, api_models: List[Dict]) -> List[Dict]:
        """Format API models to consistent structure."""
        formatted_models = []
        
        for model in api_models:
            try:
                provider = model.get('id', '').split('/')[0] if '/' in model.get('id', '') else ''
                
                formatted_model = {
                    'id': model.get('id', ''),
                    'name': model.get('name', ''),
                    'description': model.get('description', ''),
                    'provider': provider,
                    'provider_url': f"https://openrouter.ai/{provider}" if provider else '',
                    'model_url': f"https://openrouter.ai/{model.get('id', '')}" if model.get('id') else '',
                    'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                    'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt'), 'input'),
                    'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion'), 'output'),
                    'image_pricing': self.format_pricing(model.get('pricing', {}).get('image'), 'image'),
                }
                formatted_models.append(formatted_model)
                
            except Exception as e:
                print(f"⚠️  Error formatting model: {e}")
                continue
        
        return formatted_models

    def format_pricing(self, pricing: Optional[str], pricing_type: str = "tokens") -> str:
        """Format pricing for display."""
        if not pricing or pricing == "0":
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

    def scrape_web_models(self) -> List[Dict]:
        """Attempt to scrape models from web interface."""
        try:
            print("🕷️  Attempting web scraping...")
            response = self.session.get(self.models_url, timeout=30)
            response.raise_for_status()
            
            # Save HTML for inspection
            with open('openrouter_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 Saved page HTML to openrouter_page.html")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check if page seems to have meaningful content
            if len(response.text) < 5000:
                print("⚠️  Page appears to be JavaScript-rendered")
                return []
            
            models = []
            
            # Try to find model links
            all_links = soup.find_all('a', href=True)
            model_links = [link for link in all_links 
                          if re.search(r'/models/', link.get('href', ''))]
            
            print(f"🔗 Found {len(model_links)} potential model links")
            
            # Extract basic info from links
            for link in model_links[:100]:  # Limit to prevent too many
                try:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    
                    if text and len(text) > 2:
                        model_info = {
                            'name': text,
                            'model_url': urljoin(self.base_url, href),
                            'id': href.replace('/models/', '').replace('--', '/'),
                            'provider': href.split('/')[-1].split('--')[0] if '--' in href else 'unknown',
                            'description': '',
                            'context_window': '',
                            'input_pricing': '',
                            'output_pricing': '',
                            'image_pricing': '',
                            'provider_url': ''
                        }
                        
                        if model_info['provider'] != 'unknown':
                            model_info['provider_url'] = f"https://openrouter.ai/providers/{model_info['provider']}"
                        
                        models.append(model_info)
                        
                except Exception as e:
                    continue
            
            print(f"✅ Web scraping found {len(models)} models")
            return models
            
        except Exception as e:
            print(f"❌ Web scraping failed: {e}")
            return []

    def save_models(self, models: List[Dict], method: str):
        """Save models to CSV and JSON files."""
        if not models:
            print("⚠️  No models to save")
            return
        
        # Save CSV
        csv_filename = f"openrouter_models_{method}.csv"
        try:
            df = pd.DataFrame(models)
            # Ensure consistent column order
            columns = ['id', 'name', 'provider', 'provider_url', 'model_url', 
                      'description', 'context_window', 'input_pricing', 
                      'output_pricing', 'image_pricing']
            
            # Add any missing columns
            for col in columns:
                if col not in df.columns:
                    df[col] = ''
            
            # Reorder columns
            df = df[columns]
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"✅ Saved CSV: {csv_filename}")
            
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")
        
        # Save JSON
        json_filename = f"openrouter_models_{method}.json"
        try:
            output_data = {
                'metadata': {
                    'total_models': len(models),
                    'generated_at': datetime.now().isoformat(),
                    'method': method,
                    'parser_version': '12.0'
                },
                'models': models
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved JSON: {json_filename}")
            
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

    def display_summary(self, models: List[Dict]):
        """Display summary of parsed models."""
        if not models:
            print("❌ No models found")
            return
        
        print(f"\n📊 Summary:")
        print(f"   Total models: {len(models)}")
        
        # Provider breakdown
        providers = {}
        for model in models:
            provider = model.get('provider', 'Unknown')
            providers[provider] = providers.get(provider, 0) + 1
        
        print(f"   Unique providers: {len(providers)}")
        
        # Top 5 providers
        sorted_providers = sorted(providers.items(), key=lambda x: x[1], reverse=True)
        print(f"   Top providers:")
        for provider, count in sorted_providers[:5]:
            print(f"      {provider}: {count} models")
        
        # Data completeness
        with_pricing = len([m for m in models if m.get('input_pricing')])
        with_description = len([m for m in models if m.get('description')])
        free_models = len([m for m in models if m.get('input_pricing') == 'Free'])
        
        print(f"   Models with pricing: {with_pricing} ({with_pricing/len(models)*100:.1f}%)")
        print(f"   Models with description: {with_description} ({with_description/len(models)*100:.1f}%)")
        print(f"   Free models: {free_models}")

    def run(self, method: str = 'api') -> List[Dict]:
        """Main parsing method."""
        print("🚀 OpenRouter Model Parser v12")
        print("=" * 40)
        
        models = []
        
        if method == 'api':
            api_models = self.fetch_api_models()
            if api_models:
                models = self.format_api_models(api_models)
                method_used = 'api'
            else:
                print("❌ API method failed")
                return []
                
        elif method == 'web':
            models = self.scrape_web_models()
            method_used = 'web_scraping'
            
        elif method == 'both':
            # Try API first
            api_models = self.fetch_api_models()
            web_models = self.scrape_web_models()
            
            if api_models and web_models:
                if len(web_models) > len(api_models):
                    models = web_models
                    method_used = 'web_scraping'
                    print(f"🎯 Using web scraping ({len(web_models)} vs {len(api_models)} models)")
                else:
                    models = self.format_api_models(api_models)
                    method_used = 'api'
                    print(f"🎯 Using API ({len(api_models)} vs {len(web_models)} models)")
            elif api_models:
                models = self.format_api_models(api_models)
                method_used = 'api'
                print("🎯 Using API (web scraping failed)")
            elif web_models:
                models = web_models
                method_used = 'web_scraping'
                print("🎯 Using web scraping (API failed)")
            else:
                print("❌ Both methods failed")
                return []
        
        if models:
            self.display_summary(models)
            self.save_models(models, method_used)
        
        return models


def main():
    """Main function."""
    print("🔍 OpenRouter Model Parser")
    print("Choose method:")
    print("1. API only (reliable, ~320 models)")
    print("2. Web scraping only (experimental)")
    print("3. Both (try both, use best result)")
    
    choice = input("\nEnter 1, 2, or 3 (default: 1): ").strip()
    
    parser = OpenRouterParser()
    
    if choice == '2':
        models = parser.run('web')
    elif choice == '3':
        models = parser.run('both')
    else:
        models = parser.run('api')
    
    print(f"\n🎉 Complete! Found {len(models)} models")
    
    if models:
        print("\n📁 Files generated:")
        print("  - CSV file for spreadsheet use")
        print("  - JSON file for programmatic use")
        print("  - HTML file (web scraping debug)")
        
        print(f"\n💡 Ready for your Streamlit app!")
        print(f"   Load the CSV file as your primary data source")
    else:
        print(f"\n❌ No models found. Try option 1 (API only)")


if __name__ == "__main__":
    main()
