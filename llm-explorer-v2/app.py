import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="OpenRouter LLM Model Explorer",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .category-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .free-badge {
        background-color: #10b981;
        color: white;
    }
    .paid-badge {
        background-color: #f59e0b;
        color: white;
    }
    .unknown-badge {
        background-color: #6b7280;
        color: white;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .user-guide {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    """
    Load model data from CSV file
    """
    try:
        df = pd.read_csv('openrouter_models.csv')
        return df
    except FileNotFoundError:
        st.error("Model data file not found. Please run the scraper first.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def create_aggrid_config(df):
    """
    Create AgGrid configuration with search and filter options
    """
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configure grid options
    gb.configure_default_column(
        filterable=True,
        sortable=True,
        resizable=True,
        wrapText=True,
        autoHeight=True
    )
    
    # Configure specific columns
    gb.configure_column(
        "name",
        header_name="Model Name",
        width=200,
        filter='agTextColumnFilter',
        filter_params={'filterOptions': ['contains', 'notContains', 'startsWith', 'endsWith']}
    )
    
    gb.configure_column(
        "category",
        header_name="Category",
        width=120,
        filter='agSetColumnFilter',
        cellStyle={'styleConditions': [
            {'condition': 'params.value == "Free"', 'style': {'backgroundColor': '#d1fae5', 'color': '#065f46'}},
            {'condition': 'params.value == "Paid"', 'style': {'backgroundColor': '#fed7aa', 'color': '#92400e'}},
            {'condition': 'params.value == "Unknown"', 'style': {'backgroundColor': '#e5e7eb', 'color': '#374151'}}
        ]}
    )
    
    gb.configure_column(
        "description",
        header_name="Description",
        width=300,
        filter='agTextColumnFilter',
        autoHeight=True
    )
    
    gb.configure_column(
        "pricing",
        header_name="Pricing",
        width=150,
        filter='agTextColumnFilter'
    )
    
    gb.configure_column(
        "provider",
        header_name="Provider",
        width=150,
        filter='agSetColumnFilter'
    )
    
    gb.configure_column(
        "context_length",
        header_name="Context Length",
        width=130,
        filter='agTextColumnFilter'
    )
    
    # Configure grid features
    gb.configure_selection(
        selection_mode='single',
        use_checkbox=False,
        pre_selected_rows=[]
    )
    
    gb.configure_side_bar(
        filters_panel=True,
        columns_panel=True
    )
    
    gridOptions = gb.build()
    
    return gridOptions

def create_visualizations(df):
    """
    Create interactive visualizations
    """
    # Category distribution
    category_counts = df['category'].value_counts()
    
    fig_category = px.pie(
        values=category_counts.values,
        names=category_counts.index,
        title="Model Distribution by Category",
        color=category_counts.index,
        color_discrete_map={
            'Free': '#10b981',
            'Paid': '#f59e0b',
            'Unknown': '#6b7280'
        }
    )
    fig_category.update_layout(
        showlegend=True,
        legend_title_text="Category"
    )
    
    # Provider distribution
    if 'provider' in df.columns and df['provider'].notna().any():
        provider_counts = df['provider'].value_counts().head(10)
        fig_provider = px.bar(
            x=provider_counts.values,
            y=provider_counts.index,
            orientation='h',
            title="Top 10 Providers",
            labels={'x': 'Number of Models', 'y': 'Provider'}
        )
        fig_provider.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=400
        )
    else:
        fig_provider = None
    
    return fig_category, fig_provider

def display_user_guide():
    """
    Display user guide for exploring and selecting models
    """
    st.markdown("""
    <div class="user-guide">
        <h3>📚 User Guide: How to Explore and Select LLM Models</h3>
        
        <h4>🔍 **Searching and Filtering**</h4>
        <ul>
            <li><strong>Text Search:</strong> Use the search bar to find models by name, description, or any text field</li>
            <li><strong>Column Filters:</strong> Click the filter icon (≡) on any column header to filter by specific values</li>
            <li><strong>Category Filter:</strong> Filter models by Free, Paid, or Unknown pricing categories</li>
            <li><strong>Provider Filter:</strong> Filter models by specific providers (OpenAI, Anthropic, etc.)</li>
        </ul>
        
        <h4>📊 **Understanding the Data**</h4>
        <ul>
            <li><strong>Model Name:</strong> The official name of the LLM model</li>
            <li><strong>Category:</strong> 
                <span class="category-badge free-badge">Free</span> - No cost models
                <span class="category-badge paid-badge">Paid</span> - Requires payment
                <span class="category-badge unknown-badge">Unknown</span> - Pricing information not available
            </li>
            <li><strong>Description:</strong> Brief description of the model's capabilities</li>
            <li><strong>Pricing:</strong> Cost information for using the model</li>
            <li><strong>Provider:</strong> Company or organization that created the model</li>
            <li><strong>Context Length:</strong> Maximum input tokens the model can process</li>
        </ul>
        
        <h4>🎯 **Selecting the Right Model**</h4>
        <ul>
            <li><strong>For Testing/Learning:</strong> Start with <strong>Free</strong> models to experiment without cost</li>
            <li><strong>For Production:</strong> Consider <strong>Paid</strong> models for better performance and reliability</li>
            <li><strong>Check Context Length:</strong> Larger context lengths are better for processing long documents</li>
            <li><strong>Consider Provider:</strong> Some providers specialize in specific types of models</li>
            <li><strong>Read Descriptions:</strong> Look for models that match your specific use case</li>
        </ul>
        
        <h4>💡 **Tips for Model Selection**</h4>
        <ul>
            <li><strong>Start Small:</strong> Begin with smaller, free models to understand your requirements</li>
            <li><strong>Compare Performance:</strong> Test multiple models to see which works best for your needs</li>
            <li><strong>Monitor Costs:</strong> Keep track of usage costs when using paid models</li>
            <li><strong>Stay Updated:</strong> New models are frequently added, so check back regularly</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def main():
    """
    Main Streamlit application
    """
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🤖 OpenRouter LLM Model Explorer</h1>
        <p>Explore and compare 300+ LLM models available on OpenRouter.ai</p>
        <p><em>Last updated: {}</em></p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    if df is None:
        st.stop()
    
    # Sidebar with filters and information
    with st.sidebar:
        st.header("🔧 Controls & Info")
        
        # Data refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()
        
        # Category filter
        st.subheader("Filter by Category")
        categories = ['All'] + sorted(df['category'].unique().tolist())
        selected_category = st.selectbox("Select Category:", categories)
        
        # Provider filter
        if 'provider' in df.columns:
            providers = ['All'] + sorted([p for p in df['provider'].unique() if pd.notna(p) and p != ''])
            selected_provider = st.selectbox("Select Provider:", providers)
        else:
            selected_provider = 'All'
        
        # Search functionality
        st.subheader("Search Models")
        search_term = st.text_input("Search by name or description:")
        
        # Show user guide button
        if st.button("📖 Show User Guide"):
            st.session_state['show_guide'] = not st.session_state.get('show_guide', False)
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    if selected_provider != 'All' and 'provider' in df.columns:
        filtered_df = filtered_df[filtered_df['provider'] == selected_provider]
    
    if search_term:
        search_mask = (
            filtered_df['name'].str.contains(search_term, case=False, na=False) |
            filtered_df['description'].str.contains(search_term, case=False, na=False)
        )
        filtered_df = filtered_df[search_mask]
    
    # Main content area
    # Show user guide if requested
    if st.session_state.get('show_guide', False):
        display_user_guide()
        st.markdown("---")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(df)}</h3>
            <p>Total Models</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        free_count = len(df[df['category'] == 'Free'])
        st.markdown(f"""
        <div class="metric-card">
            <h3>{free_count}</h3>
            <p>Free Models</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        paid_count = len(df[df['category'] == 'Paid'])
        st.markdown(f"""
        <div class="metric-card">
            <h3>{paid_count}</h3>
            <p>Paid Models</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{len(filtered_df)}</h3>
            <p>Filtered Results</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Visualizations
    st.subheader("📊 Model Analytics")
    col1, col2 = st.columns(2)
    
    with col1:
        fig_category, fig_provider = create_visualizations(df)
        st.plotly_chart(fig_category, use_container_width=True)
    
    with col2:
        if fig_provider:
            st.plotly_chart(fig_provider, use_container_width=True)
        else:
            st.info("Provider data not available in the current dataset")
    
    # Data table with AgGrid
    st.subheader(f"📋 Model Data ({len(filtered_df)} models)")
    
    if not filtered_df.empty:
        # Prepare data for AgGrid
        display_df = filtered_df.copy()
        
        # Add some formatting
        if 'category' in display_df.columns:
            display_df['category'] = display_df['category'].apply(
                lambda x: f'<span class="category-badge {x.lower()}-badge">{x}</span>'
            )
        
        # Create grid options
        gridOptions = create_aggrid_config(display_df)
        
        # Display AgGrid
        grid_response = AgGrid(
            display_df,
            gridOptions=gridOptions,
            height=600,
            width='100%',
            enable_enterprise_modules=True,
            allow_unsafe_jscode=True,
            update_mode='MODEL_CHANGED'
        )
        
        # Show selected model details
        if grid_response['selected_rows']:
            selected_model = grid_response['selected_rows'][0]
            st.subheader("🎯 Selected Model Details")
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Name:**", selected_model.get('name', 'N/A'))
                st.write("**Category:**", selected_model.get('category', 'N/A'))
                st.write("**Provider:**", selected_model.get('provider', 'N/A'))
                st.write("**Context Length:**", selected_model.get('context_length', 'N/A'))
            
            with col2:
                st.write("**Pricing:**", selected_model.get('pricing', 'N/A'))
                st.write("**Architecture:**", selected_model.get('architecture', 'N/A'))
                if 'website' in selected_model and selected_model['website']:
                    st.write("**Website:**", f"[Visit]({selected_model['website']})")
            
            if 'description' in selected_model:
                st.write("**Description:**", selected_model['description'])
    
    else:
        st.warning("No models match your current filters. Try adjusting your search criteria.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6b7280;">
        <p>Data sourced from OpenRouter.ai | Last scraped: {}</p>
        <p>💡 Tip: Click the filter icons in the table headers for advanced filtering options</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()