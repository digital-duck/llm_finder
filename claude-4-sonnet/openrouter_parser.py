#!/usr/bin/env python3
"""
OpenRouter Model Parser - Clean Working Version

This script parses LLM model information from OpenRouter using both API
and web scraping approaches with comprehensive failure logging.

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
from urllib.parse import urljoin
from typing import Dict, List, Optional
import time
from datetime import datetime


class OpenRouterParser:
    def __init__(self):
        self.base_url = "https://openrouter.ai"
        self.models_url = "https://openrouter.ai/models"
        self.api_url = "https://openrouter.ai/api/v1/models"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Failure tracking
        self.failures = []
        self.stats = {
            'api_attempts': 0,
            'api_success': 0,
            'web_attempts': 0, 
            'web_success': 0,
            'validation_failures': 0
        }

    def fetch_models_via_api(self) -> List[Dict]:
        """Fetch model information using OpenRouter's API."""
        self.stats['api_attempts'] += 1
        
        try:
            print("📡 Fetching models via API...")
            response = self.session.get(self.api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            models = data.get('data', [])
            
            if models:
                self.stats['api_success'] += 1
                print(f"✅ API successful: {len(models)} models found")
            else:
                print("⚠️  API returned no models")
                
            return models
            
        except Exception as e:
            error_info = {
                'method': 'api',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.failures.append(error_info)
            print(f"❌ API failed: {e}")
            return []

    def parse_web_interface(self) -> List[Dict]:
        """Parse model information from web interface."""
        self.stats['web_attempts'] += 1
        
        try:
            print("🕷️  Fetching models via web scraping...")
            
            # Try to get the page with longer timeout and better headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(self.models_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Save HTML for debugging
            with open('openrouter_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("💾 Saved HTML to openrouter_page.html")
            
            # Check if page is mostly empty (JavaScript-rendered)
            if len(response.text) < 5000 or 'models' not in response.text.lower():
                print("⚠️  Page appears to be JavaScript-rendered, trying API fallback")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            models = []
            
            # Strategy 1: Look for various link patterns
            print("🔍 Strategy 1: Looking for model links...")
            link_patterns = [
                r'/models/[^/\s]+

    def extract_from_links(self, soup, model_links) -> List[Dict]:
        """Extract models from HTML links."""
        models = []
        
        for link in model_links[:50]:  # Limit to prevent too many attempts
            try:
                # Basic info from link
                model_info = {
                    'name': link.get_text(strip=True),
                    'model_url': urljoin(self.base_url, link['href']),
                    'id': link['href'].replace('/models/', '').replace('--', '/')
                }
                
                # Find container with more info
                container = link.parent
                for _ in range(5):  # Look up to 5 levels up
                    if container and container.parent:
                        container = container.parent
                        text = container.get_text()
                        if 'tokens' in text and ('$' in text or 'free' in text.lower()):
                            break
                
                if container:
                    self.extract_details_from_container(container, model_info)
                
                if model_info.get('name'):
                    models.append(model_info)
                    
            except Exception as e:
                self.failures.append({
                    'method': 'link_extraction',
                    'link': str(link)[:100],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                continue
        
        return models

    def extract_details_from_container(self, container, model_info):
        """Extract detailed info from HTML container."""
        text = container.get_text()
        
        # Extract provider
        provider_match = re.search(r'by\s+([^|$\n]+)', text, re.IGNORECASE)
        if provider_match:
            provider = provider_match.group(1).strip()
            model_info['provider'] = provider
            model_info['provider_url'] = f"https://openrouter.ai/providers/{provider.lower().replace(' ', '-')}"
        
        # Extract context window
        context_match = re.search(r'(\d+(?:,\d+)*)\s*[KM]?\s*(?:context|tokens)', text, re.IGNORECASE)
        if context_match:
            model_info['context_window'] = f"{context_match.group(1)} tokens"
        
        # Extract pricing
        input_match = re.search(r'\$([0-9.]+)/M\s+input', text, re.IGNORECASE)
        if input_match:
            model_info['input_pricing'] = f"${input_match.group(1)}/M tokens"
        elif 'free' in text.lower():
            model_info['input_pricing'] = 'Free'
        else:
            model_info['input_pricing'] = ''
        
        output_match = re.search(r'\$([0-9.]+)/M\s+output', text, re.IGNORECASE)
        if output_match:
            model_info['output_pricing'] = f"${output_match.group(1)}/M tokens"
        else:
            model_info['output_pricing'] = ''
        
        image_match = re.search(r'\$([0-9.]+)/K.*img', text, re.IGNORECASE)
        if image_match:
            model_info['image_pricing'] = f"${image_match.group(1)}/K images"
        else:
            model_info['image_pricing'] = ''
        
        # Extract description
        desc_elements = container.find_all(['p', 'div'])
        for elem in desc_elements:
            elem_text = elem.get_text(strip=True)
            if (len(elem_text) > 50 and 
                'tokens' not in elem_text.lower() and 
                '$' not in elem_text):
                model_info['description'] = elem_text[:300]
                break

    def extract_from_json(self, soup) -> List[Dict]:
        """Extract models from JSON script tags."""
        models = []
        
        # Look for JSON scripts
        script_tags = soup.find_all('script', type='application/json')
        script_tags.extend(soup.find_all('script', id='__NEXT_DATA__'))
        
        for script in script_tags:
            try:
                if script.string:
                    data = json.loads(script.string)
                    found_models = self.parse_json_data(data)
                    if found_models:
                        models.extend(found_models)
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return models

    def parse_json_data(self, data) -> List[Dict]:
        """Parse models from JSON data structure."""
        models = []
        
        # Try different possible locations
        possible_paths = [
            data.get('models', []),
            data.get('data', []),
            data.get('props', {}).get('pageProps', {}).get('models', []),
            data.get('props', {}).get('pageProps', {}).get('data', [])
        ]
        
        for model_list in possible_paths:
            if isinstance(model_list, list) and model_list:
                for item in model_list:
                    if isinstance(item, dict):
                        model_info = self.format_json_model(item)
                        if model_info:
                            models.append(model_info)
                break
        
        return models

    def format_json_model(self, item) -> Optional[Dict]:
        """Format model from JSON item."""
        try:
            model_info = {
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'provider': item.get('id', '').split('/')[0] if '/' in item.get('id', '') else '',
                'model_url': f"https://openrouter.ai/models/{item.get('id', '').replace('/', '--')}"
            }
            
            # Context window
            context = item.get('context_length', 0)
            if context:
                model_info['context_window'] = f"{context:,} tokens"
            
            # Pricing
            pricing = item.get('pricing', {})
            if pricing:
                model_info['input_pricing'] = self.format_pricing(pricing.get('prompt'), 'input')
                model_info['output_pricing'] = self.format_pricing(pricing.get('completion'), 'output')
                model_info['image_pricing'] = self.format_pricing(pricing.get('image'), 'image')
            
            # Provider URL
            if model_info['provider']:
                model_info['provider_url'] = f"https://openrouter.ai/providers/{model_info['provider']}"
            
            return model_info if model_info.get('name') else None
            
        except Exception as e:
            self.failures.append({
                'method': 'json_parsing',
                'item': str(item)[:100],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return None

    def extract_from_patterns(self, soup) -> List[Dict]:
        """Extract models using text patterns - Enhanced version."""
        models = []
        
        try:
            text = soup.get_text()
            print(f"   Analyzing {len(text)} characters of text content")
            
            # Enhanced model ID patterns
            patterns_and_providers = [
                (r'openai/gpt-[0-9a-z\-\.]+', 'openai'),
                (r'anthropic/claude-[0-9a-z\-\.]+', 'anthropic'),
                (r'google/gemini-[0-9a-z\-\.]+', 'google'),
                (r'meta-llama/[0-9a-z\-\.]+', 'meta-llama'),
                (r'mistralai/[0-9a-z\-\.]+', 'mistralai'),
                (r'qwen/[0-9a-z\-\.]+', 'qwen'),
                (r'microsoft/[0-9a-z\-\.]+', 'microsoft'),
                (r'cohere/[0-9a-z\-\.]+', 'cohere'),
                # More generic patterns
                (r'[a-z0-9\-_]+/(gpt|claude|gemini|llama|mistral)[0-9a-z\-\.]*', None),
                (r'[a-z0-9\-_]+/[a-z0-9\-_]+', None)  # Very generic
            ]
            
            found_models = set()
            
            for pattern, expected_provider in patterns_and_providers:
                matches = re.findall(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if isinstance(match, tuple):
                        model_id = match[0] if match[0] else f"unknown/{match[1]}"
                    else:
                        model_id = match
                    
                    # Skip if already found
                    if model_id in found_models:
                        continue
                    
                    # Basic validation
                    if len(model_id.split('/')) != 2:
                        continue
                    
                    provider, model_name = model_id.split('/')
                    
                    # Skip obvious false positives
                    if any(skip in model_id.lower() for skip in ['http', 'www', 'api', 'docs', 'github']):
                        continue
                    
                    model_info = {
                        'id': model_id.lower(),
                        'name': model_name.replace('-', ' ').replace('_', ' ').title(),
                        'provider': provider.lower(),
                        'model_url': f"https://openrouter.ai/models/{model_id.replace('/', '--')}",
                        'provider_url': f"https://openrouter.ai/providers/{provider.lower()}",
                        'description': '',
                        'context_window': '',
                        'input_pricing': '',
                        'output_pricing': '',
                        'image_pricing': ''
                    }
                    
                    found_models.add(model_id)
                    models.append(model_info)
                    
                    # Limit to prevent too many false positives
                    if len(models) >= 50:
                        break
                
                if len(models) >= 50:
                    break
            
            print(f"   Found {len(models)} potential models from text patterns")
            
        except Exception as e:
            self.failures.append({
                'method': 'pattern_extraction',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return models

    def run(self, method='both'):
        """Main execution method with better error handling."""
        print("🚀 OpenRouter Model Parser v11 (Clean)")
        print("=" * 50)
        
        api_models = []
        web_models = []
        
        # Try API first if requested
        if method in ['api', 'both']:
            print("\n📡 Phase 1: API Method")
            print("-" * 30)
            api_models = self.fetch_models_via_api()
            if api_models:
                api_models = self.format_api_data(api_models)
                print(f"✅ API method: {len(api_models)} models")
            else:
                print("❌ API method failed")
        
        # Try web scraping if requested
        if method in ['web', 'both']:
            print(f"\n🕷️  Phase 2: Web Scraping Method")
            print("-" * 30)
            web_models = self.parse_web_interface()
            if web_models:
                print(f"✅ Web scraping: {len(web_models)} models")
            else:
                print("❌ Web scraping failed")
        
        # Determine which result to use
        if method == 'api':
            models = api_models
            used_method = 'api'
        elif method == 'web':
            models = web_models  
            used_method = 'web_scraping'
        else:  # both
            if web_models and len(web_models) > len(api_models):
                models = web_models
                used_method = 'web_scraping'
                print(f"\n🎯 Using web scraping results ({len(web_models)} > {len(api_models)})")
            elif api_models:
                models = api_models
                used_method = 'api'
                print(f"\n🎯 Using API results ({len(api_models)} models)")
            else:
                models = []
                used_method = 'none'
                print("\n❌ Both methods failed")
        
        if not models:
            print("\n❌ No models found with any method!")
            print("\n🔧 Troubleshooting suggestions:")
            print("1. Check your internet connection")
            print("2. Try API-only method (option 1)")
            print("3. Check openrouter_page.html to see what was downloaded")
            print("4. The website might be blocking automated requests")
            self.save_failures()
            return []
        
        print(f"\n📊 Processing {len(models)} models...")
        
        # Validate and save
        models = self.validate_models(models)
        
        if models:
            self.display_summary(models)
            self.save_results(models, used_method)
        
        self.save_failures()
        
        return models

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

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """Format API data to consistent structure."""
        formatted = []
        
        for model in api_models:
            provider = model.get('id', '').split('/')[0] if '/' in model.get('id', '') else ''
            
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': provider,
                'provider_url': f"https://openrouter.ai/providers/{provider}" if provider else '',
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt'), "input"),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion'), "output"),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image'), "image"),
            }
            formatted.append(formatted_model)
        
        return formatted

    def validate_models(self, models: List[Dict]) -> List[Dict]:
        """Validate and clean model data."""
        valid_models = []
        
        for model in models:
            # Check essential fields
            if not model.get('name') and not model.get('id'):
                self.stats['validation_failures'] += 1
                self.failures.append({
                    'method': 'validation',
                    'model': str(model)[:100],
                    'error': 'Missing name and id',
                    'timestamp': datetime.now().isoformat()
                })
                continue
            
            # Clean and generate missing fields
            if model.get('id') and not model.get('model_url'):
                model['model_url'] = f"https://openrouter.ai/models/{model['id'].replace('/', '--')}"
            
            if model.get('provider') and not model.get('provider_url'):
                model['provider_url'] = f"https://openrouter.ai/providers/{model['provider'].lower()}"
            
            # Ensure all required fields exist
            required_fields = ['id', 'name', 'provider', 'model_url', 'provider_url', 
                             'description', 'context_window', 'input_pricing', 
                             'output_pricing', 'image_pricing']
            
            for field in required_fields:
                if field not in model:
                    model[field] = ''
            
            valid_models.append(model)
        
        return valid_models

    def save_results(self, models: List[Dict], method: str):
        """Save results to files."""
        if not models:
            print("⚠️  No models to save")
            return
        
        # Save CSV
        csv_filename = f"openrouter_models_{method}.csv"
        try:
            df = pd.DataFrame(models)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"✅ Saved {len(models)} models to {csv_filename}")
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
                    'parser_version': '11.0'
                },
                'models': models
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved {len(models)} models to {json_filename}")
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

    def save_failures(self):
        """Save failure analysis."""
        if not self.failures:
            return
        
        failure_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_failures': len(self.failures)
            },
            'statistics': self.stats,
            'failures': self.failures
        }
        
        try:
            with open('parsing_failures.json', 'w', encoding='utf-8') as f:
                json.dump(failure_data, f, indent=2, ensure_ascii=False)
            print(f"📋 Saved failure analysis ({len(self.failures)} failures)")
        except Exception as e:
            print(f"❌ Error saving failures: {e}")

    def display_summary(self, models: List[Dict]):
        """Display parsing summary."""
        if not models:
            print("❌ No models found")
            return
        
        print(f"\n📊 Parsing Summary:")
        print(f"✅ Total models: {len(models)}")
        
        # Provider stats
        providers = set(m.get('provider', 'Unknown') for m in models if m.get('provider'))
        print(f"🏢 Providers: {len(providers)}")
        
        # Data completeness
        with_pricing = len([m for m in models if m.get('input_pricing')])
        with_description = len([m for m in models if m.get('description')])
        free_models = len([m for m in models if m.get('input_pricing') == 'Free'])
        
        print(f"💰 With pricing: {with_pricing}/{len(models)} ({with_pricing/len(models)*100:.1f}%)")
        print(f"📝 With description: {with_description}/{len(models)} ({with_description/len(models)*100:.1f}%)")
        print(f"🆓 Free models: {free_models}")
        
        # Top providers
        if providers:
            from collections import Counter
            provider_counts = Counter(m.get('provider', 'Unknown') for m in models)
            print(f"\n🏆 Top 5 Providers:")
            for provider, count in provider_counts.most_common(5):
                print(f"   {provider}: {count} models")

    def run(self, method='both'):
        """Main execution method."""
        print("🚀 OpenRouter Model Parser v11 (Clean)")
        print("=" * 50)
        
        api_models = []
        web_models = []
        
        if method in ['api', 'both']:
            api_models = self.fetch_models_via_api()
            if api_models:
                api_models = self.format_api_data(api_models)
        
        if method in ['web', 'both']:
            web_models = self.parse_web_interface()
        
        # Choose best result
        if method == 'api' or (api_models and not web_models):
            models = api_models
            used_method = 'api'
        elif method == 'web' or (web_models and not api_models):
            models = web_models
            used_method = 'web_scraping'
        elif web_models:  # Prefer web scraping if both available
            models = web_models
            used_method = 'web_scraping'
        elif api_models:
            models = api_models
            used_method = 'api'
        else:
            print("❌ No models found with any method")
            self.save_failures()
            return []
        
        print(f"\n🎯 Using {used_method} results")
        
        # Validate and save
        models = self.validate_models(models)
        self.display_summary(models)
        self.save_results(models, used_method)
        self.save_failures()
        
        return models


def main():
    """Main function with improved guidance."""
    parser = OpenRouterParser()
    
    print("🔍 OpenRouter Model Parser v11 (Clean)")
    print("=" * 50)
    print("\nChoose parsing method:")
    print("1. 📡 API only (reliable, ~320 models)")
    print("2. 🕷️  Web scraping only (experimental, ~477 models if working)")  
    print("3. 🔄 Both (recommended - API with web scraping fallback)")
    
    choice = input("\nEnter choice (1-3) or press Enter for default (1): ").strip()
    
    if choice == "2":
        method = 'web'
        print("\n⚠️  Note: Web scraping may not work if the site is JavaScript-rendered")
    elif choice == "3":
        method = 'both'
    else:
        method = 'api'
        print("\n✅ Using reliable API method")
    
    models = parser.run(method)
    
    print(f"\n🎉 Complete! Found {len(models)} models")
    
    if models:
        print("\n📁 Files created:")
        print("- CSV and JSON files with model data")
        if parser.failures:
            print("- parsing_failures.json (failure analysis)")
        print("- openrouter_page.html (web page for debugging)")
        
        print(f"\n💡 Success! Your enhanced Streamlit app can now use:")
        print(f"   - {len(models)} models with rich metadata")
        print(f"   - Provider URLs and accurate pricing")
        print(f"   - Complete model information")
        
    else:
        print(f"\n❌ No models found. Recommendations:")
        print("1. Try option 1 (API only) - most reliable")
        print("2. Check your internet connection")
        print("3. OpenRouter might be blocking automated requests")
        print("4. Check openrouter_page.html to see what was downloaded")
    
    return models


if __name__ == "__main__":
    main()
,
                r'/models/[^/\s]+--[^/\s]+

    def extract_from_links(self, soup, model_links) -> List[Dict]:
        """Extract models from HTML links."""
        models = []
        
        for link in model_links[:50]:  # Limit to prevent too many attempts
            try:
                # Basic info from link
                model_info = {
                    'name': link.get_text(strip=True),
                    'model_url': urljoin(self.base_url, link['href']),
                    'id': link['href'].replace('/models/', '').replace('--', '/')
                }
                
                # Find container with more info
                container = link.parent
                for _ in range(5):  # Look up to 5 levels up
                    if container and container.parent:
                        container = container.parent
                        text = container.get_text()
                        if 'tokens' in text and ('$' in text or 'free' in text.lower()):
                            break
                
                if container:
                    self.extract_details_from_container(container, model_info)
                
                if model_info.get('name'):
                    models.append(model_info)
                    
            except Exception as e:
                self.failures.append({
                    'method': 'link_extraction',
                    'link': str(link)[:100],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                continue
        
        return models

    def extract_details_from_container(self, container, model_info):
        """Extract detailed info from HTML container."""
        text = container.get_text()
        
        # Extract provider
        provider_match = re.search(r'by\s+([^|$\n]+)', text, re.IGNORECASE)
        if provider_match:
            provider = provider_match.group(1).strip()
            model_info['provider'] = provider
            model_info['provider_url'] = f"https://openrouter.ai/providers/{provider.lower().replace(' ', '-')}"
        
        # Extract context window
        context_match = re.search(r'(\d+(?:,\d+)*)\s*[KM]?\s*(?:context|tokens)', text, re.IGNORECASE)
        if context_match:
            model_info['context_window'] = f"{context_match.group(1)} tokens"
        
        # Extract pricing
        input_match = re.search(r'\$([0-9.]+)/M\s+input', text, re.IGNORECASE)
        if input_match:
            model_info['input_pricing'] = f"${input_match.group(1)}/M tokens"
        elif 'free' in text.lower():
            model_info['input_pricing'] = 'Free'
        else:
            model_info['input_pricing'] = ''
        
        output_match = re.search(r'\$([0-9.]+)/M\s+output', text, re.IGNORECASE)
        if output_match:
            model_info['output_pricing'] = f"${output_match.group(1)}/M tokens"
        else:
            model_info['output_pricing'] = ''
        
        image_match = re.search(r'\$([0-9.]+)/K.*img', text, re.IGNORECASE)
        if image_match:
            model_info['image_pricing'] = f"${image_match.group(1)}/K images"
        else:
            model_info['image_pricing'] = ''
        
        # Extract description
        desc_elements = container.find_all(['p', 'div'])
        for elem in desc_elements:
            elem_text = elem.get_text(strip=True)
            if (len(elem_text) > 50 and 
                'tokens' not in elem_text.lower() and 
                '$' not in elem_text):
                model_info['description'] = elem_text[:300]
                break

    def extract_from_json(self, soup) -> List[Dict]:
        """Extract models from JSON script tags."""
        models = []
        
        # Look for JSON scripts
        script_tags = soup.find_all('script', type='application/json')
        script_tags.extend(soup.find_all('script', id='__NEXT_DATA__'))
        
        for script in script_tags:
            try:
                if script.string:
                    data = json.loads(script.string)
                    found_models = self.parse_json_data(data)
                    if found_models:
                        models.extend(found_models)
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return models

    def parse_json_data(self, data) -> List[Dict]:
        """Parse models from JSON data structure."""
        models = []
        
        # Try different possible locations
        possible_paths = [
            data.get('models', []),
            data.get('data', []),
            data.get('props', {}).get('pageProps', {}).get('models', []),
            data.get('props', {}).get('pageProps', {}).get('data', [])
        ]
        
        for model_list in possible_paths:
            if isinstance(model_list, list) and model_list:
                for item in model_list:
                    if isinstance(item, dict):
                        model_info = self.format_json_model(item)
                        if model_info:
                            models.append(model_info)
                break
        
        return models

    def format_json_model(self, item) -> Optional[Dict]:
        """Format model from JSON item."""
        try:
            model_info = {
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'provider': item.get('id', '').split('/')[0] if '/' in item.get('id', '') else '',
                'model_url': f"https://openrouter.ai/models/{item.get('id', '').replace('/', '--')}"
            }
            
            # Context window
            context = item.get('context_length', 0)
            if context:
                model_info['context_window'] = f"{context:,} tokens"
            
            # Pricing
            pricing = item.get('pricing', {})
            if pricing:
                model_info['input_pricing'] = self.format_pricing(pricing.get('prompt'), 'input')
                model_info['output_pricing'] = self.format_pricing(pricing.get('completion'), 'output')
                model_info['image_pricing'] = self.format_pricing(pricing.get('image'), 'image')
            
            # Provider URL
            if model_info['provider']:
                model_info['provider_url'] = f"https://openrouter.ai/providers/{model_info['provider']}"
            
            return model_info if model_info.get('name') else None
            
        except Exception as e:
            self.failures.append({
                'method': 'json_parsing',
                'item': str(item)[:100],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return None

    def extract_from_patterns(self, soup) -> List[Dict]:
        """Extract models using text patterns."""
        models = []
        
        try:
            text = soup.get_text()
            
            # Find model ID patterns
            model_pattern = r'([a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_\.]+)'
            potential_ids = re.findall(model_pattern, text)
            
            # Filter likely model IDs
            providers = ['openai', 'anthropic', 'google', 'meta-llama', 'mistralai', 'qwen']
            
            for model_id in set(potential_ids):
                provider = model_id.split('/')[0].lower()
                if provider in providers:
                    model_info = {
                        'id': model_id,
                        'name': model_id.split('/')[-1].replace('-', ' ').title(),
                        'provider': provider,
                        'model_url': f"https://openrouter.ai/models/{model_id.replace('/', '--')}",
                        'provider_url': f"https://openrouter.ai/providers/{provider}"
                    }
                    models.append(model_info)
                    
                    if len(models) >= 20:  # Limit to prevent too many
                        break
            
        except Exception as e:
            self.failures.append({
                'method': 'pattern_extraction',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return models

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

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """Format API data to consistent structure."""
        formatted = []
        
        for model in api_models:
            provider = model.get('id', '').split('/')[0] if '/' in model.get('id', '') else ''
            
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': provider,
                'provider_url': f"https://openrouter.ai/providers/{provider}" if provider else '',
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt'), "input"),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion'), "output"),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image'), "image"),
            }
            formatted.append(formatted_model)
        
        return formatted

    def validate_models(self, models: List[Dict]) -> List[Dict]:
        """Validate and clean model data."""
        valid_models = []
        
        for model in models:
            # Check essential fields
            if not model.get('name') and not model.get('id'):
                self.stats['validation_failures'] += 1
                self.failures.append({
                    'method': 'validation',
                    'model': str(model)[:100],
                    'error': 'Missing name and id',
                    'timestamp': datetime.now().isoformat()
                })
                continue
            
            # Clean and generate missing fields
            if model.get('id') and not model.get('model_url'):
                model['model_url'] = f"https://openrouter.ai/models/{model['id'].replace('/', '--')}"
            
            if model.get('provider') and not model.get('provider_url'):
                model['provider_url'] = f"https://openrouter.ai/providers/{model['provider'].lower()}"
            
            # Ensure all required fields exist
            required_fields = ['id', 'name', 'provider', 'model_url', 'provider_url', 
                             'description', 'context_window', 'input_pricing', 
                             'output_pricing', 'image_pricing']
            
            for field in required_fields:
                if field not in model:
                    model[field] = ''
            
            valid_models.append(model)
        
        return valid_models

    def save_results(self, models: List[Dict], method: str):
        """Save results to files."""
        if not models:
            print("⚠️  No models to save")
            return
        
        # Save CSV
        csv_filename = f"openrouter_models_{method}.csv"
        try:
            df = pd.DataFrame(models)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"✅ Saved {len(models)} models to {csv_filename}")
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
                    'parser_version': '11.0'
                },
                'models': models
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved {len(models)} models to {json_filename}")
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

    def save_failures(self):
        """Save failure analysis."""
        if not self.failures:
            return
        
        failure_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_failures': len(self.failures)
            },
            'statistics': self.stats,
            'failures': self.failures
        }
        
        try:
            with open('parsing_failures.json', 'w', encoding='utf-8') as f:
                json.dump(failure_data, f, indent=2, ensure_ascii=False)
            print(f"📋 Saved failure analysis ({len(self.failures)} failures)")
        except Exception as e:
            print(f"❌ Error saving failures: {e}")

    def display_summary(self, models: List[Dict]):
        """Display parsing summary."""
        if not models:
            print("❌ No models found")
            return
        
        print(f"\n📊 Parsing Summary:")
        print(f"✅ Total models: {len(models)}")
        
        # Provider stats
        providers = set(m.get('provider', 'Unknown') for m in models if m.get('provider'))
        print(f"🏢 Providers: {len(providers)}")
        
        # Data completeness
        with_pricing = len([m for m in models if m.get('input_pricing')])
        with_description = len([m for m in models if m.get('description')])
        free_models = len([m for m in models if m.get('input_pricing') == 'Free'])
        
        print(f"💰 With pricing: {with_pricing}/{len(models)} ({with_pricing/len(models)*100:.1f}%)")
        print(f"📝 With description: {with_description}/{len(models)} ({with_description/len(models)*100:.1f}%)")
        print(f"🆓 Free models: {free_models}")
        
        # Top providers
        if providers:
            from collections import Counter
            provider_counts = Counter(m.get('provider', 'Unknown') for m in models)
            print(f"\n🏆 Top 5 Providers:")
            for provider, count in provider_counts.most_common(5):
                print(f"   {provider}: {count} models")

    def run(self, method='both'):
        """Main execution method."""
        print("🚀 OpenRouter Model Parser v11 (Clean)")
        print("=" * 50)
        
        api_models = []
        web_models = []
        
        if method in ['api', 'both']:
            api_models = self.fetch_models_via_api()
            if api_models:
                api_models = self.format_api_data(api_models)
        
        if method in ['web', 'both']:
            web_models = self.parse_web_interface()
        
        # Choose best result
        if method == 'api' or (api_models and not web_models):
            models = api_models
            used_method = 'api'
        elif method == 'web' or (web_models and not api_models):
            models = web_models
            used_method = 'web_scraping'
        elif web_models:  # Prefer web scraping if both available
            models = web_models
            used_method = 'web_scraping'
        elif api_models:
            models = api_models
            used_method = 'api'
        else:
            print("❌ No models found with any method")
            self.save_failures()
            return []
        
        print(f"\n🎯 Using {used_method} results")
        
        # Validate and save
        models = self.validate_models(models)
        self.display_summary(models)
        self.save_results(models, used_method)
        self.save_failures()
        
        return models


def main():
    """Main function."""
    parser = OpenRouterParser()
    
    print("Choose parsing method:")
    print("1. API only (fast, ~320 models)")
    print("2. Web scraping only (comprehensive, ~477 models)")  
    print("3. Both (recommended)")
    
    choice = input("Enter choice (1-3) or press Enter for default (3): ").strip()
    
    if choice == "1":
        method = 'api'
    elif choice == "2":
        method = 'web'
    else:
        method = 'both'
    
    models = parser.run(method)
    
    print(f"\n🎉 Complete! Found {len(models)} models")
    
    if models:
        print("\n📁 Files created:")
        print("- CSV and JSON files with model data")
        print("- parsing_failures.json (failure analysis)")
        print("- openrouter_page.html (web page for debugging)")
        
        print(f"\n💡 Next steps:")
        print("1. Review the CSV/JSON files")
        print("2. Use this data in your Streamlit app")
        print("3. Check parsing_failures.json for improvements")
    
    return models


if __name__ == "__main__":
    main()
,
                r'/[^/\s]+/[^/\s]+

    def extract_from_links(self, soup, model_links) -> List[Dict]:
        """Extract models from HTML links."""
        models = []
        
        for link in model_links[:50]:  # Limit to prevent too many attempts
            try:
                # Basic info from link
                model_info = {
                    'name': link.get_text(strip=True),
                    'model_url': urljoin(self.base_url, link['href']),
                    'id': link['href'].replace('/models/', '').replace('--', '/')
                }
                
                # Find container with more info
                container = link.parent
                for _ in range(5):  # Look up to 5 levels up
                    if container and container.parent:
                        container = container.parent
                        text = container.get_text()
                        if 'tokens' in text and ('$' in text or 'free' in text.lower()):
                            break
                
                if container:
                    self.extract_details_from_container(container, model_info)
                
                if model_info.get('name'):
                    models.append(model_info)
                    
            except Exception as e:
                self.failures.append({
                    'method': 'link_extraction',
                    'link': str(link)[:100],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                continue
        
        return models

    def extract_details_from_container(self, container, model_info):
        """Extract detailed info from HTML container."""
        text = container.get_text()
        
        # Extract provider
        provider_match = re.search(r'by\s+([^|$\n]+)', text, re.IGNORECASE)
        if provider_match:
            provider = provider_match.group(1).strip()
            model_info['provider'] = provider
            model_info['provider_url'] = f"https://openrouter.ai/providers/{provider.lower().replace(' ', '-')}"
        
        # Extract context window
        context_match = re.search(r'(\d+(?:,\d+)*)\s*[KM]?\s*(?:context|tokens)', text, re.IGNORECASE)
        if context_match:
            model_info['context_window'] = f"{context_match.group(1)} tokens"
        
        # Extract pricing
        input_match = re.search(r'\$([0-9.]+)/M\s+input', text, re.IGNORECASE)
        if input_match:
            model_info['input_pricing'] = f"${input_match.group(1)}/M tokens"
        elif 'free' in text.lower():
            model_info['input_pricing'] = 'Free'
        else:
            model_info['input_pricing'] = ''
        
        output_match = re.search(r'\$([0-9.]+)/M\s+output', text, re.IGNORECASE)
        if output_match:
            model_info['output_pricing'] = f"${output_match.group(1)}/M tokens"
        else:
            model_info['output_pricing'] = ''
        
        image_match = re.search(r'\$([0-9.]+)/K.*img', text, re.IGNORECASE)
        if image_match:
            model_info['image_pricing'] = f"${image_match.group(1)}/K images"
        else:
            model_info['image_pricing'] = ''
        
        # Extract description
        desc_elements = container.find_all(['p', 'div'])
        for elem in desc_elements:
            elem_text = elem.get_text(strip=True)
            if (len(elem_text) > 50 and 
                'tokens' not in elem_text.lower() and 
                '$' not in elem_text):
                model_info['description'] = elem_text[:300]
                break

    def extract_from_json(self, soup) -> List[Dict]:
        """Extract models from JSON script tags."""
        models = []
        
        # Look for JSON scripts
        script_tags = soup.find_all('script', type='application/json')
        script_tags.extend(soup.find_all('script', id='__NEXT_DATA__'))
        
        for script in script_tags:
            try:
                if script.string:
                    data = json.loads(script.string)
                    found_models = self.parse_json_data(data)
                    if found_models:
                        models.extend(found_models)
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return models

    def parse_json_data(self, data) -> List[Dict]:
        """Parse models from JSON data structure."""
        models = []
        
        # Try different possible locations
        possible_paths = [
            data.get('models', []),
            data.get('data', []),
            data.get('props', {}).get('pageProps', {}).get('models', []),
            data.get('props', {}).get('pageProps', {}).get('data', [])
        ]
        
        for model_list in possible_paths:
            if isinstance(model_list, list) and model_list:
                for item in model_list:
                    if isinstance(item, dict):
                        model_info = self.format_json_model(item)
                        if model_info:
                            models.append(model_info)
                break
        
        return models

    def format_json_model(self, item) -> Optional[Dict]:
        """Format model from JSON item."""
        try:
            model_info = {
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'provider': item.get('id', '').split('/')[0] if '/' in item.get('id', '') else '',
                'model_url': f"https://openrouter.ai/models/{item.get('id', '').replace('/', '--')}"
            }
            
            # Context window
            context = item.get('context_length', 0)
            if context:
                model_info['context_window'] = f"{context:,} tokens"
            
            # Pricing
            pricing = item.get('pricing', {})
            if pricing:
                model_info['input_pricing'] = self.format_pricing(pricing.get('prompt'), 'input')
                model_info['output_pricing'] = self.format_pricing(pricing.get('completion'), 'output')
                model_info['image_pricing'] = self.format_pricing(pricing.get('image'), 'image')
            
            # Provider URL
            if model_info['provider']:
                model_info['provider_url'] = f"https://openrouter.ai/providers/{model_info['provider']}"
            
            return model_info if model_info.get('name') else None
            
        except Exception as e:
            self.failures.append({
                'method': 'json_parsing',
                'item': str(item)[:100],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return None

    def extract_from_patterns(self, soup) -> List[Dict]:
        """Extract models using text patterns."""
        models = []
        
        try:
            text = soup.get_text()
            
            # Find model ID patterns
            model_pattern = r'([a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_\.]+)'
            potential_ids = re.findall(model_pattern, text)
            
            # Filter likely model IDs
            providers = ['openai', 'anthropic', 'google', 'meta-llama', 'mistralai', 'qwen']
            
            for model_id in set(potential_ids):
                provider = model_id.split('/')[0].lower()
                if provider in providers:
                    model_info = {
                        'id': model_id,
                        'name': model_id.split('/')[-1].replace('-', ' ').title(),
                        'provider': provider,
                        'model_url': f"https://openrouter.ai/models/{model_id.replace('/', '--')}",
                        'provider_url': f"https://openrouter.ai/providers/{provider}"
                    }
                    models.append(model_info)
                    
                    if len(models) >= 20:  # Limit to prevent too many
                        break
            
        except Exception as e:
            self.failures.append({
                'method': 'pattern_extraction',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return models

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

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """Format API data to consistent structure."""
        formatted = []
        
        for model in api_models:
            provider = model.get('id', '').split('/')[0] if '/' in model.get('id', '') else ''
            
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': provider,
                'provider_url': f"https://openrouter.ai/providers/{provider}" if provider else '',
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt'), "input"),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion'), "output"),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image'), "image"),
            }
            formatted.append(formatted_model)
        
        return formatted

    def validate_models(self, models: List[Dict]) -> List[Dict]:
        """Validate and clean model data."""
        valid_models = []
        
        for model in models:
            # Check essential fields
            if not model.get('name') and not model.get('id'):
                self.stats['validation_failures'] += 1
                self.failures.append({
                    'method': 'validation',
                    'model': str(model)[:100],
                    'error': 'Missing name and id',
                    'timestamp': datetime.now().isoformat()
                })
                continue
            
            # Clean and generate missing fields
            if model.get('id') and not model.get('model_url'):
                model['model_url'] = f"https://openrouter.ai/models/{model['id'].replace('/', '--')}"
            
            if model.get('provider') and not model.get('provider_url'):
                model['provider_url'] = f"https://openrouter.ai/providers/{model['provider'].lower()}"
            
            # Ensure all required fields exist
            required_fields = ['id', 'name', 'provider', 'model_url', 'provider_url', 
                             'description', 'context_window', 'input_pricing', 
                             'output_pricing', 'image_pricing']
            
            for field in required_fields:
                if field not in model:
                    model[field] = ''
            
            valid_models.append(model)
        
        return valid_models

    def save_results(self, models: List[Dict], method: str):
        """Save results to files."""
        if not models:
            print("⚠️  No models to save")
            return
        
        # Save CSV
        csv_filename = f"openrouter_models_{method}.csv"
        try:
            df = pd.DataFrame(models)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"✅ Saved {len(models)} models to {csv_filename}")
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
                    'parser_version': '11.0'
                },
                'models': models
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved {len(models)} models to {json_filename}")
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

    def save_failures(self):
        """Save failure analysis."""
        if not self.failures:
            return
        
        failure_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_failures': len(self.failures)
            },
            'statistics': self.stats,
            'failures': self.failures
        }
        
        try:
            with open('parsing_failures.json', 'w', encoding='utf-8') as f:
                json.dump(failure_data, f, indent=2, ensure_ascii=False)
            print(f"📋 Saved failure analysis ({len(self.failures)} failures)")
        except Exception as e:
            print(f"❌ Error saving failures: {e}")

    def display_summary(self, models: List[Dict]):
        """Display parsing summary."""
        if not models:
            print("❌ No models found")
            return
        
        print(f"\n📊 Parsing Summary:")
        print(f"✅ Total models: {len(models)}")
        
        # Provider stats
        providers = set(m.get('provider', 'Unknown') for m in models if m.get('provider'))
        print(f"🏢 Providers: {len(providers)}")
        
        # Data completeness
        with_pricing = len([m for m in models if m.get('input_pricing')])
        with_description = len([m for m in models if m.get('description')])
        free_models = len([m for m in models if m.get('input_pricing') == 'Free'])
        
        print(f"💰 With pricing: {with_pricing}/{len(models)} ({with_pricing/len(models)*100:.1f}%)")
        print(f"📝 With description: {with_description}/{len(models)} ({with_description/len(models)*100:.1f}%)")
        print(f"🆓 Free models: {free_models}")
        
        # Top providers
        if providers:
            from collections import Counter
            provider_counts = Counter(m.get('provider', 'Unknown') for m in models)
            print(f"\n🏆 Top 5 Providers:")
            for provider, count in provider_counts.most_common(5):
                print(f"   {provider}: {count} models")

    def run(self, method='both'):
        """Main execution method."""
        print("🚀 OpenRouter Model Parser v11 (Clean)")
        print("=" * 50)
        
        api_models = []
        web_models = []
        
        if method in ['api', 'both']:
            api_models = self.fetch_models_via_api()
            if api_models:
                api_models = self.format_api_data(api_models)
        
        if method in ['web', 'both']:
            web_models = self.parse_web_interface()
        
        # Choose best result
        if method == 'api' or (api_models and not web_models):
            models = api_models
            used_method = 'api'
        elif method == 'web' or (web_models and not api_models):
            models = web_models
            used_method = 'web_scraping'
        elif web_models:  # Prefer web scraping if both available
            models = web_models
            used_method = 'web_scraping'
        elif api_models:
            models = api_models
            used_method = 'api'
        else:
            print("❌ No models found with any method")
            self.save_failures()
            return []
        
        print(f"\n🎯 Using {used_method} results")
        
        # Validate and save
        models = self.validate_models(models)
        self.display_summary(models)
        self.save_results(models, used_method)
        self.save_failures()
        
        return models


def main():
    """Main function."""
    parser = OpenRouterParser()
    
    print("Choose parsing method:")
    print("1. API only (fast, ~320 models)")
    print("2. Web scraping only (comprehensive, ~477 models)")  
    print("3. Both (recommended)")
    
    choice = input("Enter choice (1-3) or press Enter for default (3): ").strip()
    
    if choice == "1":
        method = 'api'
    elif choice == "2":
        method = 'web'
    else:
        method = 'both'
    
    models = parser.run(method)
    
    print(f"\n🎉 Complete! Found {len(models)} models")
    
    if models:
        print("\n📁 Files created:")
        print("- CSV and JSON files with model data")
        print("- parsing_failures.json (failure analysis)")
        print("- openrouter_page.html (web page for debugging)")
        
        print(f"\n💡 Next steps:")
        print("1. Review the CSV/JSON files")
        print("2. Use this data in your Streamlit app")
        print("3. Check parsing_failures.json for improvements")
    
    return models


if __name__ == "__main__":
    main()

            ]
            
            all_links = soup.find_all('a', href=True)
            model_links = []
            
            for pattern in link_patterns:
                links = [link for link in all_links if re.search(pattern, link.get('href', ''))]
                model_links.extend(links)
                if links:
                    print(f"   Found {len(links)} links matching pattern: {pattern}")
            
            # Remove duplicates
            seen_hrefs = set()
            unique_links = []
            for link in model_links:
                href = link.get('href', '')
                if href not in seen_hrefs:
                    seen_hrefs.add(href)
                    unique_links.append(link)
            
            print(f"🔗 Found {len(unique_links)} unique model links")
            
            if unique_links:
                models = self.extract_from_links(soup, unique_links)
            
            # Strategy 2: Look for JSON data in script tags
            if not models:
                print("🔍 Strategy 2: Looking for JSON data...")
                models = self.extract_from_json(soup)
            
            # Strategy 3: Look for data in specific elements
            if not models:
                print("🔍 Strategy 3: Looking for data elements...")
                models = self.extract_from_elements(soup)
            
            # Strategy 4: Text pattern extraction as last resort
            if not models:
                print("🔍 Strategy 4: Pattern extraction...")
                models = self.extract_from_patterns(soup)
            
            if models:
                self.stats['web_success'] += 1
                print(f"✅ Web scraping successful: {len(models)} models found")
            else:
                print("⚠️  Web scraping found no models")
                print("💡 The page might be JavaScript-rendered. Try API method or check openrouter_page.html")
                
            return models
            
        except Exception as e:
            error_info = {
                'method': 'web_scraping',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.failures.append(error_info)
            print(f"❌ Web scraping failed: {e}")
            return []

    def extract_from_elements(self, soup) -> List[Dict]:
        """Extract models from specific HTML elements."""
        models = []
        
        try:
            # Look for common patterns in model display
            potential_containers = []
            
            # Look for divs that might contain model info
            divs_with_text = soup.find_all('div', string=re.compile(r'(gpt|claude|gemini|llama|mistral)', re.IGNORECASE))
            potential_containers.extend(divs_with_text)
            
            # Look for elements with model-like IDs or classes
            model_elements = soup.find_all(['div', 'article', 'section'], 
                                         class_=re.compile(r'(model|card|item)', re.IGNORECASE))
            potential_containers.extend(model_elements)
            
            # Look for elements containing pricing info
            pricing_elements = soup.find_all(string=re.compile(r'\$\d+\.?\d*/[MK]'))
            for elem in pricing_elements:
                if elem.parent:
                    potential_containers.append(elem.parent)
            
            print(f"   Found {len(potential_containers)} potential containers")
            
            # Extract data from containers
            for container in potential_containers[:50]:  # Limit to prevent too many
                text = container.get_text()
                
                # Look for model-like names in the text
                model_patterns = [
                    r'(gpt-?[0-9.]+[a-z]*)',
                    r'(claude-?[0-9.]+[a-z]*)', 
                    r'(gemini-?[a-z0-9.]*)',
                    r'(llama-?[0-9.]+[a-z]*)',
                    r'(mistral-?[0-9.]+[a-z]*)'
                ]
                
                for pattern in model_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        model_info = {
                            'name': match.title(),
                            'id': f"unknown/{match.lower()}",
                            'description': text[:200] if len(text) > 50 else '',
                            'provider': 'unknown',
                            'model_url': f"https://openrouter.ai/models/unknown--{match.lower()}",
                            'provider_url': 'https://openrouter.ai/providers/unknown'
                        }
                        
                        # Try to extract more details
                        self.extract_details_from_container(container, model_info)
                        models.append(model_info)
                        
                        if len(models) >= 20:  # Limit to prevent too many duplicates
                            break
                    
                    if len(models) >= 20:
                        break
                
                if len(models) >= 20:
                    break
            
        except Exception as e:
            self.failures.append({
                'method': 'element_extraction',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return models

    def extract_from_links(self, soup, model_links) -> List[Dict]:
        """Extract models from HTML links."""
        models = []
        
        for link in model_links[:50]:  # Limit to prevent too many attempts
            try:
                # Basic info from link
                model_info = {
                    'name': link.get_text(strip=True),
                    'model_url': urljoin(self.base_url, link['href']),
                    'id': link['href'].replace('/models/', '').replace('--', '/')
                }
                
                # Find container with more info
                container = link.parent
                for _ in range(5):  # Look up to 5 levels up
                    if container and container.parent:
                        container = container.parent
                        text = container.get_text()
                        if 'tokens' in text and ('$' in text or 'free' in text.lower()):
                            break
                
                if container:
                    self.extract_details_from_container(container, model_info)
                
                if model_info.get('name'):
                    models.append(model_info)
                    
            except Exception as e:
                self.failures.append({
                    'method': 'link_extraction',
                    'link': str(link)[:100],
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                continue
        
        return models

    def extract_details_from_container(self, container, model_info):
        """Extract detailed info from HTML container."""
        text = container.get_text()
        
        # Extract provider
        provider_match = re.search(r'by\s+([^|$\n]+)', text, re.IGNORECASE)
        if provider_match:
            provider = provider_match.group(1).strip()
            model_info['provider'] = provider
            model_info['provider_url'] = f"https://openrouter.ai/providers/{provider.lower().replace(' ', '-')}"
        
        # Extract context window
        context_match = re.search(r'(\d+(?:,\d+)*)\s*[KM]?\s*(?:context|tokens)', text, re.IGNORECASE)
        if context_match:
            model_info['context_window'] = f"{context_match.group(1)} tokens"
        
        # Extract pricing
        input_match = re.search(r'\$([0-9.]+)/M\s+input', text, re.IGNORECASE)
        if input_match:
            model_info['input_pricing'] = f"${input_match.group(1)}/M tokens"
        elif 'free' in text.lower():
            model_info['input_pricing'] = 'Free'
        else:
            model_info['input_pricing'] = ''
        
        output_match = re.search(r'\$([0-9.]+)/M\s+output', text, re.IGNORECASE)
        if output_match:
            model_info['output_pricing'] = f"${output_match.group(1)}/M tokens"
        else:
            model_info['output_pricing'] = ''
        
        image_match = re.search(r'\$([0-9.]+)/K.*img', text, re.IGNORECASE)
        if image_match:
            model_info['image_pricing'] = f"${image_match.group(1)}/K images"
        else:
            model_info['image_pricing'] = ''
        
        # Extract description
        desc_elements = container.find_all(['p', 'div'])
        for elem in desc_elements:
            elem_text = elem.get_text(strip=True)
            if (len(elem_text) > 50 and 
                'tokens' not in elem_text.lower() and 
                '$' not in elem_text):
                model_info['description'] = elem_text[:300]
                break

    def extract_from_json(self, soup) -> List[Dict]:
        """Extract models from JSON script tags."""
        models = []
        
        # Look for JSON scripts
        script_tags = soup.find_all('script', type='application/json')
        script_tags.extend(soup.find_all('script', id='__NEXT_DATA__'))
        
        for script in script_tags:
            try:
                if script.string:
                    data = json.loads(script.string)
                    found_models = self.parse_json_data(data)
                    if found_models:
                        models.extend(found_models)
                        break
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return models

    def parse_json_data(self, data) -> List[Dict]:
        """Parse models from JSON data structure."""
        models = []
        
        # Try different possible locations
        possible_paths = [
            data.get('models', []),
            data.get('data', []),
            data.get('props', {}).get('pageProps', {}).get('models', []),
            data.get('props', {}).get('pageProps', {}).get('data', [])
        ]
        
        for model_list in possible_paths:
            if isinstance(model_list, list) and model_list:
                for item in model_list:
                    if isinstance(item, dict):
                        model_info = self.format_json_model(item)
                        if model_info:
                            models.append(model_info)
                break
        
        return models

    def format_json_model(self, item) -> Optional[Dict]:
        """Format model from JSON item."""
        try:
            model_info = {
                'id': item.get('id', ''),
                'name': item.get('name', ''),
                'description': item.get('description', ''),
                'provider': item.get('id', '').split('/')[0] if '/' in item.get('id', '') else '',
                'model_url': f"https://openrouter.ai/models/{item.get('id', '').replace('/', '--')}"
            }
            
            # Context window
            context = item.get('context_length', 0)
            if context:
                model_info['context_window'] = f"{context:,} tokens"
            
            # Pricing
            pricing = item.get('pricing', {})
            if pricing:
                model_info['input_pricing'] = self.format_pricing(pricing.get('prompt'), 'input')
                model_info['output_pricing'] = self.format_pricing(pricing.get('completion'), 'output')
                model_info['image_pricing'] = self.format_pricing(pricing.get('image'), 'image')
            
            # Provider URL
            if model_info['provider']:
                model_info['provider_url'] = f"https://openrouter.ai/providers/{model_info['provider']}"
            
            return model_info if model_info.get('name') else None
            
        except Exception as e:
            self.failures.append({
                'method': 'json_parsing',
                'item': str(item)[:100],
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
            return None

    def extract_from_patterns(self, soup) -> List[Dict]:
        """Extract models using text patterns."""
        models = []
        
        try:
            text = soup.get_text()
            
            # Find model ID patterns
            model_pattern = r'([a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_\.]+)'
            potential_ids = re.findall(model_pattern, text)
            
            # Filter likely model IDs
            providers = ['openai', 'anthropic', 'google', 'meta-llama', 'mistralai', 'qwen']
            
            for model_id in set(potential_ids):
                provider = model_id.split('/')[0].lower()
                if provider in providers:
                    model_info = {
                        'id': model_id,
                        'name': model_id.split('/')[-1].replace('-', ' ').title(),
                        'provider': provider,
                        'model_url': f"https://openrouter.ai/models/{model_id.replace('/', '--')}",
                        'provider_url': f"https://openrouter.ai/providers/{provider}"
                    }
                    models.append(model_info)
                    
                    if len(models) >= 20:  # Limit to prevent too many
                        break
            
        except Exception as e:
            self.failures.append({
                'method': 'pattern_extraction',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
        return models

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

    def format_api_data(self, api_models: List[Dict]) -> List[Dict]:
        """Format API data to consistent structure."""
        formatted = []
        
        for model in api_models:
            provider = model.get('id', '').split('/')[0] if '/' in model.get('id', '') else ''
            
            formatted_model = {
                'id': model.get('id', ''),
                'name': model.get('name', ''),
                'model_url': f"https://openrouter.ai/models/{model.get('id', '').replace('/', '--')}",
                'description': model.get('description', ''),
                'context_window': f"{model.get('context_length', 0):,} tokens" if model.get('context_length') else '',
                'provider': provider,
                'provider_url': f"https://openrouter.ai/providers/{provider}" if provider else '',
                'input_pricing': self.format_pricing(model.get('pricing', {}).get('prompt'), "input"),
                'output_pricing': self.format_pricing(model.get('pricing', {}).get('completion'), "output"),
                'image_pricing': self.format_pricing(model.get('pricing', {}).get('image'), "image"),
            }
            formatted.append(formatted_model)
        
        return formatted

    def validate_models(self, models: List[Dict]) -> List[Dict]:
        """Validate and clean model data."""
        valid_models = []
        
        for model in models:
            # Check essential fields
            if not model.get('name') and not model.get('id'):
                self.stats['validation_failures'] += 1
                self.failures.append({
                    'method': 'validation',
                    'model': str(model)[:100],
                    'error': 'Missing name and id',
                    'timestamp': datetime.now().isoformat()
                })
                continue
            
            # Clean and generate missing fields
            if model.get('id') and not model.get('model_url'):
                model['model_url'] = f"https://openrouter.ai/models/{model['id'].replace('/', '--')}"
            
            if model.get('provider') and not model.get('provider_url'):
                model['provider_url'] = f"https://openrouter.ai/providers/{model['provider'].lower()}"
            
            # Ensure all required fields exist
            required_fields = ['id', 'name', 'provider', 'model_url', 'provider_url', 
                             'description', 'context_window', 'input_pricing', 
                             'output_pricing', 'image_pricing']
            
            for field in required_fields:
                if field not in model:
                    model[field] = ''
            
            valid_models.append(model)
        
        return valid_models

    def save_results(self, models: List[Dict], method: str):
        """Save results to files."""
        if not models:
            print("⚠️  No models to save")
            return
        
        # Save CSV
        csv_filename = f"openrouter_models_{method}.csv"
        try:
            df = pd.DataFrame(models)
            df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"✅ Saved {len(models)} models to {csv_filename}")
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
                    'parser_version': '11.0'
                },
                'models': models
            }
            
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved {len(models)} models to {json_filename}")
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

    def save_failures(self):
        """Save failure analysis."""
        if not self.failures:
            return
        
        failure_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_failures': len(self.failures)
            },
            'statistics': self.stats,
            'failures': self.failures
        }
        
        try:
            with open('parsing_failures.json', 'w', encoding='utf-8') as f:
                json.dump(failure_data, f, indent=2, ensure_ascii=False)
            print(f"📋 Saved failure analysis ({len(self.failures)} failures)")
        except Exception as e:
            print(f"❌ Error saving failures: {e}")

    def display_summary(self, models: List[Dict]):
        """Display parsing summary."""
        if not models:
            print("❌ No models found")
            return
        
        print(f"\n📊 Parsing Summary:")
        print(f"✅ Total models: {len(models)}")
        
        # Provider stats
        providers = set(m.get('provider', 'Unknown') for m in models if m.get('provider'))
        print(f"🏢 Providers: {len(providers)}")
        
        # Data completeness
        with_pricing = len([m for m in models if m.get('input_pricing')])
        with_description = len([m for m in models if m.get('description')])
        free_models = len([m for m in models if m.get('input_pricing') == 'Free'])
        
        print(f"💰 With pricing: {with_pricing}/{len(models)} ({with_pricing/len(models)*100:.1f}%)")
        print(f"📝 With description: {with_description}/{len(models)} ({with_description/len(models)*100:.1f}%)")
        print(f"🆓 Free models: {free_models}")
        
        # Top providers
        if providers:
            from collections import Counter
            provider_counts = Counter(m.get('provider', 'Unknown') for m in models)
            print(f"\n🏆 Top 5 Providers:")
            for provider, count in provider_counts.most_common(5):
                print(f"   {provider}: {count} models")

    def run(self, method='both'):
        """Main execution method."""
        print("🚀 OpenRouter Model Parser v11 (Clean)")
        print("=" * 50)
        
        api_models = []
        web_models = []
        
        if method in ['api', 'both']:
            api_models = self.fetch_models_via_api()
            if api_models:
                api_models = self.format_api_data(api_models)
        
        if method in ['web', 'both']:
            web_models = self.parse_web_interface()
        
        # Choose best result
        if method == 'api' or (api_models and not web_models):
            models = api_models
            used_method = 'api'
        elif method == 'web' or (web_models and not api_models):
            models = web_models
            used_method = 'web_scraping'
        elif web_models:  # Prefer web scraping if both available
            models = web_models
            used_method = 'web_scraping'
        elif api_models:
            models = api_models
            used_method = 'api'
        else:
            print("❌ No models found with any method")
            self.save_failures()
            return []
        
        print(f"\n🎯 Using {used_method} results")
        
        # Validate and save
        models = self.validate_models(models)
        self.display_summary(models)
        self.save_results(models, used_method)
        self.save_failures()
        
        return models


def main():
    """Main function."""
    parser = OpenRouterParser()
    
    print("Choose parsing method:")
    print("1. API only (fast, ~320 models)")
    print("2. Web scraping only (comprehensive, ~477 models)")  
    print("3. Both (recommended)")
    
    choice = input("Enter choice (1-3) or press Enter for default (3): ").strip()
    
    if choice == "1":
        method = 'api'
    elif choice == "2":
        method = 'web'
    else:
        method = 'both'
    
    models = parser.run(method)
    
    print(f"\n🎉 Complete! Found {len(models)} models")
    
    if models:
        print("\n📁 Files created:")
        print("- CSV and JSON files with model data")
        print("- parsing_failures.json (failure analysis)")
        print("- openrouter_page.html (web page for debugging)")
        
        print(f"\n💡 Next steps:")
        print("1. Review the CSV/JSON files")
        print("2. Use this data in your Streamlit app")
        print("3. Check parsing_failures.json for improvements")
    
    return models


if __name__ == "__main__":
    main()
