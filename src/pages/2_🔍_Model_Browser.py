# pages/2_🔍_Model_Browser.py
import streamlit as st
import pandas as pd
import numpy as np
import math
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from utils import *

# Try to import AgGrid
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False

st.set_page_config(page_title="Model Browser", page_icon="🔍", layout="wide")

# Check if data is available
if 'df' not in st.session_state:
    st.error("❌ Data not loaded. Please go back to the main page first.")
    st.stop()

df = st.session_state.df

@st.cache_resource
def load_embedding_model():
    """Load sentence transformer model for semantic search"""
    try:
        return SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        st.error(f"Error loading embedding model: {e}")
        return None

def semantic_search(query, df, embeddings, model_texts, top_k=5):
    """Perform semantic search on models"""
    if embeddings is None:
        return df.head(top_k)
    
    model = load_embedding_model()
    if model is None:
        return df.head(top_k)
    
    # Get the full dataset for semantic search
    full_df = st.session_state.df  # Original unfiltered dataset
    
    query_embedding = model.encode([query])
    similarities = cosine_similarity(query_embedding, embeddings)[0]
    
    # Get top k most similar models from FULL dataset
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    # Get results from full dataset using correct indices
    results = full_df.iloc[top_indices].copy()
    results['similarity'] = similarities[top_indices]
    
    # Now filter results to match the current filtered dataset
    # This ensures we only return models that match current filters
    if len(df) < len(full_df):  # If df is filtered
        # Get the IDs/identifiers that are in the filtered df
        filtered_ids = set(df['llm_model'].values)  # Assuming 'llm_model' is unique identifier
        
        # Keep only results that are in the filtered dataset
        results = results[results['llm_model'].isin(filtered_ids)]
    
    return results.head(top_k)  # Ensure we don't exceed top_k

def create_model_table_display_aggrid(df):
    """Create AgGrid model table display with advanced features"""
    if not HAS_AGGRID:
        st.warning("⚠️ Install streamlit-aggrid for enhanced table features: `pip install streamlit-aggrid`")
        return create_model_table_display_basic(df)
    
    # Format data for display
    display_cols = ['model_name', 'provider', 'cost', 'llm_model']
    if 'similarity' in df.columns:
        display_cols.append('similarity')
    
    display_df_formatted = df[display_cols].copy()
    col_names = ['Model Name', 'Provider', 'Cost', 'API Identifier']
    if 'similarity' in df.columns:
        col_names.append('Relevance')
    display_df_formatted.columns = col_names
    
    # Create AgGrid
    gb = GridOptionsBuilder.from_dataframe(display_df_formatted)
    
    # Configure pagination and features - SET TO 10 ROWS PER PAGE
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_side_bar()
    gb.configure_selection('single', use_checkbox=True)
    gb.configure_default_column(
        groupable=True,
        value=True,
        enableRowGroup=True,
        editable=False,
        filter=True,
        sortable=True,
        resizable=True
    )
    
    # Configure specific columns
    gb.configure_column('Model Name', pinned='left', width=200, checkboxSelection=True)
    gb.configure_column('Provider', width=120)
    gb.configure_column('Cost', width=120)
    gb.configure_column('API Identifier', width=250)
    
    if 'Relevance' in display_df_formatted.columns:
        gb.configure_column('Relevance', width=100, type=["numericColumn"], precision=3)
    
    # Add custom CSS for better styling
    custom_css = {
        ".ag-header-cell-text": {"font-weight": "bold !important"},
        ".ag-theme-streamlit .ag-header": {"background-color": "#f0f2f6 !important"},
        ".ag-theme-streamlit .ag-row-even": {"background-color": "#fafafa !important"},
    }
    
    gridOptions = gb.build()
    
    # Display the grid
    grid_response = AgGrid(
        display_df_formatted,
        gridOptions=gridOptions,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,
        height=370,  # Reduced height for 10 rows per page
        theme='streamlit',
        custom_css=custom_css,
        allow_unsafe_jscode=True
    )
    
    # Show selection info
    if grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
        # st.info(f"✅ Selected {len(grid_response['selected_rows'])} model(s)")
        st.write(grid_response['selected_rows'])
        
        # Option to export selected rows
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("📥 Export Selected Models"):
                selected_df = pd.DataFrame(grid_response['selected_rows'])
                csv = selected_df.to_csv(index=False)
                st.download_button(
                    label="Download Selected Models CSV",
                    data=csv,
                    file_name=f"selected_models_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="download_selected"
                )
    
    return grid_response

def create_model_table_display_basic(df):
    """Basic fallback table display when AgGrid is not available"""
    total_models = len(df)
    page_size = 20
    total_pages = math.ceil(total_models / page_size)
    
    # Page selection
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        current_page = st.selectbox(
            f"Page (showing {page_size} models per page)",
            range(1, total_pages + 1),
            index=0,
            key="page_selector"
        )
    
    # Calculate slice indices
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_models)
    
    # Display current page info
    st.caption(f"Showing models {start_idx + 1}-{end_idx} of {total_models}")
    
    # Format data for display
    display_df = df.iloc[start_idx:end_idx].copy()
    display_cols = ['model_name', 'provider', 'cost', 'llm_model']
    if 'similarity' in display_df.columns:
        display_cols.append('similarity')
    
    display_df_formatted = display_df[display_cols].copy()
    col_names = ['Model Name', 'Provider', 'Cost', 'API Identifier']
    if 'similarity' in display_df.columns:
        col_names.append('Relevance')
    display_df_formatted.columns = col_names
    
    # Display table
    st.dataframe(
        display_df_formatted,
        use_container_width=True,
        height=600,
        column_config={
            "Model Name": st.column_config.TextColumn(width="medium"),
            "Provider": st.column_config.TextColumn(width="small"),
            "Cost": st.column_config.TextColumn(width="small"),
            "API Identifier": st.column_config.TextColumn(width="large"),
            "Relevance": st.column_config.NumberColumn(width="small", format="%.3f") if 'similarity' in display_df.columns else None
        }
    )
    
    return display_df_formatted

def create_model_table_display(df):
    """Main function that chooses between AgGrid and basic table"""
    if HAS_AGGRID:
        return create_model_table_display_aggrid(df)
    else:
        return create_model_table_display_basic(df)

def main():

    st.markdown("##### 🔍 Model Browser")

    # 4-COLUMN LAYOUT
    col2_1, col2_2, col2_3,  col3 = st.columns([3, 3, 3, 2])


    with col2_1:
        # st.markdown("##### 🔎 Filters")
        # st.markdown("##### 💰 Cost Type")
        cost_filter = st.radio("Cost Type", ["All", "Free Only", "Paid Only"], key="cost_type_filter")
        
        if cost_filter != "Free Only":
            paid_costs = df[df['numeric_cost'] > 0]['numeric_cost']
            if len(paid_costs) > 0:
                min_cost, max_cost = float(paid_costs.min()), float(paid_costs.max())
                cost_range = st.slider(
                    "Cost Range ($/1M tokens)", 
                    min_value=min_cost, 
                    max_value=max_cost, 
                    value=(min_cost, max_cost),
                    format="%.9f",
                    key="cost_range_filter"
                )
            else:
                cost_range = (0, 0)

    with col2_2:
        
        providers = ["All"] + sorted(df['provider'].unique().tolist())
        selected_provider = st.selectbox("Provider", providers, key="provider_filter")
        
        model_search = st.text_input(
            "Model Name", 
            placeholder="e.g., GPT, Claude, Llama",
            key="model_name_search"
        )

    with col2_3:
        # st.markdown("##### 🧠 Semantic Search")
        semantic_query = st.text_area(
            "🧠 Semantic Search:",
            placeholder="e.g., 'affordable models for creative writing'",
            height=120,
            key="semantic_search"
        )
        btn_search = st.button("🔍 Search", key="semantic_search_btn")

    with col3:
        st.markdown("⚙️ Display Options")
        sort_by = st.selectbox("Sort by", ["model_name", "provider", "numeric_cost"], key="sort_by_filter")
        sort_order = st.radio("Sort order", ["Ascending", "Descending"], key="sort_order_filter")

    # Apply all filters
    display_df = df.copy()

    if selected_provider != "All":
        display_df = display_df[display_df['provider'] == selected_provider]

    if cost_filter == "Free Only":
        display_df = display_df[display_df['is_free_bool']]
    elif cost_filter == "Paid Only":
        display_df = display_df[~display_df['is_free_bool']]
        if cost_filter != "Free Only":
            display_df = display_df[
                (display_df['numeric_cost'] >= cost_range[0]) & 
                (display_df['numeric_cost'] <= cost_range[1])
            ]

    if model_search:
        mask = (
            display_df['model_name'].str.contains(model_search, case=False, na=False) |
            display_df['llm_model'].str.contains(model_search, case=False, na=False)
        )
        display_df = display_df[mask]

    # Apply semantic search
    if semantic_query and 'embeddings' in st.session_state and btn_search:
        with st.spinner("🔍 Searching..."):
            semantic_results = semantic_search(semantic_query, display_df, st.session_state.embeddings, st.session_state.model_texts, top_k=min(100, len(display_df)))
            st.success(f"Found {len(semantic_results)} relevant models")
            display_df = semantic_results

    st.markdown(f"**Showing {len(display_df)} models**")

    if len(display_df) == 0:
        st.warning("No models match your current filters. Try adjusting the criteria.")
    else:
        # Sort data
        ascending = sort_order == "Ascending"
        display_df = display_df.sort_values(sort_by, ascending=ascending)
        
        # Create table display
        table_result = create_model_table_display(display_df)
        
        # Export options
        st.markdown("##### 📥 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            st.download_button(
                label="Download All Filtered Results (CSV)",
                data=display_df.to_csv(index=False),
                file_name=f"openrouter_models_filtered_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if HAS_AGGRID:
                st.markdown("*Use checkboxes in table to select specific models for export*")
            else:
                st.markdown("*Install streamlit-aggrid for selective export functionality*")

if __name__ == "__main__":
    show_sidebar()
    main()