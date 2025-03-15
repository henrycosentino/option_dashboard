import streamlit as st
import numpy as np
from plotting import Plotting
from BlackScholes import BlackScholes
import requests
import yfinance as yf
from datetime import timedelta
from datetime import datetime

# Title
st.title("Butterfly Option Strategy")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar 
st.sidebar.header("Option Inputs")

# Ticker Input
if "name" not in st.session_state:
    st.session_state.name = "SPY"
name = st.sidebar.text_input("Ticker:", value=st.session_state.name).upper()
st.session_state.name = name

# Sub-Strategy Selection
if "sub_strategy" not in st.session_state:
    st.session_state.sub_strategy = "Long Call Butterfly"
sub_strategy = st.sidebar.selectbox("Sub-Strategy:", ["Long Call Butterfly", "Short Call Butterfly",
                                                      "Long Put Butterfly", "Short Put Butterfly",
                                                      "Iron Butterfly", "Reverse Iron Butterfly"]
                                                      )
if sub_strategy in ["Long Call Butterfly", "Short Call Butterfly",
                    "Long Put Butterfly", "Short Put Butterfly"]:
    
    optionType = "Call" if "Call" in sub_strategy else "Put"

    if "low_strike" not in st.session_state:
        st.session_state.low_strike = 550
    low_strike_input = st.sidebar.text_input(f"Strike Price of Low {optionType} Option:")
    try:
        low_strike = float(low_strike_input) if low_strike_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for Strike Price of Low {optionType} Option.")
        low_strike = None

    if "low_px" not in st.session_state:
        st.session_state.low_px = 3.00
    low_px_input = st.sidebar.text_input(f"Low Strike {optionType} Option Price:")
    try:
        low_px = float(low_px_input) if low_px_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for Low Strike {optionType} Option Price.")
        low_px = None

    if "low_iv" not in st.session_state:
        st.session_state.low_iv = 0.35
    low_iv_input = st.sidebar.text_input(f"IV for Low Strike {optionType} (%):")
    try:
        low_iv = float(low_iv_input) / 100 if low_iv_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for Low Strike {optionType} IV.")
        low_iv = None

    if "atm_strike" not in st.session_state:
        st.session_state.atm_strike = 565
    atm_strike_input = st.sidebar.text_input(f"Strike Price of ATM {optionType} Option:")
    try:
        atm_strike = float(atm_strike_input) if atm_strike_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for Strike Price of ATM {optionType} Option.")
        atm_strike = None

    if "atm_px" not in st.session_state:
        st.session_state.atm_px = 4.00
    atm_px_input = st.sidebar.text_input(f"ATM Strike {optionType} Option Price:")
    try:
        atm_px = float(atm_px_input) if atm_px_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for ATM Strike {optionType} Option Price.")
        atm_px = None

    if "atm_iv" not in st.session_state:
        st.session_state.atm_iv = 0.40
    atm_iv_input = st.sidebar.text_input(f"IV for ATM Strike {optionType} (%):")
    try:
        atm_iv = float(atm_iv_input) / 100 if atm_iv_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for ATM Strike {optionType} IV.")
        atm_iv = None

    if "high_strike" not in st.session_state:
        st.session_state.high_strike = 580
    high_strike_input = st.sidebar.text_input(f"Strike Price of High {optionType} Option:")
    try:
        high_strike = float(high_strike_input) if high_strike_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for Strike Price of High {optionType} Option.")
        high_strike = None

    if "high_px" not in st.session_state:
        st.session_state.high_px = 5.00
    high_px_input = st.sidebar.text_input(f"High Strike {optionType} Option Price:")
    try:
        high_px = float(high_px_input) if high_px_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for High Strike {optionType} Option Price.")
        high_px = None

    if "high_iv" not in st.session_state:
        st.session_state.high_iv = 0.45
    high_iv_input = st.sidebar.text_input(f"IV for High Strike {optionType} (%):")
    try:
        high_iv = float(high_iv_input) / 100 if high_iv_input else None
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for High Strike {optionType} IV.")
        high_iv = None

elif sub_strategy in ["Iron Butterfly", "Reverse Iron Butterfly"]:
    pass

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
        st.session_state.dividend_yield = stock.info.get("dividendYield", None) / 100 if stock.info.get("dividendYield") else 0
        st.sidebar.write(f"**Dividend Yield:** {100*st.session_state.dividend_yield:.2f}%")
    except:
        st.sidebar.error("Failed to retrieve dividend yield.")
        st.session_state.dividend_yield = 0
dividend_yield = st.session_state.dividend_yield

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

# Output
if all(v is not None for v in [spot, low_px, low_iv, low_strike, rate, time, dividend_yield, 
                               name, atm_px, high_px, atm_iv, high_iv, atm_strike, high_strike, 
                               sub_strategy, spot_stp, iv_stp]):
    # Greek Calculation
    low_bs = BlackScholes(k=low_strike, s=spot,r=rate, t=time, iv=low_iv, b=dividend_yield)
    atm_bs = BlackScholes(k=atm_strike, s=spot,r=rate, t=time, iv=atm_iv, b=dividend_yield)
    high_bs = BlackScholes(k=high_strike, s=spot,r=rate, t=time, iv=high_iv, b=dividend_yield)

    if sub_strategy in ["Long Call Butterfly", "Short Call Butterfly",
                        "Long Put Butterfly", "Short Put Butterfly"]:
        sign = 1 if "Long" in sub_strategy else -1
        delta = sign * (low_bs.delta(optionType=optionType) - atm_bs.delta(optionType=optionType)*2 + high_bs.delta(optionType=optionType))
        gamma = sign * (low_bs.gamma() - atm_bs.gamma()*2 + high_bs.gamma())
        vega = sign * (low_bs.vega() - atm_bs.vega()*2 + high_bs.vega())
        theta = sign * (low_bs.theta(optionType=optionType) - atm_bs.theta(optionType=optionType)*2 + high_bs.theta(optionType=optionType))
        rho = sign * (low_bs.rho(optionType=optionType) - atm_bs.rho(optionType=optionType)*2 + high_bs.rho(optionType=optionType))
        vanna = sign * (low_bs.vanna() - atm_bs.vanna()*2 + high_bs.vanna())
        charm = sign * (low_bs.charm(optionType=optionType) - atm_bs.charm(optionType=optionType)*2 + high_bs.charm(optionType=optionType)) 
        volga = sign * (low_bs.volga() - atm_bs.volga()*2 + high_bs.volga())

    col1, col2 = st.columns([1,4])
    # Greeks Output
    with col1:
        st.subheader("Strategy Greeks")
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
                <p>Delta: <span>{delta:.2f}</span></p>
                <p>Gamma: <span>{gamma:.2f}</span></p>
                <p>Vega: <span>{vega:.2f}</span></p>
                <p>Volga: <span>{volga:.2f}</span></p>
                <p>Theta: <span>{theta:.2f}</span></p>
                <p>Rho: <span>{rho:.2f}</span></p>
                <p>Vanna: <span>{vanna:.2f}</span></p>
                <p>Charm: <span>{charm:.2f}</span></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("*Greeks represent the size and direction for the initial strategy level position")

    # Graph Output
    with col2:
            fig = Plotting(spot=spot, call_px=low_px, put_px=low_px, 
                        call_iv=low_iv, put_iv=low_iv, k=low_strike,
                        r=rate, t=time, b=dividend_yield, name=name,
                        px_atm=atm_px, px_high=high_px, iv_atm=atm_iv,
                        iv_high=high_iv, k_atm=atm_strike, 
                        k_high=high_strike, strategy=sub_strategy,
                        spot_stp=spot_stp, iv_stp=iv_stp).plot()
            st.pyplot(fig)
else:
    st.warning("Enter all inputs...")