"""
Streamlit Dashboard for Expense Analysis
Shows category spending with drill-down to merchant details
"""

import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict

# Page configuration
st.set_page_config(page_title="Expense Dashboard", layout="wide")
st.title("💰 Expense Analysis Dashboard")

# Load data
@st.cache_data
def load_transactions():
    with open('output/all_transactions_categorized.json', 'r') as f:
        data = json.load(f)
    # Convert JSON to DataFrame
    df = pd.DataFrame(data)
    # Convert amount to float and parse date
    df['amount'] = df['amount'].astype(float)
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M').astype(str)
    return df

df = load_transactions()

# ===== SIDEBAR =====
st.sidebar.header("Dashboard Options")
selected_category = st.sidebar.selectbox(
    "Select Category to Drill Down",
    ["All Categories"] + sorted(df['category_name'].unique())
)

# ===== MAIN CONTENT =====
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Transactions", len(df))
with col2:
    st.metric("Total Spending", f"${df['amount'].sum():,.2f}")
with col3:
    st.metric("Average Transaction", f"${df['amount'].mean():,.2f}")

st.divider()

# ===== CATEGORY OVERVIEW =====
st.header("📊 Spending by Category")

category_spending = df.groupby('category_name').agg({
    'amount': ['sum', 'count']
}).round(2)
category_spending.columns = ['Total Amount', 'Transaction Count']
category_spending = category_spending.sort_values('Total Amount', ascending=False)

# Calculate total spending and percentage
total_spending = category_spending['Total Amount'].sum()
category_spending['Percentage'] = (category_spending['Total Amount'] / total_spending * 100).round(2)

# Create pie chart for categories
fig_categories = px.pie(
    category_spending.reset_index(),
    values='Total Amount',
    names='category_name',
    title='Total Spending by Category',
    hover_data={'Total Amount': ':,.2f', 'Percentage': ':.2f%', 'Transaction Count': True},
    labels={'Total Amount': 'Amount ($)', 'category_name': 'Category'}
)
fig_categories.update_traces(
    textposition='inside',
    textinfo='percent+label',
    hovertemplate='<b>%{label}</b><br>' +
                  'Total Spent: $%{value:,.2f}<br>' +
                  'Percentage: %{percent}<br>' +
                  'Transactions: %{customdata[1]}<br>' +
                  '<extra></extra>'
)
fig_categories.update_layout(
    height=600,
    showlegend=True
)
st.plotly_chart(fig_categories, use_container_width=True)

# Display spending trends with tabs
st.subheader("Spending Trends Over Time")

# Create tabs for different views
tab1, tab2 = st.tabs(["📈 Total Monthly Spending", "📊 Spending by Category"])

with tab1:
    # Extract year from month for filtering
    df['year'] = df['date'].dt.year
    available_years = sorted(df['year'].unique())
    
    # Add year filter dropdown
    year_options = ['All Years'] + [str(year) for year in available_years]
    selected_year = st.selectbox('Select Year:', year_options, key='year_filter')
    
    # Filter data based on selection
    if selected_year == 'All Years':
        filtered_df = df
        chart_title = 'Total Monthly Spending (All Years)'
    else:
        filtered_df = df[df['year'] == int(selected_year)]
        chart_title = f'Total Monthly Spending ({selected_year})'
    
    # Total monthly spending (all categories combined)
    monthly_total_spending = filtered_df.groupby('month')['amount'].sum().reset_index()
    monthly_total_spending = monthly_total_spending.sort_values('month')
    
    # Calculate average spending across filtered months
    average_spending = monthly_total_spending['amount'].mean()
    
    fig_total_trends = px.line(
        monthly_total_spending,
        x='month',
        y='amount',
        title=chart_title,
        labels={'amount': 'Amount Spent ($)', 'month': 'Month'},
        markers=True
    )
    fig_total_trends.update_traces(
        line_color='#636EFA',
        line_width=3,
        marker=dict(size=8),
        hovertemplate='<b>Month:</b> %{x}<br><b>Total Spent:</b> $%{y:,.2f}<extra></extra>',
        name='Monthly Spending'
    )
    
    # Add average line
    fig_total_trends.add_hline(
        y=average_spending,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Average: ${average_spending:,.2f}",
        annotation_position="right",
        annotation=dict(font_size=12, font_color="red")
    )
    
    fig_total_trends.update_layout(
        height=500,
        xaxis_title='Month',
        yaxis_title='Amount Spent ($)',
        hovermode='x unified',
        showlegend=True
    )
    st.plotly_chart(fig_total_trends, use_container_width=True)

with tab2:
    # Spending by category breakdown
    monthly_category_spending = df.groupby(['month', 'category_name'])['amount'].sum().reset_index()
    
    fig_category_trends = px.line(
        monthly_category_spending,
        x='month',
        y='amount',
        color='category_name',
        title='Monthly Spending by Category',
        labels={'amount': 'Amount Spent ($)', 'month': 'Month', 'category_name': 'Category'},
        markers=True
    )
    fig_category_trends.update_layout(
        height=500,
        xaxis_title='Month',
        yaxis_title='Amount Spent ($)',
        legend_title='Category',
        hovermode='x unified'
    )
    fig_category_trends.update_traces(
        hovertemplate='$%{y:,.2f}<extra></extra>'
    )
    st.plotly_chart(fig_category_trends, use_container_width=True)

st.divider()

# ===== MERCHANT SCATTER PLOT =====
st.header("🔍 Merchant Analysis Scatter Plot")

# Filter data based on selected category
if selected_category != "All Categories":
    scatter_df = df[df['category_name'] == selected_category]
    scatter_title = f'Merchant Spending vs Transaction Frequency - {selected_category}'
else:
    scatter_df = df
    scatter_title = 'Merchant Spending vs Transaction Frequency - All Categories'

merchant_analysis = scatter_df.groupby('merchant').agg({
    'amount': ['sum', 'count', 'median']
}).round(2)
merchant_analysis.columns = ['Total Amount', 'Transaction Count', 'Median Amount']
merchant_analysis = merchant_analysis.reset_index()

# Add absolute value column for size (to handle negative amounts/credits)
merchant_analysis['Size'] = merchant_analysis['Total Amount'].abs()

fig_scatter = px.scatter(
    merchant_analysis,
    x='Transaction Count',
    y='Total Amount',
    hover_data={'Transaction Count': True, 'Total Amount': ':.2f', 'Median Amount': ':.2f', 'merchant': True, 'Size': False},
    title=scatter_title,
    labels={'Total Amount': 'Total Spent ($)', 'Transaction Count': 'Number of Transactions'},
    size='Size',
    color='Total Amount',
    color_continuous_scale='Viridis',
    hover_name='merchant',
    custom_data=['Median Amount']
)
fig_scatter.update_layout(
    height=600,
    showlegend=True
)
st.plotly_chart(fig_scatter, use_container_width=True)

st.divider()

# ===== MERCHANT DRILL-DOWN =====
if selected_category != "All Categories":
    st.header(f"🏪 Merchants in '{selected_category}'")
    
    # Filter data for selected category
    category_df = df[df['category_name'] == selected_category]
    
    # Group by merchant
    merchant_spending = category_df.groupby('merchant').agg({
        'amount': ['sum', 'count']
    }).round(2)
    merchant_spending.columns = ['Total Amount', 'Transaction Count']
    merchant_spending = merchant_spending.sort_values('Total Amount', ascending=False)
    
    # Create bar chart for merchants
    fig_merchants = px.bar(
        merchant_spending.reset_index(),
        x='merchant',
        y='Total Amount',
        title=f'Top Merchants in {selected_category}',
        labels={'Total Amount': 'Amount ($)', 'merchant': 'Merchant'},
        color='Total Amount',
        color_continuous_scale='Plasma'
    )
    fig_merchants.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False
    )
    st.plotly_chart(fig_merchants, use_container_width=True)
    
    # Display merchant summary table
    st.subheader(f"Merchants in {selected_category}")
    st.dataframe(
        merchant_spending.reset_index().rename(columns={'merchant': 'Merchant'}),
        use_container_width=True,
        hide_index=True
    )
    
    # Display transactions for this category
    st.subheader(f"Transactions in {selected_category}")
    display_columns = ['date', 'merchant', 'description', 'amount']
    st.dataframe(
        category_df[display_columns].sort_values('date', ascending=False),
        use_container_width=True,
        hide_index=True
    )

else:
    # Show merchant breakdown for all categories
    st.header("🏪 Top Merchants Overall")
    
    merchant_spending = df.groupby('merchant').agg({
        'amount': ['sum', 'count']
    }).round(2)
    merchant_spending.columns = ['Total Amount', 'Transaction Count']
    merchant_spending = merchant_spending.sort_values('Total Amount', ascending=False).head(20)
    
    fig_merchants = px.bar(
        merchant_spending.reset_index(),
        x='merchant',
        y='Total Amount',
        title='Top 20 Merchants by Spending',
        labels={'Total Amount': 'Amount ($)', 'merchant': 'Merchant'},
        color='Total Amount',
        color_continuous_scale='Plasma'
    )
    fig_merchants.update_layout(
        xaxis_tickangle=-45,
        height=500,
        showlegend=False
    )
    st.plotly_chart(fig_merchants, use_container_width=True)
    
    st.subheader("Top 20 Merchants")
    st.dataframe(
        merchant_spending.reset_index().rename(columns={'merchant': 'Merchant'}),
        use_container_width=True,
        hide_index=True
    )
