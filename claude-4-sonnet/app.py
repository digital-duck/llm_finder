import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json
import re
from datetime import datetime
from collections import Counter
import sqlite3
import os

# Page configuration
st.set_page_config(
    page_title="🔍 LLM Model Finder Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(145deg, #f0f2f6, #ffffff);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }
    .provider-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        margin: 0.25rem;
        background-color: #e1f5fe;
        color: #0277bd;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .price-tag {
        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    .free-tag {
        background: linear-gradient(45deg, #51cf66, #40c057);
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    .context-window {
        background: linear-gradient(45deg, #845ef7, #7048e8);
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)


class LLMModelFinder:
    def __init__(self):
        self.initialize_session_state()
        self.data = self.load_model_data()

    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'favorite_models' not in st.session_state:
            st.session_state.favorite_models = set()
        if 'comparison_list' not in st.session_state:
            st.session_state.comparison_list = []
        if 'selected_models' not in st.session_state:
            st.session_state.selected_models = []

    @st.cache_data
    def load_model_data(_self):
        """Load model data from CSV file."""
        try:
            # First try to load the API data
            if os.path.exists('openrouter_models_api.csv'):
                df = pd.read_csv('openrouter_models_api.csv')
                st.success("✅ Loaded OpenRouter API data!")
                return df
            else:
                st.error("❌ Could not find 'openrouter_models_api.csv'. Please run the parser first.")
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            return pd.DataFrame()

    def render_header(self):
        """Render the main header with stats."""
        st.markdown('<h1 class="main-header">🔍 LLM Model Finder Pro</h1>', unsafe_allow_html=True)
        st.markdown("**Discover, compare, and choose the perfect LLM for your needs**")
        
        if not self.data.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            total_models = len(self.data)
            total_providers = self.data['provider'].nunique()
            free_models = len(self.data[self.data['input_pricing'] == 'Free'])
            
            # Calculate average context window
            context_nums = self.data['context_window'].str.extract(r'(\d+)').astype(float)
            avg_context = context_nums.mean().iloc[0] if not context_nums.empty else 0
            
            with col1:
                st.metric("📊 Total Models", total_models)
            with col2:
                st.metric("🏢 Providers", total_providers)
            with col3:
                st.metric("🆓 Free Models", free_models)
            with col4:
                if not pd.isna(avg_context):
                    st.metric("🧠 Avg Context", f"{avg_context/1000:.0f}K")
                else:
                    st.metric("🧠 Avg Context", "N/A")

    def render_sidebar_filters(self):
        """Render sidebar with filters."""
        st.sidebar.title("🎛️ Filters & Controls")
        
        if self.data.empty:
            st.sidebar.error("No data loaded")
            return self.data
        
        # Provider filter
        st.sidebar.subheader("🏢 Provider")
        providers = ['All'] + sorted(self.data['provider'].dropna().unique())
        selected_provider = st.sidebar.selectbox("Select Provider", providers)
        
        # Pricing filter
        st.sidebar.subheader("💰 Pricing")
        pricing_options = ['All', 'Free Only', 'Paid Only']
        selected_pricing = st.sidebar.selectbox("Pricing Type", pricing_options)
        
        # Context window filter
        st.sidebar.subheader("🧠 Context Window")
        context_ranges = ['All', '< 32K', '32K - 128K', '128K - 1M', '> 1M']
        selected_context = st.sidebar.selectbox("Context Range", context_ranges)
        
        # Search
        st.sidebar.subheader("🔍 Search")
        search_term = st.sidebar.text_input("Search models", placeholder="Enter model name or description...")
        
        # Apply filters
        filtered_df = self.data.copy()
        
        if selected_provider != 'All':
            filtered_df = filtered_df[filtered_df['provider'] == selected_provider]
        
        if selected_pricing == 'Free Only':
            filtered_df = filtered_df[filtered_df['input_pricing'] == 'Free']
        elif selected_pricing == 'Paid Only':
            filtered_df = filtered_df[filtered_df['input_pricing'] != 'Free']
        
        if selected_context != 'All':
            # Extract numeric context values
            filtered_df['context_numeric'] = filtered_df['context_window'].str.extract(r'(\d+)').astype(float)
            
            if selected_context == '< 32K':
                filtered_df = filtered_df[filtered_df['context_numeric'] < 32000]
            elif selected_context == '32K - 128K':
                filtered_df = filtered_df[(filtered_df['context_numeric'] >= 32000) & 
                                        (filtered_df['context_numeric'] <= 128000)]
            elif selected_context == '128K - 1M':
                filtered_df = filtered_df[(filtered_df['context_numeric'] > 128000) & 
                                        (filtered_df['context_numeric'] <= 1000000)]
            elif selected_context == '> 1M':
                filtered_df = filtered_df[filtered_df['context_numeric'] > 1000000]
        
        if search_term:
            mask = (filtered_df['name'].str.contains(search_term, case=False, na=False) |
                   filtered_df['description'].str.contains(search_term, case=False, na=False) |
                   filtered_df['provider'].str.contains(search_term, case=False, na=False))
            filtered_df = filtered_df[mask]
        
        # Show filter results
        st.sidebar.markdown(f"**Found: {len(filtered_df)} models**")
        
        return filtered_df

    def render_model_cards(self, df):
        """Render model cards with enhanced information."""
        st.subheader(f"📋 Models ({len(df)} found)")
        
        if df.empty:
            st.info("No models match your criteria. Try adjusting the filters.")
            return
        
        # Sorting options
        col1, col2 = st.columns([3, 1])
        with col2:
            sort_options = ["Name", "Provider", "Context Window", "Input Price"]
            sort_by = st.selectbox("Sort by", sort_options)
        
        # Sort dataframe
        if sort_by == "Context Window":
            df['context_numeric'] = df['context_window'].str.extract(r'(\d+)').astype(float)
            df = df.sort_values('context_numeric', ascending=False, na_position='last')
        elif sort_by == "Input Price":
            def price_sort_key(price):
                if pd.isna(price) or price == '' or price == 'Free':
                    return 0
                try:
                    # Extract number from price string
                    match = re.search(r'\$([0-9.]+)', str(price))
                    return float(match.group(1)) if match else 999999
                except:
                    return 999999
            
            df['price_numeric'] = df['input_pricing'].apply(price_sort_key)
            df = df.sort_values('price_numeric')
        else:
            sort_column = sort_by.lower().replace(" ", "_")
            if sort_column in df.columns:
                df = df.sort_values(sort_column)
        
        # Display models in expandable cards
        for idx, row in df.iterrows():
            with st.expander(f"**{row['name']}** by {row['provider']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Description
                    if pd.notna(row['description']) and row['description']:
                        st.markdown(f"**Description:** {row['description'][:300]}{'...' if len(str(row['description'])) > 300 else ''}")
                    else:
                        st.markdown("*No description available*")
                    
                    # Model details
                    details_col1, details_col2 = st.columns(2)
                    
                    with details_col1:
                        st.markdown(f"**ID:** `{row['id']}`")
                        st.markdown(f"**Context:** {row['context_window']}")
                    
                    with details_col2:
                        st.markdown(f"**Input Price:** {row['input_pricing']}")
                        st.markdown(f"**Output Price:** {row['output_pricing']}")
                        if row['image_pricing']:
                            st.markdown(f"**Image Price:** {row['image_pricing']}")
                
                with col2:
                    # Action buttons
                    button_col1, button_col2 = st.columns(2)
                    
                    with button_col1:
                        if st.button("⭐ Favorite", key=f"fav_{idx}"):
                            st.session_state.favorite_models.add(row['id'])
                            st.success("Added to favorites!")
                            st.rerun()
                        
                        if st.button("🔗 View", key=f"view_{idx}"):
                            if pd.notna(row['model_url']):
                                st.markdown(f"[Open Model Page]({row['model_url']})")
                    
                    with button_col2:
                        if st.button("📊 Compare", key=f"compare_{idx}"):
                            if row['id'] not in st.session_state.comparison_list:
                                st.session_state.comparison_list.append(row['id'])
                                st.success("Added to comparison!")
                                st.rerun()
                            else:
                                st.warning("Already in comparison")
                        
                        if pd.notna(row['provider_url']):
                            if st.button("🏢 Provider", key=f"provider_{idx}"):
                                st.markdown(f"[View Provider]({row['provider_url']})")

    def render_analytics_dashboard(self, df):
        """Render analytics dashboard with visualizations."""
        st.subheader("📊 Analytics Dashboard")
        
        if df.empty:
            st.info("No data to display analytics.")
            return
        
        # Top row - Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Models Found", len(df))
        with col2:
            providers_count = df['provider'].nunique()
            st.metric("Providers", providers_count)
        with col3:
            free_count = len(df[df['input_pricing'] == 'Free'])
            st.metric("Free Models", free_count)
        with col4:
            paid_count = len(df[df['input_pricing'] != 'Free'])
            st.metric("Paid Models", paid_count)
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Provider distribution
            provider_counts = df['provider'].value_counts().head(10)
            if not provider_counts.empty:
                fig = px.bar(
                    x=provider_counts.values,
                    y=provider_counts.index,
                    orientation='h',
                    title="Top 10 Providers by Model Count",
                    labels={'x': 'Number of Models', 'y': 'Provider'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pricing distribution
            pricing_data = df['input_pricing'].apply(lambda x: 'Free' if x == 'Free' else 'Paid').value_counts()
            if not pricing_data.empty:
                fig = px.pie(
                    values=pricing_data.values,
                    names=pricing_data.index,
                    title="Free vs Paid Models Distribution"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Context window analysis
        st.subheader("🧠 Context Window Analysis")
        
        # Extract context window numbers
        df_context = df.copy()
        df_context['context_numeric'] = df_context['context_window'].str.extract(r'(\d+)').astype(float)
        df_context = df_context.dropna(subset=['context_numeric'])
        
        if not df_context.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Context window histogram
                fig = px.histogram(
                    df_context,
                    x='context_numeric',
                    nbins=20,
                    title="Context Window Distribution",
                    labels={'context_numeric': 'Context Length (tokens)', 'count': 'Number of Models'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Context vs Provider
                context_provider = df_context.groupby('provider')['context_numeric'].mean().sort_values(ascending=False).head(10)
                fig = px.bar(
                    x=context_provider.values,
                    y=context_provider.index,
                    orientation='h',
                    title="Average Context Window by Provider",
                    labels={'x': 'Average Context Length (tokens)', 'y': 'Provider'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    def render_comparison_tool(self):
        """Render model comparison tool."""
        st.subheader("🔄 Model Comparison")
        
        if not st.session_state.comparison_list:
            st.info("Add models to comparison using the 📊 Compare button in the model cards above.")
            return
        
        # Get comparison models
        comparison_models = self.data[self.data['id'].isin(st.session_state.comparison_list)]
        
        if comparison_models.empty:
            st.warning("No valid models in comparison list.")
            return
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🗑️ Clear All"):
                st.session_state.comparison_list = []
                st.rerun()
        
        with col1:
            st.write(f"Comparing {len(comparison_models)} models:")
        
        # Display comparison table
        comparison_cols = ['name', 'provider', 'context_window', 'input_pricing', 'output_pricing', 'description']
        display_df = comparison_models[comparison_cols].copy()
        
        # Truncate description for better display
        display_df['description'] = display_df['description'].apply(
            lambda x: str(x)[:100] + '...' if pd.notna(x) and len(str(x)) > 100 else x
        )
        
        st.dataframe(display_df, use_container_width=True)
        
        # Side-by-side detailed comparison
        if len(comparison_models) <= 4:  # Only for small numbers
            st.subheader("📋 Detailed Comparison")
            cols = st.columns(len(comparison_models))
            
            for idx, (_, model) in enumerate(comparison_models.iterrows()):
                with cols[idx]:
                    st.markdown(f"### {model['name']}")
                    st.markdown(f"**Provider:** {model['provider']}")
                    st.markdown(f"**Context:** {model['context_window']}")
                    st.markdown(f"**Input:** {model['input_pricing']}")
                    st.markdown(f"**Output:** {model['output_pricing']}")
                    if model['image_pricing']:
                        st.markdown(f"**Images:** {model['image_pricing']}")
                    
                    if st.button(f"Remove", key=f"remove_{model['id']}"):
                        st.session_state.comparison_list.remove(model['id'])
                        st.rerun()

    def render_favorites(self):
        """Render favorites section."""
        st.subheader("⭐ Your Favorite Models")
        
        if not st.session_state.favorite_models:
            st.info("No favorite models yet. Add some using the ⭐ Favorite button!")
            return
        
        favorite_models = self.data[self.data['id'].isin(st.session_state.favorite_models)]
        
        if favorite_models.empty:
            st.warning("Favorite models not found in current dataset.")
            return
        
        for _, model in favorite_models.iterrows():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"**{model['name']}** by {model['provider']}")
                st.markdown(f"💰 {model['input_pricing']} | 🧠 {model['context_window']}")
                
            with col2:
                if st.button("🗑️", key=f"unfav_{model['id']}", help="Remove from favorites"):
                    st.session_state.favorite_models.remove(model['id'])
                    st.rerun()

    def run(self):
        """Main application runner."""
        self.render_header()
        
        if self.data.empty:
            st.error("❌ No data available. Please ensure 'openrouter_models_api.csv' exists and run the parser.")
            st.markdown("""
            ### 🔧 How to fix this:
            1. Make sure you have run `python openrouter_parser.py`
            2. Choose option 1 (API only) to generate the CSV file
            3. Ensure `openrouter_models_api.csv` is in the same directory as this app
            """)
            return
        
        # Sidebar filters
        filtered_df = self.render_sidebar_filters()
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Models", "📊 Analytics", "🔄 Compare", "⭐ Favorites"])
        
        with tab1:
            self.render_model_cards(filtered_df)
        
        with tab2:
            self.render_analytics_dashboard(filtered_df)
        
        with tab3:
            self.render_comparison_tool()
        
        with tab4:
            self.render_favorites()


def main():
    """Main function to run the Streamlit app."""
    try:
        app = LLMModelFinder()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.markdown("Please ensure all required files are present and try refreshing the page.")


if __name__ == "__main__":
    main()
