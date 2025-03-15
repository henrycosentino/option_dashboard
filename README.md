## Streamlit App Link
- https://optiondashboard-727xijizdnq8revxsgmxa7.streamlit.app/
## Project Overview
- The purpose of this project was to develop a dashboard that displays profit and loss (PnL) and option Greeks for a vanilla call or put stock option. The dashboard could be used by a trader in their workflow, or by an investor looking to hedge out risk in one of their positions.
## Black-Scholes Class:
- The class was created to automate the process of various option metric calculations and is used in the dashboard.py and plotting.py files
- Calculates the value of a call and put option, along with first and second-order option Greeks
- Relys on the methodology expressed in Option Volatility and Pricing: Advanced Trading Strategies and Techniques, 2nd Edition 
## Plotting Class:
- The class was created for two purposes: construct a matrix of option prices for different spot and implied volatility levels and plot the matrix cleanly
- Matrix Construction
  - The class begins with matrix construction, referencing the BlackScholes class to calculate call and put prices for a given spot price and implied volatility
  - The spot and implied volatility are dynamic as they can be offset by spot_stp and iv_stp, which can be manually tuned within the live dashboard
- Potting
  - The class follows by instantiating two helper functions to assist the final plotting method
  - This code is not dynamic, instead, the design of the graph was done at my discretion. If desired, it can be updated to fit different preferences
## Dashboard:
- The dashboard can be broken down into three parts: single, straddle, and butterfly
  - Single: a single option strategy either long or short call or put option
  - Straddle: a straddle option strategy either long or short straddle with the same expiration and strike price, quantity can be changed for both options
  - Butterfly: various butterfly strategies can be analyzed, "Reverse Iron Butterfly" and "Iron Butterfly" have not been added yet
- Inputs
  - Inputs into the dashboard primarily concern the necessary parameters for the BlackScholes class (model)
  - Unique features include a calendar pop-up provided by Streamlit .date_input() to set the expiration date, the interpolation of the risk-free using the FRED API to stream current US Yield Curve date, and implied volatility and the spot price are capable of being offset by their respective sliders
- Outputs
  - The Greeks are output into an HTML formatted box (I want to emphasize that I do not know how to write HTML and relied on ChatGPT for assistance on this part)
  - The heatmap graph of the options PnL matrix is displayed on the right-hand side once all the parameters have been set
  - The dashboard looks best when Streamlit is on “wide mode” and the user may need to tinker with the spot price and implied volatility sliders to show the heatmap
