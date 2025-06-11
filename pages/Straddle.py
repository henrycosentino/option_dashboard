import streamlit as st
import yfinance as yf
from datetime import timedelta
from datetime import datetime
from helpers import BlackScholes, Plotting, Matrix, get_rates_value_dict, interpolate_rates

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
st.session_state.straddle_ticker = ticker

# Direction Selection
if "straddle_direction" not in st.session_state:
    st.session_state.straddle_direction = "Long" 
direction = st.sidebar.selectbox("Direction:", ["Long", "Short"])
st.session_state.straddle_direction = direction

# Call Option Price Input
if "straddle_call_px" not in st.session_state:
    st.session_state.straddle_call_px = 3.00
straddle_call_px_input = st.sidebar.text_input("Call Price:")
try:
    call_px = float(straddle_call_px_input) if straddle_call_px_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Call Price...")
    call_px = None
st.session_state.straddle_call_px = call_px

# Call Option Implied Volatility Input
if "straddle_call_iv" not in st.session_state:
    st.session_state.straddle_call_iv = 0.25
straddle_call_iv_input = st.sidebar.text_input("IV for Call (%):")
try:
    call_iv = float(straddle_call_iv_input) / 100 if straddle_call_iv_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Call IV...")
    call_iv = None
st.session_state.straddle_call_iv = call_iv

# Call Option Quantity Input
if "straddle_call_quantity" not in st.session_state:
    st.session_state.straddle_call_quantity = 1
straddle_call_quantity = st.sidebar.text_input("Call Quantity:")
try:
    call_quantity = int(straddle_call_quantity) if straddle_call_quantity else None
except:
    st.sidebar.error("Please enter a valid integer for Call Quantity...")
    call_quantity = None
st.session_state.straddle_call_quantity = call_quantity

# Put Option Price Input
if "straddle_put_px" not in st.session_state:
    st.session_state.straddle_put_px = 3.00
straddle_put_px_input = st.sidebar.text_input("Put Option Price:")
try:
    put_px = float(straddle_put_px_input) if straddle_put_px_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Put Option Price...")
    put_px = None
st.session_state.straddle_put_px = put_px

# Put Option Implied Volatility Input
if "straddle_put_iv" not in st.session_state:
    st.session_state.straddle_put_iv = 0.25
straddle_put_iv_input = st.sidebar.text_input("IV for Put (%):")
try:
    put_iv = float(straddle_put_iv_input) / 100 if straddle_put_iv_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Put IV...")
    put_iv = None
st.session_state.straddle_put_iv = put_iv

# Put Option Quantity Input
if "straddle_put_quantity" not in st.session_state:
    st.session_state.straddle_put_quantity = 1
straddle_put_quantity = st.sidebar.text_input("Put Quantity:")
try:
    put_quantity = int(straddle_put_quantity) if straddle_put_quantity else None
except:
    st.sidebar.error("Please enter a valid number for Put Quantity...")
    put_quantity = None
st.session_state.straddle_put_quantity = put_quantity

# Strike Input
if "straddle_strike" not in st.session_state:
    st.session_state.straddle_strike = 650.00
straddle_strike_input = st.sidebar.text_input("Strike:")
try:
    strike = float(straddle_strike_input) if straddle_strike_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Strike...")
    strike = None
st.session_state.straddle_strike = strike

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

# yfinance Stock Request for Spot & Diviend Yield
spot = None
dividend_yield = None
if "straddle_spot" not in st.session_state: st.session_state.straddle_spot = 600.0
if "straddle_dividend_yield" not in st.session_state: st.session_state.straddle_dividend_yield = 0.017
if ticker:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d")
        if not hist.empty:
            spot = hist.iloc[0,3]
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

if dividend_yield:
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

# Spot Step Slider
spot_step_raw_value = st.sidebar.slider('Spot Step Slider:',
                             min_value=1,
                             max_value=25,
                             step=1,
                             format="%d%%")
spot_step = spot_step_raw_value / 100
st.session_state.spot_step = spot_step

# Implied Volatility Step Slider
iv_step_raw_value = st.sidebar.slider('IV Step Slider:',
                             min_value=1,
                             max_value=25,
                             step=1,
                             format="%d%%")
iv_step = iv_step_raw_value / 100
st.session_state.iv_step = iv_step


### OUTPUT ###
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
                                          b=dividend_yield, option_type='Call', spot_step=spot_step, 
                                          iv_step=iv_step)
            put_matrix_instance = Matrix(spot=spot, px=put_px, iv=put_iv, k=strike, r=rate, t=time, 
                                         b=dividend_yield, option_type='Put', spot_step=spot_step, 
                                         iv_step=iv_step)

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
