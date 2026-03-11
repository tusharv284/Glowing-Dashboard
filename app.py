import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="🌌 Glowy GL Dashboard", layout="wide", page_icon="🌌")

# Custom CSS for glowy neon UI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap');
    body { background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%) !important; color: #fff; }
    .main { padding: 2rem; }
    h1 { text-align: center; font-family: 'Orbitron', monospace; font-size: 3em; 
         background: linear-gradient(45deg, #00f5ff, #ff00ff, #00ff88); 
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
         animation: glow 2s ease-in-out infinite alternate; text-shadow: 0 0 20px #00f5ff; margin-bottom: 1rem; }
    @keyframes glow { from { filter: drop-shadow(0 0 10px #00f5ff); } to { filter: drop-shadow(0 0 30px #ff00ff); } }
    .metric-container { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); 
                        border-radius: 20px; padding: 1.5rem; text-align: center; 
                        box-shadow: inset 0 0 20px rgba(0,245,255,0.1), 0 0 30px rgba(0,245,255,0.2); 
                        border: 1px solid rgba(0,245,255,0.3); transition: all 0.3s; margin: 0.5rem 0; }
    .metric-container:hover { box-shadow: inset 0 0 20px rgba(255,0,255,0.2), 0 0 50px rgba(255,0,255,0.4); 
                              transform: translateY(-5px); }
    .metric-value { font-size: 2.5em; font-weight: 900; font-family: 'Orbitron', monospace;
                    background: linear-gradient(45deg, #00f5ff, #ff00ff); -webkit-background-clip: text; 
                    -webkit-text-fill-color: transparent; }
    .stPlotlyChart { border-radius: 20px; box-shadow: 0 0 30px rgba(0,245,255,0.3) !important; margin: 1rem 0; }
    .stDataFrame { border-radius: 10px; box-shadow: 0 0 20px rgba(0,245,255,0.3) !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🌌 Glowy General Ledger Dashboard")

# Auto-refresh cache function
@st.cache_data(ttl=300)  # 5 min cache
def load_gl_csv(csv_url):
    """Load CSV from GitHub raw URL or local upload"""
    try:
        if csv_url.startswith('http'):
            df = pd.read_csv(csv_url)
        else:
            df = pd.DataFrame()  # Fallback
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
        df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
        df['Balance'] = df['Debit'] - df['Credit']
        df = df.dropna(subset=['Date'])
        return df.sort_values('Date')
    except Exception as e:
        st.error(f"❌ Load failed: {str(e)}")
        return pd.DataFrame()

# Sidebar Controls
st.sidebar.header("⚡ Controls")
csv_url = st.sidebar.text_input(
    "🔗 GitHub Raw CSV URL", 
    value="https://raw.githubusercontent.com/YOURUSERNAME/glowy-gl-dashboard/main/sample_gl.csv",
    help="https://raw.githubusercontent.com/USER/REPO/main/FILENAME.csv"
)
upload_file = st.sidebar.file_uploader("📁 Or Upload CSV", type="csv")

if st.sidebar.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

# Load data (prefer GitHub, fallback upload)
if csv_url or upload_file:
    if upload_file:
        df = pd.read_csv(upload_file)
        csv_url = "Uploaded file"
    else:
        df = load_gl_csv(csv_url)
else:
    df = pd.DataFrame()

# Filters
if not df.empty:
    min_date, max_date = df['Date'].min(), df['Date'].max()
    date_range = st.sidebar.date_input("📅 Date Range", 
                                      value=(min_date.date(), max_date.date()),
                                      min_value=min_date.date(), 
                                      max_value=max_date.date())
    accounts = st.sidebar.multiselect("🏦 Filter Accounts", 
                                     options=sorted(df['Account'].unique()), 
                                     default=sorted(df['Account'].unique()))

# Main content
if df.empty:
    st.info("👆 Enter GitHub raw CSV URL or upload file to activate glow!")
    st.markdown("**Sample CSV format:**")
    sample_data = {
        'Date': ['2026-03-01', '2026-03-02', '2026-03-03', '2026-03-04'],
        'Account': ['Cash', 'Revenue', 'Expenses', 'Cash'],
        'Description': ['Deposit', 'Sales', 'Rent', 'Payment'],
        'Debit': [5000, 0, 0, 0],
        'Credit': [0, 4500, 800, 200]
    }
    st.dataframe(pd.DataFrame(sample_data))
else:
    # Apply filters
    mask = (df['Date'].dt.date >= date_range[0]) & (df['Date'].dt.date <= date_range[1])
    if accounts:
        mask &= df['Account'].isin(accounts)
    df_filtered = df[mask].copy()
    
    # Update sidebar accounts if filtered
    st.sidebar.markdown("---")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    total_debits = df_filtered['Debit'].sum()
    total_credits = df_filtered['Credit'].sum()
    net_balance = total_debits - total_credits
    tx_count = len(df_filtered)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div>💰 Total Debits</div>
            <div class="metric-value">${total_debits:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div>💳 Total Credits</div>
            <div class="metric-value">${total_credits:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div>⚖️ Net Balance</div>
            <div class="metric-value">${net_balance:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-container">
            <div>📊 Transactions</div>
            <div class="metric-value">{tx_count:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts Row 1
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("<h3>🥧 Debit vs Credit</h3>", unsafe_allow_html=True)
        fig_pie = px.pie(values=[total_debits, total_credits], names=['Debits', 'Credits'],
                        color_discrete_sequence=['#00f5ff', '#ff00ff'], hole=0.4)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(showlegend=True, font=dict(color='white'), paper_bgcolor='rgba(0,0,0,0)',
                            legend=dict(x=0.8, y=0.5))
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_b:
        st.markdown("<h3>📈 Net by Account</h3>", unsafe_allow_html=True)
        account_net = df_filtered.groupby('Account')['Balance'].sum().reset_index()
        fig_bar = px.bar(account_net, x='Account', y='Balance', color='Balance',
                        color_continuous_scale=['#ff00ff', '#00ff88'],
                        title="Net Balance per Account")
        fig_bar.update_layout(font=dict(color='white'), paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Charts Row 2
    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("<h3>📊 Daily Trends</h3>", unsafe_allow_html=True)
        df_ts = df_filtered.set_index('Date').resample('D').agg({'Debit': 'sum', 'Credit': 'sum'}).reset_index()
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(x=df_ts['Date'], y=df_ts['Debit'], name='Debits', 
                                    line=dict(color='#00f5ff', width=4)))
        fig_line.add_trace(go.Scatter(x=df_ts['Date'], y=df_ts['Credit'], name='Credits', 
                                    line=dict(color='#ff00ff', width=4)))
        fig_line.update_layout(title="Daily Debits vs Credits", hovermode='x unified', 
                             font=dict(color='white'), paper_bgcolor='rgba(0,0,0,0)',
                             plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_line, use_container_width=True)
    
    with col_d:
        st.markdown("<h3>📉 Running Balance</h3>", unsafe_allow_html=True)
        df_filtered['Cum_Balance'] = df_filtered['Balance'].cumsum()
        fig_cum = px.line(df_filtered, x='Date', y='Cum_Balance', markers=True, 
                         line_shape='spline', color_discrete_sequence=['#00ff88'])
        fig_cum.update_layout(title="Cumulative Balance", font=dict(color='white'), 
                            paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_cum, use_container_width=True)
    
    # Interactive Table
    st.markdown("<h3>✏️ Editable GL Table</h3>", unsafe_allow_html=True)
    edited_df = st.data_editor(
        df_filtered[['Date', 'Account', 'Description', 'Debit', 'Credit', 'Balance']], 
        num_rows='dynamic', use_container_width=True,
        column_config={
            "Debit": st.column_config.NumberColumn("Debit", format="%.2f"),
            "Credit": st.column_config.NumberColumn("Credit", format="%.2f"),
            "Balance": st.column_config.NumberColumn("Balance", disabled=True, format="%.2f")
        }
    )
    
    # Actions
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        csv_download = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Download Updated CSV", csv_download, "gl_dashboard.csv", "text/csv")
    with col_btn2:
        if st.button("🔄 Refresh All", type="secondary"):
            st.rerun()
    
    st.caption(f"Loaded from: {csv_url} | Rows: {len(df_filtered)} | Auto-refresh: 5 min")

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: #00f5ff;'>✨ Powered by Streamlit & Plotly | Glowy GL v2.0</p>", unsafe_allow_html=True)
