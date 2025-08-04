import yfinance as yf
from helpers import *
import streamlit as st
from datetime import timedelta
from datetime import datetime

if "ticker" not in st.session_state: st.session_state.ticker = "SPY"
if "expiration_date" not in st.session_state: st.session_state.expiration_date = (datetime.today() + timedelta(days=90)).date()
if "spot_step" not in st.session_state: st.session_state.spot_step = 0.05
if "iv_step" not in st.session_state: st.session_state.iv_step = 0.10
if "dividend_yield" not in st.session_state: st.session_state.dividend_yield = 0.017 
if "rate" not in st.session_state: st.session_state.rate = 0.04 

if "strategy_inputs" not in st.session_state:
    st.session_state.strategy_inputs = {
        "Long Call Butterfly": {
            "low_strike": 550.0, "low_px": 5.00, "low_iv": 0.15,
            "atm_strike": 565.0, "atm_px": 4.00, "atm_iv": 0.13,
            "high_strike": 580.0, "high_px": 3.00, "high_iv": 0.11,
        },
        "Short Call Butterfly": {
            "low_strike": 550.0, "low_px": 5.00, "low_iv": 0.15,
            "atm_strike": 565.0, "atm_px": 4.00, "atm_iv": 0.13,
            "high_strike": 580.0, "high_px": 3.00, "high_iv": 0.11,
        },
        "Long Put Butterfly": {
            "low_strike": 550.0, "low_px": 5.00, "low_iv": 0.15,
            "atm_strike": 565.0, "atm_px": 4.00, "atm_iv": 0.13,
            "high_strike": 580.0, "high_px": 3.00, "high_iv": 0.11,
        },
        "Short Put Butterfly": {
            "low_strike": 550.0, "low_px": 5.00, "low_iv": 0.15,
            "atm_strike": 565.0, "atm_px": 4.00, "atm_iv": 0.13,
            "high_strike": 580.0, "high_px": 3.00, "high_iv": 0.11,
        },
        "Iron Butterfly": {
            "low_strike": 550.0, "low_px": 3.00, "low_iv": 0.11,
            "atm_strike": 565.0, "atm_px": 4.00, "atm_iv": 0.13,
            "atm_strike_2": 565.0, "atm_px_2": 4.00, "atm_iv_2": 0.13,
            "high_strike": 580.0, "high_px": 3.00, "high_iv": 0.11,
        },
        "Reverse Iron Butterfly": {
            "low_strike": 550.0, "low_px": 3.00, "low_iv": 0.11,
            "atm_strike": 565.0, "atm_px": 4.00, "atm_iv": 0.13,
            "atm_strike_2": 565.0, "atm_px_2": 4.00, "atm_iv_2": 0.13,
            "high_strike": 580.0, "high_px": 3.00, "high_iv": 0.11,
        },
    }

# --- Streamlit App Input & Layout --- 
# Title
st.title("Butterfly Option Strategy")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("Option Inputs")

# Ticker Input
ticker = st.sidebar.text_input("Ticker:", value=st.session_state.ticker).upper()
st.session_state.ticker = ticker

# yfinance Stock Request for Spot & Dividend Yield
stock_info = None
spot = None
dividend_yield = 0.0
if ticker:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            spot = hist['Close'].iloc[-1]
        else:
            st.sidebar.error(f"Failed to retrieve price for {ticker} (check yfinance indexing)...")

        stock_info = stock.info
        dividend_yield_value = stock_info.get("dividendYield", None)
        if dividend_yield_value is not None:
            dividend_yield = dividend_yield_value / 100
        else:
            dividend_yield = 0.0

    except:
        st.sidebar.error(f"Failed to retrieve data for {ticker}...")

# Sub-Strategy Selection
if "sub_strategy" not in st.session_state:
    st.session_state.sub_strategy = "Long Call Butterfly"
sub_strategy = st.sidebar.selectbox("Sub-Strategy:",
                                    list(st.session_state.strategy_inputs.keys()),
                                    index=list(st.session_state.strategy_inputs.keys()).index(st.session_state.sub_strategy)
                                   )
st.session_state.sub_strategy = sub_strategy

current_strategy_inputs = st.session_state.strategy_inputs[sub_strategy]

if sub_strategy in ["Long Call Butterfly", "Short Call Butterfly",
                    "Long Put Butterfly", "Short Put Butterfly"]:

    option_type = "Call" if "Call" in sub_strategy else "Put"

    # Low Strike
    low_strike_input = st.sidebar.text_input(f"Strike Price of Low {option_type} Option:", value=str(current_strategy_inputs["low_strike"]))
    try:
        low_strike = float(low_strike_input) if low_strike_input else None
        if low_strike is not None: current_strategy_inputs["low_strike"] = low_strike
    except ValueError: st.sidebar.error("Please enter a valid number for Low Strike...")

    # Low Price
    low_px_input = st.sidebar.text_input(f"Low Strike {option_type} Option Price ($):", value=str(current_strategy_inputs["low_px"]))
    try:
        low_px = float(low_px_input) if low_px_input else None
        if low_px is not None: current_strategy_inputs["low_px"] = low_px
    except ValueError: st.sidebar.error("Please enter a valid number for Low Option Price...")

    # Low IV
    low_iv_input = st.sidebar.text_input(f"IV for Low Strike {option_type} (%):", value=str(current_strategy_inputs["low_iv"] * 100))
    try:
        low_iv = float(low_iv_input) / 100 if low_iv_input else None
        if low_iv is not None: current_strategy_inputs["low_iv"] = low_iv
    except ValueError: st.sidebar.error("Please enter a valid number for Low IV...")

    # ATM Strike
    atm_strike_input = st.sidebar.text_input(f"Strike Price of ATM {option_type} Option:", value=str(current_strategy_inputs["atm_strike"]))
    try:
        atm_strike = float(atm_strike_input) if atm_strike_input else None
        if atm_strike is not None: current_strategy_inputs["atm_strike"] = atm_strike
    except ValueError: st.sidebar.error("Please enter a valid number for ATM Strike...")

    # ATM Price
    atm_px_input = st.sidebar.text_input(f"ATM Strike {option_type} Option Price ($):", value=str(current_strategy_inputs["atm_px"]))
    try:
        atm_px = float(atm_px_input) if atm_px_input else None
        if atm_px is not None: current_strategy_inputs["atm_px"] = atm_px
    except ValueError: st.sidebar.error("Please enter a valid number for ATM Option Price...")

    # ATM IV
    atm_iv_input = st.sidebar.text_input(f"IV for ATM Strike {option_type} (%):", value=str(current_strategy_inputs["atm_iv"] * 100))
    try:
        atm_iv = float(atm_iv_input) / 100 if atm_iv_input else None
        if atm_iv is not None: current_strategy_inputs["atm_iv"] = atm_iv
    except ValueError: st.sidebar.error("Please enter a valid number for ATM IV...")

    # High Strike
    high_strike_input = st.sidebar.text_input(f"Strike Price of High {option_type} Option:", value=str(current_strategy_inputs["high_strike"]))
    try:
        high_strike = float(high_strike_input) if high_strike_input else None
        if high_strike is not None: current_strategy_inputs["high_strike"] = high_strike
    except ValueError: st.sidebar.error("Please enter a valid number for High Strike...")

    # High Price
    high_px_input = st.sidebar.text_input(f"High Strike {option_type} Option Price ($):", value=str(current_strategy_inputs["high_px"]))
    try:
        high_px = float(high_px_input) if high_px_input else None
        if high_px is not None: current_strategy_inputs["high_px"] = high_px
    except ValueError: st.sidebar.error("Please enter a valid number for High Option Price...")

    # High IV
    high_iv_input = st.sidebar.text_input(f"IV for High Strike {option_type} (%):", value=str(current_strategy_inputs["high_iv"] * 100))
    try:
        high_iv = float(high_iv_input) / 100 if high_iv_input else None
        if high_iv is not None: current_strategy_inputs["high_iv"] = high_iv
    except ValueError: st.sidebar.error("Please enter a valid number for High IV...")

    atm_strike_2 = None
    atm_px_2 = None
    atm_iv_2 = None

elif sub_strategy in ["Iron Butterfly", "Reverse Iron Butterfly"]:
    # Low Put Option
    low_strike_input = st.sidebar.text_input(f"Low Put Option Strike:", value=str(current_strategy_inputs["low_strike"]))
    try:
        low_strike = float(low_strike_input) if low_strike_input else None
        if low_strike is not None: current_strategy_inputs["low_strike"] = low_strike
    except ValueError: st.sidebar.error("Please enter a valid number for Low Put Option Strike...")

    low_px_input = st.sidebar.text_input(f"Low Put Option Price ($):", value=str(current_strategy_inputs["low_px"]))
    try:
        low_px = float(low_px_input) if low_px_input else None
        if low_px is not None: current_strategy_inputs["low_px"] = low_px
    except ValueError: st.sidebar.error("Please enter a valid number for Low Put Option Price...")

    low_iv_input = st.sidebar.text_input(f"Lower Strike Put Option IV (%):", value=str(current_strategy_inputs["low_iv"] * 100))
    try:
        low_iv = float(low_iv_input) / 100 if low_iv_input else None
        if low_iv is not None: current_strategy_inputs["low_iv"] = low_iv
    except ValueError: st.sidebar.error("Please enter a valid number for Low Put Option IV...")

    # ATM Put Option
    atm_strike_input = st.sidebar.text_input(f"ATM Put Option Strike:", value=str(current_strategy_inputs["atm_strike"]))
    try:
        atm_strike = float(atm_strike_input) if atm_strike_input else None
        if atm_strike is not None: current_strategy_inputs["atm_strike"] = atm_strike
    except ValueError: st.sidebar.error("Please enter a valid number for ATM Put Option Strike...")

    atm_px_input = st.sidebar.text_input(f"ATM Put Option Price ($):", value=str(current_strategy_inputs["atm_px"]))
    try:
        atm_px = float(atm_px_input) if atm_px_input else None
        if atm_px is not None: current_strategy_inputs["atm_px"] = atm_px
    except ValueError: st.sidebar.error("Please enter a valid number for ATM Put Option Price...")

    atm_iv_input = st.sidebar.text_input(f"ATM Put Option IV (%):", value=str(current_strategy_inputs["atm_iv"] * 100))
    try:
        atm_iv = float(atm_iv_input) / 100 if atm_iv_input else None
        if atm_iv is not None: current_strategy_inputs["atm_iv"] = atm_iv
    except ValueError: st.sidebar.error("Please enter a valid number for ATM Put Option IV...")

    # ATM Call Option
    atm_strike_input_2 = st.sidebar.text_input(f"ATM Call Option Strike:", value=str(current_strategy_inputs["atm_strike_2"]))
    try:
        atm_strike_2 = float(atm_strike_input_2) if atm_strike_input_2 else None
        if atm_strike_2 is not None: current_strategy_inputs["atm_strike_2"] = atm_strike_2
    except ValueError: st.sidebar.error("Please enter a valid number for ATM Call Option Strike...")

    atm_px_input_2 = st.sidebar.text_input(f"ATM Call Option Price ($):", value=str(current_strategy_inputs["atm_px_2"]))
    try:
        atm_px_2 = float(atm_px_input_2) if atm_px_input_2 else None
        if atm_px_2 is not None: current_strategy_inputs["atm_px_2"] = atm_px_2
    except ValueError: st.sidebar.error("Please enter a valid number for ATM Call Option Price...")

    atm_iv_2_input = st.sidebar.text_input(f"ATM Call Option IV (%):", value=str(current_strategy_inputs["atm_iv_2"] * 100))
    try:
        atm_iv_2 = float(atm_iv_2_input) / 100 if atm_iv_2_input else None
        if atm_iv_2 is not None: current_strategy_inputs["atm_iv_2"] = atm_iv_2
    except ValueError: st.sidebar.error("Please enter a valid number for ATM Call Option IV...")

    # High Call Option
    high_strike_input = st.sidebar.text_input(f"High Call Option Strike:", value=str(current_strategy_inputs["high_strike"]))
    try:
        high_strike = float(high_strike_input) if high_strike_input else None
        if high_strike is not None: current_strategy_inputs["high_strike"] = high_strike
    except ValueError: st.sidebar.error("Please enter a valid number for High Call Option Strike...")

    high_px_input = st.sidebar.text_input(f"High Call Option Price ($):", value=str(current_strategy_inputs["high_px"]))
    try:
        high_px = float(high_px_input) if high_px_input else None
        if high_px is not None: current_strategy_inputs["high_px"] = high_px
    except ValueError: st.sidebar.error("Please enter a valid number for High Call Option Price...")

    high_iv_input = st.sidebar.text_input(f"High Call Option IV (%):", value=str(current_strategy_inputs["high_iv"] * 100))
    try:
        high_iv = float(high_iv_input) / 100 if high_iv_input else None
        if high_iv is not None: current_strategy_inputs["high_iv"] = high_iv
    except ValueError: st.sidebar.error("Please enter a valid number for High Call Option IV...")

# Time Input
if "time" not in st.session_state:
    st.session_state.time = 0.5
default_expiration_date = (datetime.today() + timedelta(days=1)).date()
expiration_date = st.sidebar.date_input("Expiration Date:", 
                                        min_value=datetime.today().date() + timedelta(days=1),
                                        max_value=datetime.today().date() + timedelta(days=3650),
                                        value=(datetime.today() + timedelta(days=int(st.session_state.time * 180))).date())
time = (expiration_date - datetime.today().date()).days / 365
st.session_state.time = time
st.sidebar.write(f"**Time to Expiry:** {time:.2f} years")

# Spot Price
if spot:
    st.sidebar.write(f"**Spot Price:** ${spot:.2f}")
else:
    st.sidebar.warning("Spot price not available...")

# Dividend Yield
st.session_state.dividend_yield = dividend_yield 
st.sidebar.write(f"**Dividend Yield:** {100*st.session_state.dividend_yield:.2f}%")

# Risk-Free Rate Request
try:
    rate = interpolate_rates(get_rates_value_dict(), time)
except:
    st.sidebar.error(f"Failed to interpolate risk-free rate...")
    rate = st.session_state.rate
st.session_state.rate = rate
st.sidebar.write(f"**Risk-Free Rate:** {100*rate:.2f}%")


# Sidebar header
st.sidebar.header('Dashboard Settings')

# Style
if "butterfly_style" not in st.session_state:
    st.session_state.butterfly_style = 'European'
style = st.sidebar.selectbox("Style:", ["European", "American"], index=["European", "American"].index(st.session_state.butterfly_style))
st.session_state.butterfly_style = style

# Spot Step Slider
spot_step_raw_value = st.sidebar.slider('Spot Step Slider:',
                             min_value=1,
                             max_value=25,
                             step=1,
                             value=int(st.session_state.spot_step * 100),
                             format="%d%%")
spot_step = spot_step_raw_value / 100
st.session_state.spot_step = spot_step

# Implied Volatility Step Slider
iv_step_raw_value = st.sidebar.slider('IV Step Slider:',
                             min_value=1,
                             max_value=25,
                             step=1,
                             value=int(st.session_state.iv_step * 100),
                             format="%d%%")
iv_step = iv_step_raw_value / 100
st.session_state.iv_step = iv_step


# --- Streamlit App Output & Validation --- 
validation_errors = []

# Validation
if spot is None or spot <= 0: validation_errors.append("Spot price must be positive...")
if time <= 0: validation_errors.append("Time to expiry must be positive...")
if rate is None or rate <= 0: validation_errors.append("Risk-free rate must be positive...")
if dividend_yield is None or dividend_yield < 0: validation_errors.append("Dividend yield must be non-negative...")

if sub_strategy in ["Long Call Butterfly", "Short Call Butterfly",
                    "Long Put Butterfly", "Short Put Butterfly"]:
    low_strike = current_strategy_inputs["low_strike"]
    low_px = current_strategy_inputs["low_px"]
    low_iv = current_strategy_inputs["low_iv"]
    atm_strike = current_strategy_inputs["atm_strike"]
    atm_px = current_strategy_inputs["atm_px"]
    atm_iv = current_strategy_inputs["atm_iv"]
    high_strike = current_strategy_inputs["high_strike"]
    high_px = current_strategy_inputs["high_px"]
    high_iv = current_strategy_inputs["high_iv"]

    if low_strike is None or low_strike <= 0: validation_errors.append(f"Low {option_type} strike must be positive...")
    if low_px is None or low_px <= 0: validation_errors.append(f"Low {option_type} price must be positive...")
    if low_iv is None or low_iv <= 0: validation_errors.append(f"Low {option_type} IV must be positive...")
    if atm_strike is None or atm_strike <= 0: validation_errors.append(f"ATM {option_type} strike must be positive...")
    if atm_px is None or atm_px <= 0: validation_errors.append(f"ATM {option_type} price must be positive...")
    if atm_iv is None or atm_iv <= 0: validation_errors.append(f"ATM {option_type} IV must be positive...")
    if high_strike is None or high_strike <= 0: validation_errors.append(f"High {option_type} strike must be positive...")
    if high_px is None or high_px <= 0: validation_errors.append(f"High {option_type} price must be positive...")
    if high_iv is None or high_iv <= 0: validation_errors.append(f"High {option_type} IV must be positive...")

    if all(v is not None for v in [low_strike, atm_strike, high_strike]):
        if not (low_strike < atm_strike < high_strike):
            validation_errors.append(f"Strikes must be ordered: Low ({low_strike}) < ATM ({atm_strike}) < High ({high_strike}).")

elif sub_strategy in ["Iron Butterfly", "Reverse Iron Butterfly"]:
    low_strike = current_strategy_inputs["low_strike"]
    low_px = current_strategy_inputs["low_px"]
    low_iv = current_strategy_inputs["low_iv"]
    atm_strike = current_strategy_inputs["atm_strike"] 
    atm_px = current_strategy_inputs["atm_px"] 
    atm_iv = current_strategy_inputs["atm_iv"] 
    atm_strike_2 = current_strategy_inputs["atm_strike_2"]
    atm_px_2 = current_strategy_inputs["atm_px_2"] 
    atm_iv_2 = current_strategy_inputs["atm_iv_2"] 
    high_strike = current_strategy_inputs["high_strike"]
    high_px = current_strategy_inputs["high_px"]
    high_iv = current_strategy_inputs["high_iv"]

    if low_strike is None or low_strike <= 0: validation_errors.append("Low Put strike must be positive...")
    if low_px is None or low_px <= 0: validation_errors.append("Low Put price must be positive...")
    if low_iv is None or low_iv <= 0: validation_errors.append("Low Put IV must be positive...")
    if atm_strike is None or atm_strike <= 0: validation_errors.append("ATM Put strike must be positive...")
    if atm_px is None or atm_px <= 0: validation_errors.append("ATM Put price must be positive...")
    if atm_iv is None or atm_iv <= 0: validation_errors.append("ATM Put IV must be positive...")
    if atm_strike_2 is None or atm_strike_2 <= 0: validation_errors.append("ATM Call strike must be positive...")
    if atm_px_2 is None or atm_px_2 <= 0: validation_errors.append("ATM Call price must be positive...")
    if atm_iv_2 is None or atm_iv_2 <= 0: validation_errors.append("ATM Call IV must be positive...")
    if high_strike is None or high_strike <= 0: validation_errors.append("High Call strike must be positive...")
    if high_px is None or high_px <= 0: validation_errors.append("High Call price must be positive...")
    if high_iv is None or high_iv <= 0: validation_errors.append("High Call IV must be positive...")

    if all(v is not None for v in [low_strike, atm_strike, atm_strike_2, high_strike]):
        if not (low_strike < atm_strike and atm_strike == atm_strike_2 and atm_strike_2 < high_strike):
            validation_errors.append(f"Strikes must be ordered: Low Put ({low_strike}) < ATM Put ({atm_strike}) == ATM Call ({atm_strike_2}) < High Call ({high_strike})...")


if validation_errors:
    for error in validation_errors:
        st.error(error)
    st.warning("Please correct the inputs to view the dashboard...")
else:
    # Greek Calculation
    try:
        low_bs = BlackScholes(k=low_strike, s=spot, r=rate, t=time, iv=low_iv, b=dividend_yield)
        atm_bs = BlackScholes(k=atm_strike, s=spot, r=rate, t=time, iv=atm_iv, b=dividend_yield)

        if sub_strategy in ["Iron Butterfly", "Reverse Iron Butterfly"]:
            atm_2_bs = BlackScholes(k=atm_strike_2, s=spot, r=rate, t=time, iv=atm_iv_2, b=dividend_yield)
            high_bs = BlackScholes(k=high_strike, s=spot, r=rate, t=time, iv=high_iv, b=dividend_yield)
        elif sub_strategy in ["Long Call Butterfly", "Short Call Butterfly", "Long Put Butterfly", "Short Put Butterfly"]:
            high_bs = BlackScholes(k=high_strike, s=spot, r=rate, t=time, iv=high_iv, b=dividend_yield)
            atm_2_bs = None
        else:
            atm_2_bs = None
            high_bs = None

    except:
        st.error(f"Error calculating Black Scholes values...")
        st.stop() 


    delta, gamma, vega, theta, rho, vanna, charm, volga = [0.0] * 8

    if sub_strategy in ["Long Call Butterfly", "Short Call Butterfly",
                        "Long Put Butterfly", "Short Put Butterfly"]:
        sign = 1 if "Long" in sub_strategy else -1
        delta = sign * (low_bs.delta(option_type=option_type) - atm_bs.delta(option_type=option_type)*2 + high_bs.delta(option_type=option_type))
        gamma = sign * (low_bs.gamma() - atm_bs.gamma()*2 + high_bs.gamma())
        vega = sign * (low_bs.vega() - atm_bs.vega()*2 + high_bs.vega())
        theta = sign * (low_bs.theta(option_type=option_type) - atm_bs.theta(option_type=option_type)*2 + high_bs.theta(option_type=option_type))
        rho = sign * (low_bs.rho(option_type=option_type) - atm_bs.rho(option_type=option_type)*2 + high_bs.rho(option_type=option_type))
        vanna = sign * (low_bs.vanna() - atm_bs.vanna()*2 + high_bs.vanna())
        charm = sign * (low_bs.charm(option_type=option_type) - atm_bs.charm(option_type=option_type)*2 + high_bs.charm(option_type=option_type))
        volga = sign * (low_bs.volga() - atm_bs.volga()*2 + high_bs.volga())

    elif sub_strategy in ["Iron Butterfly", "Reverse Iron Butterfly"]:
        sign = -1 if "Reverse" in sub_strategy else 1
        delta = sign * (low_bs.delta(option_type='Put') - atm_bs.delta(option_type='Put') - atm_2_bs.delta(option_type='Call') + high_bs.delta(option_type='Call'))
        gamma = sign * (low_bs.gamma() - atm_bs.gamma() - atm_2_bs.gamma() + high_bs.gamma())
        vega = sign * (low_bs.vega() - atm_bs.vega() - atm_2_bs.vega() + high_bs.vega())
        theta = sign * (low_bs.theta(option_type='Put') - atm_bs.theta(option_type='Put') - atm_2_bs.theta(option_type='Call') + high_bs.theta(option_type='Call'))
        rho = sign * (low_bs.rho(option_type='Put') - atm_bs.rho(option_type='Put') - atm_2_bs.rho(option_type='Call') + high_bs.rho(option_type='Call'))
        vanna = sign * (low_bs.vanna() - atm_bs.vanna() - atm_2_bs.vanna() + high_bs.vanna())
        charm = sign * (low_bs.charm(option_type='Put') - atm_bs.charm(option_type='Put') - atm_2_bs.charm(option_type='Call') + high_bs.charm(option_type='Call'))
        volga = sign * (low_bs.volga() - atm_bs.volga() - atm_2_bs.volga() + high_bs.volga())

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
        st.caption("Greeks represent the size and direction for the initial strategy.")

    # Graph Generation
    matrix_list = None
    instance_list = None
    try:
        if sub_strategy == "Long Call Butterfly":
            low = Matrix(spot, low_px, low_iv, low_strike, rate, time, 
                         dividend_yield, 'Call', style, spot_step, iv_step)
            atm = Matrix(spot, atm_px, atm_iv, atm_strike, rate, time, 
                         dividend_yield, 'Call', style, spot_step, iv_step)
            high = Matrix(spot, high_px, high_iv, high_strike, rate, time,
                          dividend_yield, 'Call', style, spot_step, iv_step)
            try:
                matrix_list = process_butterfly(low, atm, high, 'Long', 'Short', 'Long')
            except:
                matrix_list = [low.get_matrix(direction='Long'), atm.get_matrix(direction='Short')*2, high.get_matrix(direction='Long')]
            instance_list = [low, atm, high]
        elif sub_strategy == "Short Call Butterfly":
            low = Matrix(spot, low_px, low_iv, low_strike, rate, time, 
                         dividend_yield, 'Call', style, spot_step, iv_step)
            atm = Matrix(spot, atm_px, atm_iv, atm_strike, rate, time, 
                         dividend_yield, 'Call', style, spot_step, iv_step)
            high = Matrix(spot, high_px, high_iv, high_strike, rate, time, 
                          dividend_yield, 'Call', style, spot_step, iv_step)
            try:
                matrix_list = process_butterfly(low, atm, high, 'Short', 'Long', 'Short')
            except:
                matrix_list = [low.get_matrix('Short'), atm.get_matrix('Long')*2, high.get_matrix('Short')]
            instance_list = [low, atm, high]
        elif sub_strategy == "Long Put Butterfly":
            low = Matrix(spot, low_px, low_iv, low_strike, rate, time, 
                         dividend_yield, 'Put', style, spot_step, iv_step)
            atm = Matrix(spot, atm_px, atm_iv, atm_strike, rate, time, 
                         dividend_yield, 'Put', style, spot_step, iv_step)
            high = Matrix(spot, high_px, high_iv, high_strike, rate, time, 
                          dividend_yield, 'Put', style, spot_step, iv_step)
            try:
                matrix_list = process_butterfly(low, atm, high, 'Long', 'Short', 'Long')
            except:
                matrix_list = [low.get_matrix('Long'), atm.get_matrix('Short')*2, high.get_matrix('Long')]
            instance_list = [low, atm, high]
        elif sub_strategy == "Short Put Butterfly":
            low = Matrix(spot, low_px, low_iv, low_strike, rate, time, 
                         dividend_yield, 'Put', style, spot_step, iv_step)
            atm = Matrix(spot, atm_px, atm_iv, atm_strike, rate, time, 
                         dividend_yield, 'Put', style, spot_step, iv_step)
            high = Matrix(spot, high_px, high_iv, high_strike, rate, time, 
                          dividend_yield, 'Put', style, spot_step, iv_step)
            try:
                matrix_list = process_butterfly(low, atm, high, 'Short', 'Long', 'Short')
            except:
                matrix_list = [low.get_matrix('Short'), atm.get_matrix('Long')*2, high.get_matrix('Short')]
            instance_list = [low, atm, high]
        elif sub_strategy == "Iron Butterfly":
            low = Matrix(spot, low_px, low_iv, low_strike, rate, time, 
                         dividend_yield, 'Put', style, spot_step, iv_step)
            atm = Matrix(spot, atm_px, atm_iv, atm_strike, rate, time, 
                         dividend_yield, 'Put', style, spot_step, iv_step)
            atm_2 = Matrix(spot, atm_px_2, atm_iv_2, atm_strike_2, rate, time, 
                           dividend_yield, 'Call', style, spot_step, iv_step)
            high = Matrix(spot, high_px, high_iv, high_strike, rate, time, 
                          dividend_yield, 'Call', style, spot_step, iv_step)
            try:
                matrix_list = process_iron_butterfly(low, atm, atm_2, high, 'Long', 'Short', 'Long')
            except:
                matrix_list = [low.get_matrix('Long'), atm.get_matrix('Short'), atm_2.get_matrix('Short'), high.get_matrix('Long')]
            instance_list = [low, atm, atm_2, high]
        elif sub_strategy == "Reverse Iron Butterfly":
            low = Matrix(spot, low_px, low_iv, low_strike, rate, time, 
                         dividend_yield, 'Put', style, spot_step, iv_step)
            atm = Matrix(spot, atm_px, atm_iv, atm_strike, rate, time, 
                         dividend_yield, 'Put', style, spot_step, iv_step)
            atm_2 = Matrix(spot, atm_px_2, atm_iv_2, atm_strike_2, rate, time, 
                           dividend_yield, 'Call', style, spot_step, iv_step)
            high = Matrix(spot, high_px, high_iv, high_strike, rate, time, 
                          dividend_yield, 'Call', style, spot_step, iv_step)
            try:
                matrix_list = process_iron_butterfly(low, atm, atm_2, high, 'Short', 'Long', 'Short')
            except:
                matrix_list = [low.get_matrix('Short'), atm.get_matrix('Long'), atm_2.get_matrix('Long'), high.get_matrix('Short')]
            instance_list = [low, atm, atm_2, high]
    except:
        st.error(f"Error generating graph...")
        st.stop()

    # Graph Output
    with col2:
            if matrix_list is None:
                raise ValueError("No matrix list generated...")
            elif instance_list is None:
                raise ValueError("No instance list generated...")
            else:
                plot_instance = Plotting(matrix_list, instance_list, sub_strategy, ticker)
                fig = plot_instance.plot()
                st.pyplot(fig, clear_figure=True)