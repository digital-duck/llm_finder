# main.py - Main application file
import streamlit as st
import pandas as pd
import numpy as np
import re
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils import *



# Page config
st.set_page_config(
    page_title="LLM Finder",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
MODEL_CSV = "./models/openrouter-models-2025-07-27.csv"

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'embeddings' not in st.session_state:
    st.session_state.embeddings = None
if 'model_texts' not in st.session_state:
    st.session_state.model_texts = None

def get_device():
    try:
        if torch.cuda.is_available():
            # Test CUDA availability
            torch.cuda.empty_cache()
            return 'cuda'
    except Exception as e:
        print(f"CUDA not available, using CPU: {e}")
    return 'cpu'

@st.cache_data
def get_latest_model_csv() -> str:
    """Get the latest OpenRouter models CSV file path"""
    model_path = Path("./models")
    files = list(model_path.glob("openrouter-models-*.csv"))
    if not files:
        return MODEL_CSV
    latest_file = max(files, key=lambda f: f.stat().st_mtime)
    return str(latest_file)

# Shared utility functions
@st.cache_data
def load_data() -> pd.DataFrame:
    """Load and process the OpenRouter models data"""
    try:
        file_path = st.session_state.get('model_csv_path', MODEL_CSV)
        df = pd.read_csv(file_path, sep='\t')
    except FileNotFoundError:
        st.error(f"⚠️ CSV file not found: {file_path}")
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Error loading CSV: {e}")
        st.stop()
            
    # df['numeric_cost'] = df['cost'].apply(extract_cost)
    df['is_free_bool'] = df['is_free'] == 'Y'
    
    return df

@st.cache_resource
def load_embedding_model():
    """Load sentence transformer model for semantic search"""
    try:
        device = get_device()
        model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
        return model
    except Exception as e:
        st.error(f"Error loading embedding model: {e}")
        return None

@st.cache_data
def create_embeddings(df):
    """Create embeddings for semantic search"""
    model = load_embedding_model()
    if model is None:
        return None, None
    
    model_texts = []
    for _, row in df.iterrows():
        text = f"{row['model_name']} by {row['provider']}. "
        text += f"Cost: {row['cost']}. "
        text += f"{'Free model' if row['is_free_bool'] else 'Paid model'}. "
        text += f"API: {row['llm_model']}. "
        
        name_lower = row['model_name'].lower()
        if 'vision' in name_lower or 'vl' in name_lower:
            text += "Supports vision and image analysis. "
        if 'code' in name_lower or 'coder' in name_lower:
            text += "Optimized for code generation and programming. "
        if 'chat' in name_lower or 'instruct' in name_lower:
            text += "Designed for conversation and instruction following. "
        if 'large' in name_lower:
            text += "Large model with high capability. "
        if 'mini' in name_lower or 'small' in name_lower:
            text += "Compact model for efficiency. "
        if 'thinking' in name_lower:
            text += "Advanced reasoning and thinking capabilities. "
            
        model_texts.append(text)
    
    embeddings = model.encode(model_texts)
    return embeddings, model_texts

def semantic_search(query, df, embeddings, model_texts, top_k=5):
    """Perform semantic search on models"""
    if embeddings is None:
        return df.head(top_k)
    
    model = load_embedding_model()
    if model is None:
        return df.head(top_k)
    
    query_embedding = model.encode([query])
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = df.iloc[top_indices].copy()
    results['similarity'] = similarities[top_indices]
    return results

# Initialize model
# Load data and initialize embeddings
model_csv_path = get_latest_model_csv()
if not Path(model_csv_path).exists():
    st.error("❌ Model data not loaded. Please visit 'Load Model' page first.")
    st.stop()

if 'model_csv_path' not in st.session_state:
    st.session_state.model_csv_path = model_csv_path

df = load_data()
if 'df' not in st.session_state:
    st.session_state.df = df


# Initialize embeddings
if st.session_state.embeddings is None:
    with st.spinner("🔄 Initializing AI search capabilities..."):
        embeddings, model_texts = create_embeddings(df)
        st.session_state.embeddings = embeddings
        st.session_state.model_texts = model_texts



def main():
    # Main content
    st.subheader("LLM Finder")
    st.markdown("**Select a page from the sidebar to get started!**")

    st.info("""
    👈 **Choose a page from the sidebar menu** to explore:

    - **AI Chat** - Ask natural language questions about models
    - **Model Browser** - Search, filter, and compare models
    - **Overview** - View key statistics and distributions
    - **Analytics** - Advanced charts and analysis
    - **Recommend** - Get recommendations and insights
    """)

    # Quick stats on main page
    col1, col2, col3, col4, _ = st.columns([1, 1, 1, 2, 1])

    with col1:
        st.metric("Total Models", len(df))
    with col2:
        st.metric("Providers", df['provider'].nunique())
    with col3:
        st.metric("Free Models", len(df[df['is_free_bool']]))
    with col4:
        paid_models = df[~df['is_free_bool']]
        avg_cost = paid_models['numeric_cost'].mean() if len(paid_models) > 0 else 0
        st.metric("Avg Cost", format_cost(avg_cost))

if __name__ == "__main__": 
    show_sidebar()
    main()