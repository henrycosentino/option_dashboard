import yfinance as yf
from helpers import *
import streamlit as st
from datetime import datetime
from datetime import timedelta

# --- Streamlit App Input & Layout --- 
# Title
st.set_page_config(page_title="Options Strategy App", layout="wide")
st.title("Single Option Strategy")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar 
st.sidebar.header("Option Inputs")

# Ticker
if "single_ticker" not in st.session_state:
    st.session_state.single_ticker = "SPY"
ticker = st.sidebar.text_input("Ticker:", value=st.session_state.single_ticker).upper()
st.session_state.single_ticker = ticker

# Option Type Selection
if "single_option_type" not in st.session_state:
    st.session_state.single_option_type = "Call"
option_type = st.sidebar.selectbox("Option Type:", ["Call", "Put"], index=["Call", "Put"].index(st.session_state.single_option_type))
st.session_state.single_option_type = option_type

# Option Direction Selection
if "single_direction" not in st.session_state:
    st.session_state.single_direction = "Long"
direction = st.sidebar.selectbox("Direction:", ["Long", "Short"], index=["Long", "Short"].index(st.session_state.single_direction))
st.session_state.single_direction = direction

if direction == 'Long':
    exposure = 1
if direction == 'Short':
    exposure = -1

# Option Price Input
if "single_px" not in st.session_state:
    st.session_state.single_px = 3.00
px_input = st.sidebar.text_input("Option Price:", value=str(st.session_state.single_px))
try:
    px = float(px_input) if px_input else None
    st.session_state.single_px = px
except ValueError:
    st.sidebar.error("Please enter a valid number for Option Price...")
    px = None

# Implied Volatility Input
if "single_iv" not in st.session_state:
    st.session_state.single_iv = 0.25
iv_input = st.sidebar.text_input("Implied Volatility (%):", value=str(st.session_state.single_iv * 100))
try:
    iv = float(iv_input) / 100 if iv_input else None
    st.session_state.single_iv = iv
except ValueError:
    st.sidebar.error("Please enter a valid number for Implied Volatility...")
    iv = None

# Strike Input
if "single_strike" not in st.session_state:
    st.session_state.single_strike = 650.00
strike_input = st.sidebar.text_input("Strike:", value=str(st.session_state.single_strike))
try:
    strike = float(strike_input) if strike_input else None
    st.session_state.single_strike = strike
except ValueError:
    st.sidebar.error("Please enter a valid number for Strike...")
    strike = None

# Time Input
if "single_time" not in st.session_state:
    st.session_state.single_time = 0.5

min_exp_date = datetime.today().date() + timedelta(days=1)
max_exp_date = datetime.today().date() + timedelta(days=3650)
default_exp_date = (datetime.today() + timedelta(days=int(st.session_state.single_time * 365))).date()

if default_exp_date < min_exp_date:
    initial_value_for_date_input = min_exp_date
elif default_exp_date > max_exp_date:
    initial_value_for_date_input = max_exp_date
else:
    initial_value_for_date_input = default_exp_date

expiration_date = st.sidebar.date_input("Expiration Date:", 
                                        min_value=min_exp_date,
                                        max_value=max_exp_date,
                                        value=initial_value_for_date_input)

time = (expiration_date - datetime.today().date()).days / 365
st.session_state.single_time = time
st.sidebar.write(f"**Time to Expiry:** {time:.2f} years")

# yfinance Stock Request for Spot & Diviend Yield
spot = None
dividend_yield = None
if "single_spot" not in st.session_state: st.session_state.single_spot = 600.0
if "single_dividend_yield" not in st.session_state: st.session_state.single_dividend_yield = 0.017
if ticker:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            spot = hist['Close'].iloc[-1]
        else:
            st.sidebar.error(f"Failed to retrieve price for {ticker} (check yfinance indexing)...")
            spot = st.session_state.single_spot

        stock_info = stock.info
        dividend_yield_value = stock_info.get("dividendYield", None)
        if dividend_yield_value is not None:
            dividend_yield = dividend_yield_value / 100
        else:
            dividend_yield = 0.0

    except:
        st.sidebar.error(f"Failed to retrieve data for {ticker}...")
        spot = st.session_state.single_spot
        dividend_yield = st.session_state.single_dividend_yield

if spot:
    st.sidebar.write(f"**Spot Price:** ${spot:.2f}")
    st.session_state.single_spot = spot

if dividend_yield:
    st.sidebar.write(f"**Dividend Yield:** {100*dividend_yield:.2f}%")
    st.session_state.single_dividend_yield = dividend_yield

# Risk-Free Rate Request
if 'single_rate' not in st.session_state:
    st.session_state.single_rate = 0.04
try:
    rate = interpolate_rates(get_rates_value_dict(), time)
except:
    st.sidebar.error(f"Error calculating risk-free rate...")
    rate = st.session_state.single_rate

st.session_state.single_rate = rate
st.sidebar.write(f"**Risk-Free Rate:** {100*rate:.2f}%")

# Sidebar header
st.sidebar.header('Dashboard Settings')

# Style
if "single_style" not in st.session_state:
    st.session_state.single_style = 'European'
style = st.sidebar.selectbox("Style:", ["European", "American"], index=["European", "American"].index(st.session_state.single_style))
st.session_state.single_style = style

# Spot Step Slider
if "single_spot_step" not in st.session_state:
    st.session_state.single_spot_step = 0.05
spot_step_raw_value = st.sidebar.slider('Spot Step Slider:',
                             min_value=1,
                             max_value=25,
                             value=int(st.session_state.single_spot_step * 100),
                             step=1,
                             format="%d%%")
spot_step = spot_step_raw_value / 100
st.session_state.single_spot_step = spot_step

# Implied Volatility Step Slider
if "single_iv_step" not in st.session_state:
    st.session_state.single_iv_step = 0.05
iv_step_raw_value = st.sidebar.slider('IV Step Slider:',
                             min_value=1,
                             max_value=25,
                             value=int(st.session_state.single_iv_step * 100),
                             step=1,
                             format="%d%%")
iv_step = iv_step_raw_value / 100
st.session_state.single_iv_step = iv_step

# --- Streamlit App Output --- 
if all(v is not None for v in [spot, iv, px, strike, rate, time, dividend_yield, ticker, 
                               option_type, direction, spot_step, iv_step]):
    if all(v >= 0 for v in [spot, iv, px, strike, rate, time, dividend_yield]):
        # Greek Calculation
        bs = BlackScholes(k=strike, s=spot,r=rate, t=time, iv=iv, b=dividend_yield)

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
                    <p>Delta: <span>{bs.delta(option_type)*exposure:.2f}</span></p>
                    <p>Gamma: <span>{bs.gamma()*exposure:.2f}</span></p>
                    <p>Vega: <span>{bs.vega()*exposure:.2f}</span></p>
                    <p>Volga: <span>{bs.volga()*exposure:.2f}</span></p>
                    <p>Theta: <span>{bs.theta(option_type)*exposure:.2f}</span></p>
                    <p>Rho: <span>{bs.rho(option_type)*exposure:.2f}</span></p>
                    <p>Vanna: <span>{bs.vanna()*exposure:.2f}</span></p>
                    <p>Charm: <span>{bs.charm(option_type)*exposure:.2f}</span></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Greeks represent the size and direction for the initial strategy")

        # Graph Output
        with col2:
                matrix_instance = Matrix(spot=spot, px=px, iv=iv, k=strike, r=rate, t=time, b=dividend_yield, style=style, 
                                         option_type=option_type, spot_step=spot_step, iv_step=iv_step)
                matrix = matrix_instance.get_matrix(direction)

                fig = Plotting(matrix, matrix_instance, 'Single', ticker).plot(direction, option_type)
                st.pyplot(fig, clear_figure=True)
    else:
        st.warning("Inputs must be greater than or equal to zero...")
else:
    st.warning("Enter all inputs to plot...")