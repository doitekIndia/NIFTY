# app.py - Professional NIFTY50 Fibonacci Scanner v2.0
# Deploy-ready for Streamlit Cloud

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone
import numpy as np
import warnings
warnings.filterwarnings("ignore")

# Page config
st.set_page_config(
    page_title="NIFTY50 Fibonacci Pro Scanner", 
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header { font-size: 3rem; color: #1f77b4; text-align: center; margin-bottom: 2rem; }
    .metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; border-radius: 10px; }
    .stPlotlyChart { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=1800)  # 30min cache
def get_nifty_data():
    """Fetch and clean NIFTY50 data with error handling"""
    try:
        data = yf.download("^NSEI", period="2mo", interval="1d", progress=False)
        
        # Handle timezone properly
        if data.index.tz is not None:
            data.index = data.index.tz_localize(None)
            
        data = data.dropna()
        st.cache_data.clear()  # Clear cache on data change
        return data.tail(30)
    except Exception as e:
        st.error(f"❌ Data fetch failed: {e}")
        return pd.DataFrame()

def send_professional_email(symbol, signals, results_df=None):
    """Send professional formatted email alerts"""
    try:
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["app_password"]
        
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=30)
        server.starttls()
        server.login(sender, password)
        
        # Professional HTML email
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1f77b4; background: #f8f9fa; padding: 20px; border-radius: 10px;">
                🚨 NIFTY50 FIBONACCI ALERT
            </h2>
            <div style="padding: 20px; background: white; border-radius: 10px; margin: 20px 0;">
                <p><strong>📈 Symbol:</strong> {symbol}</p>
                <p><strong>⏰ Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M IST')}</p>
                <p><strong>📊 Entry (50% Fib):</strong> ₹{signals['buy_50']:,.0f}</p>
                <p><strong>🛑 Stop Loss:</strong> ₹{signals['sl']:,.0f}</p>
                <p><strong>🎯 Target 1:</strong> ₹{signals['target1']:,.0f}</p>
                <hr>
                <p><em>Trade at your own risk. This is automated analysis only.</em></p>
            </div>
            <p style="text-align: center; color: #666;">
                📱 Live Dashboard: <a href="{st.secrets.get('APP_URL', 'https://nifty.streamlit.app')}">View Chart</a>
            </p>
        </div>
        """
        
        msg = MIMEText(html_body, 'html')
        msg["Subject"] = f"🚨 NIFTY50 Fibonacci Signal - {symbol}"
        msg["From"] = sender
        msg["To"] = ", ".join(st.session_state.get("email_recipients", ["xmlkeyserver@gmail.com", "nitinplus@gmail.com"]))
        
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"❌ Email error: {str(e)}")
        return False

def fibonacci_backtest(data):
    """Advanced Fibonacci backtest with multiple levels"""
    results = []
    
    for i in range(1, len(data)):
        today_open = data["Open"].iloc[i]
        yest_low = data["Low"].iloc[i-1]
        yest_high = data["High"].iloc[i-1]
        today_date = data.index[i].strftime("%d-%m-%Y")
        
        range_size = today_open - yest_low
        if range_size <= 0:
            continue
            
        # Fibonacci levels
        fib_618 = yest_low + 0.618 * range_size
        fib_50 = yest_low + 0.50 * range_size
        fib_382 = yest_low + 0.382 * range_size
        
        # Signal conditions
        case1 = today_open > yest_low
        fib_acceptance = (yest_low <= fib_618 <= yest_high) and (yest_low <= fib_50 <= yest_high)
        trigger = "TRIGGER" if case1 and fib_acceptance else "NO TRADE"
        
        # Targets
        target1 = today_open + 0.382 * range_size
        target2 = today_open + 0.618 * range_size
        
        results.append({
            "Date": today_date,
            "Open": f"₹{today_open:,.0f}",
            "Yest_Low": f"₹{yest_low:,.0f}",
            "Fib_50%": f"₹{fib_50:,.0f}",
            "Fib_61.8%": f"₹{fib_618:,.0f}",
            "SL": f"₹{yest_low:,.0f}",
            "T1": f"₹{target1:,.0f}",
            "Signal": trigger,
            "Range": f"{range_size:,.0f}"
        })
    
    return pd.DataFrame(results)

def create_candlestick_chart(data, signals_df):
    """Professional candlestick chart with signals"""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=('NIFTY50 Price Action', 'Fibonacci Signals'),
        row_heights=[0.7, 0.3]
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=data.index[-20:],
            open=data['Open'][-20:],
            high=data['High'][-20:],
            low=data['Low'][-20:],
            close=data['Close'][-20:],
            name="NIFTY50"
        ),
        row=1, col=1
    )
    
    # Signal markers
    triggers = signals_df[signals_df['Signal'] == 'TRIGGER']
    if not triggers.empty:
        fig.add_trace(
            go.Scatter(
                x=triggers['Date'].str[:10].astype('datetime64[ns]'),
                y=triggers['Fib_50%'].str.replace('₹', '').str.replace(',', '').astype(float),
                mode='markers+text',
                marker=dict(color='red', size=12, symbol='triangle-up'),
                text=['TRIGGER↑'],
                textposition="top center",
                name="Buy Signals",
                showlegend=True
            ),
            row=1, col=1
        )
    
    # Signal heatmap
    fig.add_trace(
        go.Heatmap(
            z=[1 if s == 'TRIGGER' else 0 for s in signals_df['Signal']],
            x=signals_df['Date'],
            y=['Signal'],
            colorscale='RdYlGn',
            zmid=0.5,
            showscale=False
        ),
        row=2, col=1
    )
    
    fig.update_layout(
        title="NIFTY50 Fibonacci Scanner - Live Analysis",
        xaxis_rangeslider_visible=False,
        height=700,
        template='plotly_white'
    )
    
    return fig

# ---------------- SIDEBAR ---------------- #
st.sidebar.title("⚙️ Settings")
st.session_state.email_recipients = st.sidebar.text_area(
    "📧 Email Recipients", 
    value="xmlkeyserver@gmail.com\nnitinplus@gmail.com",
    help="One email per line"
)

# ---------------- MAIN DASHBOARD ---------------- #
st.markdown('<h1 class="main-header">📈 NIFTY50 Fibonacci Pro Scanner</h1>', unsafe_allow_html=True)

# Metrics row
col1, col2, col3, col4 = st.columns(4)
data = get_nifty_data()

if not data.empty:
    col1.metric("📊 Days Analyzed", len(data), "↑2")
    col2.metric("💰 Latest Close", f"₹{data['Close'].iloc[-1]:,.0f}", "↗")
    col3.metric("📈 1M Change", f"{((data['Close'].iloc[-1]/data['Close'].iloc[0]-1)*100):+.1f}%")
    col4.metric("🕒 Last Update", data.index[-1].strftime("%d %b %Y"))

# Control buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔄 Run Full Backtest", use_container_width=True):
        with st.spinner("🔥 Analyzing 30 days of NIFTY50 data..."):
            st.session_state.results = fibonacci_backtest(data)
            st.session_state.last_analysis = datetime.now()
            st.success("✅ Backtest complete!")

with col2:
    if st.button("📧 Send Latest Signals", use_container_width=True):
        if 'results' in st.session_state and not st.session_state.results.empty:
            latest_signal = st.session_state.results.iloc[-1]
            signals = {
                'buy_50': float(latest_signal['Fib_50%'].replace('₹', '').replace(',', '')),
                'sl': float(latest_signal['SL'].replace('₹', '').replace(',', '')),
                'target1': float(latest_signal['T1'].replace('₹', '').replace(',', ''))
            }
            if send_professional_email("NIFTY50", signals):
                st.balloons()
        else:
            st.warning("⚠️ Run backtest first!")

with col3:
    if st.button("🧹 Clear Results", use_container_width=True):
        for key in ['results', 'last_analysis']:
            if key in st.session_state:
                del st.session_state[key]
        st.success("✅ Cleared!")

# Results & Charts
if 'results' in st.session_state and not st.session_state.results.empty:
    df = st.session_state.results.tail(20)
    
    # Charts
    col1, col2 = st.columns([2, 1])
    with col1:
        st.plotly_chart(create_candlestick_chart(data, df), use_container_width=True)
    
    with col2:
        # Performance metrics
        triggers = (df['Signal'] == 'TRIGGER').sum()
        hit_rate = (triggers / len(df)) * 100
        
        st.metric("🎯 Total Triggers", triggers)
        st.metric("📊 Hit Rate", f"{hit_rate:.1f}%")
        st.metric("🕒 Last Run", st.session_state.last_analysis.strftime("%H:%M:%S"))
        
        # Signal distribution
        st.subheader("📈 Signal Stats")
        signal_dist = df['Signal'].value_counts()
        st.bar_chart(signal_dist)

    # Results table
    st.subheader("📋 Detailed Results (Last 20 Days)")
    st.dataframe(
        df[['Date', 'Open', 'Fib_50%', 'SL', 'T1', 'Signal']],
        use_container_width=True,
        hide_index=True
    )
    
    # Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Download CSV",
        data=csv,
        file_name=f'nifty50_fibonacci_{datetime.now().strftime("%Y%m%d")}.csv',
        mime='text/csv'
    )
else:
    st.info("👆 Click **Run Full Backtest** to start analysis!")
    st.info("📧 Add secrets for email: `.streamlit/secrets.toml`")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666;'>"
    "Built with ❤️ for NIFTY50 traders | v2.0 Pro | Auto-updates every 30min"
    "</p>", 
    unsafe_allow_html=True
)
