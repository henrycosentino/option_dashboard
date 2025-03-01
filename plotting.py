import matplotlib.pyplot as plt
import numpy as np
from BlackScholes import BlackScholes
import matplotlib
import matplotlib.colors as mcolors
import matplotlib as mpl

class Plotting:

    def __init__(self, spot, iv, px, k, r, t, b, name, optionType, spot_stp=0.05, iv_stp=0.10):
        self.px = px # Current price of option
        self.spot = spot # Current price of underlying
        self.spot_stp = spot_stp
        self.iv = iv # Current implied volatility
        self.iv_stp = iv_stp
        self.k = k # Strike
        self.r = r # Risk free rate (annual)
        self.t = t # Time (fraction of years)
        self.b = b # Dividend rate (annual)
        self.name = name # The name of the stock
        self.optionType = optionType # Option type (call/put)

    def offset_spot_lst(self):
        step_size = self.spot_stp * self.spot
        
        lst = []
        for i in range(5):
            if not lst:
                lst.append(self.spot)
            else:
                lst.insert(0, self.spot - step_size * i)
                lst.append(self.spot + step_size * i)
    
        return lst
    
    def offset_iv_lst(self):
        step_size = self.iv_stp * self.iv
        
        lst = []
        for i in range(5):
            if not lst:
                lst.append(self.iv)
            else:
                lst.insert(0, self.iv - step_size * i)
                lst.append(self.iv + step_size * i)
    
        return lst
    
    def matrix(self):
        spot_lst = self.offset_spot_lst()
        iv_lst = self.offset_iv_lst()

        optionType = self.optionType.upper()

        matrix = []
        for iv in iv_lst:
            for spot in spot_lst:
                bs = BlackScholes(self.k, spot, self.r, self.t, iv, self.b)
                if optionType == 'CALL':
                    matrix.append(round(bs.call_px() - self.px, 2))
                if optionType == 'PUT':
                    matrix.append(round(bs.put_px() - self.px, 2))

        return np.array(matrix).reshape(9,9)
    
    def heatmap(self, ax=None, cbar_kw=None, 
                cbarlabel="", **kwargs):
        # **kwargs -- all other arguments are forwarded to imshow

        if ax is None:
            ax = plt.gca()

        if cbar_kw is None:
            cbar_kw = {}

        # Heatmap
        im = ax.imshow(self.matrix(), **kwargs)

        # Colorbar
        cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
        cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom", color='white')
        cbar.ax.yaxis.set_tick_params(color='white')  
        for label in cbar.ax.get_yticklabels():
            label.set_color('white')

        iv_lst_format = [f"{round(x*100,1)}%" for x in self.offset_iv_lst()]
        spot_lst_format = [round(x,2) for x in self.offset_spot_lst()]

        # Formatting
        ax.set_xticks(range(self.matrix().shape[1]), labels=spot_lst_format)
        ax.set_yticks(range(self.matrix().shape[0]), labels=iv_lst_format)
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')

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
            threshold = im.norm(self.matrix().max())/2.

        kw = dict(horizontalalignment="center",
                verticalalignment="center")
        kw.update(textkw)

        if isinstance(valfmt, str):
            valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

        texts = []
        for i in range(self.matrix().shape[0]):
            for j in range(self.matrix().shape[1]):
                kw.update(color=textcolors[int(im.norm(self.matrix()[i, j]) > threshold)])
                text = im.axes.text(j, i, valfmt(self.matrix()[i, j], None), **kw)
                texts.append(text)

        return texts
    
    def plot(self):
        fig, ax = plt.subplots(figsize=(10,10), facecolor='none')

        red_green_cmap = mcolors.LinearSegmentedColormap.from_list("RedGreen", ["red","white","green"])
        norm = mcolors.TwoSlopeNorm(vmin=np.min(self.matrix()), vcenter=0, vmax=np.max(self.matrix()))

        im, cbar = self.heatmap(ax=ax, cmap=red_green_cmap, norm=norm, cbarlabel="PnL",
                                cbar_kw={'shrink': 0.7})
        texts = self.annotate_heatmap(im, valfmt="{x:.2f}", textcolors=("black", "black"))

        plt.title(f"PnL for {self.name} {self.optionType} Option", fontsize=20, fontweight='bold', color='white')
        plt.xlabel("Spot Price", fontsize=14, color='white')
        plt.ylabel("Implied Volatility", fontsize=14, color='white')

        fig.tight_layout()
        plt.show()
        
        return fig