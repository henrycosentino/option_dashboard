import streamlit as st
import numpy as np
from plotting import Plotting
from BlackScholes import BlackScholes
import requests
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import timedelta
from datetime import datetime

# streamlit run "/Users/henrycosentino/Desktop/Python/Projects/Option PnL Dashboard/dashboard.py"

# To Do:
    # Implied Volatility & Historical Volatility tab (rolling, period etc)
    # Vanna might be wrong
    # Add Long/Short Call/Put
    # Add stratgies

# Title
st.title("Options - Interactive Heatmap")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar 
st.sidebar.header("Option Inputs")

# Ticker Input
if "name" not in st.session_state:
    st.session_state.name = "SPY"
name = st.sidebar.text_input("Ticker:").upper()

# Option Type Selection
if "optionType" not in st.session_state:
    st.session_state.optionType = "Call" 
optionType = st.sidebar.selectbox("Option Type:", ["Call", "Put"])

# Option Price Input
if "px" not in st.session_state:
    st.session_state.px = 3.00
px_input = st.sidebar.text_input("Option Price:")
try:
    px = float(px_input) if px_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Option Price.")
    px = None

# Implied Volatility Input
if "iv" not in st.session_state:
    st.session_state.iv = 0.25
iv_input = st.sidebar.text_input("Implied Volatility (%):")
try:
    iv = float(iv_input) / 100 if iv_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Implied Volatility.")
    iv = None

# Strike Input
if "strike" not in st.session_state:
    st.session_state.strike = 650.00
strike_input = st.sidebar.text_input("Strike:")
try:
    strike = float(strike_input) if strike_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Strike.")
    strike = None

# Time Input
if "time" not in st.session_state:
    st.session_state.time = 0.5
default_expiration_date = (datetime.today() + timedelta(days=1)).date()
expiration_date = st.sidebar.date_input("Expiration Date:", 
                                        min_value=datetime.today().date() + timedelta(days=1),
                                        max_value=datetime.today().date() + timedelta(days=3650),
                                        value=default_expiration_date)  
time = (expiration_date - datetime.today().date()).days / 365 
st.sidebar.write(f"**Time to Expiry:** {time:.2f} years")

# Spot Price Request
spot = None
if "spot" not in st.session_state:
    st.session_state.spot = 600.00
if name:
    stock = yf.Ticker(name)
    try:
        spot = stock.history(period="1d").iloc[0,3] # This indexing method may change if yfinance updates
    except (KeyError, ValueError):
        st.sidebar.error(f"Failed to retrieve price for {name}. Check the ticker.")
if spot:
    st.sidebar.write(f"**Spot Price:** ${spot:.2f}")

# Dividend Yield Request
if "dividend_yield" not in st.session_state:
    st.session_state.dividend_yield = 0.017
if name:
    stock = yf.Ticker(name)
    try:
        dividend_yield = stock.info.get("dividendYield", None) / 100 if stock.info.get("dividendYield") else 0
        st.sidebar.write(f"**Dividend Yield:** {100*dividend_yield:.2f}%")
    except:
        st.sidebar.error("Failed to retrieve dividend yield.")
        dividend_yield = 0

# Risk-Free Rate Request
fred_key = '0e26fed1b95ca710abdb6bbde2ad1a8a'

rates_series_dict = {
    'one_month': 'DGS1MO',
    'three_month': 'DGS3MO',
    'six_month': 'DGS6MO',
    'one_year': 'DGS1',
    'two_year': 'DGS2',
    'three_year': 'DGS3',
    'five_year': 'DGS5',
    'seven_year': 'DGS7',
    'ten_year': 'DGS10',
    'twenty_year': 'DGS20',
    'thirty_year': 'DGS30'
}

rates_value_dict = {}
time_lst = [30, 90, 180, 365, 730, 1095, 1825, 2555, 3650, 7300, 10950]

count = 0
for value in rates_series_dict.values():
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id={value}&api_key={fred_key}&file_type=json'
    data = requests.get(url).json()
    rate = float(data['observations'][-1]['value']) / 100

    rates_value_dict[time_lst[count]] = rate
    count += 1

def interpolate_rates(rate_dict, time):
    time_days = 365 * time  
    keys = sorted(rate_dict.keys())

    if time_days <= keys[0]:
        return rate_dict[keys[0]]
    
    if time_days >= keys[-1]:
        return rate_dict[keys[-1]]

    prev_key = None
    for key in keys:
        if time_days == key:
            return rate_dict[key]

        if prev_key is not None and prev_key < time_days < key:
            rate_one = rate_dict[prev_key]
            rate_two = rate_dict[key]
            return np.interp(time_days, [prev_key, key], [rate_one, rate_two])

        prev_key = key

if 'rate' not in st.session_state:
    st.session_state.rate = 0.04
rate = interpolate_rates(rates_value_dict, time)
st.sidebar.write(f"**Risk-Free Rate:** {100*rate:.2f}%")

# Spot Step Slider
st.session_state.spot_stp = st.session_state.get("spot_stp", 0.01)
spot_stp = st.sidebar.slider('Spot Step Slider:',
                             min_value=0.01,
                             max_value=0.25,
                             step=0.01,
                             key='spot_stp')

# Implied Volatility Step Slider
st.session_state.iv_stp = st.session_state.get("iv_stp", 0.01)
iv_stp = st.sidebar.slider('IV Step Slider:',
                           min_value=0.05,
                           max_value=0.25,
                           step=0.01,
                           key='iv_stp')

# Greek Calculation
blackScholes = BlackScholes(k=strike, s=spot,r=rate, t=time, iv=iv, b=dividend_yield)

# Output
col1, col2 = st.columns([1,4])
# Greeks Output
with col1:
    st.subheader("Greeks")
    st.markdown(
        f"""
        <style>
        .greeks-container {{
            border: 2px solid #FF6B6B;
            padding: 20px;
            border-radius: 14px;
            background-color: rgba(255, 107, 107, 0.1);
            width: 85%;
            max-width: 300px;
            font-size: 16px;
        }}
        .greeks-container p {{
            margin: 5px 0;
            color: white;
        }}
        .greeks-container span {{
            color: #FF6B6B;
            font-weight: bold;
        }}
        </style>
        <div class="greeks-container">
            <p>Delta: <span>{blackScholes.delta(optionType):.2f}</span></p>
            <p>Gamma: <span>{blackScholes.gamma():.2f}</span></p>
            <p>Vega: <span>{blackScholes.vega():.2f}</span></p>
            <p>Theta: <span>{blackScholes.theta(optionType):.2f}</span></p>
            <p>Rho: <span>{blackScholes.rho(optionType):.2f}</span></p>
            <p>Vanna: <span>{blackScholes.vanna():.2f}</span></p>
            <p>Charm: <span>{blackScholes.charm(optionType):.2f}</span></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Graph Output
with col2:
    if all(v is not None for v in [spot, iv, px, strike, time]):
        fig = Plotting(spot=spot, iv=iv, px=px, k=strike, 
                    r=rate, t=time, b=dividend_yield, 
                    name=name, optionType=optionType, 
                    spot_stp=spot_stp, iv_stp=iv_stp).plot()
        st.pyplot(fig)
    else:
        st.warning("Enter all inputs before plotting...")