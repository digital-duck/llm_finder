# pages/1_🤖_AI_Chat.py
import streamlit as st
import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from utils import *

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="wide")

# Check if data is available
if 'df' not in st.session_state:
    st.error("❌ Model data not loaded. Please visit 'Load Model' page first.")
    st.stop()

df = st.session_state.df

@st.cache_data
def load_embedding_model():
    """Load sentence transformer model for semantic search"""
    try:
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        st.error(f"Error loading embedding model: {e}")
        return None

@st.cache_data
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

def generate_chat_response(query, df, embeddings, model_texts):
    """Generate a conversational response about the models"""
    # Perform semantic search
    results = semantic_search(query, df, embeddings, model_texts, top_k=3)
    
    if len(results) == 0:
        return "I couldn't find any models matching your query. Please try rephrasing your question."
    
    # Generate response based on query type
    query_lower = query.lower()
    
    response = []
    if any(word in query_lower for word in ['cheap', 'affordable', 'low cost', 'budget']):
        response.append("Here are some affordable options:\n\n")
        for _, model in results.iterrows():
            response.append(f"• **{model['model_name']}** by {model['provider']} - {model['cost']}\n")
        
        top_free_providers = df[df['is_free_bool']]['provider'].value_counts().head(3).index.tolist()
        response.append(f"\n💡 **Tip**: Consider free models from {', '.join(top_free_providers)} for zero-cost testing!")
        
    elif any(word in query_lower for word in ['free', 'no cost', 'zero']):
        free_models = df[df['is_free_bool']].head(5)
        response.append("Here are some excellent free models:\n\n")
        for _, model in free_models.iterrows():
            response.append(f"• **{model['model_name']}** by {model['provider']}\n")
        response.append(f"\n🎉 **Total free models available**: {len(df[df['is_free_bool']])}")
        
    elif any(word in query_lower for word in ['vision', 'image', 'visual', 'see']):
        vision_models = df[df['model_name'].str.contains('vision|vl|visual', case=False, na=False)]
        if len(vision_models) > 0:
            response.append("Here are models with vision capabilities:\n\n")
            for _, model in vision_models.head(5).iterrows():
                response.append(f"• **{model['model_name']}** by {model['provider']} - {model['cost']}\n")
        else:
            response.append("I found some models that might support vision based on your search:\n\n")
            for _, model in results.iterrows():
                response.append(f"• **{model['model_name']}** by {model['provider']} - {model['cost']}\n")
                
    elif any(word in query_lower for word in ['code', 'programming', 'development']):
        response.append("Great choices for coding tasks:\n\n")
        for _, model in results.iterrows():
            response.append(f"• **{model['model_name']}** by {model['provider']} - {model['cost']}\n")
        response.append("\n💻 **Tip**: DeepSeek and OpenAI models are particularly strong for code generation!")
        
    elif any(word in query_lower for word in ['best', 'recommend', 'suggest']):
        response.append("Based on your query, here are my top recommendations:\n\n")
        for i, (_, model) in enumerate(results.iterrows(), 1):
            response.append(f"**{i}. {model['model_name']}** by {model['provider']}\n")
            response.append(f"   - **Cost**: {model['cost']}\n")
            response.append(f"   - **API**: `{model['llm_model']}`\n\n")
            
    else:
        response.append(f"I found these models related to '{query}':\n\n")
        for _, model in results.iterrows():
            response.append(f"• **{model['model_name']}** by {model['provider']} - {model['cost']}\n")
    
    return "\n".join(response)

def main():

    # Check for embeddings
    if 'embeddings' not in st.session_state or st.session_state.embeddings is None:
        st.error("❌ AI search not initialized. Please go back to the main page first.")
        st.stop()

    st.markdown("##### 💬 Chat with OpenRouter Models")
    st.markdown("*Powered by semantic search - ask question about the 320+ models!*")

    # Example queries
    st.markdown("**Try asking:**")
    example_queries = [
        "What are the cheapest models for code generation?",
        "Show me free models with vision capabilities",
        "Which providers offer the most affordable options?",
        "Recommend models for chatbot development",
        "What are the best models under $0.000001/1M?"
    ]

    cols = st.columns(len(example_queries))
    for i, query in enumerate(example_queries):
        if cols[i].button(f"💭 {query[:25]}...", key=f"example_{i}"):
            st.session_state.chat_history.append({"role": "user", "content": query})
            response = generate_chat_response(query, df, st.session_state.embeddings, st.session_state.model_texts)
            st.session_state.chat_history.append({"role": "assistant", "content": response})

    # Chat interface
    st.markdown("---")

    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.markdown("🧑 **User:**")
            st.markdown(message['content'])
        else:
            st.markdown("💬 **Assistant:**")
            st.markdown(message['content'])
            st.markdown("---")

    # Chat input
    user_query = st.text_input("Ask about OpenRouter models:", placeholder="e.g., 'What's the best free model for writing?'", key="chat_input")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Send 🚀") and user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})
            response = generate_chat_response(user_query, df, st.session_state.embeddings, st.session_state.model_texts)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            st.rerun()

    with col2:
        if st.button("Clear Chat 🗑️"):
            st.session_state.chat_history = []
            st.rerun()

if __name__ == "__main__": 
    show_sidebar()
    main()