from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json
from datetime import datetime
import requests

class OpenRouter:
    def __init__(self, openrouter_api_key: str):
        self.api_key = openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.models_url = "https://openrouter.ai/api/v1/models"

    def get_available_models(self) -> List[tuple]:
        """Get available models with enhanced categorization"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(self.models_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                models_data = response.json()
                models = []
                
                for model in models_data.get('data', []):
                    model_id = model['id']
                    model_name = model.get('name', model_id)
                    
                    # Add pricing and capability info
                    pricing = model.get('pricing', {})
                    if pricing:
                        prompt_cost = pricing.get('prompt', 'N/A')
                        cost_info = f" (${prompt_cost}/1M)"
                    else:
                        cost_info = " (Free)" if "free" in model_id.lower() else ""
                    
                    # Add reasoning capability indicator
                    reasoning_indicator = ""
                    if any(thinking_model in model_id.lower() for thinking_model in ['o1', 'r1', 'deepseek-r1']):
                        reasoning_indicator = " 🧠"
                    elif any(good_model in model_id.lower() for good_model in ['claude-3.5', 'gpt-4', 'llama-3.1-70b']):
                        reasoning_indicator = " ⚡"
                    
                    display_name = f"{model_name}{reasoning_indicator}{cost_info}"
                    models.append((model_id, display_name))
                
                return sorted(models, key=lambda x: x[1])
            else:
                return []
                
        except Exception as e:
            print(f"[Error] Failed to fetch OpenRouter models: {str(e)}")
            return []
