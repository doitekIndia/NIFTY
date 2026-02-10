# app.py - NIFTY50 LIVE SCANNER v9.0 (FIXED + ADMIN PANEL)
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time as dt_time
import smtplib
from email.mime.text import MIMEText
import pytz
import numpy as np

st.set_page_config(page_title="NIFTY50 LIVE Fibonacci Scanner", layout="wide", page_icon="📈")

# ✅ FIXED: All functions FIRST, before usage
IST = pytz.timezone('Asia/Kolkata')

def is_market_open():
    """India market: 9:15 AM - 3:30 PM IST, Mon-Fri"""
    now = datetime.now(IST)
    market_open = dt_time(9, 15)
    market_close = dt_time(15, 30)
    return now.weekday() < 5 and market_open <= now.time() <= market_close

def fibonacci_backtest(data):
    """✅ YOUR Fibonacci logic - FIXED order"""
    results = []
    for i in range(len(data)-1, 0, -1):
        today_date = data.index[i].strftime('%m/%d')
        today_open = data['Open'].iloc[i]
        yest_low = data['Low'].iloc[i-1]
        yest_high = data['High'].iloc[i-1]
        
        case1 = "YES" if today_open > yest_low else "NO"
        range_size = today_open - yest_low
        
        if range_size <= 0:
            results.append({
                'date': today_date, 'today_open': f"{today_open:.0f}",
                'yest_low': f"{yest_low:.0f}", 'case1': case1, 
                'trigger': 'NO TRADE', 'buy_50': '0.00', 'sl': f"{yest_low:.0f}"
            })
            continue
        
        buy_618 = yest_low + 0.618 * range_size
        buy_50 = yest_low + 0.5 * range_size
        acceptance = "YES" if (yest_low <= buy_618 <= yest_high and 
                             yest_low <= buy_50 <= yest_high) else "NO"
        trigger = "TRIGGER" if case1 == "YES" and acceptance == "YES" else "NO TRADE"
        
        results.append({
            'date': today_date,
            'today_open': f"{today_open:.0f}",
            'yest_low': f"{yest_low:.0f}",
            'case1': case1,
            'trigger': trigger,
            'buy_50': f"{buy_50:.0f}",
            'sl': f"{yest_low:.0f}"
        })
    return results

def get_jan_2026_data():
    """YOUR verified Jan 2026 data"""
    dates = pd.to_datetime(['2026-01-22', '2026-01-21', '2026-01-20', '2026-01-19', 
                           '2026-01-18', '2026-01-15', '2026-01-13', '2026-01-12'])
    return pd.DataFrame({
        'Open': [25345, 25344, 25141, 25580, 25653, 25696, 25649, 25897],
        'High': [25450, 25500, 25250, 25700, 25750, 25800, 25750, 25950],
        'Low': [25168, 24920, 25171, 25494, 25662, 25604, 25603, 25473],
        'Close': [25380, 25420, 25190, 25620, 25680, 25730, 25680, 25850]
    }, index=dates)

def scan_live_signal():
    """🔴 LIVE market signal"""
    try:
        ticker = yf.Ticker('^NSEI')
        data = ticker.history(period="5d").tail(2)
        if len(data) < 2:
            return None
        
        today_open = data['Open'].iloc[-1]
        yest_low = data['Low'].iloc[-2]
        yest_high = data['High'].iloc[-2]
        
        case1 = today_open > yest_low
        range_size = today_open - yest_low
        
        if range_size <= 0 or not case1:
            return None
        
        buy_618 = yest_low + 0.618 * range_size
        buy_50 = yest_low + 0.5 * range_size
        
        if yest_low <= buy_618 <= yest_high and yest_low <= buy_50 <= yest_high:
            return {
                'buy_price': round(buy_50),
                'stop_loss': round(yest_low),
                'target1': round(today_open + 0.382 * range_size),
                'timestamp': datetime.now(IST).strftime('%H:%M:%S IST')
            }
    except:
        pass
    return None

def send_email(recipients, subject, body):
    """Generic email sender"""
    try:
        sender = st.secrets["email"]["sender"]
        pwd = st.secrets["email"]["app_password"]
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, pwd)
        
        for email in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = email
            server.send_message(msg)
        server.quit()
        return True
    except:
        return False

# ---------------- ADMIN SYSTEM ----------------
def admin_login():
    """✅ Admin login from secrets"""
    if "admin_auth" not in st.session_state:
        st.session_state.admin_auth = False
    
    if st.session_state.admin_auth:
        return True
    
    # Check secrets first
    try:
        admin_user = st.secrets["admin"]["username"]
        admin_pass = st.secrets["admin"]["password"]
    except:
        admin_user = "admin"
        admin_pass = "admin123"
    
    with st.sidebar:
        st.markdown("🔐 **ADMIN LOGIN**")
        username = st.text_input("Username", key="admin_user")
        password = st.text_input("Password", type="password", key="admin_pass")
        
        if st.button("Login", key="admin_login"):
            if username == admin_user and password == admin_pass:
                st.session_state.admin_auth = True
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                st.error("❌ Wrong credentials")
    
    if not st.session_state.admin_auth:
        st.warning("👈 **Login as Admin** (sidebar) for email management")
        return False
    return True

def admin_panel():
    """✅ Admin email management"""
    if "emails" not in st.session_state:
        try:
            st.session_state.emails = st.secrets["email"]["recipients"]
        except:
            st.session_state.emails = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com"]
    
    st.subheader("📧 **Email Management**")
    col1, col2 = st.columns(2)
    
    with col1:
        new_email = st.text_input("Add Email")
        if st.button("➕ Add Email") and new_email:
            st.session_state.emails.append(new_email)
            st.success(f"✅ Added: {new_email}")
            st.rerun()
    
    with col2:
        st.write("**Current Emails:**")
        for i, email in enumerate(st.session_state.emails):
            col_remove = st.columns([4,1])
            col_remove[0].write(f"• {email}")
            if col_remove[1].button("❌", key=f"remove_{i}"):
                st.session_state.emails.pop(i)
                st.success(f"✅ Removed: {email}")
                st.rerun()
    
    if st.button("💾 **Save Email List**"):
        st.info("Email list saved in session (persists during session)")
        st.success(f"✅ {len(st.session_state.emails)} emails configured")

# ---------------- SESSION STATE ----------------
if 'live_signal' not in st.session_state:
    st.session_state.live_signal = None
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'last_scan' not in st.session_state:
    st.session_state.last_scan = None
if 'emails' not in st.session_state:
    st.session_state.emails = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com"]

# ---------------- MAIN DASHBOARD ----------------
st.title("🚀 **NIFTY50 FIBONACCI SCANNER**")
st.markdown("**🔴 LIVE (9:15-15:30 IST) | 📊 Backtest | 🔐 Admin Panel**")

# Market Status
now = datetime.now(IST)
market_open = is_market_open()
col1, col2, col3 = st.columns(3)
col1.metric("📊 **MARKET**", "🟢 **OPEN**" if market_open else "🔴 **CLOSED**")
col2.metric("🕐 **TIME**", now.strftime('%H:%M IST'))
col3.metric("📡 **LAST SCAN**", st.session_state.last_scan.strftime('%H:%M') if st.session_state.last_scan else "Never")

st.divider()

# LIVE SCANNER
st.subheader("🔴 **LIVE SIGNAL SCANNER**")
if market_open:
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 **SCAN LIVE MARKET**", key="live_scan", use_container_width=True):
            signal = scan_live_signal()
            st.session_state.live_signal = signal
            st.session_state.last_scan = datetime.now(IST)
            st.rerun()
    
    if st.session_state.live_signal:
        signal = st.session_state.live_signal
        col1, col2, col3 = st.columns(3)
        col1.metric("📈 **BUY**", f"₹{signal['buy_price']:,}")
        col2.metric("🛑 **SL**", f"₹{signal['stop_loss']:,}")
        col3.metric("🎯 **T1**", f"₹{signal['target1']:,}")
        
        if st.button("🚨 **SEND TO ALL EMAILS**", key="send_live_alert"):
            success = send_email(st.session_state.emails, "🚨 NIFTY50 LIVE SIGNAL", 
                f"LIVE BUY @ ₹{signal['buy_price']:,} | SL: ₹{signal['stop_loss']:,}")
            if success:
                st.balloons()
else:
    st.info("⚠️ **Market Closed** - Live scanning: Mon-Fri 9:15 AM - 3:30 PM IST")

st.divider()

# BACKTEST
st.subheader("📊 **JAN 2026 BACKTEST**")
col1, col2 = st.columns(2)
with col1:
    if st.button("🔥 **RUN BACKTEST**", key="run_backtest", use_container_width=True):
        data = get_jan_2026_data()
        st.session_state.backtest_results = fibonacci_backtest(data)
        st.rerun()

with col2:
    if st.button("📧 **SEND BACKTEST**", key="send_backtest") and st.session_state.backtest_results:
        df = pd.DataFrame(st.session_state.backtest_results)
        triggers = len(df[df.trigger == 'TRIGGER'])
        send_email(st.session_state.emails, "📊 NIFTY50 Backtest", 
                  f"JAN 2026: {triggers} triggers found!")

if st.session_state.backtest_results:
    df = pd.DataFrame(st.session_state.backtest_results)
    st.metric("🎯 **Triggers**", len(df[df.trigger == 'TRIGGER']))
    st.dataframe(df[['date', 'today_open', 'yest_low', 'trigger', 'buy_50', 'sl']].tail(10), 
                use_container_width=True, hide_index=True)

# ---------------- ADMIN PANEL ----------------
if admin_login():
    st.sidebar.success("✅ **ADMIN MODE**")
    admin_panel()
else:
    st.sidebar.info("🔐 **ADMIN LOGIN** 👈")

st.markdown("---")
st.markdown("*NIFTY50 Scanner v9.0 | LIVE + Backtest + Admin | Production Ready*")
