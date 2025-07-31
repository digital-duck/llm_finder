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
        
        # Initialize failure tracking
        self.parsing_failures = {
            'failed_links': [],
            'failed_json_items': [],
            'failed_pattern_matches': [],
            'validation_failures': [],
            'missing_data_issues': []
        }
        self.parsing_stats = {
            'links_attempted': 0,
            'links_successful': 0,
            'json_items_attempted': 0,
            'json_items_successful': 0,
            'patterns_attempted': 0,
            'patterns_successful': 0
        }

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
        """Save model data to CSV file with enhanced error handling."""
        if not models:
            print("⚠️  No models to save.")
            return
        
        try:
            # Ensure all models have the same keys for consistent CSV structure
            all_keys = set()
            for model in models:
                all_keys.update(model.keys())
            
            # Fill missing keys with empty strings
            for model in models:
                for key in all_keys:
                    if key not in model:
                        model[key] = ''
            
            df = pd.DataFrame(models)
            
            # Reorder columns for better readability
            preferred_order = [
                'id', 'name', 'provider', 'provider_url', 'model_url', 
                'description', 'context_window', 'input_pricing', 
                'output_pricing', 'image_pricing', 'created', 'updated', 
                'owned_by', 'architecture', 'top_provider', 'per_request_limits'
            ]
            
            # Reorder columns, putting preferred ones first
            existing_cols = [col for col in preferred_order if col in df.columns]
            other_cols = [col for col in df.columns if col not in preferred_order]
            df = df[existing_cols + other_cols]
            
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Saved {len(models)} models to {filename}")
            
            # Validate saved file
            try:
                test_df = pd.read_csv(filename)
                if len(test_df) != len(models):
                    print(f"⚠️  Warning: Saved file has {len(test_df)} rows, expected {len(models)}")
                else:
                    print(f"✅ CSV file validation passed")
            except Exception as e:
                print(f"⚠️  Warning: Could not validate saved CSV: {e}")
                
        except Exception as e:
            print(f"❌ Error saving CSV: {e}")

    def save_to_json(self, models: List[Dict], filename: str = "openrouter_models.json"):
        """Save model data to JSON file with enhanced error handling."""
        if not models:
            print("⚠️  No models to save.")
            return
        
        try:
            # Create enhanced JSON structure with metadata
            output_data = {
                'metadata': {
                    'total_models': len(models),
                    'generated_at': datetime.now().isoformat(),
                    'parser_version': '10.0',
                    'data_source': 'OpenRouter.ai',
                    'providers': list(set(m.get('provider', 'Unknown') for m in models if m.get('provider')))
                },
                'models': models
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Saved {len(models)} models to {filename}")
            
            # Validate saved file
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    test_data = json.load(f)
                if len(test_data.get('models', [])) != len(models):
                    print(f"⚠️  Warning: Saved file has {len(test_data.get('models', []))} models, expected {len(models)}")
                else:
                    print(f"✅ JSON file validation passed")
            except Exception as e:
                print(f"⚠️  Warning: Could not validate saved JSON: {e}")
                
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

    def save_failure_analysis(self, filename: str = "parsing_failures.json"):
        """Save detailed failure analysis for debugging and improvement."""
        try:
            # Calculate statistics
            total_attempts = sum([
                self.parsing_stats['links_attempted'],
                self.parsing_stats['json_items_attempted'],
                self.parsing_stats['patterns_attempted']
            ])
            
            total_successes = sum([
                self.parsing_stats['links_successful'],
                self.parsing_stats['json_items_successful'],
                self.parsing_stats['patterns_successful']
            ])
            
            success_rate = (total_successes / total_attempts * 100) if total_attempts > 0 else 0
            
            failure_report = {
                'metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'parser_version': '10.0',
                    'total_parsing_attempts': total_attempts,
                    'total_successes': total_successes,
                    'overall_success_rate': f"{success_rate:.1f}%"
                },
                'parsing_statistics': self.parsing_stats,
                'failure_breakdown': {
                    'failed_links': len(self.parsing_failures['failed_links']),
                    'failed_json_items': len(self.parsing_failures['failed_json_items']),
                    'failed_patterns': len(self.parsing_failures['failed_pattern_matches']),
                    'validation_failures': len(self.parsing_failures['validation_failures']),
                    'incomplete_data': len(self.parsing_failures['missing_data_issues'])
                },
                'detailed_failures': self.parsing_failures,
                'improvement_suggestions': self.generate_improvement_suggestions()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(failure_report, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"📋 Failure analysis saved to {filename}")
            
            # Print key insights
            if total_attempts > 0:
                print(f"📊 Parsing Success Rate: {success_rate:.1f}% ({total_successes}/{total_attempts})")
                
                if self.parsing_failures['failed_links']:
                    print(f"🔗 {len(self.parsing_failures['failed_links'])} link parsing failures")
                if self.parsing_failures['validation_failures']:
                    print(f"❌ {len(self.parsing_failures['validation_failures'])} validation failures")
                if self.parsing_failures['missing_data_issues']:
                    print(f"📉 {len(self.parsing_failures['missing_data_issues'])} models with incomplete data")
            
        except Exception as e:
            print(f"❌ Error saving failure analysis: {e}")

    def generate_improvement_suggestions(self) -> List[str]:
        """Generate suggestions for improving the parser based on failure patterns."""
        suggestions = []
        
        # Analyze failure patterns
        if len(self.parsing_failures['failed_links']) > 5:
            suggestions.append("High number of link parsing failures - consider updating CSS selectors or HTML structure analysis")
        
        if len(self.parsing_failures['failed_json_items']) > 3:
            suggestions.append("JSON parsing issues detected - check for changes in API response structure")
        
        if len(self.parsing_failures['validation_failures']) > 10:
            suggestions.append("Many validation failures - consider relaxing required field constraints")
        
        # Analyze missing data patterns
        missing_data_issues = self.parsing_failures['missing_data_issues']
        if missing_data_issues:
            common_missing = {}
            for issue in missing_data_issues:
                for field in issue.get('missing_important', []) + issue.get('missing_nice', []):
                    common_missing[field] = common_missing.get(field, 0) + 1
            
            if common_missing:
                most_missing = max(common_missing.items(), key=lambda x: x[1])
                suggestions.append(f"Field '{most_missing[0]}' is missing in {most_missing[1]} models - improve extraction logic for this field")
        
        # Check success rates by method
        if self.parsing_stats['links_attempted'] > 0:
            link_success_rate = self.parsing_stats['links_successful'] / self.parsing_stats['links_attempted']
            if link_success_rate < 0.7:
                suggestions.append("Low link parsing success rate - review HTML structure and container detection logic")
        
        if self.parsing_stats['json_items_attempted'] > 0:
            json_success_rate = self.parsing_stats['json_items_successful'] / self.parsing_stats['json_items_attempted']
            if json_success_rate < 0.8:
                suggestions.append("Low JSON parsing success rate - check for API response format changes")
        
        if not suggestions:
            suggestions.append("Parser performance looks good! Consider adding more validation rules for even better data quality.")
        
        return suggestions
        
        test_results = {
            'api_connection': False,
            'web_scraping': False,
            'data_validation': False,
            'file_operations': False
        }
        
        # Test 1: API Connection
        try:
            print("Test 1: API Connection...")
            response = self.session.get(self.api_url, timeout=10)
            if response.status_code == 200:
                test_results['api_connection'] = True
                print("✅ API connection successful")
            else:
                print(f"❌ API returned status {response.status_code}")
        except Exception as e:
            print(f"❌ API connection failed: {e}")
        
        # Test 2: Web Scraping Access
        try:
            print("Test 2: Web Scraping Access...")
            response = self.session.get(self.models_url, timeout=10)
            if response.status_code == 200 and len(response.text) > 1000:
                test_results['web_scraping'] = True
                print("✅ Web scraping access successful")
            else:
                print(f"❌ Web scraping failed (status: {response.status_code}, content length: {len(response.text)})")
        except Exception as e:
            print(f"❌ Web scraping access failed: {e}")
        
        # Test 3: Data Validation
        try:
            print("Test 3: Data Validation...")
            test_model = {
                'id': 'test/model',
                'name': 'Test Model',
                'provider': 'test-provider',
                'input_pricing': '$1.00/M tokens'
            }
            validated = self.validate_and_clean_data([test_model])
            if validated and len(validated) == 1:
                test_results['data_validation'] = True
                print("✅ Data validation working")
            else:
                print("❌ Data validation failed")
        except Exception as e:
            print(f"❌ Data validation error: {e}")
        
        # Test 4: File Operations
        try:
            print("Test 4: File Operations...")
            test_data = [{'test': 'data'}]
            self.save_to_json(test_data, 'test_output.json')
            self.save_to_csv(pd.DataFrame(test_data), 'test_output.csv')
            
            # Check if files were created
            import os
            json_exists = os.path.exists('test_output.json')
            csv_exists = os.path.exists('test_output.csv')
            
            if json_exists and csv_exists:
                test_results['file_operations'] = True
                print("✅ File operations working")
                # Clean up test files
                os.remove('test_output.json')
                os.remove('test_output.csv')
            else:
                print("❌ File operations failed")
        except Exception as e:
            print(f"❌ File operations error: {e}")
        
        # Summary
        passed_tests = sum(test_results.values())
        total_tests = len(test_results)
        
        print(f"\n📊 Test Results: {passed_tests}/{total_tests} passed")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Parser is ready to use.")
        elif passed_tests >= 2:
            print("⚠️  Some tests failed, but basic functionality should work.")
        else:
            print("❌ Multiple test failures. Please check your environment and network connection.")
        
        return test_results

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
        Main execution method with enhanced error handling and validation.
        
        Args:
            use_api: If True, use API method; if False, use web scraping
            save_csv: Save results to CSV
            save_json: Save results to JSON
            compare_methods: If True, run both methods and compare results
        """
        print("Starting OpenRouter model parsing...")
        print(f"Target: {self.models_url}")
        print(f"API endpoint: {self.api_url}")
        
        api_models = []
        web_models = []
        
        if use_api or compare_methods:
            print("\n" + "="*50)
            print("PHASE 1: API Method")
            print("="*50)
            try:
                api_models = self.fetch_models_via_api()
                if api_models:
                    api_models = self.format_api_data(api_models)
                    print(f"✅ API method successful: {len(api_models)} models")
                else:
                    print("❌ API method returned no models")
            except Exception as e:
                print(f"❌ API method failed: {e}")
        
        if not use_api or compare_methods:
            print("\n" + "="*50)
            print("PHASE 2: Web Scraping Method")
            print("="*50)
            try:
                web_models = self.parse_web_interface()
                print(f"✅ Web scraping completed: {len(web_models)} models found")
            except Exception as e:
                print(f"❌ Web scraping failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Choose primary dataset
        if use_api and api_models:
            models = api_models
            method_used = "api"
        elif web_models:
            models = web_models
            method_used = "web_scraping"
        elif api_models:
            models = api_models
            method_used = "api_fallback"
        else:
            print("❌ No models found with any method!")
            return []
        
        print(f"\n🎯 Using {method_used} results as primary dataset ({len(models)} models)")
        
        # Validate and clean data
        print("\n" + "="*50)
        print("PHASE 3: Data Validation & Cleaning")
        print("="*50)
        
        models = self.validate_and_clean_data(models)
        print(f"✅ Data validation complete: {len(models)} valid models")
        
        # Compare methods if requested
        if compare_methods and api_models and web_models:
            print("\n" + "="*50)
            print("PHASE 4: Method Comparison")
            print("="*50)
            self.compare_methods(api_models, web_models)
        
        if not models:
            print("❌ No valid models found after processing!")
            return []
        
        # Display summary
        self.display_summary(models)
        
        # Save results
        if save_csv:
            filename = f"openrouter_models_{method_used}.csv"
            self.save_to_csv(models, filename)
        
        if save_json:
            filename = f"openrouter_models_{method_used}.json"
            self.save_to_json(models, filename)
        
        # Save failure analysis for continuous improvement
        print("\n" + "="*50)
        print("PHASE 5: Failure Analysis & Logging")
        print("="*50)
        
        self.save_failure_analysis()
        
        return models

    def validate_and_clean_data(self, models: List[Dict]) -> List[Dict]:
        """Validate and clean model data with detailed failure logging."""
        valid_models = []
        
        for i, model in enumerate(models):
            issues = []
            original_model = model.copy()  # Keep original for failure analysis
            
            # Required fields validation
            if not model.get('name'):
                issues.append("Missing name")
            if not model.get('id') and not model.get('name'):
                issues.append("Missing both id and name")
            
            # Clean and validate pricing
            for pricing_field in ['input_pricing', 'output_pricing', 'image_pricing']:
                if pricing_field in model:
                    original_value = model[pricing_field]
                    cleaned_price = self.clean_pricing_field(model[pricing_field])
                    model[pricing_field] = cleaned_price
                    
                    # Log if cleaning significantly changed the value
                    if original_value != cleaned_price and original_value not in ['', None]:
                        issues.append(f"Pricing field '{pricing_field}' cleaned: '{original_value}' -> '{cleaned_price}'")
            
            # Clean context window
            if 'context_window' in model:
                original_context = model['context_window']
                cleaned_context = self.clean_context_window(model['context_window'])
                model['context_window'] = cleaned_context
                
                if original_context != cleaned_context and original_context not in ['', None]:
                    issues.append(f"Context window cleaned: '{original_context}' -> '{cleaned_context}'")
            
            # Generate missing fields
            if model.get('id') and not model.get('model_url'):
                model['model_url'] = f"https://openrouter.ai/models/{model['id'].replace('/', '--')}"
                issues.append("Generated model_url from id")
            
            if model.get('provider') and not model.get('provider_url'):
                provider_slug = model['provider'].lower().replace(' ', '-').replace('.', '')
                model['provider_url'] = f"https://openrouter.ai/providers/{provider_slug}"
                issues.append("Generated provider_url from provider name")
            
            # Check data completeness
            essential_fields = ['name', 'id', 'provider']
            important_fields = ['description', 'context_window', 'input_pricing']
            nice_to_have = ['output_pricing', 'model_url', 'provider_url']
            
            missing_essential = [f for f in essential_fields if not model.get(f)]
            missing_important = [f for f in important_fields if not model.get(f)]
            missing_nice = [f for f in nice_to_have if not model.get(f)]
            
            # Calculate completeness score
            total_fields = len(essential_fields) + len(important_fields) + len(nice_to_have)
            missing_total = len(missing_essential) + len(missing_important) + len(missing_nice)
            completeness_score = (total_fields - missing_total) / total_fields
            
            # Decide whether to keep the model
            if missing_essential:
                # Critical validation failure
                self.parsing_failures['validation_failures'].append({
                    'model_index': i,
                    'original_model': original_model,
                    'processed_model': model.copy(),
                    'missing_essential': missing_essential,
                    'missing_important': missing_important,
                    'missing_nice': missing_nice,
                    'completeness_score': completeness_score,
                    'issues': issues,
                    'failure_reason': f"Missing essential fields: {', '.join(missing_essential)}"
                })
                continue
            
            # Log models with low completeness for improvement
            if completeness_score < 0.6:  # Less than 60% complete
                self.parsing_failures['missing_data_issues'].append({
                    'model_index': i,
                    'model_id': model.get('id', 'Unknown'),
                    'model_name': model.get('name', 'Unknown'),
                    'original_model': original_model,
                    'processed_model': model.copy(),
                    'missing_important': missing_important,
                    'missing_nice': missing_nice,
                    'completeness_score': completeness_score,
                    'issues': issues,
                    'improvement_opportunity': f"Low completeness ({completeness_score:.1%})"
                })
            
            valid_models.append(model)
        
        # Print summary of validation issues
        total_failures = len(self.parsing_failures['validation_failures'])
        total_incomplete = len(self.parsing_failures['missing_data_issues'])
        
        if total_failures > 0:
            print(f"⚠️  {total_failures} models failed validation (missing essential fields)")
        if total_incomplete > 0:
            print(f"📊 {total_incomplete} models have incomplete data (improvement opportunities)")
        
        return valid_models

    def clean_pricing_field(self, price: str) -> str:
        """Clean and standardize pricing field."""
        if not price or price in ['null', 'None', 'undefined']:
            return ''
        
        # Handle boolean or numeric values
        if isinstance(price, (bool, int, float)):
            if price == 0 or price is False:
                return 'Free'
            return str(price)
        
        # Clean string values
        price = str(price).strip()
        if price.lower() in ['free', '$0', '0']:
            return 'Free'
        
        return price

    def clean_context_window(self, context: str) -> str:
        """Clean and standardize context window field."""
        if not context:
            return ''
        
        context = str(context).strip()
        
        # Extract numeric value and standardize format
        match = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?)', context)
        if match:
            num_str = match.group(1).replace(',', '')
            try:
                num = float(num_str)
                if num >= 1000000:
                    return f"{num/1000000:.1f}M tokens"
                elif num >= 1000:
                    return f"{num/1000:.0f}K tokens"
                else:
                    return f"{num:.0f} tokens"
            except ValueError:
                pass
        
        return context

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
    """Main function to run the parser with enhanced options."""
    parser = OpenRouterParser()
    
    print("🔍 OpenRouter Model Parser v10 - Enhanced & Robust")
    print("=" * 60)
    
    print("\nChoose parsing method:")
    print("1. 🚀 API only (fastest, 320+ models)")
    print("2. 🕷️  Web scraping only (comprehensive, 477+ models)")
    print("3. 🔄 Both methods with comparison (recommended)")
    print("4. 🧪 Debug mode (saves intermediate data)")
    
    choice = input("\nEnter choice (1-4) or press Enter for default (3): ").strip()
    
    if choice == "1":
        print("\n🚀 Running API-only mode...")
        models = parser.run(use_api=True, compare_methods=False)
        
    elif choice == "2":
        print("\n🕷️ Running web scraping-only mode...")
        models = parser.run(use_api=False, compare_methods=False)
        
    elif choice == "4":
        print("\n🧪 Running debug mode...")
        # Enable debug logging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        
        models = parser.run(use_api=True, compare_methods=True)
        
        # Save additional debug information
        if models:
            debug_info = {
                'total_models': len(models),
                'timestamp': datetime.now().isoformat(),
                'sample_models': models[:5],  # First 5 models as sample
                'providers': list(set(m.get('provider', 'Unknown') for m in models)),
                'parsing_method': 'debug_mode'
            }
            
            with open('debug_info.json', 'w') as f:
                json.dump(debug_info, f, indent=2, default=str)
            print("📊 Debug information saved to debug_info.json")
        
    else:  # Default to comparison mode
        print("\n🔄 Running comparison mode...")
        models = parser.run(use_api=True, compare_methods=True)
    
    # Summary and next steps
    print("\n" + "=" * 60)
    print("🎉 PARSING COMPLETE!")
    print("=" * 60)
    
    if models:
        print(f"✅ Successfully parsed {len(models)} models")
        
        # Show file outputs
        print("\n📁 Generated Files:")
        files_created = []
        
        # Check for created files
        import os
        for filename in ['openrouter_models_api.csv', 'openrouter_models_web_scraping.csv', 
                        'openrouter_models_api.json', 'openrouter_models_web_scraping.json',
                        'method_comparison.json', 'openrouter_page.html', 'debug_info.json']:
            if os.path.exists(filename):
                size = os.path.getsize(filename) / 1024  # Size in KB
                files_created.append(f"   📄 {filename} ({size:.1f} KB)")
        
        for file_info in files_created:
            print(file_info)
        
        # Data quality summary
        print(f"\n📊 Data Quality Summary:")
        providers = set(m.get('provider', 'Unknown') for m in models)
        models_with_pricing = len([m for m in models if m.get('input_pricing')])
        models_with_description = len([m for m in models if m.get('description')])
        free_models = len([m for m in models if m.get('input_pricing') == 'Free'])
        
        print(f"   🏢 Providers: {len(providers)}")
        print(f"   💰 Models with pricing: {models_with_pricing}/{len(models)} ({models_with_pricing/len(models)*100:.1f}%)")
        print(f"   📝 Models with descriptions: {models_with_description}/{len(models)} ({models_with_description/len(models)*100:.1f}%)")
        print(f"   🆓 Free models: {free_models}")
        
        # Top providers
        if providers:
            from collections import Counter
            provider_counts = Counter(m.get('provider', 'Unknown') for m in models)
            print(f"\n🏆 Top 5 Providers:")
            for provider, count in provider_counts.most_common(5):
                print(f"   {provider}: {count} models")
        
        # Next steps
        print(f"\n🚀 Next Steps:")
        print(f"   1. Review the generated CSV/JSON files")
        print(f"   2. Use this data in your enhanced Streamlit app")
        print(f"   3. Consider running both methods if you only ran one")
        print(f"   4. Check openrouter_page.html if web scraping had issues")
        
        # Integration suggestion
        print(f"\n💡 Integration Tip:")
        print(f"   Use the CSV files as data sources in your Streamlit app:")
        print(f"   - Primary: openrouter_models_web_scraping.csv (more complete)")
        print(f"   - Backup: openrouter_models_api.csv (structured data)")
        
    else:
        print("❌ No models were successfully parsed")
        print("\n🔧 Troubleshooting:")
        print("   1. Check your internet connection")
        print("   2. Verify OpenRouter.ai is accessible")
        print("   3. Try running in debug mode (option 4)")
        print("   4. Check openrouter_page.html for HTML structure changes")
    
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

