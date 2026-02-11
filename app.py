# app.py - FIXED NIFTY50 Flask → Streamlit Conversion (WORKS IMMEDIATELY)
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Streamlit config
st.set_page_config(page_title="NIFTY50 Fibonacci Scanner", layout="wide", page_icon="📈")

# GLOBAL STATE - INITIALIZED
if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = []
if 'backtest_running' not in st.session_state:
    st.session_state.backtest_running = False
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False

email_recipients = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com", "aamirlodhi46@gmail.com"]

def safe_float(value):
    """Safe float conversion"""
    try:
        if pd.isna(value) or value is None:
            return None
        if hasattr(value, 'iloc'):
            return float(value.iloc[0]) if len(value) > 0 else None
        return float(value)
    except:
        return None

@st.cache_data(ttl=1800)
def get_nifty_daily_data():
    """Get last 25 trading days"""
    try:
        ticker = yf.Ticker('^NSEI')
        data = ticker.history(period="1mo")
        if data.index.tz is not None:
            data.index = data.index.tz_convert(None)
        data = data.dropna()
        return data.tail(25)
    except:
        return pd.DataFrame()

def send_email(recipients, symbol, signals=None):
    """Send email alerts"""
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = st.secrets.get("EMAIL_SENDER", "xmlkeyserver@gmail.com")
        sender_password = st.secrets.get("EMAIL_PASSWORD", "ikbl nfjo mkii wtkr")
        
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
📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📊 Period: {signals[0]['date']} → {signals[-1]['date']}
🎯 Triggers: {len(triggers)} / {total_days} days
📈 Hit Rate: {hit_rate:.1f}%"""
            
            for trigger in triggers[-5:]:
                body += f"\n🔔 {trigger['date']} | Buy 50%: ₹{trigger['buy_50']}"
            
        else:
            body = f"""🔥 NIFTY50 LIVE TRADING ALERT
📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}
📈 Buy 50%: ₹{signals.get('buy_50', 0):,.0f}
🛑 SL: ₹{signals.get('sl', 0):,.0f}
🎯 T1: ₹{signals.get('target1', 0):,.0f}"""
        
        success_count = 0
        for recipient in recipients:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient
            server.send_message(msg)
            success_count += 1
        
        server.quit()
        st.success(f"📧 SUCCESS: {success_count} emails sent")
        return True
    except Exception as e:
        st.error(f"❌ EMAIL ERROR: {str(e)}")
        return False

def calculate_backtest(data):
    """Pure backtest calculation"""
    results = []
    
    for i in range(len(data)-1, 0, -1):
        today_date = data.index[i].strftime('%m/%d/%Y')
        today_open = safe_float(data['Open'].iloc[i])
        yest_low = safe_float(data['Low'].iloc[i-1])
        yest_high = safe_float(data['High'].iloc[i-1])
        
        if today_open is None or yest_low is None or yest_high is None:
            results.append({
                'date': today_date, 'today_open': '0.00', 'yest_low': '0', 
                'yest_high': '0', 'case1': 'NO', 'acceptance': 'NO', 
                'trigger': 'NO TRADE', 'buy_50': '0.00', 'sl': '0', 'target1': '0.00'
            })
            continue
        
        case1 = "YES" if today_open > yest_low else "NO"
        range_size = today_open - yest_low
        
        if range_size <= 0:
            trigger = 'NO TRADE'
            acceptance = 'NO'
            buy_50 = '0.00'
            sl = f"{yest_low:.0f}"
            target1 = '0.00'
        else:
            buy_618 = yest_low + 0.618 * range_size
            buy_50 = yest_low + 0.5 * range_size
            buy_382 = yest_low + 0.382 * range_size
            
            acceptance = "YES" if (yest_low <= buy_618 <= yest_high and yest_low <= buy_50 <= yest_high) else "NO"
            trigger = "TRIGGER" if case1 == "YES" and acceptance == "YES" else "NO TRADE"
            
            target1 = today_open + 0.382 * range_size
            sl = f"{yest_low:.1f}"
            
            buy_50 = f"{buy_50:.2f}"
            target1 = f"{target1:.2f}"
        
        result = {
            'date': today_date,
            'today_open': f"{today_open:.2f}",
            'yest_low': f"{yest_low:.1f}",
            'yest_high': f"{yest_high:.1f}",
            'case1': case1,
            'acceptance': acceptance,
            'trigger': trigger,
            'buy_50': buy_50,
            'sl': sl,
            'target1': target1
        }
        results.append(result)
    
    return results

# ---------------- DASHBOARD ----------------
st.title("🚀 NIFTY50 FIBONACCI SCANNER")

# Buttons Row
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 **RUN BACKTEST**", use_container_width=True, key="run_backtest"):
        st.session_state.backtest_running = True
        st.session_state.backtest_results = []
        st.rerun()

with col2:
    if st.button("📧 **TEST EMAIL**", use_container_width=True, key="test_email"):
        signals = {'buy_50': 25850, 'sl': 25750, 'target1': 25950}
        send_email(email_recipients, 'LIVE-TEST', signals)

with col3:
    if st.button("📊 **SEND REPORT**", use_container_width=True, key="send_report"):
        if st.session_state.backtest_results:
            send_email(email_recipients, "BACKTEST-REPORT", st.session_state.backtest_results)
        else:
            st.warning("⚠️ Run backtest first!")

# EXECUTE BACKTEST (Main thread)
if st.session_state.backtest_running:
    with st.spinner("🔥 Running NIFTY50 Fibonacci Backtest..."):
        data = get_nifty_daily_data()
        
        if len(data) < 10:
            st.error("❌ Not enough data. Try again later.")
            st.session_state.backtest_running = False
            st.rerun()
        
        progress_bar = st.progress(0)
        st.info(f"📊 Analyzing {len(data)} trading days...")
        
        results = calculate_backtest(data)
        st.session_state.backtest_results = results
        
        triggers = len([r for r in results if r['trigger'] == 'TRIGGER'])
        progress_bar.progress(100)
        
        st.success(f"✅ BACKTEST COMPLETE! Found {triggers} TRIGGERS")
        st.session_state.backtest_running = False
        st.rerun()

# RESULTS DISPLAY
if st.session_state.backtest_results:
    st.subheader("📋 BACKTEST RESULTS")
    
    df = pd.DataFrame(st.session_state.backtest_results[-20:])
    
    # Metrics
    triggers = len([r for r in st.session_state.backtest_results if r['trigger'] == 'TRIGGER'])
    total = len(st.session_state.backtest_results)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Triggers", triggers)
    col2.metric("📊 Hit Rate", f"{triggers/total*100:.1f}%" )
    col3.metric("📅 Days Analyzed", total)
    
    # Table
    st.dataframe(
        df[['date', 'case1', 'acceptance', 'trigger', 'buy_50', 'sl', 'target1']],
        use_container_width=True,
        column_config={
            "trigger": st.column_config.TextColumn("Signal", help="TRIGGER = Buy Signal"),
            "buy_50": st.column_config.NumberColumn("Buy 50%", format="₹%.2f"),
        },
        hide_index=True
    )
    
    # Download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Download CSV", csv, "nifty50_backtest.csv", use_container_width=True)

else:
    st.info("👆 Click **RUN BACKTEST** to analyze NIFTY50 Fibonacci levels")

# Debug info
with st.expander("🔧 Debug Info"):
    st.json({"results_count": len(st.session_state.backtest_results), 
             "running": st.session_state.backtest_running})
