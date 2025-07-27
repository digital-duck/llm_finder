
import streamlit as st
import pandas as pd

# Try to import AgGrid, fallback if not available
try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
    HAS_AGGRID = True
except ImportError:
    HAS_AGGRID = False
    
CHART_HEIGHT = 600

# helper function 
def format_cost(cost):
    """Format cost for display"""
    if cost == 0:
        return "Free"
    elif cost < 0.000001:
        return f"${cost:.9f}/1M"
    elif cost < 0.001:
        return f"${cost:.6f}/1M"
    else:
        return f"${cost:.3f}/1M"
    
# Extract numeric cost for analysis
def extract_cost(cost_str):
    if pd.isna(cost_str) or '$0/1M' in str(cost_str):
        return 0.0
    # match = re.search(r'\$([0-9.]+)', str(cost_str))
    # return float(match.group(1)) if match else 0.0
    float_cost = 0.0
    try:
        float_cost = float(cost_str.replace('$', '').replace('/1M', '').strip())
    except ValueError as e:
        print(f"Error parsing cost '{cost_str}': {e}")
    return 0 if float_cost < 0 else float_cost


def show_sidebar():
    """Render the sidebar with app info and navigation"""
    with st.sidebar:
        # Navigation help
        st.markdown("""
        Explore and compare 300+ AI models (50+ free) from 60+ providers at [OpenRouter](https://openrouter.ai/models).         Find the perfect model for your needs based on cost / provider / capability.
        - **💬 AI Chat**: Ask questions about models
        - **🔍 Model Browser**: Search and filter models  
        - **📊 Overview**: Key statistics and charts
        - **📈 Analytics**: Advanced analysis
        - **💡 Recommend**: Insights and recommendations""")

        df = st.session_state.get('df')
        model_csv_path = st.session_state.get('model_csv_path')
        
        st.markdown("---")
        st.markdown(f"""
        **Model Stats:**
        - 📊 Total Models: {len(df)}
        - 🏢 Providers: {df['provider'].nunique()}
        - 🆓 Free Models: {len(df[df['is_free_bool']])}
        - 💰 Paid Models: {len(df[~df['is_free_bool']])}

        Source: '{model_csv_path}'
        """)

        if not HAS_AGGRID:
            st.info("💡 **Tip**: Install `streamlit-aggrid` for enhanced table features!")


from .data_loader import OpenRouter