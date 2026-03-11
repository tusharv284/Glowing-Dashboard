import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Glowy GL Dashboard", layout="wide", page_icon="🌌")

# Custom CSS for glowy UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    body { background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%) !important; }
    .main { padding: 2rem; }
    h1 { text-align: center; font-family: 'Orbitron', monospace; font-size: 3em; 
         background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff88); 
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
         animation: glow 2s ease-in-out infinite alternate; text-shadow: 0 0 20px #00f5ff; }
    @keyframes glow { from { filter: drop-shadow(0 0 10px #00f5ff); } to { filter: drop-shadow(0 0 30px #ff00ff); } }
    .metric-container { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); 
                        border-radius: 20px; padding: 1.5rem; text-align: center; 
                        box-shadow: inset 0 0 20px rgba(0,245,255,0.1), 0 0 30px rgba(0,245,255,0.2); 
                        border: 1px solid rgba(0,245,255,0.3); transition: all 0.3s; }
    .metric-container:hover { box-shadow: inset 0 0 20px rgba(255,0,255,0.2), 0 0 50px rgba(255,0,255,0.4); 
                              transform: translateY(-5px); }
    .metric-value { font-size: 2.5em; font-weight: 900; font-family: 'Orbitron', monospace;
                    background: linear-gradient(45deg, #00f5ff, #ff00ff); -webkit-background-clip: text; 
                    -webkit-text-fill-color: transparent; }
    .stPlotlyChart { border-radius: 20px; box-shadow: 0 0 30px rgba(0,245,255,0.3) !important; }
    .stDataFrame { border-radius: 10px; box-shadow: 0 0 20px rgba(0,245,255,0.3) !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🌌 Glowy General Ledger Dashboard")

# Sidebar
st.sidebar.header("⚡ Controls")
uploaded_file = st.sidebar.file_uploader("📁 Upload GL CSV", type="csv", help="Date,Account,Description,Debit,Credit")
date_range = st.sidebar.date_input("Filter Dates", value=(datetime.now() - timedelta(days=30), datetime.now()))
account_filter = st.sidebar.multiselect("Filter Accounts", options=[])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df['Date'] = pd.to_datetime(df['Date'])
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    df['Balance'] = df['Debit'] - df['Credit']
    
    # Apply filters
    mask = (df['Date'] >= pd.to_datetime(date_range[0])) & (df['Date'] <= pd.to_datetime(date_range[1]))
    if account_filter:
        mask &= df['Account'].isin(account_filter)
    df_filtered = df[mask].copy()
    
    # Update sidebar filter options
    if 'df_filtered' in locals():
        account_filter = st.sidebar.multiselect("Filter Accounts", options=df_filtered['Account'].unique(), default=account_filter)
    
    col1, col2, col3, col4 = st.columns(4)
    total_debits = df_filtered['Debit'].sum()
    total_credits = df_filtered['Credit'].sum()
    net_balance = total_debits - total_credits
    tx_count = len(df_filtered)
    
    with col1:
        st.metric("💰 Total Debits", f"${total_debits:,.2f}", delta=None, help="Sum of all debits")
    with col2:
        st.metric("💳 Total Credits", f"${total_credits:,.2f}", delta=None)
    with col3:
        st.metric("⚖️ Net Balance", f"${net_balance:,.2f}", delta=None)
    with col4:
        st.metric("📊 Transactions", tx_count, delta=None)
    
    # Charts row 1
    col_a, col_b = st.columns(2)
    with col_a:
        fig_pie = px.pie(df_filtered, values=[total_debits, total_credits], names=['Debits', 'Credits'],
                         color_discrete_sequence=['#00f5ff', '#ff00ff'], hole=0.4)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=False, font=dict(color='white'), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_b:
        account_net = df_filtered.groupby('Account')['Balance'].sum().reset_index()
        fig_bar = px.bar(account_net, x='Account', y='Balance', color='Balance',
                        color_continuous_scale=['#ff00ff', '#00ff88'], 
                        title="Net by Account")
        fig_bar.update_layout(font=dict(color='white'), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Charts row 2: Time series + Cumulative
    col_c, col_d = st.columns(2)
    with col_c:
        df_filtered['Date'] = pd.to_datetime(df_filtered['Date'])
        df_ts = df_filtered.resample('D', on='Date').agg({'Debit': 'sum', 'Credit': 'sum'}).fillna(0)
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_ts.index, y=df_ts['Debit'], name='Debits', line=dict(color='#00f5ff', width=3)))
        fig_line.add_trace(go.Scatter(x=df_ts.index, y=df_ts['Credit'], name='Credits', line=dict(color='#ff00ff', width=3)))
        fig_line.update_layout(title="Daily D/C", hovermode='x unified', font=dict(color='white'), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_line, use_container_width=True)
    
    with col_d:
        df_filtered['Cum_Balance'] = df_filtered['Balance'].cumsum()
        fig_cum = px.line(df_filtered, x='Date', y='Cum_Balance', markers=True, 
                         line_shape='spline', color_discrete_sequence=['#00ff88'])
        fig_cum.update_layout(title="Running Balance", font=dict(color='white'), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cum, use_container_width=True)
    
    # Interactive Table
    st.subheader("✏️ Editable GL Table")
    edited_df = st.data_editor(df_filtered[['Date', 'Account', 'Description', 'Debit', 'Credit', 'Balance']], 
                              num_rows='dynamic', use_container_width=True,
                              column_config={
                                  "Debit": st.column_config.NumberColumn("Debit", format="%.2f"),
                                  "Credit": st.column_config.NumberColumn("Credit", format="%.2f"),
                                  "Balance": st.column_config.NumberColumn("Balance", disabled=True)
                              })
    if st.button("🔄 Refresh Metrics", type="secondary"):
        st.rerun()
    
    # Download
    csv = edited_df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download Updated CSV", csv, "gl_updated.csv", "text/csv")

else:
    st.info("👆 Upload your GL CSV (sample: Date,Account,Description,Debit,Credit) to glow up!")
    st.markdown("**Sample Data:**")
    sample = pd.DataFrame({
        'Date': ['2026-03-01', '2026-03-02', '2026-03-03'],
        'Account': ['Cash', 'Revenue', 'Expenses'],
        'Description': ['Deposit', 'Sales', 'Rent'],
        'Debit': [1000, 0, 0],
        'Credit': [0, 800, 200]
    })
    st.dataframe(sample)
