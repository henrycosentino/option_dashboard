import yfinance as yf
from helpers import *
import streamlit as st
from datetime import datetime
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

# --- Streamlit App Input & Layout --- 
# Title
st.title("Straddle Option Strategy")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar 
st.sidebar.header("Option Inputs")

# Ticker Input
if "straddle_ticker" not in st.session_state:
    st.session_state.straddle_ticker = "SPY"
ticker = st.sidebar.text_input("Ticker:", value=st.session_state.straddle_ticker).upper()
if ticker:
    st.session_state.straddle_ticker = ticker

# Direction Selection
if "straddle_direction" not in st.session_state:
    st.session_state.straddle_direction = "Long" 
direction = st.sidebar.selectbox("Direction:", ["Long", "Short"], 
                                index=0 if st.session_state.straddle_direction == "Long" else 1)
st.session_state.straddle_direction = direction

# Call Option Price Input
if "straddle_call_px" not in st.session_state:
    st.session_state.straddle_call_px = 3.00
straddle_call_px_input = st.sidebar.text_input("Call Price:", 
                                              value=str(st.session_state.straddle_call_px) if st.session_state.straddle_call_px is not None else "")
if straddle_call_px_input:
    try:
        st.session_state.straddle_call_px = float(straddle_call_px_input)
    except ValueError:
        st.sidebar.error("Please enter a valid number for Call Price...")
call_px = st.session_state.straddle_call_px

# Call Option Implied Volatility Input
if "straddle_call_iv" not in st.session_state:
    st.session_state.straddle_call_iv = 25.0
straddle_call_iv_input = st.sidebar.text_input("IV for Call (%):", 
                                              value=str(st.session_state.straddle_call_iv) if st.session_state.straddle_call_iv is not None else "")
if straddle_call_iv_input:
    try:
        st.session_state.straddle_call_iv = float(straddle_call_iv_input)
    except ValueError:
        st.sidebar.error("Please enter a valid number for Call IV...")
call_iv = st.session_state.straddle_call_iv / 100 if st.session_state.straddle_call_iv is not None else None

# Call Option Quantity Input
if "straddle_call_quantity" not in st.session_state:
    st.session_state.straddle_call_quantity = 1
straddle_call_quantity_input = st.sidebar.text_input("Call Quantity:", 
                                                    value=str(st.session_state.straddle_call_quantity) if st.session_state.straddle_call_quantity is not None else "")
if straddle_call_quantity_input:
    try:
        st.session_state.straddle_call_quantity = int(straddle_call_quantity_input)
    except ValueError:
        st.sidebar.error("Please enter a valid integer for Call Quantity...")
call_quantity = st.session_state.straddle_call_quantity

# Put Option Price Input
if "straddle_put_px" not in st.session_state:
    st.session_state.straddle_put_px = 3.00
straddle_put_px_input = st.sidebar.text_input("Put Option Price:", 
                                             value=str(st.session_state.straddle_put_px) if st.session_state.straddle_put_px is not None else "")
if straddle_put_px_input:
    try:
        st.session_state.straddle_put_px = float(straddle_put_px_input)
    except ValueError:
        st.sidebar.error("Please enter a valid number for Put Option Price...")
put_px = st.session_state.straddle_put_px

# Put Option Implied Volatility Input
if "straddle_put_iv" not in st.session_state:
    st.session_state.straddle_put_iv = 25.0
straddle_put_iv_input = st.sidebar.text_input("IV for Put (%):", 
                                             value=str(st.session_state.straddle_put_iv) if st.session_state.straddle_put_iv is not None else "")
if straddle_put_iv_input:
    try:
        st.session_state.straddle_put_iv = float(straddle_put_iv_input)
    except ValueError:
        st.sidebar.error("Please enter a valid number for Put IV...")
put_iv = st.session_state.straddle_put_iv / 100 if st.session_state.straddle_put_iv is not None else None

# Put Option Quantity Input
if "straddle_put_quantity" not in st.session_state:
    st.session_state.straddle_put_quantity = 1
straddle_put_quantity_input = st.sidebar.text_input("Put Quantity:", 
                                                   value=str(st.session_state.straddle_put_quantity) if st.session_state.straddle_put_quantity is not None else "")
if straddle_put_quantity_input:
    try:
        st.session_state.straddle_put_quantity = int(straddle_put_quantity_input)
    except ValueError:
        st.sidebar.error("Please enter a valid number for Put Quantity...")
put_quantity = st.session_state.straddle_put_quantity

# Strike Input
if "straddle_strike" not in st.session_state:
    st.session_state.straddle_strike = 650.00
straddle_strike_input = st.sidebar.text_input("Strike:", 
                                             value=str(st.session_state.straddle_strike) if st.session_state.straddle_strike is not None else "")
if straddle_strike_input:
    try:
        st.session_state.straddle_strike = float(straddle_strike_input)
    except ValueError:
        st.sidebar.error("Please enter a valid number for Strike...")
strike = st.session_state.straddle_strike

# Time Input
if "straddle_time" not in st.session_state:
    st.session_state.straddle_time = 0.5

min_exp_date = datetime.today().date() + timedelta(days=1)
max_exp_date = datetime.today().date() + timedelta(days=3650)
default_exp_date = (datetime.today() + timedelta(days=int(st.session_state.straddle_time * 365))).date()

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
st.session_state.straddle_time = time
st.sidebar.write(f"**Time to Expiry:** {time:.2f} years")

# yfinance Stock Request for Spot & Dividend Yield
spot = None
dividend_yield = None
if "straddle_spot" not in st.session_state: st.session_state.straddle_spot = 600.0
if "straddle_dividend_yield" not in st.session_state: st.session_state.straddle_dividend_yield = 0.017
if ticker:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            spot = hist['Close'].iloc[-1]
        else:
            st.sidebar.error(f"Failed to retrieve price for {ticker} (check yfinance indexing)...")
            spot = st.session_state.straddle_spot

        stock_info = stock.info
        dividend_yield_value = stock_info.get("dividendYield", None)
        if dividend_yield_value is not None:
            dividend_yield = dividend_yield_value / 100
        else:
            dividend_yield = 0.0

    except:
        st.sidebar.error(f"Failed to retrieve data for {ticker}...")
        spot = st.session_state.straddle_spot
        dividend_yield = st.session_state.straddle_dividend_yield

if spot:
    st.sidebar.write(f"**Spot Price:** ${spot:.2f}")
    st.session_state.straddle_spot = spot

if dividend_yield is not None:
    st.sidebar.write(f"**Dividend Yield:** {100*dividend_yield:.2f}%")
    st.session_state.straddle_dividend_yield = dividend_yield

# Risk-Free Rate Request
if 'straddle_rate' not in st.session_state:
    st.session_state.straddle_rate = 0.04
try:
    rate = interpolate_rates(get_rates_value_dict(), time)
except:
    st.sidebar.error(f"Error calculating risk-free rate...")
    rate = st.session_state.straddle_rate

st.session_state.straddle_rate = rate
st.sidebar.write(f"**Risk-Free Rate:** {100*rate:.2f}%")

# Sidebar header
st.sidebar.header('Dashboard Settings')

# Style
if "straddle_style" not in st.session_state:
    st.session_state.straddle_style = 'European'
style = st.sidebar.selectbox("Style:", ["European", "American"], index=["European", "American"].index(st.session_state.straddle_style))
st.session_state.straddle_style = style

# Spot Step Slider
if "spot_step" not in st.session_state:
    st.session_state.spot_step = 0.10
spot_step_raw_value = st.sidebar.slider('Spot Step Slider:',
                             min_value=1,
                             max_value=25,
                             step=1,
                             value=int(st.session_state.spot_step * 100),
                             format="%d%%")
spot_step = spot_step_raw_value / 100
st.session_state.spot_step = spot_step

# Implied Volatility Step Slider
if "iv_step" not in st.session_state:
    st.session_state.iv_step = 0.10
iv_step_raw_value = st.sidebar.slider('IV Step Slider:',
                             min_value=1,
                             max_value=25,
                             step=1,
                             value=int(st.session_state.iv_step * 100),
                             format="%d%%")
iv_step = iv_step_raw_value / 100
st.session_state.iv_step = iv_step


# --- Streamlit App Output --- 
if all(v is not None for v in [spot, call_px, put_px, call_iv, put_iv, strike, rate, 
                               time, dividend_yield, call_quantity, put_quantity, 
                               ticker, direction, spot_step, iv_step]):
    if all(v >= 0 for v in [spot, call_px, put_px, call_iv, put_iv, strike, rate, 
                            time, dividend_yield, call_quantity, put_quantity]):
        # Greek Calculation
        call_blackScholes = BlackScholes(k=strike, s=spot,r=rate, t=time, iv=call_iv, b=dividend_yield)
        put_blackScholes = BlackScholes(k=strike, s=spot,r=rate, t=time, iv=put_iv, b=dividend_yield)
        delta = call_blackScholes.delta(option_type='CALL')*call_quantity + put_blackScholes.delta(option_type='PUT')*put_quantity
        gamma = call_blackScholes.gamma()*call_quantity + put_blackScholes.gamma()*put_quantity
        vega = call_blackScholes.vega()*call_quantity + put_blackScholes.vega()*put_quantity
        theta = call_blackScholes.theta(option_type='CALL')*call_quantity + put_blackScholes.theta(option_type='PUT')*put_quantity
        rho = call_blackScholes.rho(option_type='CALL')*call_quantity + put_blackScholes.rho(option_type='PUT')*put_quantity
        vanna = call_blackScholes.vanna()*call_quantity + put_blackScholes.vanna()*put_quantity
        charm = call_blackScholes.charm(option_type='CALL')*call_quantity + put_blackScholes.charm(option_type='PUT')*put_quantity
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
            st.caption("Greeks represent the size and direction for the initial strategy")

        # Graph Output
        with col2:
            call_matrix_instance = Matrix(spot=spot, px=call_px, iv=call_iv, k=strike, r=rate, t=time, 
                                          b=dividend_yield, option_type='Call', style=style, 
                                          spot_step=spot_step, iv_step=iv_step)
            put_matrix_instance = Matrix(spot=spot, px=put_px, iv=put_iv, k=strike, r=rate, t=time, 
                                         b=dividend_yield, option_type='Put', style=style, 
                                         spot_step=spot_step, iv_step=iv_step)
        
            try:
               with ThreadPoolExecutor(max_workers=2) as executor:
                    call_future = executor.submit(call_matrix_instance.get_matrix, direction=direction)
                    put_future = executor.submit(put_matrix_instance.get_matrix, direction=direction)
                    call_matrix = call_future.result() * call_quantity
                    put_matrix = put_future.result() * put_quantity
            except:
                call_matrix = call_matrix_instance.get_matrix(direction=direction) * call_quantity
                put_matrix = put_matrix_instance.get_matrix(direction=direction) * put_quantity

            plot_instance = Plotting(matrix=[call_matrix, put_matrix], 
                                    instance=[call_matrix_instance, put_matrix_instance], 
                                    strategy='Straddle', ticker=ticker)

            fig = plot_instance.plot(direction=direction)
            st.pyplot(fig, clear_figure=True)
    else:
        st.warning("Inputs must be greater than or equal to zero...")
else:
    st.warning("Enter all inputs to plot...")