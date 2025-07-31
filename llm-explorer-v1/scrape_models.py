import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import re
from urllib.parse import urljoin

def scrape_openrouter_models():
    """
    Scrape model information from OpenRouter.ai models page
    """
    print("Scraping OpenRouter models...")
    
    # Headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Fetch the main models page
        url = "https://openrouter.ai/models"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for script tags that might contain model data
        models_data = []
        
        # Try to find JSON data in script tags
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and '__NEXT_DATA__' in script.string:
                try:
                    # Extract JSON data from Next.js
                    json_data = json.loads(script.string)
                    models_data = extract_models_from_next_data(json_data)
                    if models_data:
                        break
                except json.JSONDecodeError:
                    continue
        
        # If no data found in Next.js, try alternative parsing
        if not models_data:
            models_data = extract_models_from_html(soup)
        
        # Convert to DataFrame
        df = pd.DataFrame(models_data)
        
        # Clean and categorize data
        df = clean_and_categorize_models(df)
        
        # Save to CSV
        df.to_csv('openrouter_models.csv', index=False)
        print(f"Successfully scraped {len(df)} models and saved to openrouter_models.csv")
        
        return df
        
    except Exception as e:
        print(f"Error scraping models: {e}")
        return None

def extract_models_from_next_data(json_data):
    """
    Extract model information from Next.js JSON data
    """
    models = []
    
    try:
        # Navigate through the JSON structure to find models
        # This is a common pattern in Next.js apps
        if 'props' in json_data and 'pageProps' in json_data['props']:
            page_props = json_data['props']['pageProps']
            
            # Look for models in various possible locations
            if 'models' in page_props:
                models_data = page_props['models']
            elif 'data' in page_props and 'models' in page_props['data']:
                models_data = page_props['data']['models']
            else:
                # Try to find models anywhere in the structure
                models_data = find_models_in_dict(page_props)
            
            if models_data:
                for model in models_data:
                    if isinstance(model, dict):
                        models.append({
                            'name': model.get('name', model.get('id', '')),
                            'id': model.get('id', ''),
                            'description': model.get('description', ''),
                            'context_length': model.get('context_length', model.get('context', '')),
                            'pricing': model.get('pricing', {}),
                            'provider': model.get('provider', ''),
                            'architecture': model.get('architecture', ''),
                            'capabilities': model.get('capabilities', []),
                            'website': model.get('website', ''),
                            'image_url': model.get('image_url', '')
                        })
    
    except Exception as e:
        print(f"Error extracting from Next.js data: {e}")
    
    return models

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

def extract_models_from_html(soup):
    """
    Extract model information from HTML structure (fallback method)
    """
    models = []
    
    # Look for model cards or containers
    model_cards = soup.find_all(['div', 'article'], class_=re.compile(r'model|card', re.I))
    
    for card in model_cards:
        try:
            model_info = {}
            
            # Extract name
            name_elem = card.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if name_elem:
                model_info['name'] = name_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = card.find('p')
            if desc_elem:
                model_info['description'] = desc_elem.get_text(strip=True)
            
            # Extract any other relevant information
            for elem in card.find_all(['div', 'span']):
                text = elem.get_text(strip=True)
                if 'context' in text.lower():
                    model_info['context_length'] = text
                elif 'pricing' in text.lower() or '$' in text:
                    model_info['pricing_info'] = text
            
            if model_info.get('name'):
                models.append(model_info)
                
        except Exception as e:
            continue
    
    return models

def clean_and_categorize_models(df):
    """
    Clean the model data and categorize into free and paid
    """
    if df.empty:
        return df
    
    # Ensure required columns exist
    required_columns = ['name', 'id', 'description', 'pricing', 'category']
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
    
    # Categorize models based on pricing
    def categorize_model(pricing_info):
        if pd.isna(pricing_info) or pricing_info == '':
            return 'Unknown'
        
        pricing_str = str(pricing_info).lower()
        
        # Check for free indicators
        if any(keyword in pricing_str for keyword in ['free', '0.00', 'no cost', 'gratis']):
            return 'Free'
        
        # Check for paid indicators
        if any(keyword in pricing_str for keyword in ['$', 'paid', 'premium', 'subscribe', 'credit']):
            return 'Paid'
        
        return 'Unknown'
    
    # Apply categorization
    df['category'] = df['pricing'].apply(categorize_model)
    
    # Clean up pricing information
    def clean_pricing(pricing_info):
        if pd.isna(pricing_info):
            return ''
        
        if isinstance(pricing_info, dict):
            return json.dumps(pricing_info)
        
        return str(pricing_info)
    
    df['pricing'] = df['pricing'].apply(clean_pricing)
    
    # Clean other text fields
    text_columns = ['name', 'description', 'provider', 'architecture']
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: str(x).strip() if pd.notna(x) else '')
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['name', 'id'])
    
    # Sort by category and name
    df = df.sort_values(['category', 'name'])
    
    return df

if __name__ == "__main__":
    # Scrape the models
    df = scrape_openrouter_models()
    
    if df is not None:
        print("\nModel Summary:")
        print(f"Total models: {len(df)}")
        print(f"Free models: {len(df[df['category'] == 'Free'])}")
        print(f"Paid models: {len(df[df['category'] == 'Paid'])}")
        print(f"Unknown pricing: {len(df[df['category'] == 'Unknown'])}")
        
        # Display first few models
        print("\nFirst 5 models:")
        print(df[['name', 'category', 'description']].head())
    else:
        print("Failed to scrape models. Please check the website structure or try again later.")