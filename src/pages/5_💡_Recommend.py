# pages/5_💡_Recommend.py
import streamlit as st
import pandas as pd

from utils import *

st.set_page_config(page_title="Recommendations", page_icon="💡", layout="wide")

# Check if data is available
if 'df' not in st.session_state:
    st.error("❌ Data not loaded. Please go back to the main page first.")
    st.stop()

df = st.session_state.df


def create_selection_guide_aggrid():
    """Create an enhanced selection guide using AgGrid"""
    selection_guide_data = [
        {"Use Case": "💬 Chatbots & Customer Support", "Recommended": "OpenAI GPT models, Anthropic Claude"},
        {"Use Case": "📝 Content Generation", "Recommended": "Mistral, Meta Llama, Qwen"},
        {"Use Case": "💻 Code Generation", "Recommended": "DeepSeek Coder, OpenAI GPT-4"},
        {"Use Case": "🔍 Research & Analysis", "Recommended": "Google Gemini, Anthropic Claude"},
        {"Use Case": "🌍 Multilingual Tasks", "Recommended": "Qwen models, Google Gemini"},
        {"Use Case": "📊 Data Analysis", "Recommended": "OpenAI GPT-4, Anthropic Claude"},
        {"Use Case": "🎨 Creative Writing", "Recommended": "Meta Llama, Mistral Large"}
    ]
    
    guide_df = pd.DataFrame(selection_guide_data)
    
    if HAS_AGGRID:
        gb = GridOptionsBuilder.from_dataframe(guide_df)
        gb.configure_default_column(
            groupable=False,
            value=True,
            enableRowGroup=False,
            editable=False,
            wrapText=True,
            autoHeight=True,
            filter=False,
            sortable=False
        )
        gb.configure_column('Use Case', width=200, pinned='left')
        gb.configure_column('Recommended', width=400, wrapText=True, autoHeight=True)
        
        gridOptions = gb.build()
        
        grid_response = AgGrid(
            guide_df,
            gridOptions=gridOptions,
            data_return_mode=DataReturnMode.AS_INPUT,
            update_mode=GridUpdateMode.NO_UPDATE,
            fit_columns_on_grid_load=True,
            height=300,
            theme='streamlit'
        )
        
        return grid_response
    else:
        st.table(guide_df)
        return guide_df

def main():
    st.markdown("##### 💡 Key Insights & Recommendations")

    # Analysis insights
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 🏆 Top Performers")
        
        if len(df) > 0:
            top_provider = df['provider'].value_counts().index[0]
            st.success(f"**Most Models**: {top_provider} ({df['provider'].value_counts().iloc[0]} models)")
            
            free_models = df[df['is_free_bool']]
            if len(free_models) > 0:
                free_leader = free_models['provider'].value_counts().index[0]
                free_count = free_models['provider'].value_counts().iloc[0]
                st.info(f"**Most Free Models**: {free_leader} ({free_count} free models)")
            
            paid_models = df[df['numeric_cost'] > 0]
            if len(paid_models) > 0:
                cheapest_idx = paid_models['numeric_cost'].idxmin()
                cheapest = paid_models.loc[cheapest_idx]
                st.success(f"**Cheapest Model**: {cheapest['model_name']} by {cheapest['provider']} ({cheapest['cost']})")
            else:
                st.info("**No paid models found in dataset**")
        else:
            st.warning("No data available")

    with col2:
        st.markdown("##### 📊 Market Analysis")
        
        if len(df) > 0:
            total_models = len(df)
            free_percentage = (len(df[df['is_free_bool']]) / total_models) * 100
            
            st.metric("Free Model Ratio", f"{free_percentage:.1f}%")
            
            paid_df = df[df['numeric_cost'] > 0]
            if len(paid_df) > 0:
                cheap_threshold = paid_df['numeric_cost'].quantile(0.25)
                expensive_threshold = paid_df['numeric_cost'].quantile(0.75)
                
                cheap_count = len(paid_df[paid_df['numeric_cost'] <= cheap_threshold])
                mid_count = len(paid_df[(paid_df['numeric_cost'] > cheap_threshold) & (paid_df['numeric_cost'] <= expensive_threshold)])
                expensive_count = len(paid_df[paid_df['numeric_cost'] > expensive_threshold])
                
                st.markdown("**Cost Tiers (Paid Models):**")
                st.write(f"• Budget (≤${cheap_threshold:.6f}/1M): {cheap_count} models")
                st.write(f"• Mid-tier: {mid_count} models")
                st.write(f"• Premium (>${expensive_threshold:.6f}/1M): {expensive_count} models")
            else:
                st.info("No paid models for cost tier analysis")

    # Recommendations
    st.markdown("##### 🎯 Recommendations")

    recommendations = [
        "**For Cost-Conscious Users**: Consider free models from Google, Qwen, or DeepSeek - they offer excellent value",
        "**For Production Use**: OpenAI and Anthropic provide reliable, well-documented models with consistent performance",
        "**For Experimentation**: Mistral offers the widest variety (35 models) - great for testing different capabilities",
        "**Budget-Friendly Paid**: Look into Agentica models for extremely low costs (sub $0.000001/1M)",
        "**Enterprise Ready**: Microsoft and Google models often provide better integration with business tools"
    ]

    for rec in recommendations:
        st.markdown(f"• {rec}")

    # Model selection guide
    st.markdown("##### 🛠️ Model Selection Guide")
    create_selection_guide_aggrid()

    # Additional recommendation sections
    st.markdown("---")
    st.markdown("##### 🚀 Getting Started Tips")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🆓 Free Tier Strategy**")
        st.info("""
        Start with free models to:
        - Test your application logic
        - Understand model capabilities
        - Estimate token usage
        - Compare different providers
        """)

    with col2:
        st.markdown("**💰 Cost Optimization**")
        st.info("""
        To minimize costs:
        - Use smaller models for simple tasks
        - Implement caching for repeated queries
        - Monitor token usage patterns
        - Consider model switching based on complexity
        """)

    st.markdown("##### 🔄 Migration Path")
    st.success("""
    **Recommended Development Flow:**
    1. **Prototype** with free models (Qwen, Google, DeepSeek)
    2. **Test** with mid-tier paid models for accuracy comparison
    3. **Scale** with premium models (OpenAI, Anthropic) for production
    4. **Optimize** by mixing models based on task complexity
    """)

    # Best practices
    st.markdown("##### ✅ Best Practices")

    best_practices = [
        "**Always test with representative data** before committing to a model",
        "**Monitor costs closely** - set up alerts for unexpected usage spikes",
        "**Keep fallback options** - have 2-3 models ready for different scenarios",
        "**Document model performance** - track accuracy, speed, and cost metrics",
        "**Stay updated** - model capabilities and pricing change frequently"
    ]

    for practice in best_practices:
        st.markdown(f"• {practice}")

    st.markdown("---")
    st.info("💡 **Pro Tip**: Use this tool's Model Browser to bookmark your top 3-5 models for quick comparison and testing!")



if __name__ == "__main__": 
    show_sidebar()
    main()