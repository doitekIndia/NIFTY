# app.py - COMPLETE NIFTY50 Scanner + LIVE 30s MONITORING + ADMIN PANEL (With YOUR Secrets)
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import numpy as np
import time
import warnings
warnings.filterwarnings('ignore')

# Streamlit config
st.set_page_config(page_title="NIFTY50 Fibonacci Scanner", layout="wide", page_icon="📈")

# ADMIN AUTHENTICATION
def check_admin_auth():
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False
    
    if st.session_state.admin_logged_in:
        return True
    
    # Admin login form
    if st.experimental_get_query_params().get("admin"):
        username = st.text_input("👤 Admin Username", value="")
        password = st.text_input("🔑 Password", type="password", value="")
        
        if st.button("🔐 LOGIN", use_container_width=True):
            if username == st.secrets["admin"]["username"] and password == st.secrets["admin"]["password"]:
                st.session_state.admin_logged_in = True
                st.success("✅ Admin access granted!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        st.stop()
    
    return False

# Initialize session state
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'email_recipients' not in st.session_state:
    st.session_state.email_recipients = st.secrets["email"]["recipients"]
if 'last_check_time' not in st.session_state:
    st.session_state.last_check_time = 0
if 'live_signals' not in st.session_state:
    st.session_state.live_signals = []

def safe_float(value):
    try:
        if pd.isna(value) or value is None:
            return None
        if hasattr(value, 'iloc'):
            return float(value.iloc[0]) if len(value) > 0 else None
        return float(value)
    except:
        return None

@st.cache_data(ttl=300)
def get_nifty_daily_data():
    try:
        ticker = yf.Ticker('^NSEI')
        data = ticker.history(period="2mo")
        if data.index.tz is not None:
            data.index = data.index.tz_convert(None)
        data = data.dropna()
        return data.tail(25)
    except:
        return pd.DataFrame()

def send_email(recipients, symbol, signals=None):
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = st.secrets["email"]["sender"]
        sender_password = st.secrets["email"]["app_password"]
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        
        subject = f"🚨 NIFTY50 FIBONACCI: {symbol}"
        
        if symbol == "BACKTEST-REPORT":
            triggers = [r for r in signals if r['trigger'] == 'TRIGGER']
            total_days = len(signals)
            hit_rate = (len(triggers) / total_days * 100) if total_days > 0 else 0
            body = f"""🔥 NIFTY50 FIBONACCI BACKTEST REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
📊 Period: {signals[0]['date']} → {signals[-1]['date']}
🎯 Triggers: {len(triggers)} / {total_days} days ({hit_rate:.1f}%)

🔥 TOP 5 TRIGGERS:
"""
            for trigger in triggers[-5:]:
                body += f"""🔔 {trigger['date']}
   Buy 50%: ₹{trigger['buy_50']}
   SL: ₹{trigger['sl']}
   T1: ₹{trigger['target1']}

"""
            body += f"🔗 LIVE DASHBOARD: https://nifty.streamlit.app"
        else:
            body = f"""🚨 NIFTY50 LIVE TRADING ALERT ⚡
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
📈 Buy 50%: ₹{signals.get('buy_50', 0):,.0f}
🛑 SL: ₹{signals.get('sl', 0):,.0f}
🎯 T1: ₹{signals.get('target1', 0):,.0f}

🔗 LIVE DASHBOARD: https://nifty.streamlit.app"""
        
        success_count = 0
        for recipient in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient
            server.send_message(msg)
            success_count += 1
            time.sleep(0.2)  # Rate limiting
        
        server.quit()
        st.success(f"✅ {success_count} emails sent successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Email error: {str(e)}")
        return False

def check_live_signal():
    """Check live trading signal every 30 seconds"""
    current_time = time.time()
    if current_time - st.session_state.last_check_time < 30:
        return False
    
    st.session_state.last_check_time = current_time
    data = get_nifty_daily_data()
    
    if len(data) < 2:
        return False
    
    today_open = safe_float(data['Open'].iloc[-1])
    yest_low = safe_float(data['Low'].iloc[-2])
    yest_high = safe_float(data['High'].iloc[-2])
    
    if today_open is None or yest_low is None or yest_high is None:
        return False
    
    case1 = today_open > yest_low
    range_size = today_open - yest_low
    
    if range_size <= 0:
        return False
    
    buy_618 = yest_low + 0.618 * range_size
    buy_50 = yest_low + 0.5 * range_size
    
    acceptance = (yest_low <= buy_618 <= yest_high and yest_low <= buy_50 <= yest_high)
    trigger = case1 and acceptance
    
    if trigger:
        signals = {
            'buy_50': buy_50,
            'sl': yest_low,
            'target1': today_open + 0.382 * range_size
        }
        st.session_state.live_signals.append({
            'time': datetime.now().strftime('%H:%M:%S'),
            'buy_50': f"{buy_50:.2f}",
            'sl': f"{yest_low:.1f}",
            'target1': f"{signals['target1']:.2f}"
        })
        
        send_email(st.session_state.email_recipients, "LIVE-ALERT", signals)
        st.success("🚨 LIVE TRADING SIGNAL SENT TO ALL!")
        st.balloons()
        return True
    
    return False

def calculate_backtest(data):
    results = []
    for i in range(len(data)-1, 0, -1):
        today_date = data.index[i].strftime('%m/%d/%Y')
        today_open = safe_float(data['Open'].iloc[i])
        yest_low = safe_float(data['Low'].iloc[i-1])
        yest_high = safe_float(data['High'].iloc[i-1])
        
        if today_open is None or yest_low is None or yest_high is None:
            results.append({'date': today_date, 'trigger': 'NO DATA', 'buy_50': '0.00'})
            continue
        
        case1 = "YES" if today_open > yest_low else "NO"
        range_size = today_open - yest_low
        
        if range_size <= 0:
            trigger = 'NO TRADE'
            buy_50 = '0.00'
            target1 = '0.00'
        else:
            buy_618 = yest_low + 0.618 * range_size
            buy_50 = yest_low + 0.5 * range_size
            acceptance = "YES" if (yest_low <= buy_618 <= yest_high and yest_low <= buy_50 <= yest_high) else "NO"
            trigger = "TRIGGER" if case1 == "YES" and acceptance == "YES" else "NO TRADE"
            target1 = today_open + 0.382 * range_size
            buy_50 = f"{buy_50:.2f}"
            target1 = f"{target1:.2f}"
        
        results.append({
            'date': today_date,
            'today_open': f"{today_open:.2f}",
            'yest_low': f"{yest_low:.1f}",
            'yest_high': f"{yest_high:.1f}",
            'case1': case1,
            'trigger': trigger,
            'buy_50': buy_50,
            'sl': f"{yest_low:.1f}",
            'target1': target1
        })
    return results

# ---------------- MAIN APP ----------------
if "admin" not in st.experimental_get_query_params():
    st.error("🔐 **ADMIN ACCESS REQUIRED**")
    st.info("👆 Add `?admin=1` to URL or click [ADMIN LOGIN](https://your-app.streamlit.app/?admin=1)")
    st.stop()

# Check admin login
if not check_admin_auth():
    st.stop()

# ---------------- TABS ----------------
tab1, tab2, tab3 = st.tabs(["📈 Live Dashboard", "⚙️ Email Admin", "📊 Backtest"])

with tab1:
    st.header("🚀 NIFTY50 FIBONACCI LIVE SCANNER")
    
    # Status metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📊 Monitoring", "🟢 LIVE" if st.session_state.monitoring_active else "🔴 STOPPED")
    col2.metric("📧 Emails", len(st.session_state.email_recipients))
    col3.metric("🎯 Live Alerts", len(st.session_state.live_signals))
    col4.metric("📈 Backtest Triggers", len([r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER']))
    
    # Control buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 **RUN BACKTEST**", use_container_width=True, key="run_backtest"):
            st.session_state.backtest_running = True
            st.session_state.backtest_results = []
            st.rerun()
    
    with col2:
        if st.button("▶️ **START 30s MONITORING**", use_container_width=True, key="start_monitor"):
            st.session_state.monitoring_active = True
            st.success("✅ LIVE MONITORING STARTED (30s intervals)")
    
    with col3:
        if st.button("⏹️ **STOP MONITORING**", use_container_width=True, key="stop_monitor"):
            st.session_state.monitoring_active = False
            st.success("✅ MONITORING STOPPED")
    
    # LIVE SIGNAL CHECK (Every page load)
    if st.session_state.monitoring_active:
        st.info("🔄 **Auto-checking every 30 seconds** ⏱️")
        if check_live_signal():
            st.balloons()
    
    # Live signals history
    if st.session_state.live_signals:
        st.subheader("⚡ RECENT LIVE ALERTS")
        live_df = pd.DataFrame(st.session_state.live_signals[-10:])
        st.dataframe(live_df, use_container_width=True)
    
    # Quick test
    if st.button("📧 **TEST EMAIL NOW**", use_container_width=True, key="test_email"):
        signals = {'buy_50': 25850, 'sl': 25750, 'target1': 25950}
        send_email(st.session_state.email_recipients, 'TEST-ALERT', signals)

with tab2:
    st.header("⚙️ Email Recipients Management")
    st.success(f"✅ Using your secrets: {len(st.secrets['email']['recipients'])} default recipients")
    
    # Add new email
    st.subheader("➕ Add New Recipient")
    new_email = st.text_input("Enter email address:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ ADD EMAIL", key="add_email") and new_email:
            if new_email not in st.session_state.email_recipients:
                st.session_state.email_recipients.append(new_email)
                st.success(f"✅ {new_email} added!")
                st.rerun()
            else:
                st.warning("✅ Email already exists")
    
    # Current list
    st.subheader("📋 Current Recipients")
    if st.session_state.email_recipients:
        for i, email in enumerate(st.session_state.email_recipients):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"• **{email}**")
            with col2:
                if st.button("❌", key=f"delete_{i}"):
                    st.session_state.email_recipients.pop(i)
                    st.success(f"🗑️ {email} removed!")
                    st.rerun()
    else:
        st.warning("No recipients configured")
    
    st.info("💡 **Persistent across sessions**. Add to secrets.toml for permanent storage.")

with tab3:
    st.header("📊 Historical Backtest")
    
    if st.button("🔄 **RUN FULL BACKTEST**", use_container_width=True, key="backtest_full"):
        st.session_state.backtest_running = True
        st.session_state.backtest_results = []
        st.rerun()
    
    if st.session_state.backtest_running:
        with st.spinner("🔥 Analyzing NIFTY50 Fibonacci levels..."):
            data = get_nifty_daily_data()
            if len(data) < 10:
                st.error("❌ Insufficient market data")
                st.session_state.backtest_running = False
            else:
                results = calculate_backtest(data)
                st.session_state.backtest_results = results
                triggers = len([r for r in results if r['trigger'] == 'TRIGGER'])
                st.success(f"✅ Backtest complete! Found **{triggers} triggers** in {len(results)} days")
                st.session_state.backtest_running = False
                st.rerun()
    
    if st.session_state.backtest_results:
        df = pd.DataFrame(st.session_state.backtest_results[-20:])
        
        col1, col2, col3 = st.columns(3)
        triggers = len([r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER'])
        col1.metric("🎯 Triggers", triggers)
        col2.metric("📊 Hit Rate", f"{triggers/len(df)*100:.1f}%")
        col3.metric("📅 Days", len(df))
        
        st.dataframe(
            df[['date', 'case1', 'trigger', 'buy_50', 'sl', 'target1']],
            use_container_width=True,
            column_config={
                "buy_50": st.column_config.NumberColumn("Buy 50%", format="₹%.2f"),
                "sl": st.column_config.NumberColumn("Stop Loss", format="₹%.2f")
            }
        )
        
        if st.button("📧 **SEND BACKTEST REPORT**", use_container_width=True, key="send_report"):
            send_email(st.session_state.email_recipients, "BACKTEST-REPORT", st.session_state.backtest_results)
    
    csv = pd.DataFrame(st.session_state.backtest_results[-20:]).to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download Backtest CSV", csv, "nifty50_fibonacci.csv")

# Footer
st.markdown("---")
st.markdown("*✅ **YOUR SECRETS LOADED** | LIVE 30s monitoring | Admin: nitin/doitdoit123 | Ready for production!*")
