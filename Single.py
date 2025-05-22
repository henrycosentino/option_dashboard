import streamlit as st
from plotting import Plotting
from BlackScholes import BlackScholes
import requests
import yfinance as yf
from datetime import timedelta
from datetime import datetime
from InterpolateRate import get_rates_value_dict, interpolate_rates

# streamlit run "/Users/henrycosentino/Desktop/Python/Projects/Option PnL Dashboard/Single.py"

### TO DO ###
    # Change interpolation method from linear for forward curve (do some research for this)
    # Save all inputs in each page
    # Add more butterfly stratgies

# Title
st.set_page_config(page_title="Options Strategy App", layout="wide")
st.title("Single Option Strategy")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar 
st.sidebar.header("Option Inputs")

### INPUT ###
# Ticker
if "name" not in st.session_state:
    st.session_state.name = "SPY"
name = st.sidebar.text_input("Ticker:", value=st.session_state.get("name", "SPY")).upper()
st.session_state.name = name

# Option Type Selection
if "optionType" not in st.session_state:
    st.session_state.optionType = "Call" 
optionType = st.sidebar.selectbox("Option Type:", ["Call", "Put"])

# Option Direction Selection
if "direction" not in st.session_state:
    st.session_state.direction = "Long" 
direction = st.sidebar.selectbox("Direction:", ["Long", "Short"])
if direction == 'Long':
    exposure = 1
if direction == 'Short':
    exposure = -1

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
        st.session_state.dividend_yield = stock.info.get("dividendYield", None) / 100 if stock.info.get("dividendYield") else 0
        st.sidebar.write(f"**Dividend Yield:** {100*st.session_state.dividend_yield:.2f}%")
    except:
        st.sidebar.error("Failed to retrieve dividend yield.")
        st.session_state.dividend_yield = 0
dividend_yield = st.session_state.dividend_yield

# Risk-Free Rate Request
if 'rate' not in st.session_state:
    st.session_state.rate = 0.04
rate = interpolate_rates(get_rates_value_dict(), time)
st.sidebar.write(f"**Risk-Free Rate:** {100*rate:.2f}%")

# Sidebar header
st.sidebar.header('Dashboard Settings')

# Spot Step Slider
spot_stp_raw_value = st.sidebar.slider('Spot Step Slider:',
                             min_value=1,
                             max_value=25,
                             step=1,
                             format="%d%%")
spot_stp = spot_stp_raw_value / 100
st.session_state.spot_stp = spot_stp

# Implied Volatility Step Slider
iv_stp_raw_value = st.sidebar.slider('IV Step Slider:',
                             min_value=1,
                             max_value=25,
                             step=1,
                             format="%d%%")
iv_stp = iv_stp_raw_value / 100
st.session_state.iv_stp = iv_stp


### OUTPUT ###
if all(v is not None for v in [spot, iv, px, strike, rate, time,
                               dividend_yield, name, optionType,
                               direction, spot_stp, iv_stp]):
    # Greek Calculation
    blackScholes = BlackScholes(k=strike, s=spot,r=rate, t=time, iv=iv, b=dividend_yield)

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
                <p>Delta: <span>{blackScholes.delta(optionType)*exposure:.2f}</span></p>
                <p>Gamma: <span>{blackScholes.gamma()*exposure:.2f}</span></p>
                <p>Vega: <span>{blackScholes.vega()*exposure:.2f}</span></p>
                 <p>Volga: <span>{blackScholes.volga()*exposure:.2f}</span></p>
                <p>Theta: <span>{blackScholes.theta(optionType)*exposure:.2f}</span></p>
                <p>Rho: <span>{blackScholes.rho(optionType)*exposure:.2f}</span></p>
                <p>Vanna: <span>{blackScholes.vanna()*exposure:.2f}</span></p>
                <p>Charm: <span>{blackScholes.charm(optionType)*exposure:.2f}</span></p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("*Greeks represent the size and direction for the initial strategy level position")

    # Graph Output
    with col2:
            fig = Plotting(spot=spot, call_px=px, put_px=px,
                        call_iv=iv, put_iv=iv, k=strike, r=rate,
                        t=time, b=dividend_yield, name=name, 
                        optionType=optionType, direction=direction, 
                        spot_stp=spot_stp, iv_stp=iv_stp).plot()
            st.pyplot(fig, clear_figure=True)
else:
    st.warning("Enter all inputs...")