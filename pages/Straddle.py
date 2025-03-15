import streamlit as st
import numpy as np
from plotting import Plotting
from BlackScholes import BlackScholes
import requests
import yfinance as yf
from datetime import timedelta
from datetime import datetime

# Title
st.title("Straddle Option Strategy")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar 
st.sidebar.header("Option Inputs")

# Ticker Input
if "name" not in st.session_state:
    st.session_state.name = "SPY"
name = st.sidebar.text_input("Ticker:", value=st.session_state.name).upper()
st.session_state.name = name

# Direction Selection
if "direction" not in st.session_state:
    st.session_state.direction = "Long" 
direction = st.sidebar.selectbox("Direction:", ["Long", "Short"])

# Call Option Price Input
if "call_px" not in st.session_state:
    st.session_state.call_px = 3.00
call_px_input = st.sidebar.text_input("Call Price:")
try:
    call_px = float(call_px_input) if call_px_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Call Price.")
    call_px = None

# Call Option Quantity Input
if "call_quantity" not in st.session_state:
    st.session_state.call_quantity = 1
call_quantity = st.sidebar.text_input("Call Quantity:")
try:
    call_quantity = int(call_quantity) if call_quantity else None
except:
    st.sidebar.error("Please enter a valid integer for Call Quantity.")
    call_quantity = None

# Call Option Implied Volatility Input
if "call_iv" not in st.session_state:
    st.session_state.call_iv = 0.25
call_iv_input = st.sidebar.text_input("IV for Call (%):")
try:
    call_iv = float(call_iv_input) / 100 if call_iv_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Call IV.")
    call_iv = None

# Put Option Price Input
if "put_px" not in st.session_state:
    st.session_state.put_px = 3.00
put_px_input = st.sidebar.text_input("Put Option Price:")
try:
    put_px = float(put_px_input) if put_px_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Put Option Price.")
    put_px = None

# Put Option Quantity Input
if "put_quantity" not in st.session_state:
    st.session_state.put_quantity = 1
put_quantity = st.sidebar.text_input("Put Quantity:")
try:
    put_quantity = int(put_quantity) if put_quantity else None
except:
    st.sidebar.error("Please enter a valid number for Put Quantity.")
    put_quantity = None

# Put Option Implied Volatility Input
if "put_iv" not in st.session_state:
    st.session_state.put_iv = 0.25
put_iv_input = st.sidebar.text_input("IV for Put (%):")
try:
    put_iv = float(put_iv_input) / 100 if put_iv_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Put IV.")
    put_iv = None

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
if all(v is not None for v in [spot, call_px, put_px, call_iv, put_iv, strike,
                               rate, time, dividend_yield, call_quantity,
                               put_quantity,name, direction, spot_stp, iv_stp]):
    # Greek Calculation
    call_blackScholes = BlackScholes(k=strike, s=spot,r=rate, t=time, iv=call_iv, b=dividend_yield)
    put_blackScholes = BlackScholes(k=strike, s=spot,r=rate, t=time, iv=put_iv, b=dividend_yield)
    delta = call_blackScholes.delta(optionType='CALL')*call_quantity + put_blackScholes.delta(optionType='PUT')*put_quantity
    gamma = call_blackScholes.gamma()*call_quantity + put_blackScholes.gamma()*put_quantity
    vega = call_blackScholes.vega()*call_quantity + put_blackScholes.vega()*put_quantity
    theta = call_blackScholes.theta(optionType='CALL')*call_quantity + put_blackScholes.theta(optionType='PUT')*put_quantity
    rho = call_blackScholes.rho(optionType='CALL')*call_quantity + put_blackScholes.rho(optionType='PUT')*put_quantity
    vanna = call_blackScholes.vanna()*call_quantity + put_blackScholes.vanna()*put_quantity
    charm = call_blackScholes.charm(optionType='CALL')*call_quantity + put_blackScholes.charm(optionType='PUT')*put_quantity
    volga = call_blackScholes.volga()*call_quantity + put_blackScholes.volga()*put_quantity

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
            fig = Plotting(spot=spot, call_px=call_px, put_px=put_px, 
                           call_iv=call_iv, put_iv=put_iv, k=strike,
                           r=rate, t=time, b=dividend_yield, name=name,
                           direction=direction, strategy='STRADDLE',
                           spot_stp=spot_stp, iv_stp=iv_stp, 
                           call_quantity=call_quantity, 
                           put_quantity=put_quantity).plot()
            st.pyplot(fig)
else:
    st.warning("Enter all inputs...")