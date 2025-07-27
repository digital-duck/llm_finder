import streamlit as st
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import re
import pandas as pd
from utils import *


st.set_page_config(page_title="Load Model", page_icon="📥", layout="wide")


def parse_openrouter_model(description):
    """
    Parse OpenRouter model description into provider, model name, and cost.
    
    Args:
        description (str): Model description in various formats
    
    Returns:
        dict: {'provider': str, 'model_name': str, 'cost': str}
    """
    # Remove extra quotes and whitespace
    description = description.strip().strip("'\"")
    
    if ":" in description:
        # Format: "Provider: Model Name (cost)" or "Provider: Model Name (free) (cost)"
        parts = description.split(":", 1)
        llm_provider = parts[0].strip()
        remaining_text = parts[1].strip()
        
        # Find the last occurrence of parentheses for cost
        last_paren_start = remaining_text.rfind("(")
        if last_paren_start != -1:
            model_name = remaining_text[:last_paren_start].strip()
            cost_part = remaining_text[last_paren_start:]
            # Extract cost from parentheses
            if cost_part.startswith("(") and cost_part.endswith(")"):
                model_cost = cost_part[1:-1]  # Remove parentheses
            else:
                model_cost = cost_part
        else:
            # Fallback if no parentheses found
            model_name = remaining_text
            model_cost = "Unknown"
    else:
        # Format: "Provider Model Name (cost)"
        parts = description.split(" ")
        if len(parts) < 2:
            print(f"[ERROR-1] Unable to parse model description: {description}")
            return {} 
        
        llm_provider = parts[0]
        
        # Find the last part that looks like "(cost)"
        cost_part = ""
        model_parts = parts[1:]
        
        # Look for the last element that's in parentheses
        if model_parts and model_parts[-1].startswith("(") and model_parts[-1].endswith(")"):
            cost_part = model_parts[-1][1:-1]  # Remove parentheses
            model_parts = model_parts[:-1]  # Remove cost part from model name
        
        model_name = " ".join(model_parts)
        model_cost = cost_part if cost_part else "Unknown"
    
    return {
        'provider': llm_provider,
        'model_name': model_name,
        'cost': model_cost,
        'numeric_cost': extract_cost(model_cost),
        'free': 'Y' if "free" in description else 'N',
        'description': description,
    }

@st.cache_data
def save_openrouter_models(
        models: list,
        model_path: Path = Path("./models"),
        delimitor: str = "\t"
    ) -> str:
    headers = ["llm_model", "model_name", "provider", "is_free", "cost", "numeric_cost", "description"]
    # parse
    data = []
    for llm_model, desc in models:
        res = parse_openrouter_model(desc)
        # print(desc, res)
        if res:
            provider = res.get("provider")
            model_name = res.get("model_name")
            is_free = res.get("free")
            cost = res.get("cost")
            numeric_cost = res.get("numeric_cost", 0.0)
            description = res.get("description")
            data.append([llm_model, model_name, provider, is_free, cost, str(numeric_cost), description])

    print(data[:2])

    # save models
    model_path.mkdir(parents=True, exist_ok=True)
    dt_str = datetime.now().strftime("%Y-%m-%d")
    file_path = model_path / f"openrouter-models-{dt_str}.csv"
    if file_path.exists(): 
        return

    with open(file_path, "w") as f:
        f.write(delimitor.join(headers) + "\n")
        for row in data:
            f.write(delimitor.join(row) + "\n")

    return file_path

# @st.cache_data(ttl=3600*24)  # Cache for 1 day
def main():
    st.markdown("##### 📥 Load Model")

    dt_str = datetime.now().strftime("%Y-%m-%d")
    file_path = Path("./models") / f"openrouter-models-{dt_str}.csv"
    if file_path.exists():
        df = pd.read_csv(file_path, sep="\t")
        st.success(f"Models already loaded from {file_path}.")
        if 'df' not in st.session_state:
            st.session_state.df = df

        st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "llm_model": st.column_config.TextColumn("Model ID"),
                "model_name": st.column_config.TextColumn("Model Name"),
                "provider": st.column_config.TextColumn("Provider"),
                "is_free": st.column_config.TextColumn("Free"),
                "cost": st.column_config.TextColumn("Cost"),
                "numeric_cost": st.column_config.NumberColumn("Numeric Cost"),
                "description": st.column_config.TextColumn("Description")
            }
        )

        return

    
    api_key = st.session_state.get("openrouter_api_key", "")
    if not api_key:
        st.error("Please enter your OpenRouter API key in the sidebar.")
        return
   
    
    # Initialize OpenRouter client
    openrouter = OpenRouter(api_key)
    
    # Fetch available models
    with st.spinner("🔄 Fetching models from OpenRouter..."):
        available_models = openrouter.get_available_models()
    
    if not available_models:
        st.error("No models found. Please check your API key or try again later.")
        return
    
    file_csv = save_openrouter_models(available_models)
    st.success(f"Models loaded successfully, saved to {str(file_csv)}!")
    df = pd.read_csv(file_path, sep="\t")
    if 'df' not in st.session_state:
        st.session_state.df = df    
    
    st.markdown("##### Available Models - 10 sample models")
    for model_id, model_name in available_models[:10]:
        st.write(f"- **{model_name}** (ID: {model_id})")

if __name__ == "__main__":
    show_sidebar()
    with st.sidebar:
        st.subheader("Configuration 🔧")
        
        # API Key
        api_key = st.text_input(
            "OpenRouter API Key",
            type="password",
            value=os.getenv("OPENROUTER_API_KEY", ""),
            placeholder="Enter your OpenRouter API key here",
            help="Get your API key from https://openrouter.ai/",
            key="openrouter_api_key"
        )
        
        if not api_key:
            st.error("Please enter your OpenRouter API key to continue.")


    main()