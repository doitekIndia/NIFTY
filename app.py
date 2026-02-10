import streamlit as st
import yfinance as yf
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="NIFTY50 Scanner", layout="wide")

email_recipients = ["xmlkeyserver@gmail.com", "nitinplus@gmail.com"]

# ---------------- DATA ---------------- #
@st.cache_data(ttl=900)
def get_nifty_data():
    data = yf.download("^NSEI", period="1mo", interval="1d")
    data.index = data.index.tz_localize(None)
    return data.tail(25).dropna()

# ---------------- EMAIL ---------------- #
def send_email(symbol, signals):
    try:
        sender = st.secrets["email"]["sender"]
        password = st.secrets["email"]["app_password"]

        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.starttls()
        server.login(sender, password)

        body = f"""
NIFTY50 ALERT
Symbol: {symbol}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}

Buy 50%: {signals['buy_50']}
SL: {signals['sl']}
Target: {signals['target1']}
"""
        msg = MIMEText(body)
        msg["Subject"] = f"NIFTY50 Alert – {symbol}"
        msg["From"] = sender
        msg["To"] = ", ".join(email_recipients)

        server.send_message(msg)
        server.quit()

        st.success("✅ Email sent successfully")
    except Exception as e:
        st.error(f"❌ Email failed: {e}")

# ---------------- BACKTEST ---------------- #
def run_backtest(data):
    results = []

    for i in range(1, len(data)):
        today_open = data["Open"].iloc[i]
        y_low = data["Low"].iloc[i - 1]
        y_high = data["High"].iloc[i - 1]

        range_size = today_open - y_low
        if range_size <= 0:
            continue

        buy_50 = y_low + 0.5 * range_size
        trigger = "TRIGGER" if y_low <= buy_50 <= y_high and today_open > y_low else "NO TRADE"

        results.append({
            "Date": data.index[i].strftime("%d-%m"),
            "Open": round(today_open),
            "Buy 50%": round(buy_50),
            "SL": round(y_low),
            "Trigger": trigger
        })

    return pd.DataFrame(results)

# ---------------- UI ---------------- #
st.title("🚀 NIFTY50 Fibonacci Scanner")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Run Backtest"):
        with st.spinner("Running backtest..."):
            data = get_nifty_data()
            df = run_backtest(data)
            st.session_state["results"] = df

with col2:
    if st.button("📧 Test Email"):
        send_email("NIFTY", {"buy_50": 25850, "sl": 25750, "target1": 25950})

# ---------------- OUTPUT ---------------- #
if "results" in st.session_state:
    df = st.session_state["results"].tail(20)
    st.dataframe(df, use_container_width=True)

    triggers = (df["Trigger"] == "TRIGGER").sum()
    st.metric("🎯 Triggers", triggers, f"{(triggers/len(df))*100:.1f}%")
