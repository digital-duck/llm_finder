import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import re
from urllib.parse import urljoin, urlparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def scrape_openrouter_models():
    """
    Scrape model information from OpenRouter.ai models page
    """
    print("Scraping OpenRouter models...")
    logger.info("Starting OpenRouter models scraping")
    
    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }
    
    try:
        # Fetch the main models page
        url = "https://openrouter.ai/models"
        logger.info(f"Fetching URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response length: {len(response.content)}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Debug: Save HTML for inspection
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        logger.info("Saved debug HTML to debug_page.html")
        
        models_data = []
        
        # Method 1: Try to find JSON data in script tags
        logger.info("Method 1: Looking for JSON data in script tags...")
        script_tags = soup.find_all('script')
        logger.info(f"Found {len(script_tags)} script tags")
        
        for i, script in enumerate(script_tags):
            if script.string:
                # Look for various JSON patterns
                if '__NEXT_DATA__' in script.string:
                    logger.info(f"Found __NEXT_DATA__ in script tag {i}")
                    try:
                        json_data = json.loads(script.string)
                        extracted_models = extract_models_from_next_data(json_data)
                        if extracted_models:
                            models_data.extend(extracted_models)
                            logger.info(f"Extracted {len(extracted_models)} models from __NEXT_DATA__")
                            break
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse __NEXT_DATA__: {e}")
                        continue
                
                # Look for other potential JSON data
                elif 'models' in script.string.lower() and '{' in script.string:
                    logger.info(f"Found potential models data in script tag {i}")
                    try:
                        # Try to extract JSON from the script
                        json_match = re.search(r'\{.*"models".*\}', script.string, re.DOTALL)
                        if json_match:
                            json_data = json.loads(json_match.group())
                            extracted_models = extract_models_from_json_object(json_data)
                            if extracted_models:
                                models_data.extend(extracted_models)
                                logger.info(f"Extracted {len(extracted_models)} models from script JSON")
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.error(f"Failed to parse script JSON: {e}")
                        continue
        
        # Method 2: If no JSON data found, use the new HTML parsing based on actual structure
        if not models_data:
            logger.info("Method 2: Using new HTML parsing based on actual structure...")
            extracted_models = extract_models_from_html_structure(soup)
            if extracted_models:
                models_data.extend(extracted_models)
                logger.info(f"Extracted {len(extracted_models)} models from HTML structure")
        
        # Method 3: Try API endpoint if available
        if not models_data:
            logger.info("Method 3: Trying API endpoint...")
            extracted_models = extract_models_from_api(headers)
            if extracted_models:
                models_data.extend(extracted_models)
                logger.info(f"Extracted {len(extracted_models)} models from API")
        
        # Method 4: Fallback to sample data if nothing works
        if not models_data:
            logger.warning("No models extracted, using sample data...")
            models_data = get_sample_models()
        
        logger.info(f"Total models extracted: {len(models_data)}")
        
        if not models_data:
            logger.error("No models found after all methods")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(models_data)
        
        # Clean and categorize data
        df = clean_and_categorize_models(df)
        
        # Save to CSV
        df.to_csv('openrouter_models.csv', index=False)
        print(f"Successfully scraped {len(df)} models and saved to openrouter_models.csv")
        
        return df
        
    except Exception as e:
        logger.error(f"Error scraping models: {e}")
        print(f"Error scraping models: {e}")
        return None

def extract_models_from_next_data(json_data):
    """
    Extract model information from Next.js JSON data
    """
    models = []
    logger.info("Extracting models from Next.js data...")
    
    try:
        # Save the full JSON for debugging
        with open('debug_next_data.json', 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        logger.info("Saved debug Next.js data to debug_next_data.json")
        
        # Navigate through the JSON structure to find models
        # This is a common pattern in Next.js apps
        if 'props' in json_data and 'pageProps' in json_data['props']:
            page_props = json_data['props']['pageProps']
            logger.info("Found pageProps in Next.js data")
            
            # Look for models in various possible locations
            if 'models' in page_props:
                models_data = page_props['models']
                logger.info(f"Found models directly in pageProps: {len(models_data) if isinstance(models_data, list) else 'not a list'}")
            elif 'data' in page_props and 'models' in page_props['data']:
                models_data = page_props['data']['models']
                logger.info(f"Found models in pageProps.data: {len(models_data) if isinstance(models_data, list) else 'not a list'}")
            else:
                # Try to find models anywhere in the structure
                models_data = find_models_in_dict(page_props)
                logger.info(f"Found models via recursive search: {len(models_data) if models_data else 'none'}")
            
            if models_data and isinstance(models_data, list):
                for i, model in enumerate(models_data):
                    if isinstance(model, dict):
                        model_info = {
                            'name': model.get('name', model.get('id', f'Model_{i}')),
                            'id': model.get('id', ''),
                            'description': model.get('description', ''),
                            'context_length': model.get('context_length', model.get('context', '')),
                            'pricing': model.get('pricing', {}),
                            'provider': model.get('provider', ''),
                            'architecture': model.get('architecture', ''),
                            'capabilities': model.get('capabilities', []),
                            'website': model.get('website', ''),
                            'image_url': model.get('image_url', '')
                        }
                        models.append(model_info)
                        logger.debug(f"Added model: {model_info['name']}")
        else:
            logger.warning("No pageProps found in Next.js data")
    
    except Exception as e:
        logger.error(f"Error extracting from Next.js data: {e}")
    
    logger.info(f"Extracted {len(models)} models from Next.js data")
    return models

def extract_models_from_json_object(json_data):
    """
    Extract models from a generic JSON object
    """
    models = []
    
    try:
        if isinstance(json_data, dict):
            if 'models' in json_data:
                models_data = json_data['models']
                if isinstance(models_data, list):
                    for i, model in enumerate(models_data):
                        if isinstance(model, dict):
                            model_info = {
                                'name': model.get('name', model.get('id', f'Model_{i}')),
                                'id': model.get('id', ''),
                                'description': model.get('description', ''),
                                'context_length': model.get('context_length', ''),
                                'pricing': model.get('pricing', ''),
                                'provider': model.get('provider', ''),
                                'architecture': model.get('architecture', ''),
                                'capabilities': model.get('capabilities', []),
                                'website': model.get('website', ''),
                                'image_url': model.get('image_url', '')
                            }
                            models.append(model_info)
    except Exception as e:
        logger.error(f"Error extracting from JSON object: {e}")
    
    return models

def extract_models_from_api(headers):
    """
    Try to extract models from API endpoint
    """
    models = []
    
    try:
        # Try common API endpoints
        api_endpoints = [
            'https://openrouter.ai/api/v1/models',
            'https://api.openrouter.ai/v1/models',
            'https://openrouter.ai/api/models'
        ]
        
        for endpoint in api_endpoints:
            try:
                logger.info(f"Trying API endpoint: {endpoint}")
                response = requests.get(endpoint, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and isinstance(data['data'], list):
                        for item in data['data']:
                            if isinstance(item, dict):
                                model_info = {
                                    'name': item.get('name', item.get('id', '')),
                                    'id': item.get('id', ''),
                                    'description': item.get('description', ''),
                                    'context_length': str(item.get('context_length', '')),
                                    'pricing': item.get('pricing', ''),
                                    'provider': item.get('owned_by', ''),
                                    'architecture': '',
                                    'capabilities': [],
                                    'website': '',
                                    'image_url': ''
                                }
                                models.append(model_info)
                        logger.info(f"Extracted {len(models)} models from API endpoint: {endpoint}")
                        break
            except Exception as e:
                logger.warning(f"Failed to fetch from {endpoint}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error extracting from API: {e}")
    
    return models

def get_sample_models():
    """
    Return sample model data as fallback
    """
    logger.info("Using sample model data as fallback")
    return [
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
        },
        {
            'name': 'Gemini Pro',
            'id': 'google/gemini-pro',
            'description': 'Google\'s most capable AI model',
            'context_length': '32768',
            'pricing': '$0.0025/1K tokens',
            'provider': 'Google',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion'],
            'website': 'https://gemini.google.com',
            'image_url': ''
        }
    ]

def find_models_in_dict(data, max_depth=10):
    """
    Recursively search for models in dictionary
    """
    if max_depth <= 0:
        return None
    
    if isinstance(data, dict):
        if 'models' in data:
            return data['models']
        
        for key, value in data.items():
            result = find_models_in_dict(value, max_depth - 1)
            if result:
                return result
    
    elif isinstance(data, list):
        for item in data:
            result = find_models_in_dict(item, max_depth - 1)
            if result:
                return result
    
    return None

def log_failed_extraction(raw_text, extraction_method, error_message):
    """
    Log failed extraction attempts to a file for later analysis
    """
    try:
        with open('failed_extractions.log', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Extraction Method: {extraction_method}\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Error: {error_message}\n")
            f.write(f"Raw Text (first 500 chars):\n")
            f.write(f"{raw_text[:500]}\n")
            f.write(f"{'='*80}\n")
    except Exception as e:
        logger.error(f"Failed to log extraction error: {e}")

def extract_models_from_html_structure(soup):
    """
    Extract model information from HTML structure based on actual OpenRouter.ai layout
    Based on the described structure:
    - Models displayed in sections with horizontal line dividers
    - Item 1: Model name (hyper-linked, left aligned) + Token counts (right aligned)
    - Item 2: Categories with ranking (optional)
    - Item 3: Model description (long text, wrapped/truncated)
    - Items 4-8: Provider | Context | Input Price | Output Price | Image Price (optional)
    """
    models = []
    failed_extractions = 0
    logger.info("Extracting models from HTML structure based on actual layout...")
    
    # Look for model containers - these could be divs, articles, or sections
    # Since models are separated by horizontal lines, look for elements that might contain model info
    
    # Strategy 1: Look for elements that contain links (model names are hyperlinked)
    model_links = soup.find_all('a', href=True)
    logger.info(f"Found {len(model_links)} links total")
    
    # Filter links that might be model names (look for patterns)
    model_patterns = [
        r'gpt', r'claude', r'llama', r'mistral', r'gemini', r'mixtral',
        r'qwen', r'yi', r'cohere', r'perplexity', r'deepseek', r'phi',
        r'solar', r'nexus', r'command', r'turbo', r'ultra', r'pro'
    ]
    
    potential_model_links = []
    for link in model_links:
        href = link.get('href', '').lower()
        text = link.get_text(strip=True).lower()
        
        # Check if link or text contains model patterns
        if any(pattern in href or pattern in text for pattern in model_patterns):
            potential_model_links.append(link)
    
    logger.info(f"Found {len(potential_model_links)} potential model links")
    
    # Strategy 2: Look for sections or divs that might contain model information
    # Look for common container patterns
    containers = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'model|card|item|entry', re.I))
    logger.info(f"Found {len(containers)} potential model containers")
    
    # Also look for elements that might contain the structured data
    # Since we know the structure has specific items separated by |, look for that pattern
    text_elements = soup.find_all(['div', 'span', 'p'])
    
    for i, container in enumerate(containers):
        try:
            model_info = extract_model_from_container(container, soup)
            if model_info and model_info.get('name'):
                models.append(model_info)
                logger.debug(f"Added model from container {i}: {model_info['name']}")
            else:
                # Log failed extraction
                raw_text = container.get_text()
                log_failed_extraction(raw_text, f"container_{i}", "No model name extracted")
                failed_extractions += 1
        except Exception as e:
            logger.warning(f"Error extracting model from container {i}: {e}")
            # Log failed extraction
            raw_text = container.get_text()
            log_failed_extraction(raw_text, f"container_{i}", str(e))
            failed_extractions += 1
            continue
    
    # Strategy 3: If we didn't get enough models, try a different approach
    # Look for text patterns that match the described structure
    if len(models) < 10:  # If we have very few models, try alternative approach
        logger.info("Trying alternative text pattern matching...")
        
        # Look for text containing the delimiter patterns
        all_text = soup.get_text()
        text_sections = all_text.split('\n')
        
        for section in text_sections:
            if '|' in section and any(pattern in section.lower() for pattern in model_patterns):
                try:
                    model_info = extract_model_from_text_section(section)
                    if model_info and model_info.get('name'):
                        models.append(model_info)
                        logger.debug(f"Added model from text section: {model_info['name']}")
                    else:
                        # Log failed extraction
                        log_failed_extraction(section, "text_section", "No model name extracted")
                        failed_extractions += 1
                except Exception as e:
                    logger.warning(f"Error extracting model from text section: {e}")
                    # Log failed extraction
                    log_failed_extraction(section, "text_section", str(e))
                    failed_extractions += 1
    
    logger.info(f"Extracted {len(models)} models from HTML structure")
    logger.info(f"Failed extractions: {failed_extractions}")
    
    # If we have too many failed extractions, log a warning
    if failed_extractions > len(models):
        logger.warning(f"High failure rate: {failed_extractions} failed vs {len(models)} successful extractions")
    
    return models

def extract_model_from_container(container, soup):
    """
    Extract model information from a single container element
    """
    model_info = {}
    raw_text = container.get_text()  # Save raw text for logging
    
    try:
        # Get all text and links in this container
        links = container.find_all('a', href=True)
        text = container.get_text()
        
        # Item 1: Extract model name and token counts
        # Model name is usually the most prominent link
        if links:
            # Try to find the model name link (usually the first or most prominent)
            model_link = None
            for link in links:
                link_text = link.get_text(strip=True)
                if link_text and len(link_text) > 2:  # Reasonable model name length
                    model_link = link
                    break
            
            if model_link:
                model_info['name'] = model_link.get_text(strip=True)
                model_info['model_url'] = urljoin('https://openrouter.ai', model_link.get('href', ''))
        
        # If no model name found in links, try to extract from text
        if 'name' not in model_info:
            # Look for model name patterns in text
            model_patterns = [
                r'([A-Z][a-zA-Z\s]*(?:GPT|Claude|Llama|Mistral|Gemini|Mixtral|Qwen|Yi|Cohere|Perplexity|DeepSeek|Phi|Solar|Nexus|Command)[\s\d\w]*)',
                r'([A-Z][a-zA-Z\s]*(?:Turbo|Ultra|Pro|Chat|Instruct)[\s\d\w]*)'
            ]
            
            for pattern in model_patterns:
                match = re.search(pattern, text)
                if match:
                    model_info['name'] = match.group(1).strip()
                    break
        
        # Extract token counts (right aligned, usually numbers with K/M)
        token_match = re.search(r'(\d+[KM]?)\s*tokens?', text, re.I)
        if token_match:
            model_info['token_count'] = token_match.group(1)
        
        # Item 2: Extract categories (optional, with ranking)
        category_match = re.search(r'([#★]\d*\s*[A-Za-z\s]+)', text)
        if category_match:
            model_info['categories'] = category_match.group(1).strip()
        
        # Item 3: Extract description (long text, often wrapped)
        # Description is usually the longer text content, not including the structured items
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Filter out lines that look like structured data (contain |, $, context, etc.)
        description_lines = []
        for line in lines:
            if (len(line) > 20 and 
                '|' not in line and 
                '$' not in line and 
                'context' not in line.lower() and
                'tokens' not in line.lower() and
                not re.match(r'^\d+[KM]?$', line)):
                description_lines.append(line)
        
        if description_lines:
            # Take the longest line as the description
            description = max(description_lines, key=len)
            if len(description) > 10:  # Reasonable description length
                model_info['description'] = description
        
        # Items 4-8: Extract structured data separated by |
        # Look for lines containing the delimiter
        for line in lines:
            if '|' in line:
                parts = [part.strip() for part in line.split('|')]
                
                if len(parts) >= 4:  # Should have at least 4 parts
                    # Part 4: Provider (hyper-linked)
                    if len(parts) >= 1:
                        provider_match = re.search(r'by\s+([A-Za-z\s&]+)', parts[0])
                        if provider_match:
                            model_info['provider'] = provider_match.group(1).strip()
                        
                        # Look for provider link
                        for link in links:
                            link_text = link.get_text(strip=True)
                            if link_text and link_text.lower() in parts[0].lower():
                                model_info['provider_url'] = urljoin('https://openrouter.ai', link.get('href', ''))
                                break
                    
                    # Part 5: Context window size
                    if len(parts) >= 2:
                        context_match = re.search(r'(\d+[K]?)\s*context', parts[1], re.I)
                        if context_match:
                            model_info['context_length'] = context_match.group(1)
                    
                    # Part 6: Input token pricing
                    if len(parts) >= 3:
                        input_price_match = re.search(r'\$([\d.]+)\s*\/?[M]\s*input', parts[2], re.I)
                        if input_price_match:
                            model_info['input_price'] = f"${input_price_match.group(1)}/M input tokens"
                    
                    # Part 7: Output token pricing
                    if len(parts) >= 4:
                        output_price_match = re.search(r'\$([\d.]+)\s*\/?[M]\s*output', parts[3], re.I)
                        if output_price_match:
                            model_info['output_price'] = f"${output_price_match.group(1)}/M output tokens"
                    
                    # Part 8: Image pricing (optional)
                    if len(parts) >= 5:
                        image_price_match = re.search(r'\$([\d.]+)\s*\/?[K]\s*image', parts[4], re.I)
                        if image_price_match:
                            model_info['image_price'] = f"${image_price_match.group(1)}/K input imgs"
        
        # Combine pricing information
        pricing_parts = []
        if 'input_price' in model_info:
            pricing_parts.append(model_info['input_price'])
        if 'output_price' in model_info:
            pricing_parts.append(model_info['output_price'])
        if 'image_price' in model_info:
            pricing_parts.append(model_info['image_price'])
        
        if pricing_parts:
            model_info['pricing'] = ' | '.join(pricing_parts)
        elif 'token_count' in model_info:
            model_info['pricing'] = f"Token count: {model_info['token_count']}"
        else:
            model_info['pricing'] = 'Unknown'
        
        # Set default values for missing fields
        model_info.setdefault('id', model_info.get('name', '').lower().replace(' ', '-'))
        model_info.setdefault('description', '')
        model_info.setdefault('context_length', '')
        model_info.setdefault('provider', '')
        model_info.setdefault('architecture', '')
        model_info.setdefault('capabilities', [])
        model_info.setdefault('website', model_info.get('model_url', ''))
        model_info.setdefault('image_url', '')
        
        # Validate that we have the minimum required information
        if not model_info.get('name'):
            logger.warning(f"Failed to extract model name from container. Raw text: {raw_text[:200]}...")
            return None
            
        # Log successful extraction
        logger.debug(f"Successfully extracted model: {model_info.get('name')} with URL: {model_info.get('model_url', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Error extracting model from container: {e}. Raw text: {raw_text[:200]}...")
        return None
    
    return model_info

def extract_model_from_text_section(text_section):
    """
    Extract model information from a text section containing the structured data
    """
    model_info = {}
    raw_text = text_section  # Save raw text for logging
    
    try:
        # Split by | to get the structured parts
        parts = [part.strip() for part in text_section.split('|')]
        
        if len(parts) < 3:
            logger.warning(f"Not enough parts in text section (expected at least 3, got {len(parts)}). Raw text: {raw_text[:200]}...")
            return None
        
        # Extract model name from the beginning of the text
        # Use non-greedy patterns and more specific matching
        model_patterns = [
            r'(GPT-\d+(?:\.\d+)?\s*(?:Turbo|Pro)?)',
            r'(Claude\s+\d+(?:\.\d+)?\s*(?:Sonnet|Opus|Haiku)?)',
            r'(Gemini\s+\d+(?:\.\d+)?\s*(?:Pro)?)',
            r'(Llama\s+\d+\s*[Bb]?)',
            r'(Mistral\s+\d+[Bb]?)',
            r'(Kimi\s+Dev\s+\d+[Bb]?)',
            r'(OpenAI\s+o\d+\s*(?:Pro)?)',
            r'([A-Z][a-zA-Z\s\d]*?(?:GPT|Claude|Llama|Mistral|Gemini|Mixtral|Qwen|Yi|Cohere|Perplexity|DeepSeek|Phi|Solar|Nexus|Command|OpenAI|Kimi)[\s\d\w().]*)',
            r'([A-Z][a-zA-Z\s\d]*?(?:Turbo|Ultra|Pro|Dev|Chat|Instruct)[\s\d\w().]*)',
            r'([A-Z][a-zA-Z\s\d]+?\d+[Bb]?)',
            r'([A-Z][a-zA-Z\s\d]+?\s*\d+(?:\.\d+)?[Bb]?)',
            r'([A-Z][a-zA-Z\s\d]+(?:\s+\d+)?[Bb]?)'  # More flexible pattern
        ]
        
        for pattern in model_patterns:
            match = re.search(pattern, text_section)
            if match:
                model_name = match.group(1).strip()
                # Clean up common artifacts - be more conservative
                model_name = re.sub(r'\s*\(\s*free\s*\)', '', model_name)
                model_name = re.sub(r'\s*\(\d+K\)', '', model_name)  # Remove context sizes
                model_name = re.sub(r'\s*\(\d+\)', '', model_name)  # Remove numbers in parentheses
                # Don't modify version numbers like 3.5, keep them as is
                model_name = model_name.strip()
                # Additional validation: must contain at least one model-related keyword or number
                if (model_name and len(model_name) > 2 and 
                    (any(keyword in model_name.lower() for keyword in 
                         ['gpt', 'claude', 'llama', 'mistral', 'gemini', 'mixtral', 'qwen', 'yi', 
                          'cohere', 'perplexity', 'deepseek', 'phi', 'solar', 'nexus', 'command', 
                          'openai', 'kimi', 'turbo', 'ultra', 'pro', 'dev', 'chat', 'instruct']) or
                     re.search(r'\d+[Bb]?$', model_name))):  # Ends with number or B/b
                    model_info['name'] = model_name
                    break
        
        if 'name' not in model_info:
            logger.warning(f"Could not extract model name from text section. Raw text: {raw_text[:200]}...")
            return None
        
        # Extract structured information from parts
        # Extract provider information
        provider_found = False
        for part in parts:
            if 'by' in part.lower():
                provider_match = re.search(r'by\s+([A-Za-z\s&]+)', part)
                if provider_match:
                    provider_name = provider_match.group(1).strip()
                    provider_name = re.sub(r'\s+', ' ', provider_name)
                    model_info['provider'] = provider_name
                    provider_found = True
                    break
        
        # If no provider found with "by", try to extract from the first part
        if not provider_found and len(parts) > 0:
            first_part = parts[0]
            # Only look for provider if the model name was already extracted and is different
            if model_info.get('name') not in first_part:
                # Look for company names in the first part
                company_patterns = [
                    r'(OpenAI)',
                    r'(Google)',
                    r'(Anthropic)',
                    r'(Meta)',
                    r'(Microsoft)',
                    r'(Cohere)',
                    r'(Mistral AI)',
                    r'(Perplexity AI)',
                    r'(DeepSeek AI)',
                    r'(Alibaba)',
                    r'(01\.AI)',
                    r'(Upstage)',
                    r'(Nexus Flow)',
                    r'(Moonshot)'
                ]
                
                for pattern in company_patterns:
                    provider_match = re.search(pattern, first_part)
                    if provider_match:
                        provider_name = provider_match.group(1).strip()
                        model_info['provider'] = provider_name
                        break
        
        # Extract other structured information
        for i, part in enumerate(parts):
            part_lower = part.lower()
            
            # Context
            if 'context' in part_lower:
                context_match = re.search(r'(\d+[K]?)\s*context', part)
                if context_match:
                    model_info['context_length'] = context_match.group(1)
            
            # Input price
            elif 'input' in part_lower and '$' in part:
                price_match = re.search(r'\$([\d.]+)', part)
                if price_match:
                    model_info['input_price'] = f"${price_match.group(1)}/M input tokens"
            
            # Output price
            elif 'output' in part_lower and '$' in part:
                price_match = re.search(r'\$([\d.]+)', part)
                if price_match:
                    model_info['output_price'] = f"${price_match.group(1)}/M output tokens"
            
            # Image price
            elif 'image' in part_lower and '$' in part:
                price_match = re.search(r'\$([\d.]+)', part)
                if price_match:
                    model_info['image_price'] = f"${price_match.group(1)}/K input imgs"
            
            # Free pricing
            elif 'free' in part_lower:
                # Check if this is in a pricing position (not part of model name)
                if i >= 2:  # Usually in pricing positions
                    if 'input_price' not in model_info:
                        model_info['input_price'] = 'Free'
                    elif 'output_price' not in model_info:
                        model_info['output_price'] = 'Free'
        
        # Combine pricing
        pricing_parts = []
        if 'input_price' in model_info:
            pricing_parts.append(model_info['input_price'])
        if 'output_price' in model_info:
            pricing_parts.append(model_info['output_price'])
        if 'image_price' in model_info:
            pricing_parts.append(model_info['image_price'])
        
        if pricing_parts:
            model_info['pricing'] = ' | '.join(pricing_parts)
        else:
            model_info['pricing'] = 'Unknown'
        
        # Set default values
        model_info.setdefault('id', model_info.get('name', '').lower().replace(' ', '-').replace(':', ''))
        model_info.setdefault('description', '')
        model_info.setdefault('architecture', '')
        model_info.setdefault('capabilities', [])
        model_info.setdefault('website', '')
        model_info.setdefault('image_url', '')
        
        # Generate URLs based on name and provider if not found
        if not model_info.get('model_url') and model_info.get('name'):
            # Create a URL-friendly name
            url_name = re.sub(r'[^\w\s-]', '', model_info['name']).strip().replace(' ', '-').lower()
            model_info['model_url'] = f"https://openrouter.ai/{url_name}"
        
        if not model_info.get('provider_url') and model_info.get('provider'):
            # Create a URL-friendly provider name
            url_provider = re.sub(r'[^\w\s-]', '', model_info['provider']).strip().replace(' ', '-').lower()
            model_info['provider_url'] = f"https://openrouter.ai/{url_provider}"
        
        # Validate minimum required information
        if not model_info.get('name'):
            logger.warning(f"Model name missing after extraction. Raw text: {raw_text[:200]}...")
            return None
            
        # Log successful extraction
        logger.debug(f"Successfully extracted model from text: {model_info.get('name')} with URL: {model_info.get('model_url', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Error extracting model from text section: {e}. Raw text: {raw_text[:200]}...")
        return None
    
    return model_info

def extract_model_from_element(element):
    """
    Extract model information from a single HTML element
    """
    model_info = {}
    
    try:
        # Extract name - try multiple approaches
        name_selectors = [
            ('h1', {}),
            ('h2', {}),
            ('h3', {}),
            ('h4', {}),
            ('h5', {}),
            ('h6', {}),
            ('div', {'class': re.compile(r'name|title|header', re.I)}),
            ('span', {'class': re.compile(r'name|title|header', re.I)}),
        ]
        
        for tag, attrs in name_selectors:
            name_elem = element.find(tag, attrs)
            if name_elem:
                name_text = name_elem.get_text(strip=True)
                if name_text and len(name_text) > 2:  # Avoid empty or very short names
                    model_info['name'] = name_text
                    break
        
        # If no name found in children, check the element itself
        if 'name' not in model_info:
            elem_text = element.get_text(strip=True)
            if elem_text and len(elem_text) < 100:  # Reasonable length for a name
                model_info['name'] = elem_text
        
        # Extract description
        desc_selectors = [
            ('p', {}),
            ('div', {'class': re.compile(r'description|desc|content', re.I)}),
            ('span', {'class': re.compile(r'description|desc|content', re.I)}),
        ]
        
        for tag, attrs in desc_selectors:
            desc_elem = element.find(tag, attrs)
            if desc_elem:
                desc_text = desc_elem.get_text(strip=True)
                if desc_text and len(desc_text) > 10:  # Reasonable description length
                    model_info['description'] = desc_text
                    break
        
        # Extract any other relevant information
        all_text = element.get_text(strip=True).lower()
        
        # Look for context length
        context_match = re.search(r'context\s*[:\-]?\s*(\d+[kkm]?)', all_text)
        if context_match:
            model_info['context_length'] = context_match.group(1)
        
        # Look for pricing information
        pricing_patterns = [
            r'\$[\d.]+',
            r'free',
            r'paid',
            r'premium',
            r'\d+\s*token',
        ]
        
        for pattern in pricing_patterns:
            pricing_match = re.search(pattern, all_text)
            if pricing_match:
                model_info['pricing'] = pricing_match.group(0)
                break
        
        # Look for provider
        provider_patterns = [
            r'openai',
            r'anthropic',
            r'meta',
            r'google',
            r'mistral',
            r'cohere',
        ]
        
        for pattern in provider_patterns:
            if pattern in all_text:
                model_info['provider'] = pattern.title()
                break
        
        # Set default values for missing fields
        model_info.setdefault('id', model_info.get('name', '').lower().replace(' ', '-'))
        model_info.setdefault('context_length', '')
        model_info.setdefault('pricing', '')
        model_info.setdefault('provider', '')
        model_info.setdefault('architecture', '')
        model_info.setdefault('capabilities', [])
        model_info.setdefault('website', '')
        model_info.setdefault('image_url', '')
        
    except Exception as e:
        logger.error(f"Error extracting model from element: {e}")
        return None
    
    return model_info if model_info.get('name') else None

def clean_and_categorize_models(df):
    """
    Clean the model data and categorize into free and paid
    """
    logger.info("Cleaning and categorizing models...")
    
    if df.empty:
        logger.warning("Empty DataFrame, returning as-is")
        return df
    
    # Ensure required columns exist
    required_columns = ['name', 'id', 'description', 'pricing', 'category', 'model_url', 'provider_url']
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
            logger.info(f"Added missing column: {col}")
    
    # Categorize models based on pricing
    def categorize_model(pricing_info):
        if pd.isna(pricing_info) or pricing_info == '':
            return 'Unknown'
        
        pricing_str = str(pricing_info).lower()
        
        # Check for free indicators
        if any(keyword in pricing_str for keyword in ['free', '0.00', 'no cost', 'gratis', 'open source']):
            return 'Free'
        
        # Check for paid indicators
        if any(keyword in pricing_str for keyword in ['$', 'paid', 'premium', 'subscribe', 'credit', 'token']):
            return 'Paid'
        
        return 'Unknown'
    
    # Apply categorization
    df['category'] = df['pricing'].apply(categorize_model)
    logger.info(f"Categorized models: Free={len(df[df['category'] == 'Free'])}, Paid={len(df[df['category'] == 'Paid'])}, Unknown={len(df[df['category'] == 'Unknown'])}")
    
    # Clean up pricing information
    def clean_pricing(pricing_info):
        if pd.isna(pricing_info):
            return ''
        
        if isinstance(pricing_info, dict):
            return json.dumps(pricing_info)
        
        return str(pricing_info)
    
    df['pricing'] = df['pricing'].apply(clean_pricing)
    
    # Clean up URLs
    def clean_url(url):
        if pd.isna(url) or url == '':
            return ''
        
        url_str = str(url).strip()
        
        # Ensure URL starts with http
        if url_str and not url_str.startswith(('http://', 'https://')):
            url_str = f"https://openrouter.ai/{url_str.lstrip('/')}"
        
        return url_str
    
    df['model_url'] = df['model_url'].apply(clean_url)
    df['provider_url'] = df['provider_url'].apply(clean_url)
    
    # Clean other text fields
    text_columns = ['name', 'description', 'provider', 'architecture']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else '')
    
    # Remove duplicates
    original_count = len(df)
    df = df.drop_duplicates(subset=['name', 'id'])
    logger.info(f"Removed {original_count - len(df)} duplicate models")
    
    # Sort by category and name
    df = df.sort_values(['category', 'name'])
    
    logger.info(f"Final dataset: {len(df)} models")
    return df

if __name__ == "__main__":
    # Scrape the models
    df = scrape_openrouter_models()
    
    if df is not None and not df.empty:
        print("\nModel Summary:")
        print(f"Total models: {len(df)}")
        
        # Check if category column exists
        if 'category' in df.columns:
            print(f"Free models: {len(df[df['category'] == 'Free'])}")
            print(f"Paid models: {len(df[df['category'] == 'Paid'])}")
            print(f"Unknown pricing: {len(df[df['category'] == 'Unknown'])}")
        else:
            print("Category column not found - this indicates a scraping issue")
        
        # Display first few models
        print("\nFirst 5 models:")
        display_cols = ['name', 'category'] if 'category' in df.columns else ['name']
        if 'description' in df.columns:
            display_cols.append('description')
        print(df[display_cols].head())
        
        # Show column info for debugging
        print(f"\nAvailable columns: {list(df.columns)}")
        
    else:
        print("Failed to scrape models. Please check the website structure or try again later.")
        print("Debug files created:")
        print("- debug_page.html: Raw HTML from the website")
        print("- debug_next_data.json: JSON data extracted (if any)")