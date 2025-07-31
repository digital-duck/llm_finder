#!/usr/bin/env python3
"""
Create sample model data for testing the app without scraping
"""

import csv
import json

def create_sample_models():
    """Create a comprehensive sample dataset of LLM models"""
    
    models = [
        {
            'name': 'GPT-4',
            'id': 'openai/gpt-4',
            'description': 'Most capable GPT-4 model, great for complex tasks that require advanced reasoning',
            'context_length': '8192',
            'pricing': '$0.03/1K tokens',
            'provider': 'OpenAI',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'reasoning'],
            'website': 'https://openai.com/gpt-4',
            'image_url': ''
        },
        {
            'name': 'GPT-4 Turbo',
            'id': 'openai/gpt-4-turbo',
            'description': 'Latest GPT-4 model with improved capabilities and knowledge cutoff',
            'context_length': '128000',
            'pricing': '$0.01/1K tokens',
            'provider': 'OpenAI',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'reasoning'],
            'website': 'https://openai.com/gpt-4',
            'image_url': ''
        },
        {
            'name': 'Claude 2.1',
            'id': 'anthropic/claude-2.1',
            'description': 'Helpful, harmless, and honest AI assistant with large context window',
            'context_length': '200000',
            'pricing': '$0.011/1K tokens',
            'provider': 'Anthropic',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'analysis'],
            'website': 'https://anthropic.com/claude',
            'image_url': ''
        },
        {
            'name': 'Claude Instant',
            'id': 'anthropic/claude-instant',
            'description': 'Faster, more compact version of Claude for quick responses',
            'context_length': '100000',
            'pricing': '$0.0011/1K tokens',
            'provider': 'Anthropic',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion'],
            'website': 'https://anthropic.com/claude',
            'image_url': ''
        },
        {
            'name': 'Llama 2 70B',
            'id': 'meta-llama/llama-2-70b-chat',
            'description': 'Open source large language model from Meta',
            'context_length': '4096',
            'pricing': 'Free',
            'provider': 'Meta',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion'],
            'website': 'https://ai.meta.com/llama',
            'image_url': ''
        },
        {
            'name': 'Llama 2 13B',
            'id': 'meta-llama/llama-2-13b-chat',
            'description': 'Smaller open source model from Meta, faster but less capable',
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
            'description': 'High-performance open source model with strong reasoning capabilities',
            'context_length': '8192',
            'pricing': 'Free',
            'provider': 'Mistral AI',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'reasoning'],
            'website': 'https://mistral.ai',
            'image_url': ''
        },
        {
            'name': 'Mixtral 8x7B',
            'id': 'mistralai/mixtral-8x7b-instruct',
            'description': 'Mixture of Experts model with superior performance',
            'context_length': '32768',
            'pricing': '$0.0025/1K tokens',
            'provider': 'Mistral AI',
            'architecture': 'Mixture of Experts',
            'capabilities': ['chat', 'completion', 'reasoning'],
            'website': 'https://mistral.ai',
            'image_url': ''
        },
        {
            'name': 'Gemini Pro',
            'id': 'google/gemini-pro',
            'description': 'Google\'s most capable AI model with multimodal capabilities',
            'context_length': '32768',
            'pricing': '$0.0025/1K tokens',
            'provider': 'Google',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'multimodal'],
            'website': 'https://gemini.google.com',
            'image_url': ''
        },
        {
            'name': 'Gemini Ultra',
            'id': 'google/gemini-ultra',
            'description': 'Google\'s most advanced model with state-of-the-art performance',
            'context_length': '32768',
            'pricing': '$0.01/1K tokens',
            'provider': 'Google',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'multimodal', 'reasoning'],
            'website': 'https://gemini.google.com',
            'image_url': ''
        },
        {
            'name': 'Cohere Command',
            'id': 'cohere/command',
            'description': 'Enterprise-grade language model optimized for business applications',
            'context_length': '4096',
            'pricing': '$0.003/1K tokens',
            'provider': 'Cohere',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'summarization'],
            'website': 'https://cohere.com',
            'image_url': ''
        },
        {
            'name': 'Cohere Command R+',
            'id': 'cohere/command-r-plus',
            'description': 'Advanced version with improved reasoning and larger context',
            'context_length': '128000',
            'pricing': '$0.015/1K tokens',
            'provider': 'Cohere',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'reasoning', 'summarization'],
            'website': 'https://cohere.com',
            'image_url': ''
        },
        {
            'name': 'Perplexity Online',
            'id': 'perplexity/perplexity-online',
            'description': 'AI model with real-time internet access for up-to-date information',
            'context_length': '4096',
            'pricing': '$0.002/1K tokens',
            'provider': 'Perplexity AI',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'web_search'],
            'website': 'https://perplexity.ai',
            'image_url': ''
        },
        {
            'name': 'Qwen 72B',
            'id': 'qwen/qwen-72b-chat',
            'description': 'Large language model from Alibaba with strong multilingual capabilities',
            'context_length': '32768',
            'pricing': 'Free',
            'provider': 'Alibaba',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'multilingual'],
            'website': 'https://qwenlm.com',
            'image_url': ''
        },
        {
            'name': 'Yi 34B',
            'id': '01-ai/yi-34b-chat',
            'description': 'High-performance open source model with strong reasoning capabilities',
            'context_length': '4096',
            'pricing': 'Free',
            'provider': '01.AI',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'reasoning'],
            'website': 'https://01.ai',
            'image_url': ''
        },
        {
            'name': 'DeepSeek-V2',
            'id': 'deepseek-ai/deepseek-v2',
            'description': 'Advanced reasoning model with strong mathematical capabilities',
            'context_length': '16384',
            'pricing': '$0.002/1K tokens',
            'provider': 'DeepSeek AI',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'reasoning', 'math'],
            'website': 'https://deepseek.ai',
            'image_url': ''
        },
        {
            'name': 'Code Llama 34B',
            'id': 'meta-llama/code-llama-34b',
            'description': 'Specialized model for code generation and programming tasks',
            'context_length': '16384',
            'pricing': 'Free',
            'provider': 'Meta',
            'architecture': 'Transformer',
            'capabilities': ['code', 'completion', 'chat'],
            'website': 'https://ai.meta.com/llama',
            'image_url': ''
        },
        {
            'name': 'Solar Pro',
            'id': 'upstage/solar-pro',
            'description': 'Korean-language model with strong multilingual capabilities',
            'context_length': '4096',
            'pricing': '$0.005/1K tokens',
            'provider': 'Upstage',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'multilingual'],
            'website': 'https://upstage.ai',
            'image_url': ''
        },
        {
            'name': 'Nexus Raven',
            'id': 'nexus-stream/nexus-raven',
            'description': 'Specialized model for function calling and tool use',
            'context_length': '4096',
            'pricing': 'Free',
            'provider': 'Nexus Flow',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion', 'function_calling'],
            'website': 'https://nexusflow.ai',
            'image_url': ''
        },
        {
            'name': 'Phi-2',
            'id': 'microsoft/phi-2',
            'description': 'Small but capable model from Microsoft, good for local deployment',
            'context_length': '2048',
            'pricing': 'Free',
            'provider': 'Microsoft',
            'architecture': 'Transformer',
            'capabilities': ['chat', 'completion'],
            'website': 'https://azure.microsoft.com',
            'image_url': ''
        }
    ]
    
    return models

def categorize_model(pricing_info):
    """Categorize model based on pricing information"""
    if not pricing_info:
        return 'Unknown'
    
    pricing_str = str(pricing_info).lower()
    
    # Check for free indicators
    if any(keyword in pricing_str for keyword in ['free', '0.00', 'no cost', 'gratis', 'open source']):
        return 'Free'
    
    # Check for paid indicators
    if any(keyword in pricing_str for keyword in ['$', 'paid', 'premium', 'subscribe', 'credit']):
        return 'Paid'
    
    return 'Unknown'

def main():
    """Main function to create sample data"""
    print("Creating sample LLM model data...")
    
    # Get sample models
    models = create_sample_models()
    
    # Categorize models
    for model in models:
        model['category'] = categorize_model(model['pricing'])
    
    # Convert capabilities list to string for CSV
    for model in models:
        if isinstance(model['capabilities'], list):
            model['capabilities'] = ', '.join(model['capabilities'])
    
    # Save to CSV
    try:
        with open('openrouter_models.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['name', 'id', 'description', 'pricing', 'provider', 'category', 'context_length', 'architecture', 'capabilities', 'website', 'image_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(models)
        
        print(f"✅ Successfully created openrouter_models.csv with {len(models)} models")
        
        # Show summary
        free_count = len([m for m in models if m['category'] == 'Free'])
        paid_count = len([m for m in models if m['category'] == 'Paid'])
        unknown_count = len([m for m in models if m['category'] == 'Unknown'])
        
        print(f"\n📊 Model Summary:")
        print(f"   Total models: {len(models)}")
        print(f"   Free models: {free_count}")
        print(f"   Paid models: {paid_count}")
        print(f"   Unknown pricing: {unknown_count}")
        
        # Show providers
        providers = list(set(m['provider'] for m in models))
        print(f"   Providers: {len(providers)} ({', '.join(providers)})")
        
        print(f"\n🚀 You can now run the Streamlit app!")
        print(f"   streamlit run app.py")
        
    except Exception as e:
        print(f"❌ Error creating CSV file: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()