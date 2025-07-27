# pages/4_📈_Analytics.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

st.set_page_config(page_title="Analytics", page_icon="📈", layout="wide")

# Check if data is available
if 'df' not in st.session_state:
    st.error("❌ Data not loaded. Please go back to the main page first.")
    st.stop()

df = st.session_state.df

def main():

    st.markdown("##### 📈 Analytics")

    col1, col2 = st.columns(2)

    with col1:
        # Provider cost comparison - Fixed version
        provider_stats = df.groupby('provider').agg({
            'numeric_cost': ['mean', 'min', 'max', 'count'],
            'is_free_bool': 'sum'
        }).round(10)
        
        provider_stats.columns = ['Avg_Cost', 'Min_Cost', 'Max_Cost', 'Total_Models', 'Free_Models']
        provider_stats = provider_stats[provider_stats['Total_Models'] >= 2].sort_values('Avg_Cost', ascending=False)
        
        fig_provider_cost = px.scatter(
            provider_stats.reset_index(),
            x='Total_Models',
            y='Avg_Cost',
            size='Free_Models',
            hover_name='provider',
            title="Provider Comparison: Model Count vs Average Cost",
            labels={'Total_Models': 'Total # of Models', 'Avg_Cost': 'Average Cost ($/1M)'}
        )

        # Set y-axis range based on actual data - Fixed range
        y_min = -0.00000009
        y_max = 0.0000007
        fig_provider_cost.update_yaxes(
            range=[y_min, y_max],
            tickformat='.9f'  # Show more decimal places
        )
        fig_provider_cost.update_layout(height=CHART_HEIGHT)
        st.plotly_chart(fig_provider_cost, use_container_width=True)

    with col2:
        # Free vs Paid by provider
        free_paid_stats = df.groupby(['provider', 'is_free_bool']).size().unstack(fill_value=0)
        if len(free_paid_stats.columns) == 2:
            free_paid_stats.columns = ['Paid', 'Free']
        elif False in free_paid_stats.columns:
            free_paid_stats = free_paid_stats.rename(columns={False: 'Paid', True: 'Free'})
            if 'Free' not in free_paid_stats.columns:
                free_paid_stats['Free'] = 0
            if 'Paid' not in free_paid_stats.columns:
                free_paid_stats['Paid'] = 0
        
        free_paid_stats = free_paid_stats.sort_values('Free', ascending=False).head(10)
        
        fig_free_paid = px.bar(
            free_paid_stats.reset_index(),
            x='provider',
            y=['Free', 'Paid'],
            title="Top 10 Providers: Free vs Paid Models",
            labels={'value': 'Number of Models', 'provider': 'Provider'}
        )
        fig_free_paid.update_xaxes(tickangle=45)
        fig_free_paid.update_layout(height=CHART_HEIGHT)
        st.plotly_chart(fig_free_paid, use_container_width=True)

    # Additional analytics sections
    st.markdown("---")
    st.markdown("##### 📊 Additional Insights")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Cost Distribution Analysis**")
        paid_models = df[df['numeric_cost'] > 0]
        if len(paid_models) > 0:
            st.metric("Cheapest Paid Model", f"${paid_models['numeric_cost'].min():.9f}/1M")
            st.metric("Most Expensive", f"${paid_models['numeric_cost'].max():.6f}/1M")
            st.metric("Median Cost", f"${paid_models['numeric_cost'].median():.9f}/1M")

    with col2:
        st.markdown("**Provider Diversity**")
        st.metric("Total Providers", df['provider'].nunique())
        st.metric("Providers with Free Models", len(df[df['is_free_bool']]['provider'].unique()))
        st.metric("Average Models per Provider", f"{len(df) / df['provider'].nunique():.1f}")

    with col3:
        st.markdown("**Model Categories**")
        vision_models = len(df[df['model_name'].str.contains('vision|vl', case=False, na=False)])
        code_models = len(df[df['model_name'].str.contains('code|coder', case=False, na=False)])
        chat_models = len(df[df['model_name'].str.contains('chat|instruct', case=False, na=False)])
        
        st.metric("Vision Models", vision_models)
        st.metric("Code Models", code_models)
        st.metric("Chat/Instruct Models", chat_models)


if __name__ == "__main__": 
    show_sidebar()
    main()