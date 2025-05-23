from Volatility import Volatility
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scipy.interpolate import griddata
import numpy as np

# Title
st.set_page_config(page_title="Options Strategy App", layout="wide")
st.title("Volatility Surface")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar 
st.sidebar.header("Option Inputs")

### INPUT ###
# Ticker Input
if "name" not in st.session_state:
    st.session_state.name = "SPY"
name = st.sidebar.text_input("Ticker:", value=st.session_state.get("name", "SPY")).upper()
st.session_state.name = name

# Option Type Selection
if "option_type" not in st.session_state:
    st.session_state.option_type = "Call" 
option_type = st.sidebar.selectbox("Option Type:", ["Call", "Put"])

# Validation
options_df = pd.DataFrame()
if name and option_type:
    vol = Volatility(ticker=name)
    options_df = vol.spot_iv_surface(option_type)
    px = vol.last_px()
else:
    st.warning("Please enter a ticker and option type to plot...")

# Sidebar header
st.sidebar.header('Dashboard Settings')

# Min Days til Expiry
if "min_expiry" not in st.session_state:
    st.session_state.min_expiry = 0
min_expiry = st.sidebar.number_input("Min Expiry Day:", 
                                     min_value=0, 
                                     value=st.session_state.get("min_expiry", 0))
st.session_state.min_expiry = min_expiry

# Max Days til Expiry
if "max_expiry" not in st.session_state:
    st.session_state.max_expiry = 100_000
max_expiry = st.sidebar.number_input("Max Expiry Day:", 
                                     min_value=1, 
                                     value=st.session_state.get("max_expiry", 100_000))
st.session_state.max_expiry = max_expiry

# Day Range Validation
if max_expiry < min_expiry:
    st.sidebar.error("End day must be larger than start day...")

# Min Strike
if "min_strike" not in st.session_state:
    st.session_state.min_strike = 0
min_strike = st.sidebar.number_input("Min Strike:", 
                                     min_value=0, 
                                     value=st.session_state.get("min_strike", 1))
st.session_state.min_strike = min_strike

# Max Strike
if "max_strike" not in st.session_state:
    st.session_state.max_strike = 5_000
max_strike = st.sidebar.number_input("Max Strike:", 
                                     min_value=1, 
                                     value=st.session_state.get("max_strike", 5_000))
st.session_state.max_strike = max_strike

# Stike Range Validation
if min_strike > max_strike:
    st.sidebar.warning("Max strike must be greater than min strike...")

# Meshgrid Toggle
on = st.sidebar.toggle("Activate Meshgrid")

### OUTPUT ###
if not options_df.empty:
    options_df = options_df[(options_df['expiryDays'] >= int(min_expiry)) & (options_df['expiryDays'] <= int(max_expiry))].copy()
    options_df = options_df[(options_df['strike'] >= int(min_strike)) & (options_df['strike'] <= int(max_strike))].copy()
    options_df = options_df[(options_df['impliedVolatility'] > 1)].copy()

    if options_df.empty:
        st.warning("No data available for the selected filters. Please adjust the ranges...")
    else:
        fig = go.Figure()

        fig.add_trace(go.Scatter3d(
            x=options_df['expiryDays'],
            y=options_df['strike'],
            z=options_df['impliedVolatility'],
            mode='markers',
            marker=dict(
                size=3,
                color=options_df['impliedVolatility'],
                colorscale='Magma',
                opacity=0.8
            )
        ))

        # Meshgrid
        if on:
            if len(options_df) > 3: 
                try:
                    grid_expiry = np.linspace(options_df['expiryDays'].min(), options_df['expiryDays'].max(), 50)
                    grid_strike = np.linspace(options_df['strike'].min(), options_df['strike'].max(), 50)
                    X, Y = np.meshgrid(grid_expiry, grid_strike)

                    Z = griddata((options_df['expiryDays'], options_df['strike']),
                                options_df['impliedVolatility'],
                                (X, Y),
                                method='linear')

                    if np.isfinite(Z).any():
                        fig.add_trace(go.Surface(
                            x=X,
                            y=Y,
                            z=Z,
                            colorscale='Magma',
                            opacity=0.3,
                            showscale=False,
                            name='Volatility Surface'
                        ))
                    else:
                        st.info("Interpolated surface contains no finite values.")

                except Exception as e:
                    st.warning(f"Meshgrid interpolation failed: {e}")
            else:
                st.info("Not enough data points after filtering to generate a smooth volatility surface...")

        fig.update_layout(
            title=dict(
                text=f"Implied Volatility Surface for {name} {option_type} Options",
                font=dict(size=30, weight='bold'),
            ),
            scene=dict(
                xaxis_title='Days until Expiration',
                yaxis_title='Strike',
                zaxis_title='Implied Volatility (%)'
            ),
            height=1000,
            margin=dict(l=50, r=50, b=50, t=50),
        )

        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No data returned from Volatility surface generator.")