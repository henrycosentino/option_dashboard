import requests
import matplotlib
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from concurrent.futures import ThreadPoolExecutor


# --- BlackScholes Option Pricing Class ---
class BlackScholes:
    def __init__(self, k, s, r, t, iv, b):
        assert all(x >= 0 for x in [k, s, r, t, iv, b]), "Input parameters for BlackScholes must be greater than or equal to zero..."
        k, s, r, t, iv, b = [float(x) for x in [k, s, r, t, iv, b]]

        self.k = k # Strike
        self.s = s # Spot
        self.r = r # Risk free rate (annual; input in decimal form ie 5.0% --> 0.05)
        self.t = t # Time (fraction of years; input in decimal form ie 3 months --> 0.25)
        self.iv = iv # Implied volatility (input in decimal form ie 20.0% --> 0.20)
        self.b = b # Dividend rate (annual; input in decimal form ie 2.0% --> 0.02)

    def _d1(self) -> float:
        return (np.log(self.s/self.k) + (self.b + self.iv**2 * 0.5) * self.t) / (np.sqrt(self.t) * self.iv)
        
    def _d2(self) -> float:
        return self._d1() - self.iv * np.sqrt(self.t)
    
    def call_px(self) -> float:
        return self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(self._d1()) - self.k * np.exp(-self.r * self.t) * norm.cdf(self._d2())
    
    def put_px(self) -> float:
        return self.k * np.exp(-self.r * self.t) * norm.cdf(-self._d2()) - self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(-self._d1())

    def delta(self, option_type: str = 'Call') -> float:
        option_type = option_type.capitalize()
        if option_type not in ['Call', 'Put']:
            raise ValueError("Option type must be 'Call' or 'Put'...")
        
        if option_type == 'Call':
            return np.exp((self.b-self.r) * self.t) * norm.cdf(self._d1())
        else:
            return -np.exp((self.b-self.r) * self.t) * norm.cdf(-self._d1())
        
    def gamma(self) -> float:
        return (np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1())) / (self.s * self.iv * np.sqrt(self.t))
    
    def vega(self) -> float:
        return (self.s * np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * np.sqrt(self.t)) / 100 # Scales to a one percentage point change (ie 1%)

    def rho(self, option_type: str = 'Call') -> float:
        option_type = option_type.capitalize()
        if option_type not in ['Call', 'Put']:
            raise ValueError("Option type must be 'Call' or 'Put'...")
        
        if option_type == 'Call':
            return self.t * self.k * np.exp(-self.r * self.t) * norm.cdf(self._d2()) / 100  # Scales to a one percentage point change (ie 1%)
        else:
            return -self.t * self.k * np.exp(-self.r * self.t) * norm.cdf(-self._d2()) / 100 # Scales to a one percentage point change (ie 1%)
    
    def theta(self, option_type: str = 'Call') -> float:
        option_type = option_type.capitalize()
        if option_type not in ['Call', 'Put']:
            raise ValueError("Option type must be 'Call' or 'Put'...")
        
        term1 = -(self.s * np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * self.iv) / (2 * np.sqrt(self.t))
        if option_type == 'Call':
            term2 = (self.b - self.r) * self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(self._d1()) - (self.r * self.k * np.exp(-self.r * self.t) * norm.cdf(self._d2()))
            return (term1 + term2) / 365 # Scaled to represent a one day change 
        else:
            term2 = (self.b - self.r) * self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(-self._d1()) + (self.r * self.k * np.exp(-self.r * self.t) * norm.cdf(-self._d2()))
            return (term1 + term2) / 365 # Scaled to represent a one day change 
        
    def vanna(self) -> float:
        return -np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * (self._d2() / self.iv)

    def charm(self, option_type: str = 'Call') -> float:
        option_type = option_type.capitalize()
        if option_type not in ['Call', 'Put']:
            raise ValueError("Option type must be 'Call' or 'Put'...")
        
        term1 = norm.pdf(self._d1()) * ((self.b / (self.iv * np.sqrt(self.t))) - (self._d2() / (2 * self.t)))
        term2 = (self.b - self.r) * norm.cdf(self._d1())
        if option_type == 'Call':
            return -np.exp((self.b - self.r) * self.t) * (term1 + term2) / 252 # Scaled to represent trading calendar
        else:
            return -np.exp((self.b - self.r) * self.t) * (term1 - (self.b - self.r) * norm.cdf(-self._d1())) / 252 # Scaled to represent trading calendar
        
    def volga(self) -> float:
        return self.vega() * (self._d1() * self._d2() / self.iv) / 100


# --- Binomial Option Pricing Class ---
class Binomial:
    def __init__(self, k, s, r, t, iv, b, n: int=300, style='American', calc='lin_alg'):
        assert all(x >= 0 for x in [k, s, r, t, iv, b, n]), "Input parameters for Binomial must be greater than or equal to zero..."
        assert style in ['American', 'European'], "style must be 'American' or 'European'..."
        assert calc in ['lin_alg', 'recursive'], "calc must be 'lin_alg or 'recursive'..."
        k, s, r, t, iv, b = [float(x) for x in [k, s, r, t, iv, b]]
        n = int(n)
        
        self.k = k # Strike
        self.s = s # Spot
        self.r = r # Risk free rate (annual; input in decimal form ie 5.0% --> 0.05)
        self.t = t # Time (fraction of years; input in decimal form ie 3 months --> 0.25)
        self.iv = iv # Implied volatility (input in decimal form ie 20.0% --> 0.20)
        self.b = b # Dividend rate (annual; input in decimal form ie 2.0% --> 0.02)
        self.n = n # Number of steps
        self.style = style
        self.calc = calc
        self.dt = t / n
        self.u = np.exp(self.iv * np.sqrt(self.dt))
        self.d = 1 / self.u
        self.adj_r = self.r - self.b
        self.p = (np.exp(self.adj_r * self.dt) - self.d) / (self.u - self.d)
        self._C_delta = [0, 0] # Call or put step values for delta calculation
        self._C_gamma = [0, 0, 0] # Call or put step values for gamma calculation

    def _recursive_call(self) -> float:
        # Stock prices at maturity
        S = np.zeros(self.n + 1)
        for j in range(0, self.n + 1):
            S[j] = self.s * self.u**j * self.d**(self.n - j)

        # Option payoff at maturity
        C = np.zeros(self.n + 1)
        for j in range(0, self.n + 1):
            C[j] = max(S[j] - self.k, 0)

        # Backward recursion
        for i in range(self.n - 1, -1, -1):
            for j in range(0, i + 1):

                ev = np.exp(-self.r*self.dt) * (self.p * C[j + 1] + (1 - self.p) * C[j])

                if self.style == 'American':
                    current_S_node = self.s * (self.u**j) * (self.d**(i - j))
                    C[j] = max(ev, current_S_node - self.k)
                else:
                    C[j] = ev

                # For delta and gamma calculations
                if i == 1:
                    self._C_delta[0] = C[0]
                    self._C_delta[1] = C[1]
                elif i == 2:
                    self._C_gamma[0] = C[0] 
                    self._C_gamma[1] = C[1] 
                    self._C_gamma[2] = C[2]

        return C[0]
    
    def _lin_alg_call(self) -> float:
        # Stock prices at maturity
        S = self.s * self.d**(np.arange(self.n,-1,-1)) * self.u**(np.arange(0,self.n+1,1))

        # Option payoff at maturity
        C = np.maximum(0, S - self.k)

        # Backward recursion
        for i in np.arange(self.n - 1, -1, -1):
            S = self.s * self.d**(np.arange(i,-1,-1)) * self.u**(np.arange(0,i+1,1))
            C[:i+1] = np.exp(-self.r*self.dt) * (self.p*C[1:i+2] + (1-self.p)*C[0:i+1])
            
            if self.style == 'American':
                C[:i+1] = np.maximum(C[:i+1], S - self.k)
            
            C = C[:-1]
        
        return C[0]

    def call_px(self) -> float:
        if self.calc == 'lin_alg':
            return self._lin_alg_call()
        
        if self.calc == 'recursive':
            return self._recursive_call()

    def _recursive_put(self) -> float:
        # Stock prices at maturity
        S = np.zeros(self.n + 1)
        for j in range(0, self.n + 1):
            S[j] = self.s * self.u**j * self.d**(self.n - j)

        # Option payoff at maturity
        C = np.zeros(self.n + 1)
        for j in range(0, self.n + 1):
            C[j] = max(self.k - S[j], 0)

        # Backward recursion
        for i in range(self.n - 1, -1, -1):
            for j in range(0, i + 1):

                ev = np.exp(-self.r*self.dt) * (self.p * C[j + 1] + (1 - self.p) * C[j])

                if self.style == 'American':
                    current_S_node = self.s * (self.u**j) * (self.d**(i - j))
                    C[j] = max(ev, self.k - current_S_node)
                else:
                    C[j] = ev

                # For delta and gamma calculations
                if i == 1:
                    self._C_delta[0] = C[0]
                    self._C_delta[1] = C[1]
                elif i == 2:
                    self._C_gamma[0] = C[0] 
                    self._C_gamma[1] = C[1] 
                    self._C_gamma[2] = C[2]
                    
        return C[0]
    
    def _lin_alg_put(self) -> float:
        # Stock prices at maturity
        S = self.s * self.d**(np.arange(self.n,-1,-1)) * self.u**(np.arange(0,self.n+1,1))

        # Option payoff at maturity
        P = np.maximum(0, self.k - S)

        # Backward recursion
        for i in np.arange(self.n - 1, -1, -1):
            S = self.s * self.d**(np.arange(i,-1,-1)) * self.u**(np.arange(0,i+1,1))
            P[:i+1] = np.exp(-self.r*self.dt) * (self.p*P[1:i+2] + (1-self.p)*P[0:i+1])
            
            if self.style == 'American':
                P[:i+1] = np.maximum(P[:i+1], self.k - S)
            
            P = P[:-1]
        
        return P[0]
    
    def put_px(self) -> float:
        if self.calc == 'lin_alg':
            return self._lin_alg_put()
        
        if self.calc == 'recursive':
            return self._recursive_put()


# --- Matrix PnL Generation Class ---
class Matrix:
    def __init__(self, spot, px, iv, k, r, t, b, option_type: str, style: str='European', 
                 spot_step: float=0.05, iv_step: float=0.05):
        
        assert all(x >= 0 for x in [spot, px, k, r, t, b, spot_step, iv_step]), "Input parameters for Matrix must be greater than or equal to zero..."

        option_type = option_type.capitalize()
        if option_type not in ['Call', 'Put']:
            raise ValueError("Option type must be 'Call' or 'Put'...")
        
        style = style.capitalize()
        if style not in ['American', 'European']:
            raise ValueError("Contract type must be 'American' or 'European'...")

        self.spot = spot # Spot price of the asset
        self.px = px # Spot price of the option
        self.iv = iv # Implied volatility of the option (decimal, ie 20% --> 0.20)
        self.k = k # Strike price
        self.r = r # Risk free rate (annual in decimal, ie 4.5% --> 0.045)
        self.t = t # Time (years in decimal, ie 6 months --> 0.50)
        self.b = b # Dividend yield (decimal, ie 3.5% --> 0.035)
        self.option_type = option_type # Type of option (call or put)
        self.style = style
        self.spot_step = spot_step # Used to adjust the dashboard output
        self.iv_step = iv_step # Used to adjust the dashboard output
        self.direction = None
    
    def offset_spot_arr(self) -> np.ndarray:
        return self.spot + (self.spot_step * self.spot) * np.arange(-4, 5)
    
    def offset_iv_arr(self) -> np.ndarray:
        return self.iv + (self.iv_step * self.iv) * np.arange(-4, 5)
 
    def format_iv_list(self) -> list:
        return [f"{round(x*100,1)}%" for x in self.offset_iv_arr()]
    
    def _calc_pnl(self, iv, spot, direction) -> float:
        pnl = None
        if self.style == 'American':
            bn = Binomial(self.k, spot, self.r, self.t, iv, self.b, style=self.style, calc='lin_alg')
            if direction == "Long":
                if self.option_type == 'Call':
                    pnl = bn.call_px() - self.px
                else:
                    pnl = bn.put_px() - self.px
            else:
                if self.option_type == 'Call':
                    pnl = self.px - bn.call_px()
                else:
                    pnl = self.px - bn.put_px()

        if self.style == 'European':
            bs = BlackScholes(self.k, spot, self.r, self.t, iv, self.b)
            if direction == "Long":
                if self.option_type == 'Call':
                    pnl = bs.call_px() - self.px
                else:
                    pnl = bs.put_px() - self.px
            else:
                if self.option_type == 'Call':
                    pnl = self.px - bs.call_px()
                else:
                    pnl = self.px - bs.put_px()

        return round(pnl, 2)
    
    def get_matrix(self, direction="Long") -> np.ndarray:
        spot_list = self.offset_spot_arr()
        iv_list = self.offset_iv_arr()    

        combos = [(iv, spot) for iv in iv_list for spot in spot_list]

        with ThreadPoolExecutor(max_workers=11) as executor:
            futures = [executor.submit(self._calc_pnl, iv, spot, direction) for iv, spot in combos]
            matrix = [future.result() for future in futures]

        self.direction = direction

        return np.array(matrix).reshape(9,9)


# --- Heatmap Plotting Class --- 
class Plotting(Matrix):
    def __init__(self, matrix, instance, strategy: str, ticker: str):
        
        self.matrix = matrix
        self.instance = instance
        self.strategy = strategy
        self.ticker = ticker

    # Internal helper method, generates the master matrix that will be plotted
    def _get_matrix(self) -> np.ndarray:
        if isinstance(self.matrix, np.ndarray):
            return self.matrix
        elif isinstance(self.matrix, list) and len(self.matrix) > 0:
            if all(isinstance(m, np.ndarray) for m in self.matrix):
                return np.sum(self.matrix, axis=0)
            else:
                raise ValueError("All elements in matrix list must be numpy arrays...")
        else:
            raise ValueError("Matrix must be a numpy array or a list of numpy arrays...")
    
    # Internal helper method, generates the formatted IV list for the graph
    def _get_iv_list(self):
        if isinstance(self.instance, Matrix):
            return self.instance.format_iv_list()
        
        if isinstance(self.instance, list):
            iv_list = [matrix.format_iv_list() for matrix in self.instance]

            iv_list_format = []
            for lst_el in range(len(iv_list[0])):
                iv_string = ""
                for idx in range(len(self.instance)):
                    if iv_string == "":
                        iv_string = iv_list[idx][lst_el]
                    else:
                        iv_string += f" / {iv_list[idx][lst_el]}"
                iv_list_format.append(iv_string)

            return iv_list_format
        
        raise TypeError("Invalid type, must be Matrix or list of Matrix instances...")
    
    def heatmap(self, ax=None, cbar_kw=None, cbarlabel="", **kwargs):
        if ax is None:
            ax = plt.gca()

        if cbar_kw is None:
            cbar_kw = {}

        cbar_kw.setdefault("shrink", 0.7)

        matrix = self._get_matrix()

        im = ax.imshow(matrix, **kwargs)

        cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
        cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom", color='white')
        cbar.ax.yaxis.set_tick_params(color='white')  
        for label in cbar.ax.get_yticklabels():
            label.set_color('white')

        iv_list_format = self._get_iv_list()
        if isinstance(self.instance, list):
            spot_list_format = [round(x, 2) for x in self.instance[0].offset_spot_arr()]
        else:
            spot_list_format = [round(x, 2) for x in self.instance.offset_spot_arr()]

        ax.set_xticks(range(matrix.shape[1]), labels=spot_list_format)
        ax.set_yticks(range(matrix.shape[0]), labels=iv_list_format)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')

        ax.spines[:].set_visible(False)
        ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
        ax.tick_params(which="minor", bottom=False, left=False)

        return im, cbar

    def annotate_heatmap(self, im, valfmt="{x:.2f}",
                        textcolors=("black", "black"),
                        threshold=None, **textkw):
        
        matrix = self._get_matrix()

        if threshold is not None:
            threshold = im.norm(threshold)
        else:
            threshold = im.norm(matrix.max())/2.

        kw = dict(horizontalalignment="center",
                verticalalignment="center")
        kw.update(textkw)

        if isinstance(valfmt, str):
            valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

        texts = []
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                kw.update(color=textcolors[int(im.norm(matrix[i, j]) > threshold)])
                text = im.axes.text(j, i, valfmt(matrix[i, j], None), **kw)
                texts.append(text)

        return texts
    
    def plot(self, direction='Long', option_type='Call'):
        fig, ax = plt.subplots(figsize=(10,10), facecolor='none')

        color_map = mcolors.LinearSegmentedColormap.from_list("Default RedGreen", ["red","white","green"])
        strategy_values = np.array(self._get_matrix())
        vmin, vmax = np.min(strategy_values), np.max(strategy_values)
        if vmin < 0 and vmax < 0:  
            vcenter = np.mean(strategy_values)
            color_map = mcolors.LinearSegmentedColormap.from_list("RedYellow", ["red", "orange", "yellow", "white"])
        elif vmin < 0 and vmax > 0:  
            vcenter = 0
            color_map = mcolors.LinearSegmentedColormap.from_list("RedGreen", ["red", "white", "green"])
        elif vmin > 0:  
            vcenter = np.mean(strategy_values)
            color_map = mcolors.LinearSegmentedColormap.from_list("BlueGreen", ["white", "lightblue", "green"])
        norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=vcenter, vmax=vmax)

        im, cbar = self.heatmap(ax=ax, cmap=color_map, norm=norm, cbarlabel="PnL", cbar_kw={'shrink': 0.7})
        texts = self.annotate_heatmap(im, valfmt="{x:.2f}", textcolors=("black", "black"))

        if self.strategy == 'Straddle':
            title = f"PnL of {direction} Straddle for {self.ticker}"
            ylabel = "Implied Volatility (call / put)"
        elif self.strategy == 'Long Call Butterfly':
            title = f"PnL of {self.strategy} for {self.ticker}"
            ylabel = "Implied Volatility (low / atm / high)"
        elif self.strategy == 'Short Call Butterfly':
            title = f"PnL of {self.strategy} for {self.ticker}"
            ylabel = "Implied Volatility (low / atm / high)"
        elif self.strategy == 'Long Put Butterfly':
            title = f"PnL of {self.strategy} for {self.ticker}"
            ylabel = "Implied Volatility (low / atm / high)"
        elif self.strategy == 'Short Put Butterfly':
            title = f"PnL of {self.strategy} for {self.ticker}"
            ylabel = "Implied Volatility (low / atm / high)"
        elif self.strategy == "Iron Butterfly":
            title = f"PnL of {self.strategy} for {self.ticker}"
            ylabel = "Implied Volatility (low / atm (p) / atm (c) / high)"
        elif self.strategy == "Reverse Iron Butterfly":
            title = f"PnL of {self.strategy} for {self.ticker}"
            ylabel = "Implied Volatility (low / atm (p) / atm (c) / high)"
        else:
            title = f"PnL for {direction} {self.ticker} {option_type} Option"
            ylabel = "Implied Volatility"
        
        plt.title(title, fontsize=20, fontweight='bold', color='white')
        plt.xlabel("Spot Price", fontsize=14, color='white')
        plt.ylabel(ylabel, fontsize=14, color='white')

        fig.tight_layout()
        
        return fig


# --- Volatility Analysis Classes --- 
class Underlying:
    def __init__(self, ticker: str):
        assert isinstance(ticker, str)

        self._ticker = ticker
        self._stock = yf.Ticker(self._ticker) if self._ticker else None

    @property
    def ticker(self):
        return self._ticker
    
    @ticker.setter
    def ticker(self, new_ticker):
        if isinstance(new_ticker, str):
            self._ticker = new_ticker.upper()
            self._stock = yf.Ticker(self._ticker)
        else:
            raise TypeError("Ticker must be a string.")
        
    @ticker.deleter
    def ticker(self):
        print(f"Deleting {self._ticker} from {self}.")
        del self._ticker
    
    @property
    def stock(self):
        return self._stock if self._stock else None
    
    def last_px(self) -> float:
        """Returns the last available stock price"""
        return self.stock.history(period='1d')['Close'].iloc[-1]
    

class Volatility(Underlying):
    def __init__(self, ticker: str, pct_band: float = 0.05, frwd_period: int = 15):
        super().__init__(ticker)
        self.pct_band = pct_band
        self.frwd_period = frwd_period
        self.stock_px = self.last_px()
    
    def expirations_dates(self) -> list[str]:
        """Returns a list of expiration dates"""
        return self.stock.options

    def expirations_days(self) -> list[int]:
        """Returns a list of expiration days"""
        expirations_formatted = [datetime.strptime(date, '%Y-%m-%d') for date in self.expirations_dates()]
        today = datetime.today()
        return [(exp - today).days for exp in expirations_formatted]
    
    def cutoff_expiration_days_dates(self, cutoff=3) -> tuple[list, list]:
        expiry_days_ls = self.expirations_days()
        expiry_dates_ls = self.expirations_dates()

        if isinstance(cutoff, int) and cutoff > 0:
            cutoff_expiry_dates_ls, cutoff_expiry_days_ls = [], []
            for i, date in enumerate(expiry_dates_ls):
                if expiry_days_ls[i] < cutoff:
                    continue
                else:
                    cutoff_expiry_dates_ls.append(date)
                    cutoff_expiry_days_ls.append(expiry_days_ls[i])
        
        return cutoff_expiry_dates_ls, cutoff_expiry_days_ls

    # Internal helper method for spot_iv method - not intended for external use
    def _calculate_weighted_iv(self, df: pd.DataFrame) -> float:
        low_band = self.stock_px - self.stock_px * self.pct_band
        high_band = self.stock_px + self.stock_px * self.pct_band
        df[['strike', 'volume', 'impliedVolatility']] = df[['strike', 'volume', 'impliedVolatility']].apply(pd.to_numeric, errors='coerce')
        df = df[(df['strike'] > low_band) & (df['strike'] < high_band)]

        if df['volume'].sum() == 0 or df['impliedVolatility'].isna().all():
            return np.nan
        
        return (df['impliedVolatility'] * df['volume']).sum() / df['volume'].sum()
    
    # Internal helper method for spot_iv and spot_iv_surface - not intended for external use
    def _threading_option_chain(self) -> list:
        cutoff_expiry_dates_ls = self.cutoff_expiration_days_dates()[0]
        with ThreadPoolExecutor(max_workers=min(len(cutoff_expiry_dates_ls), 10)) as executor:
            futures = [executor.submit(self.stock.option_chain, date) for date in cutoff_expiry_dates_ls]
            options_chain_list = [future.result() for future in futures]

        return options_chain_list

    def spot_iv(self) -> tuple[list[float], list[float]]:
        """Returns two lists (call and put) of spot IV for each expiration date"""
        try:
            options_chain_list = self._threading_option_chain()
            spot_call_iv_ls, spot_put_iv_ls = [], []
            for chain in options_chain_list:
                spot_call_iv_ls.append(self._calculate_weighted_iv(pd.DataFrame(chain.calls)))
                spot_put_iv_ls.append(self._calculate_weighted_iv(pd.DataFrame(chain.puts)))
        except:
            cutoff_expiry_dates_ls = self.cutoff_expiration_days_dates()[0]
            spot_call_iv_ls, spot_put_iv_ls = [], []
            for date in cutoff_expiry_dates_ls:
                option_chain = self.stock.option_chain(date)
                spot_call_iv_ls.append(self._calculate_weighted_iv(pd.DataFrame(option_chain.calls)))
                spot_put_iv_ls.append(self._calculate_weighted_iv(pd.DataFrame(option_chain.puts)))
        return spot_call_iv_ls, spot_put_iv_ls
    
    # Internal helper method for forward_iv method - not intended for external use
    def _forward_expiration_days(self) -> list[int]:
        expiry_days_ls = self.cutoff_expiration_days_dates()[1]
        expiry_days_ls = expiry_days_ls[:len(expiry_days_ls)-1]
        forward_days_ls = list(np.array(expiry_days_ls) + self.frwd_period)
        return [self.frwd_period] + forward_days_ls
    
    # Internal helper method for forward_iv method - not intended for external use
    def _interpolate_spot_iv(self) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
        spot_call_iv_ls, spot_put_iv_ls = self.spot_iv()

        expiry_days_ls = self.cutoff_expiration_days_dates()[1]
        forward_days_ls = self._forward_expiration_days()

        interpolated_call_iv = np.exp(np.interp(forward_days_ls, expiry_days_ls, np.log(spot_call_iv_ls)))
        interpolated_put_iv = np.exp(np.interp(forward_days_ls, expiry_days_ls, np.log(spot_put_iv_ls)))

        return list(zip(forward_days_ls, interpolated_call_iv)), list(zip(forward_days_ls, interpolated_put_iv))
 
    def forward_iv(self) -> tuple[dict[int, float], dict[int, float]]:
        """
        Calculates and returns the forward IV term structure of expiration days.

        For instance, if self.frwd_period=15 and one of the days in the expiration
        list is 30, then this function will return the 15D 30D Forward IV for
        that specific day.
        """
        expiry_days_ls = self.cutoff_expiration_days_dates()[1]
        expiry_days_ls = expiry_days_ls[:len(expiry_days_ls)-1]
        interp_spot_call_iv_ls, interp_spot_put_iv_ls = self._interpolate_spot_iv()

        t1_call = interp_spot_call_iv_ls[0][0]
        s1_call = interp_spot_call_iv_ls[0][1] ** 2
        t1_put = interp_spot_put_iv_ls[0][0]
        s1_put = interp_spot_put_iv_ls[0][1] ** 2

        frwd_call_iv_dict = {}
        frwd_put_iv_dict = {}
        for i in range(len(expiry_days_ls)):

            t2_call = interp_spot_call_iv_ls[i + 1][0]
            s2_call = interp_spot_call_iv_ls[i + 1][1] ** 2
            t2_put = interp_spot_put_iv_ls[i + 1][0]
            s2_put = interp_spot_put_iv_ls[i + 1][1] ** 2

            frwd_call_iv_dict[expiry_days_ls[i]] = np.sqrt(((s2_call*t2_call)-(s1_call*t1_call)) / (t2_call-t1_call))
            frwd_put_iv_dict[expiry_days_ls[i]] = np.sqrt(((s2_put*t2_put)-(s1_put*t1_put)) / (t2_put-t1_put))

        return frwd_call_iv_dict, frwd_put_iv_dict

    def spot_iv_surface(self, option_type: str):
        """Returns a data frame that can be plotted to represent a volatility surface."""
        cutoff_expiry_dates_ls = self.cutoff_expiration_days_dates()[0]
        try:
            options_chain_list = self._threading_option_chain()
            options_df = pd.DataFrame()
            for date, chain in zip(cutoff_expiry_dates_ls, options_chain_list):
                if option_type.upper() == 'CALL':
                    call_df = pd.DataFrame(chain.calls)[['impliedVolatility', 'strike']]
                    call_df['expiryDate'] = date
                    options_df = pd.concat([options_df, call_df], ignore_index=True)
                elif option_type.upper() == 'PUT':
                    put_df = pd.DataFrame(chain.puts)[['impliedVolatility', 'strike']]
                    put_df['expiryDate'] = date
                    options_df = pd.concat([options_df, put_df], ignore_index=True)
                else:
                    raise ValueError("Argument option_type should be: CALL or PUT")
        except:
            options_df = pd.DataFrame()
            for date in cutoff_expiry_dates_ls:
                option_chain = self.stock.option_chain(date)
                if option_type.upper() == 'CALL':
                    call_df = pd.DataFrame(option_chain.calls)[['impliedVolatility', 'strike']]
                    call_df['expiryDate'] = date
                    options_df = pd.concat([options_df, call_df], ignore_index=True)
                elif option_type.upper() == 'PUT':
                    put_df = pd.DataFrame(option_chain.puts)[['impliedVolatility', 'strike']]
                    put_df['expiryDate'] = date
                    options_df = pd.concat([options_df, put_df], ignore_index=True)
                else:
                    raise ValueError("Argument option_type should be: CALL or PUT")

        options_df['expiryDate'] = pd.to_datetime(options_df['expiryDate']).dt.date
        options_df['impliedVolatility'] = options_df['impliedVolatility'] * 100
        today = datetime.today().date()
        options_df['expiryDays'] = options_df['expiryDate'].apply(lambda x: (x - today).days).astype(int)

        return options_df

    def spot_average_iv_surface(self, period=15):
        pass
    

# --- Interest Rate Interpolation Function --- 
def get_rates_value_dict() -> dict:
    fred_key = '0e26fed1b95ca710abdb6bbde2ad1a8a'
    rates_series_dict = {
        'one_month': 'DGS1MO',
        'three_month': 'DGS3MO',
        'six_month': 'DGS6MO',
        'one_year': 'DGS1',
        'two_year': 'DGS2',
        'three_year': 'DGS3',
        'five_year': 'DGS5',
        'seven_year': 'DGS7',
        'ten_year': 'DGS10',
        'twenty_year': 'DGS20',
        'thirty_year': 'DGS30'
        }
    time_lst = [30, 90, 180, 365, 730, 1095, 1825, 2555, 3650, 7300, 10950]

    def load_url(url):
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data['observations'][-1]['value']) / 100

    try:
        rates_value_dict = {}
        with ThreadPoolExecutor(max_workers=11) as executor:
            futures = [executor.submit(load_url, f'https://api.stlouisfed.org/fred/series/observations?series_id={v}&api_key={fred_key}&file_type=json') for v in rates_series_dict.values()]
            for i, future in enumerate(futures):
                data = future.result()
                rates_value_dict[time_lst[i]] = data
    except:
        rates_value_dict = {}
        for i, v in enumerate(rates_series_dict.values()):
            url = f'https://api.stlouisfed.org/fred/series/observations?series_id={v}&api_key={fred_key}&file_type=json'
            data = requests.get(url).json()
            rate = float(data['observations'][-1]['value']) / 100

            rates_value_dict[time_lst[i]] = rate
           
    return rates_value_dict

def interpolate_rates(rate_dict: dict, time: float) -> float:
    time_days = 365 * time  
    keys = sorted(rate_dict.keys())

    if time_days <= keys[0]:
        return rate_dict[keys[0]]
    
    if time_days >= keys[-1]:
        return rate_dict[keys[-1]]

    prev_key = None
    for key in keys:
        if time_days == key:
            return rate_dict[key]

        if prev_key is not None and prev_key < time_days < key:
            rate_one = rate_dict[prev_key]
            rate_two = rate_dict[key]
            return np.interp(time_days, [prev_key, key], [rate_one, rate_two])

        prev_key = key


# --- Day Filter Helper Function --- 
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


# --- ThreadPoolExecutor Helper Functions ---
def process_butterfly(low, atm, high, dir_low, dir_atm, dir_high) -> list:
    with ThreadPoolExecutor(max_workers=3) as executor:
        low_future = executor.submit(low.get_matrix, dir_low)
        atm_future = executor.submit(atm.get_matrix, dir_atm)
        high_future = executor.submit(high.get_matrix, dir_high)

        low_matrix = low_future.result()
        atm_matrix = atm_future.result()
        high_matrix = high_future.result()
    
    return [low_matrix, atm_matrix * 2, high_matrix]

def process_iron_butterfly(low, atm, atm_2, high, dir_low, dir_atm, dir_high) -> list:
    with ThreadPoolExecutor(max_workers=4) as executor:
        low_future = executor.submit(low.get_matrix, dir_low)
        atm_future = executor.submit(atm.get_matrix, dir_atm)
        atm_2_future = executor.submit(atm_2.get_matrix, dir_atm)
        high_future = executor.submit(high.get_matrix, dir_high)

        low_matrix = low_future.result()
        atm_matrix = atm_future.result()
        atm_2_matrix = atm_2_future.result()
        high_matrix = high_future.result()
    
    return [low_matrix, atm_matrix, atm_2_matrix, high_matrix]