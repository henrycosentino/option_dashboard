import matplotlib.pyplot as plt
import numpy as np
from BlackScholes import BlackScholes
import matplotlib
import matplotlib.colors as mcolors

class Plotting:

    def __init__(self, spot, call_px, put_px, call_iv, put_iv, k, r, t, b, 
                 name, optionType=None, direction=None, strategy=None, 
                 call_quantity=None, put_quantity=None, spot_stp=0.05, 
                 iv_stp=0.10, px_atm=None, px_high=None, iv_atm=None,
                 iv_high=None, k_atm=None, k_high=None):
        
        self.spot = spot # Current price of underlying       
        self.call_px = call_px # Current call price
        self.put_px = put_px # Current put price
        self.call_iv = call_iv # Implied volatility of call option
        self.put_iv = put_iv # Implied volatility of put option
        self.k = k # Strike
        self.r = r # Risk free rate (annual)
        self.t = t # Time (fraction of years)
        self.b = b # Dividend rate (annual)
        self.name = name # The name of the stock
        self.optionType = optionType.title() if optionType else None # Option type (call/put)
        self.direction = direction.title() if direction else None # Market position (long/short)
        self.strategy = strategy.title() if strategy else None # The type of strategy we put on (straddle, butterfly)
        self.spot_stp = spot_stp
        self.iv_stp = iv_stp
        self.call_quantity = call_quantity
        self.put_quantity = put_quantity
        self.iv_lst_call = None
        self.iv_lst_put = None
        self.px_atm = px_atm
        self.px_high = px_high
        self.iv_atm = iv_atm
        self.iv_high = iv_high
        self.k_atm = k_atm
        self.k_high = k_high
        self.iv_lst_atm = None
        self.iv_lst_high = None

    def offset_spot_lst(self):
        step_size = self.spot_stp * self.spot
        return [self.spot + step_size * (i - 4) for i in range(9)]
    
    def offset_iv_lst(self):
        if self.optionType == 'Call':
            iv = self.call_iv
        if self.optionType == 'Put':
            iv = self.put_iv
        
        step_size = self.iv_stp * iv
        
        lst = []
        for i in range(5):
            if not lst:
                lst.append(iv)
            else:
                lst.insert(0, iv - step_size * i)
                lst.append(iv + step_size * i)
        
        if self.optionType == 'Call':
            self.iv_lst_call = lst
        if self.optionType == 'Put':
            self.iv_lst_put = lst
    
        return lst
    
    def matrix(self):
        spot_lst = self.offset_spot_lst()
        iv_lst = self.offset_iv_lst()

        matrix = []
        for iv in iv_lst:
            for spot in spot_lst:
                bs = BlackScholes(self.k, float(spot), self.r, self.t, float(iv), self.b)
                # Long Call
                if self.optionType == 'Call' and self.direction == 'Long':
                    matrix.append(round(bs.call_px() - self.call_px, 2))
                # Long Put
                elif self.optionType == 'Put' and self.direction == 'Long':
                    matrix.append(round(bs.put_px() - self.put_px, 2))
                # Short Call
                elif self.optionType == 'Call' and self.direction == 'Short':
                    matrix.append(round(self.call_px - bs.call_px(), 2))
                # Short Put
                elif self.optionType == 'Put' and self.direction == 'Short':
                    matrix.append(round(self.put_px - bs.put_px(), 2))
        return np.array(matrix).reshape(9,9)
    
    def strategies(self):
        # Long Call
        if self.optionType == 'Call' and self.direction == 'Long':
            return self.matrix()
        # Long Put
        elif self.optionType == 'Put' and self.direction == 'Long':
            return self.matrix()
        # Short Call
        elif self.optionType == 'Call' and self.direction == 'Short':
            return self.matrix()
        # Short Put
        elif self.optionType == 'Put' and self.direction == 'Short':
            return self.matrix()
        # Long Straddle
        elif self.strategy == 'Straddle' and self.direction == 'Long':
            call_instance = Plotting(self.spot, self.call_px, self.put_px, self.call_iv, self.put_iv,
                           self.k, self.r, self.t, self.b, self.name, optionType='Call', 
                           direction='Long')
            put_instance = Plotting(self.spot, self.call_px, self.put_px, self.call_iv, self.put_iv,
                          self.k, self.r, self.t, self.b, self.name, optionType='Put', 
                          direction='Long')
            
            self.iv_lst_call = call_instance.offset_iv_lst()
            self.iv_lst_put = put_instance.offset_iv_lst()
    
            call_matrix = call_instance.matrix() * self.call_quantity
            put_matrix = put_instance.matrix() * self.put_quantity
            
            return call_matrix + put_matrix
        # Short Straddle
        elif self.strategy == 'Straddle' and self.direction == 'Short':
            call_instance = Plotting(self.spot, self.call_px, self.put_px, self.call_iv, self.put_iv,
                           self.k, self.r, self.t, self.b, self.name, optionType='Call', 
                           direction='Short')
            put_instance = Plotting(self.spot, self.call_px, self.put_px, self.call_iv, self.put_iv,
                          self.k, self.r, self.t, self.b, self.name, optionType='Put', 
                          direction='Short')
            
            self.iv_lst_call = call_instance.offset_iv_lst()
            self.iv_lst_put = put_instance.offset_iv_lst()
    
            call_matrix = call_instance.matrix() * self.call_quantity
            put_matrix = put_instance.matrix() * self.put_quantity
            
            return call_matrix + put_matrix
        # Long Call Butterfly & Long Put Butterfly
        elif self.strategy in ['Long Call Butterfly', 'Long Put Butterfly']:
            optionType = 'Call'.capitalize() if 'Call' in self.strategy else 'Put'
            
            low_instance = Plotting(self.spot, call_px=self.call_px, put_px=self.put_px,
                                    call_iv=self.call_iv, put_iv=self.put_iv, k=self.k,
                                    r=self.r, b=self.b, t=self.t, name=self.name, 
                                    optionType=optionType, direction='Long') 
            atm_instance = Plotting(self.spot, call_px=self.px_atm, put_px=self.px_atm,
                                    call_iv=self.iv_atm, put_iv=self.iv_atm, t=self.t, 
                                    k=self.k_atm, r=self.r, b=self.b, 
                                    name=self.name, optionType=optionType, direction='Short')
            high_instance = Plotting(self.spot, call_px=self.px_high, put_px=self.px_high,
                                    call_iv=self.iv_high, put_iv=self.iv_high, t=self.t, 
                                    k=self.k_high, r=self.r, b=self.b, 
                                    name=self.name, optionType=optionType, direction='Long') 

            low_matrix = low_instance.matrix()
            atm_matrix = atm_instance.matrix() * 2
            high_matrix = high_instance.matrix()

            self.iv_lst_call = low_instance.offset_iv_lst() if optionType == 'Call' else None
            self.iv_lst_put = low_instance.offset_iv_lst() if optionType == 'Put' else None
            self.iv_lst_atm = atm_instance.offset_iv_lst()
            self.iv_lst_high = high_instance.offset_iv_lst()

            return low_matrix + atm_matrix + high_matrix

        # Short Call Butterfly & Short Put Butterfly
        elif self.strategy in ['Short Call Butterfly', 'Short Put Butterfly']:
            pass
    
    def heatmap(self, ax=None, cbar_kw=None, 
                cbarlabel="", **kwargs):
        # **kwargs -- all other arguments are forwarded to imshow

        if ax is None:
            ax = plt.gca()

        if cbar_kw is None:
            cbar_kw = {}

        # Heatmap
        im = ax.imshow(self.strategies(), **kwargs)

        # Colorbar
        cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
        cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom", color='white')
        cbar.ax.yaxis.set_tick_params(color='white')  
        for label in cbar.ax.get_yticklabels():
            label.set_color('white')

        if self.strategy == 'Straddle':
            iv_lst_call_format = [f"{round(x*100,1)}%" for x in self.iv_lst_call]
            iv_lst_put_format = [f"{round(x*100,1)}%" for x in self.iv_lst_put]
            iv_lst_format = [f"{call_iv} / {put_iv}" for call_iv, put_iv in zip(iv_lst_call_format, iv_lst_put_format)]  
        elif self.strategy in ['Long Call Butterfly', 'Short Call Butterfly']:
            iv_lst_low_format = [f"{round(x*100,1)}%" for x in self.iv_lst_call]
            iv_lst_atm_format = [f"{round(x*100,1)}%" for x in self.iv_lst_atm]
            iv_lst_high_format = [f"{round(x*100,1)}%" for x in self.iv_lst_high]
            iv_lst_format = [f"{low_iv} / {atm_iv} / {high_iv}" for low_iv, atm_iv, high_iv in zip(iv_lst_low_format, iv_lst_atm_format, iv_lst_high_format)]  
        elif self.strategy in ['Long Put Butterfly', 'Short Put Butterfly']:
            iv_lst_low_format = [f"{round(x*100,1)}%" for x in self.iv_lst_put]
            iv_lst_atm_format = [f"{round(x*100,1)}%" for x in self.iv_lst_atm]
            iv_lst_high_format = [f"{round(x*100,1)}%" for x in self.iv_lst_high]
            iv_lst_format = [f"{low_iv} / {atm_iv} / {high_iv}" for low_iv, atm_iv, high_iv in zip(iv_lst_low_format, iv_lst_atm_format, iv_lst_high_format)]  
        else:
            iv_lst_format = [f"{round(x*100,1)}%" for x in self.offset_iv_lst()]
        spot_lst_format = [round(x,2) for x in self.offset_spot_lst()]

        # Formatting for the main axis
        ax.set_xticks(range(self.strategies().shape[1]), labels=spot_lst_format)
        ax.set_yticks(range(self.strategies().shape[0]), labels=iv_lst_format)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')

        # Hide spines and grid for aesthetics
        ax.spines[:].set_visible(False)
        ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
        ax.tick_params(which="minor", bottom=False, left=False)

        return im, cbar

    def annotate_heatmap(self, im, valfmt="{x:.2f}",
                        textcolors=("black", "black"),
                        threshold=None, **textkw):

        if threshold is not None:
            threshold = im.norm(threshold)
        else:
            threshold = im.norm(self.strategies().max())/2.

        kw = dict(horizontalalignment="center",
                verticalalignment="center")
        kw.update(textkw)

        if isinstance(valfmt, str):
            valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

        texts = []
        for i in range(self.strategies().shape[0]):
            for j in range(self.strategies().shape[1]):
                kw.update(color=textcolors[int(im.norm(self.strategies()[i, j]) > threshold)])
                text = im.axes.text(j, i, valfmt(self.strategies()[i, j], None), **kw)
                texts.append(text)

        return texts
    
    def plot(self):
        fig, ax = plt.subplots(figsize=(10,10), facecolor='none')

        color_map = mcolors.LinearSegmentedColormap.from_list("Default RedGreen", ["red","white","green"])
        strategy_values = np.array(self.strategies())
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

        im, cbar = self.heatmap(ax=ax, cmap=color_map, norm=norm, cbarlabel="PnL",
                                cbar_kw={'shrink': 0.7})
        texts = self.annotate_heatmap(im, valfmt="{x:.2f}", textcolors=("black", "black"))

        if self.strategy == 'Straddle':
            title = f"PnL of {self.direction} Straddle for {self.name}"
            ylabel = "Implied Volatility (call / put)"
        elif self.strategy == 'Long Call Butterfly':
            title = f"PnL of {self.strategy} for {self.name}"
            ylabel = "Implied Volatility (low / atm / high)"
        elif self.strategy == 'Short Call Butterfly':
            title = f"PnL of {self.strategy} for {self.name}"
            ylabel = "Implied Volatility (low / atm / high)"
        elif self.strategy == 'Long Put Butterfly':
            title = f"PnL of {self.strategy} for {self.name}"
            ylabel = "Implied Volatility (low / atm / high)"
        elif self.strategy == 'Short Put Butterfly':
            title = f"PnL of {self.strategy} for {self.name}"
            ylabel = "Implied Volatility (low / atm / high)"
        else:
            title = f"PnL for {self.direction} {self.name} {self.optionType} Option"
            ylabel = "Implied Volatility"
        
        plt.title(title, fontsize=20, fontweight='bold', color='white')
        plt.xlabel("Spot Price", fontsize=14, color='white')
        plt.ylabel(ylabel, fontsize=14, color='white')

        fig.tight_layout()
        
        return fig