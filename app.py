# app.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Property Risk Dashboard", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("home_insurance_2008_2012.csv", parse_dates=["QUOTE_DATE"])
    df['QUOTE_YEAR'] = df['QUOTE_DATE'].dt.year
    df['QUOTE_MONTH'] = df['QUOTE_DATE'].dt.to_period("M").astype(str)

    # Risk category buckets
    def get_risk_category(risk_val):
        if pd.isna(risk_val): return 'Unknown'
        elif risk_val <= 3: return 'Low'
        elif risk_val <= 7: return 'Medium'
        elif risk_val <= 10: return 'High'
        else: return 'Very High'
    
    df['RISK_CATEGORY'] = df['RISK_RATED_AREA_B'].apply(get_risk_category)

    # Sum insured bucket
    def get_sum_bucket(val):
        if pd.isna(val) or val == 0: return "Not Specified"
        elif val < 100_000: return "<$100K"
        elif val < 500_000: return "$100–500K"
        elif val < 1_000_000: return "$500K–1M"
        else: return "$1M+"
    
    df['SUM_BUCKET'] = df['SUM_INSURED_BUILDINGS'].apply(get_sum_bucket)
    return df

df = load_data()

# Sidebar filters
st.sidebar.header("Filter Data")
years = sorted(df['QUOTE_YEAR'].dropna().unique())
statuses = df['POL_STATUS'].dropna().unique()
risk_categories = ['Low', 'Medium', 'High', 'Very High', 'Unknown']
claim_flags = ['Y', 'N']

year_filter = st.sidebar.multiselect("Quote Year", years, default=years)
status_filter = st.sidebar.multiselect("Policy Status", statuses, default=statuses)
risk_filter = st.sidebar.multiselect("Risk Category", risk_categories, default=risk_categories)
claim_filter = st.sidebar.multiselect("Claim in Last 3 Years", claim_flags, default=claim_flags)

filtered_df = df[
    df['QUOTE_YEAR'].isin(year_filter) &
    df['POL_STATUS'].isin(status_filter) &
    df['RISK_CATEGORY'].isin(risk_filter) &
    df['CLAIM3YEARS'].isin(claim_filter)
]

# KPIs
st.title("Property Risk Analysis Dashboard")
col1, col2, col3, col4, col5 = st.columns(5)

total_policies = len(filtered_df)
avg_premium = filtered_df['LAST_ANN_PREM_GROSS'].mean()
high_risk_pct = 100 * len(filtered_df[filtered_df['RISK_CATEGORY'].isin(['High', 'Very High'])]) / total_policies
claims_pct = 100 * len(filtered_df[filtered_df['CLAIM3YEARS'] == 'Y']) / total_policies
live_pct = 100 * len(filtered_df[filtered_df['POL_STATUS'] == 'Live']) / total_policies

col1.metric("Total Policies", f"{total_policies:,}")
col2.metric("Avg Premium", f"${avg_premium:,.2f}")
col3.metric("High Risk %", f"{high_risk_pct:.1f}%")
col4.metric("Claims %", f"{claims_pct:.1f}%")
col5.metric("Live Policy %", f"{live_pct:.1f}%")

st.markdown("---")

# Time Series
monthly_summary = filtered_df.groupby("QUOTE_MONTH").agg(
    quote_count=("QUOTE_DATE", "count"),
    avg_premium=("LAST_ANN_PREM_GROSS", "mean")
).reset_index()

fig_ts = px.bar(monthly_summary, x="QUOTE_MONTH", y="quote_count", title="Monthly Quote Volume", labels={"quote_count": "Number of Quotes"})
fig_line = px.line(monthly_summary, x="QUOTE_MONTH", y="avg_premium", title="Avg Premium Over Time", markers=True)

col6, col7 = st.columns(2)
col6.plotly_chart(fig_ts, use_container_width=True)
col7.plotly_chart(fig_line, use_container_width=True)

# Risk Category Pie
risk_dist = filtered_df['RISK_CATEGORY'].value_counts().reset_index()
risk_dist.columns = ['Risk Category', 'Count']
fig_pie = px.pie(risk_dist, names='Risk Category', values='Count', title="Risk Category Distribution")
st.plotly_chart(fig_pie, use_container_width=True)

# Policy Status by Year
status_year = filtered_df.groupby(['QUOTE_YEAR', 'POL_STATUS']).size().reset_index(name='count')
fig_bar = px.bar(status_year, x="QUOTE_YEAR", y="count", color="POL_STATUS", title="Policy Status by Year", barmode="stack")
st.plotly_chart(fig_bar, use_container_width=True)

