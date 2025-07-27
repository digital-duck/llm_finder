# pages/3_📊_Overview.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils import *

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")


# Check if data is available
if 'df' not in st.session_state:
    st.error("❌ Data not loaded. Please go back to the main page first.")
    st.stop()

df = st.session_state.df


def main():

    st.markdown("##### 📊 Overview")

    # Key metrics
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

    # Quick stats
    # st.markdown("##### 📈 Quick Statistics")

    col1, col2 = st.columns(2)

    with col1:
        # Top 20 providers by model count
        provider_counts = df['provider'].value_counts().head(20)
        fig_providers = px.bar(
            x=provider_counts.values,
            y=provider_counts.index,
            orientation='h',
            title="Top 20 Providers by Model Count",
            labels={'x': 'Number of Models', 'y': 'Provider'}
        )
        fig_providers.update_layout(height=600)
        st.plotly_chart(fig_providers, use_container_width=True)

    with col2:
        # Cost distribution
        paid_df = df[df['numeric_cost'] > 0]
        if len(paid_df) > 0:
            fig_cost = px.histogram(
                paid_df,
                x='numeric_cost',
                title="Cost Distribution (Paid Models)",
                labels={'numeric_cost': 'Cost ($/1M tokens)', 'count': 'Number of Models'},
                nbins=30
            )
            fig_cost.update_layout(height=CHART_HEIGHT)
            st.plotly_chart(fig_cost, use_container_width=True)
        else:
            st.info("No paid models available for cost distribution")



if __name__ == "__main__": 
    show_sidebar()
    main()