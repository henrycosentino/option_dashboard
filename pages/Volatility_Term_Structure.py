import streamlit as st
import matplotlib.pyplot as plt
from helpers import Volatility
import numpy as np

# --- Streamlit App Input & Layout --- 
# Title
st.set_page_config(page_title="Options Strategy App", layout="wide")
st.title("Volatility Term Structure")
st.markdown("<hr style='border: 1px solid white;'>", unsafe_allow_html=True)

# Sidebar 
st.sidebar.header("Option Inputs")

# Ticker
if "name" not in st.session_state:
    st.session_state.name = "SPY"
name = st.sidebar.text_input("Ticker:", value=st.session_state.get("name", "SPY")).upper()
st.session_state.name = name

# Forward Period (days)
if "frwd_period" not in st.session_state:
    st.session_state.frwd_period = 15
frwd_period = st.sidebar.number_input("Forward Period (days):", 
                                      min_value=1,
                                      value=st.session_state.get("frwd_period", 15))
st.session_state.frwd_period = frwd_period

# Sidebar 
st.sidebar.header("Dashboard Settings")

# Forward Period Validation
if frwd_period < 1:
    st.sidebar.error("Forward period must be larger than one...")

# Start Day
if "start_day" not in st.session_state:
    st.session_state.start_day = 0
start_day = st.sidebar.number_input("Start Day:", 
                                   min_value=0, 
                                   value=st.session_state.get("start_day", 0))
st.session_state.start_day = start_day

# End Day
if "end_day" not in st.session_state:
    st.session_state.end_day = 100_000
end_day = st.sidebar.number_input("End Day:", 
                                 min_value=1, 
                                 value=st.session_state.get("end_day", 100_000))
st.session_state.end_day = end_day

# Day Range Validation
if end_day < start_day:
    st.sidebar.error("End day must be larger than start day...")

# ATM Percent Band 
percent_band_display = st.sidebar.slider("ATM Band:",
                                         min_value=5,
                                         max_value=15,
                                         step=1,
                                         format="%d%%")
pct_band = percent_band_display / 100.0
st.session_state.pct_band = pct_band

def day_filter(days_ls, iv_ls, start_day, end_day):
    filtered_days = []
    start_idx = None
    end_idx = None

    for i, day in enumerate(days_ls):
        if day >= start_day:
            if day <= end_day:
                if start_idx is None:
                    start_idx = i
                end_idx = i 
                filtered_days.append(day)
    
    if start_idx is not None and end_idx is not None:
        filtered_iv = iv_ls[start_idx : end_idx + 1]
    else:
        filtered_iv = []
    
    return filtered_days, filtered_iv


# --- Streamlit App Ouput --- 
if all(v is not None for v in [name, pct_band, frwd_period]):
    col1, col2 = st.columns([3,3])

    vol = Volatility(ticker=name, pct_band=pct_band, frwd_period=int(frwd_period))

    spot_call_iv_ls, spot_put_iv_ls = vol.spot_iv()
    expiration_days_ls = vol.cutoff_expiration_days_dates()[1]

    frwd_call_iv_dict, frwd_put_iv_dict = vol.forward_iv()
    frwd_call_iv_ls = list(frwd_call_iv_dict.values())
    frwd_put_iv_ls = list(frwd_put_iv_dict.values())
    frwd_call_day_ls = list(frwd_call_iv_dict.keys())
    frwd_put_day_ls = list(frwd_put_iv_dict.keys())

    frwd_call_day_ls, frwd_call_iv_ls = day_filter(frwd_call_day_ls, frwd_call_iv_ls, start_day, end_day)
    frwd_put_day_ls, frwd_put_iv_ls = day_filter(frwd_put_day_ls, frwd_put_iv_ls, start_day, end_day)
    spot_day_ls, spot_call_iv_ls = day_filter(expiration_days_ls, spot_call_iv_ls, start_day, end_day)
    spot_day_ls, spot_put_iv_ls = day_filter(expiration_days_ls, spot_put_iv_ls, start_day, end_day)

    # Call Term Structure
    with col1:
        all_call_iv = np.concatenate((spot_call_iv_ls, frwd_call_iv_ls))

        max_call_iv = np.max(all_call_iv)
        min_call_iv = np.min(all_call_iv)

        step = (max_call_iv - min_call_iv) / len(all_call_iv)
        master_iv = []
        for i in range(0, len(all_call_iv), 4):
            master_iv.append(max_call_iv - step * i)
        y_tick_labels = [f"{round(iv*100,1)}%" for iv in master_iv]

        fig, ax = plt.subplots(figsize=(10,6))
        fig.patch.set_alpha(0.001)
        ax.patch.set_alpha(0.001)

        ax.plot(spot_day_ls, spot_call_iv_ls, marker='o', linestyle='-', label='Spot IV', color='orange')
        ax.plot(frwd_call_day_ls, frwd_call_iv_ls, marker='s', linestyle='--', label='Forward IV', color='pink')

        ax.set_title(f"Call IV Term Structure for ATM Options on {name}", fontsize=18, fontweight='bold', color='white')
        ax.set_ylabel("Implied Volatility", color='white')
        ax.set_xlabel("Days til Expiry", color='white')

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.grid(True, linestyle='-', alpha=0.3, color='white')
        ax.set_yticks(master_iv)
        ax.set_yticklabels(y_tick_labels, color='white')
        ax.tick_params(axis='x', colors='white', rotation=35)
        ax.tick_params(axis='y', colors='white')
        legend = ax.legend(framealpha=0.001)
        plt.setp(legend.get_texts(), fontweight='bold', color='white')

        plt.tight_layout()
        st.pyplot(fig)

    # Put Term Structure
    with col2:      
        all_put_iv = np.concatenate((spot_put_iv_ls, frwd_put_iv_ls))

        max_put_iv = np.max(all_put_iv)
        min_put_iv = np.min(all_put_iv)

        step = (max_put_iv - min_put_iv) / len(all_put_iv)
        master_iv = []
        for i in range(0, len(all_put_iv), 4):
            master_iv.append(max_put_iv - step * i)
        y_tick_labels = [f"{round(iv*100,1)}%" for iv in master_iv]

        fig, ax = plt.subplots(figsize=(10,6))
        fig.patch.set_alpha(0.001)
        ax.patch.set_alpha(0.001)

        ax.plot(spot_day_ls, spot_put_iv_ls, marker='o', linestyle='-', label='Spot IV', color='orange')
        ax.plot(frwd_put_day_ls, frwd_put_iv_ls, marker='s', linestyle='--', label='Forward IV', color='pink')

        ax.set_title(f"Put IV Term Structure for ATM Options on {name}", fontsize=18, fontweight='bold', color='white')
        ax.set_ylabel("Implied Volatility", color='white')
        ax.set_xlabel("Days til Expiry", color='white')

        for spine in ax.spines.values():
            spine.set_visible(False)

        ax.grid(True, linestyle='-', alpha=0.3, color='white')
        ax.set_yticks(master_iv)
        ax.set_yticklabels(y_tick_labels, color='white')
        ax.tick_params(axis='x', colors='white', rotation=35)
        ax.tick_params(axis='y', colors='white')
        legend = ax.legend(framealpha=0.001)
        plt.setp(legend.get_texts(), fontweight='bold', color='white')

        plt.tight_layout()
        st.pyplot(fig)