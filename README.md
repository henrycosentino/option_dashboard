## Streamlit App Link
- https://optiondashboard-727xijizdnq8revxsgmxa7.streamlit.app/
- Use dark mode
- I manage the app frequently; however, the yfinance and FRED APIs may update their codebase, causing the app to fail...
## Project Overview
- The purpose of this project was to develop a dashboard that displays profit and loss (PnL) and option Greeks for a vanilla call or put stock option. The dashboard could be used by a trader in their workflow, or by an investor looking to hedge out risk in one of their positions.
## Dashboard
- The dashboard can be broken down into two parts: strategies and volatility
  - Strategies:
    - Single: a single option strategy, either a long or short call or put option
    - Straddle: a straddle option strategy, where either a long or short straddle is used with the same expiration and strike price; quantity can be changed for both options
    - Butterfly: various butterfly strategies can be analyzed, "Reverse Iron Butterfly" and "Iron Butterfly" have not been added yet
    - Inputs
      - Inputs into the dashboard primarily concern the necessary parameters for the BlackScholes class (model)
      - Unique features include a calendar pop-up provided by Streamlit .date_input() to set the expiration date, the interpolation of the risk-free using the FRED API to stream current US Yield Curve data, and implied volatility and the spot price are capable of being offset by their respective sliders
    - Outputs
      - The Greeks are output into an HTML-formatted box (I want to emphasize that I do not know how to write HTML and relied on ChatGPT for assistance on this part)
      - The heatmap graph of the options PnL matrix is displayed on the right-hand side once all the parameters have been set
      - The dashboard looks best when Streamlit is on “wide mode” and the browser is in a "dark mode" setting, and the user may need to tinker with the spot price and implied volatility sliders to show the heatmap
  - Volatility
    - Term Structure: analyzes the term structure of spot and forward volatility
    - Surface: analyzes the current volatility surface of all traded options for the underlying
## Classes
- Black-Scholes Class
  - The class was created to automate the process of various option metric calculations and is used in the dashboard.py and plotting.py files
  - Calculates the value of a call and put option, along with first and second-order option Greeks
  - Relys on the methodology expressed in Option Volatility and Pricing: Advanced Trading Strategies and Techniques, 2nd Edition
- Plotting Class
  - The class was created for two purposes: to construct a matrix of option prices for different spot and implied volatility levels, and to plot the matrix cleanly
  - Matrix Construction
    - The class begins with matrix construction, referencing the BlackScholes class to calculate call and put prices for a given spot price and implied volatility
    - The spot and implied volatility are dynamic as they can be offset by spot_stp and iv_stp, which can be manually tuned within the live dashboard (for example, if Spot Step Slider is set to 0.05, or 5%, then each spot price directly surrounding the base spot will be offset by 5% and so forth as you move farther from the base spot rate)
  - Plotting
    - The class is followed by instantiating two helper functions to assist the final plotting method
    - This code is not dynamic, instead, the design of the graph was done at my discretion. If desired, it can be updated to fit different preferences
- Volatility Class
  - ...
