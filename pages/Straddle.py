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
if "ticker" not in st.session_state:
    st.session_state.ticker = "SPY"
ticker = st.sidebar.text_input("Ticker:", value=st.session_state.ticker).upper()
st.session_state.ticker = ticker

# Direction Selection
if "direction" not in st.session_state:
    st.session_state.direction = "Long" 
direction = st.sidebar.selectbox("Direction:", ["Long", "Short"])
st.session_state.direction = direction

# Call Option Price Input
if "call_px" not in st.session_state:
    st.session_state.call_px = 3.00
call_px_input = st.sidebar.text_input("Call Price:")
try:
    call_px = float(call_px_input) if call_px_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Call Price.")
    call_px = None

# Call Option Implied Volatility Input
if "call_iv" not in st.session_state:
    st.session_state.call_iv = 0.25
call_iv_input = st.sidebar.text_input("IV for Call (%):")
try:
    call_iv = float(call_iv_input) / 100 if call_iv_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Call IV.")
    call_iv = None

# Call Option Quantity Input
if "call_quantity" not in st.session_state:
    st.session_state.call_quantity = 1
call_quantity = st.sidebar.text_input("Call Quantity:")
try:
    call_quantity = int(call_quantity) if call_quantity else None
except:
    st.sidebar.error("Please enter a valid integer for Call Quantity.")
    call_quantity = None

# Put Option Price Input
if "put_px" not in st.session_state:
    st.session_state.put_px = 3.00
put_px_input = st.sidebar.text_input("Put Option Price:")
try:
    put_px = float(put_px_input) if put_px_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Put Option Price.")
    put_px = None

# Put Option Implied Volatility Input
if "put_iv" not in st.session_state:
    st.session_state.put_iv = 0.25
put_iv_input = st.sidebar.text_input("IV for Put (%):")
try:
    put_iv = float(put_iv_input) / 100 if put_iv_input else None
except ValueError:
    st.sidebar.error("Please enter a valid number for Put IV.")
    put_iv = None

# Put Option Quantity Input
if "put_quantity" not in st.session_state:
    st.session_state.put_quantity = 1
put_quantity = st.sidebar.text_input("Put Quantity:")
try:
    put_quantity = int(put_quantity) if put_quantity else None
except:
    st.sidebar.error("Please enter a valid number for Put Quantity.")
    put_quantity = None

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
                                        value=(datetime.today() + timedelta(days=int(st.session_state.time * 180))).date())
time = (expiration_date - datetime.today().date()).days / 365
st.session_state.time = time
st.sidebar.write(f"**Time to Expiry:** {time:.2f} years")

# Spot Price Request
spot = None
if "spot" not in st.session_state:
    st.session_state.spot = 600.00
if ticker:
    stock = yf.Ticker(ticker)
    try:
        spot = float(stock.history(period="1d").iloc[0,3]) # This indexing method may change if yfinance updates
    except (KeyError, ValueError):
        st.sidebar.error(f"Failed to retrieve price for {ticker}. Check the ticker.")
if spot:
    st.sidebar.write(f"**Spot Price:** ${spot:.2f}")

# Dividend Yield Request
if "dividend_yield" not in st.session_state:
    st.session_state.dividend_yield = 0.017
if ticker:
    stock = yf.Ticker(ticker)
    try:
        st.session_state.dividend_yield = float(stock.info.get("dividendYield", None) / 100) if stock.info.get("dividendYield") else 0.0
        st.sidebar.write(f"**Dividend Yield:** {100*st.session_state.dividend_yield:.2f}%")
    except:
        st.sidebar.error("Failed to retrieve dividend yield.")
        st.session_state.dividend_yield = 0
dividend_yield = st.session_state.dividend_yield

# Risk-Free Rate Request
if 'rate' not in st.session_state:
    st.session_state.rate = 0.04
rate = float(interpolate_rates(get_rates_value_dict(), time))
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
            st.caption("Greeks represent the size and direction for the initial strategy.")

        # Graph Output
        with col2:
            call_matrix_instance = Matrix(spot=spot, px=call_px, iv=call_iv, k=strike, r=rate, t=time, 
                                          b=dividend_yield, type='Call', spot_step=spot_step, 
                                          iv_step=iv_step)
            put_matrix_instance = Matrix(spot=spot, px=put_px, iv=put_iv, k=strike, r=rate, t=time, 
                                         b=dividend_yield, type='Put', spot_step=spot_step, 
                                         iv_step=iv_step)

            call_matrix = call_matrix_instance.get_matrix(direction=direction) * call_quantity
            put_matrix = put_matrix_instance.get_matrix(direction=direction) * put_quantity

            plot_instance = Plotting(matrix=[call_matrix, put_matrix], 
                                    instance=[call_matrix_instance, put_matrix_instance], 
                                    strategy='Straddle', ticker=ticker)

            fig = plot_instance.plot(direction='Long')
            st.pyplot(fig, clear_figure=True)
    else:
        st.warning("Inputs must be greater than or equal to zero...")
else:
    st.warning("Enter all inputs to plot...")