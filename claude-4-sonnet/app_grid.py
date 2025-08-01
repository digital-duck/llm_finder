import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
from st_aggrid.shared import ColumnsAutoSizeMode
import numpy as np
import json
import re
from datetime import datetime
from collections import Counter
import os

# Page configuration
st.set_page_config(
    page_title="🔍 LLM Model Finder Pro (Grid View)",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .selected-model-card {
        background: linear-gradient(145deg, #f0f2f6, #ffffff);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
        border-left: 5px solid #1f77b4;
    }
    .model-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .model-provider {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 1rem;
    }
    .detail-section {
        margin: 1rem 0;
    }
    .detail-label {
        font-weight: bold;
        color: #333;
        display: inline-block;
        width: 120px;
    }
    .detail-value {
        color: #555;
    }
    .price-free {
        background: linear-gradient(45deg, #51cf66, #40c057);
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 15px;
        font-weight: bold;
    }
    .price-paid {
        background: linear-gradient(45deg, #ff6b6b, #ee5a52);
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 15px;
        font-weight: bold;
    }
    .context-badge {
        background: linear-gradient(45deg, #845ef7, #7048e8);
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 15px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


class LLMModelFinderGrid:
    def __init__(self):
        self.initialize_session_state()
        self.data = self.load_model_data()

    def initialize_session_state(self):
        """Initialize session state variables."""
        if 'selected_model' not in st.session_state:
            st.session_state.selected_model = None
        if 'favorite_models' not in st.session_state:
            st.session_state.favorite_models = set()
        if 'grid_key' not in st.session_state:
            st.session_state.grid_key = 0

    @st.cache_data
    def load_model_data(_self):
        """Load model data from CSV file."""
        try:
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
        st.markdown('<h1 class="main-header">🔍 LLM Model Finder Pro (Grid View)</h1>', unsafe_allow_html=True)
        st.markdown("**Discover, compare, and choose the perfect LLM with advanced grid interface**")
        
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
        """Render sidebar with filters and return filtered data."""
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
        
        # Search functionality will be handled in the grid itself
        
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
            
            # Remove helper column
            if 'context_numeric' in filtered_df.columns:
                filtered_df = filtered_df.drop('context_numeric', axis=1)
        
        # Show filter results
        st.sidebar.markdown(f"**Found: {len(filtered_df)} models**")
        
        # Grid refresh button
        if st.sidebar.button("🔄 Refresh Grid"):
            st.session_state.grid_key += 1
            st.session_state.selected_model = None
        
        return filtered_df

    def create_grid_options(self, df):
        """Create AgGrid options with enhanced features."""
        gb = GridOptionsBuilder.from_dataframe(df)
        
        # Configure grid options
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)  # Set to 10 rows
        gb.configure_side_bar()
        gb.configure_selection(
            selection_mode="single",
            use_checkbox=True,  # Add checkbox in first column
            rowMultiSelectWithClick=False,
            suppressRowDeselection=False
        )
        gb.configure_default_column(
            groupable=True,
            value=True,
            enableRowGroup=True,
            aggFunc="sum",
            editable=False,
            filter=True,
            sortable=True,
            resizable=True
        )
        
        # Configure specific columns
        gb.configure_column("id", hide=True)  # Hide ID column
        
        # Model name with hyperlink using JsCode
        gb.configure_column(
            "name", 
            header_name="Model Name",
            width=300,
            cellRenderer=JsCode("""
                class UrlCellRenderer {
                    init(params) {
                        this.eGui = document.createElement('div');
                        if (params.data.model_url && params.data.model_url.trim() !== '') {
                            this.eGui.innerHTML = '<a href="' + params.data.model_url + '" target="_blank" style="color: #1f77b4; text-decoration: none; font-weight: bold;">' + params.value + '</a>';
                        } else {
                            this.eGui.innerHTML = '<span style="font-weight: bold;">' + params.value + '</span>';
                        }
                    }
                    getGui() {
                        return this.eGui;
                    }
                }
            """),
            tooltipField="name"
        )
        
        # Provider with hyperlink using JsCode
        gb.configure_column(
            "provider", 
            header_name="Provider",
            width=150,
            cellRenderer=JsCode("""
                class ProviderUrlCellRenderer {
                    init(params) {
                        this.eGui = document.createElement('div');
                        if (params.data.provider_url && params.data.provider_url.trim() !== '') {
                            this.eGui.innerHTML = '<a href="' + params.data.provider_url + '" target="_blank" style="color: #1f77b4; text-decoration: none; font-weight: bold;">' + params.value + '</a>';
                        } else {
                            this.eGui.innerHTML = '<span style="color: #1f77b4; font-weight: bold;">' + params.value + '</span>';
                        }
                    }
                    getGui() {
                        return this.eGui;
                    }
                }
            """)
        )
        
        gb.configure_column(
            "context_window", 
            header_name="Context",
            width=120,
            cellStyle={"text-align": "center"}
        )
        
        # Input pricing - display text only, no HTML styling
        gb.configure_column(
            "input_pricing", 
            header_name="Input Price",
            width=130,
            cellStyle={"text-align": "center"}
        )
        
        # Output pricing - display text only, no HTML styling
        gb.configure_column(
            "output_pricing", 
            header_name="Output Price",
            width=130,
            cellStyle={"text-align": "center"}
        )
        
        gb.configure_column(
            "description", 
            header_name="Description",
            width=400,
            tooltipField="description",
            cellRenderer=JsCode("""
                class DescriptionCellRenderer {
                    init(params) {
                        this.eGui = document.createElement('div');
                        if (params.value && params.value.length > 100) {
                            this.eGui.innerHTML = params.value.substring(0, 100) + '...';
                        } else {
                            this.eGui.innerHTML = params.value || '';
                        }
                    }
                    getGui() {
                        return this.eGui;
                    }
                }
            """)
        )
        
        # Hide some columns by default but keep them accessible
        gb.configure_column("model_url", hide=True)
        gb.configure_column("provider_url", hide=True)
        gb.configure_column("image_pricing", hide=True)
        
        # Enable search across all columns
        gb.configure_grid_options(
            enableFilter=True,
            enableSorting=True,
            enableColResize=True,
            enableRangeSelection=True,
            animateRows=True,
            rowSelection="single"
        )
        
        return gb.build()

    def render_model_grid(self, df):
        """Render the main model grid using AgGrid."""
        st.subheader(f"📊 Models Grid ({len(df)} models)")
        
        if df.empty:
            st.info("No models match your criteria. Try adjusting the filters.")
            return None
        
        # Prepare data for grid (create a copy to avoid modifying original)
        grid_df = df.copy()
        
        # Ensure all required columns exist and handle NaN values
        required_columns = ['id', 'name', 'provider', 'model_url', 'provider_url', 
                          'context_window', 'input_pricing', 'output_pricing', 'description']
        
        for col in required_columns:
            if col not in grid_df.columns:
                grid_df[col] = ''
            else:
                grid_df[col] = grid_df[col].fillna('')
        
        # Reset index to ensure we have a clean index
        grid_df = grid_df.reset_index(drop=True)
        
        # Create grid options
        grid_options = self.create_grid_options(grid_df)
        
        # Custom CSS for the grid
        custom_css = {
            ".ag-theme-streamlit": {
                "--ag-grid-size": "6px",
                "--ag-list-item-height": "6px",
            },
            ".ag-theme-streamlit .ag-row": {
                "font-size": "14px"
            },
            ".ag-theme-streamlit .ag-header-cell": {
                "font-weight": "bold",
                "color": "#1f77b4"
            }
        }
        
        try:
            # Render the grid
            grid_response = AgGrid(
                grid_df,
                gridOptions=grid_options,
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,  # Back to this mode
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
                theme='streamlit',
                key=f"models_grid_{st.session_state.grid_key}",
                allow_unsafe_jscode=True,
                custom_css=custom_css,
                height=500,
                reload_data=False
            )
            
            # Multiple ways to detect selection
            selected_model = None
            
            # Method 1: Check selected_rows
            if 'selected_rows' in grid_response and grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
                selected_row = grid_response['selected_rows'][0]
                selected_model = dict(selected_row)
                st.success("✅ Model selected via selected_rows!")  # Debug message
            
            # Method 2: Check if any row selection exists in the data
            elif 'data' in grid_response:
                # Look through the grid data to see if any row has selection indicator
                data_df = grid_response['data']
                if hasattr(data_df, 'index') and len(data_df) > 0:
                    # For now, let's try a different approach - detect row clicks
                    pass
            
            # Method 3: Use session state from previous selection
            if selected_model is None and st.session_state.selected_model is not None:
                selected_model = st.session_state.selected_model
            
            # If we found a selected model, clean and store it
            if selected_model:
                # Clean the selected model data
                selected_model_dict = {}
                for key, value in selected_model.items():
                    if pd.isna(value):
                        selected_model_dict[key] = ''
                    else:
                        selected_model_dict[key] = str(value) if value is not None else ''
                
                st.session_state.selected_model = selected_model_dict
                return selected_model_dict
            else:
                # Show helpful message
                if st.session_state.selected_model is None:
                    st.info("👆 Click the checkbox next to a model to select it and view details below")
                return st.session_state.selected_model
                
        except Exception as e:
            st.error(f"Grid error: {str(e)}")
            st.info("There was an issue with the grid. Please try refreshing the page.")
            return None

    def render_selected_model_details(self, selected_model):
        """Render detailed view of selected model."""
        if not selected_model:
            return
        
        try:
            st.markdown("---")
            st.subheader("📋 Selected Model Details")
            
            # Get values safely
            name = selected_model.get('name', 'Unknown Model')
            provider = selected_model.get('provider', 'Unknown Provider')
            description = selected_model.get('description', 'No description available')
            model_id = selected_model.get('id', 'N/A')
            context_window = selected_model.get('context_window', 'N/A')
            input_pricing = selected_model.get('input_pricing', 'N/A')
            output_pricing = selected_model.get('output_pricing', 'N/A')
            image_pricing = selected_model.get('image_pricing', '')
            model_url = selected_model.get('model_url', '')
            provider_url = selected_model.get('provider_url', '')
            
            # Model card with enhanced styling
            st.markdown(f"""
            <div class="selected-model-card">
                <div class="model-title">{name}</div>
                <div class="model-provider">by {provider}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Details in columns
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Description
                st.markdown("### 📝 Description")
                if description and description != 'No description available' and description.strip():
                    st.markdown(description)
                else:
                    st.markdown("*No description available*")
                
                # Technical details
                st.markdown("### ⚙️ Technical Details")
                
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown(f"**Model ID:** `{model_id}`")
                    st.markdown(f"**Provider:** {provider}")
                    st.markdown(f"**Context Window:** {context_window}")
                
                with detail_col2:
                    # Pricing with styled badges
                    st.markdown("**Input Pricing:**")
                    if input_pricing == 'Free':
                        st.markdown('<span class="price-free">Free</span>', unsafe_allow_html=True)
                    elif input_pricing and input_pricing != 'N/A':
                        st.markdown(f'<span class="price-paid">{input_pricing}</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('N/A')
                    
                    st.markdown("**Output Pricing:**")
                    if output_pricing == 'Free' or not output_pricing or output_pricing == 'N/A':
                        st.markdown('<span class="price-free">Free</span>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<span class="price-paid">{output_pricing}</span>', unsafe_allow_html=True)
                    
                    if image_pricing and image_pricing.strip():
                        st.markdown("**Image Pricing:**")
                        st.markdown(f'<span class="price-paid">{image_pricing}</span>', unsafe_allow_html=True)
            
            with col2:
                # Action buttons
                st.markdown("### 🎯 Actions")
                
                # Favorite button
                is_favorite = model_id in st.session_state.favorite_models
                
                if is_favorite:
                    if st.button("💖 Remove from Favorites", key="unfavorite_btn"):
                        st.session_state.favorite_models.remove(model_id)
                        st.success("Removed from favorites!")
                        st.rerun()
                else:
                    if st.button("⭐ Add to Favorites", key="favorite_btn"):
                        st.session_state.favorite_models.add(model_id)
                        st.success("Added to favorites!")
                        st.rerun()
                
                # External links
                if model_url and model_url.strip():
                    st.markdown(f"🔗 [View Model Page]({model_url})")
                
                if provider_url and provider_url.strip():
                    st.markdown(f"🏢 [View Provider Page]({provider_url})")
                
                # Copy model ID
                if st.button("📋 Copy Model ID", key="copy_id_btn"):
                    st.code(model_id)
                    st.success("Model ID displayed above!")
                
                # Model statistics (if we have context info)
                if context_window and context_window != 'N/A':
                    st.markdown("### 📊 Quick Stats")
                    # Extract number from context window
                    context_match = re.search(r'(\d+)', context_window)
                    if context_match:
                        try:
                            context_num = int(context_match.group(1))
                            st.metric("Context Tokens", f"{context_num:,}")
                            
                            # Estimate words (rough: 1 token ≈ 0.75 words)
                            est_words = int(context_num * 0.75)
                            st.metric("Est. Words", f"{est_words:,}")
                        except ValueError:
                            pass
                            
        except Exception as e:
            st.error(f"Error displaying model details: {str(e)}")
            st.info("Please try selecting the model again.")

    def render_favorites_section(self):
        """Render favorites section."""
        st.subheader("⭐ Your Favorite Models")
        
        if not st.session_state.favorite_models:
            st.info("No favorite models yet. Select models from the grid and add them to favorites!")
            return
        
        # Get favorite models data
        favorite_models = self.data[self.data['id'].isin(st.session_state.favorite_models)]
        
        if favorite_models.empty:
            st.warning("Favorite models not found in current dataset.")
            return
        
        # Display favorites in a compact format
        for _, model in favorite_models.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.markdown(f"**{model['name']}**")
                st.markdown(f"*by {model['provider']}*")
            
            with col2:
                st.markdown(f"💰 {model['input_pricing']}")
                st.markdown(f"🧠 {model['context_window']}")
            
            with col3:
                if st.button("🗑️", key=f"remove_fav_{model['id']}", help="Remove from favorites"):
                    st.session_state.favorite_models.remove(model['id'])
                    st.rerun()
                
                if st.button("👁️", key=f"view_fav_{model['id']}", help="View details"):
                    st.session_state.selected_model = model.to_dict()
                    st.rerun()

    def render_analytics_summary(self, df):
        """Render a quick analytics summary."""
        if df.empty:
            return
        
        st.subheader("📈 Quick Analytics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Top provider
            top_provider = df['provider'].value_counts().index[0] if not df.empty else "N/A"
            top_count = df['provider'].value_counts().iloc[0] if not df.empty else 0
            st.metric("Top Provider", f"{top_provider} ({top_count})")
        
        with col2:
            # Free model percentage
            free_count = len(df[df['input_pricing'] == 'Free'])
            free_pct = (free_count / len(df) * 100) if len(df) > 0 else 0
            st.metric("Free Models", f"{free_pct:.1f}%")
        
        with col3:
            # Average context (if available)
            context_nums = df['context_window'].str.extract(r'(\d+)').astype(float)
            if not context_nums.empty:
                avg_context = context_nums.mean().iloc[0]
                st.metric("Avg Context", f"{avg_context/1000:.0f}K")

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
        
        # Main content
        tab1, tab2 = st.tabs(["📊 Models Grid", "⭐ Favorites"])
        
        with tab1:
            # Quick analytics
            self.render_analytics_summary(filtered_df)
            
            # Add manual model selector as backup
            st.subheader("🎯 Quick Model Selector")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Dropdown to manually select a model
                model_options = ["Select a model..."] + [f"{row['name']} ({row['provider']})" for _, row in filtered_df.iterrows()]
                selected_option = st.selectbox("Or select directly:", model_options, key="manual_selector")
                
                if selected_option != "Select a model...":
                    # Find the selected model
                    for _, row in filtered_df.iterrows():
                        if f"{row['name']} ({row['provider']})" == selected_option:
                            selected_model_dict = {}
                            for key, value in row.items():
                                if pd.isna(value):
                                    selected_model_dict[key] = ''
                                else:
                                    selected_model_dict[key] = str(value) if value is not None else ''
                            st.session_state.selected_model = selected_model_dict
                            break
            
            with col2:
                if st.button("🗑️ Clear Selection"):
                    st.session_state.selected_model = None
                    st.rerun()
            
            # Main grid
            selected_model = self.render_model_grid(filtered_df)
            
            # Selected model details
            self.render_selected_model_details(selected_model)
        
        with tab2:
            self.render_favorites_section()


def main():
    """Main function to run the Streamlit app."""
    try:
        app = LLMModelFinderGrid()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.markdown("Please ensure all required files are present and try refreshing the page.")


if __name__ == "__main__":
    main()
