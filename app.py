# app.py - PUBLIC VIEWER + AUTO BACKTEST ON LOAD + MARKET HOURS
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import smtplib
from email.mime.text import MIMEText
import numpy as np
import time
import warnings
warnings.filterwarnings('ignore')
from datetime import timezone

# Streamlit config
st.set_page_config(page_title="NIFTY50 Fibonacci Scanner", layout="wide", page_icon="📈")

# Market Hours Check (9:15 AM - 3:30 PM IST, Mon-Fri)
def is_market_hours():
    now = datetime.now(timezone.utc).astimezone()
    ist_hour = now.hour + 5.5  # UTC to IST
    ist_minute = now.minute
    
    ist_time = time(ist_hour, ist_minute)
    market_open = time(9, 15)
    market_close = time(15, 30)
    
    is_weekday = now.weekday() < 5  # Mon-Fri
    return is_weekday and market_open <= ist_time <= market_close

# Initialize session state
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = is_market_hours()
if 'email_recipients' not in st.session_state:
    st.session_state.email_recipients = st.secrets["email"]["recipients"]
if 'live_signals' not in st.session_state:
    st.session_state.live_signals = []

# ==================== LEFT SIDEBAR ADMIN (Optional) ====================
with st.sidebar:
    st.markdown("🔐 **ADMIN PANEL**")
    
    # Admin login (OPTIONAL - public can still see data)
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if not st.session_state.admin_logged_in:
        st.markdown("### 👀 **Public Viewer - No Login Needed**")
        if st.button("🔐 ADMIN LOGIN", use_container_width=True):
            st.session_state.show_admin = True
            st.rerun()
    else:
        # Admin controls (same as before)
        st.success("✅ **ADMIN ACTIVE**")
        # ... rest of admin code ...

# PUBLIC VIEWER - Show data WITHOUT login
st.title("🚀 NIFTY50 FIBONACCI SCANNER 📈")
st.markdown("**Live signals | Backtest viewer | Market: 9:15AM-3:30PM IST**")

# Market status
market_open = is_market_hours()
col1, col2, col3 = st.columns(3)
col1.metric("📈 Market", "🟢 OPEN" if market_open else "🔴 CLOSED")
col2.metric("⏱️ Time", datetime.now().strftime("%H:%M IST"))
col3.metric("📧 Recipients", len(st.session_state.email_recipients))

# AUTO BACKTEST ON LOAD (Public viewer)
if not st.session_state.backtest_results:
    with st.spinner("🔥 Loading latest NIFTY50 analysis..."):
        data = get_nifty_daily_data()
        if len(data) >= 10:
            results = calculate_backtest(data)
            st.session_state.backtest_results = results
            triggers = len([r for r in results if r['trigger'] == 'TRIGGER'])
            st.success(f"✅ Loaded! Found {triggers} signals in last 25 days")

# Show backtest results (Public)
if st.session_state.backtest_results:
    df = pd.DataFrame(st.session_state.backtest_results[-20:])
    
    col1, col2, col3 = st.columns(3)
    triggers = len([r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER'])
    col1.metric("🎯 Triggers", triggers)
    col2.metric("📊 Hit Rate", f"{triggers/len(df)*100:.1f}%")
    col3.metric("📅 Days", len(df))
    
    # HIGHLIGHT TRIGGERS
    def highlight_triggers(row):
        return ['background-color: #d4edda' if row['trigger'] == 'TRIGGER' else '' for _ in row]
    
    st.dataframe(df.style.apply(highlight_triggers, axis=1), use_container_width=True)

# Control buttons (Public + Admin)
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🔄 REFRESH BACKTEST", use_container_width=True):
        st.session_state.backtest_running = True
        st.rerun()
with col2:
    st.info(f"🚨 **Auto-monitor:** {'🟢 ACTIVE' if market_open else '⏸️ PAUSED (Market Closed)'}")
with col3:
    st.markdown("💰 [Donate via Razorpay](https://razorpay.me/@DOITEKINDIA)")

# RAZORPAY DONATION
st.markdown("---")
st.markdown("### 💎 **Premium Features**")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    ✅ **FREE**: Backtest viewer + Signal history
    🔒 **PREMIUM** (₹99/month):
    • Live 30s alerts to YOUR email
    • Custom watchlist
    • Priority support
    """)
with col2:
    st.markdown("![Razorpay](https://razorpay.me/@DOITEKINDIA)")
    st.info("👆 **Support this project** → Click Razorpay link above")

# Footer
st.markdown("*📈 Public NIFTY50 Scanner | Auto-loads data | Market hours only | Made in India 🇮🇳*")
