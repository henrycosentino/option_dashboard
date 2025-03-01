import numpy as np
from scipy.stats import norm


class BlackScholes:

    def __init__(self, k, s, r, t, iv, b):
        self.k = k # Strike
        self.s = s # Price
        self.r = r # Risk free rate (annual)
        self.t = t # Time (fraction of years)
        self.iv = iv # Implied volatility
        self.b = b # Dividend rate (annual)

    def _d1(self):
        return (np.log(self.s/self.k) + (self.b + self.iv**2 * 0.5) * self.t) / (np.sqrt(self.t) * self.iv)
        
    def _d2(self):
        return self._d1() - self.iv * np.sqrt(self.t)
    
    def call_px(self):
        return self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(self._d1()) - self.k * np.exp(-self.r * self.t) * norm.cdf(self._d2())
    
    def put_px(self):
        return self.k * np.exp(-self.r * self.t) * norm.cdf(-self._d2()) - self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(-self._d1())

    def delta(self, type):
        type = type.upper()
        if type == 'CALL':
            return np.exp((self.b-self.r) * self.t) * norm.cdf(self._d1())
        if type == 'PUT':
            return -np.exp((self.b-self.r) * self.t) * norm.cdf(-self._d1())
        
    def gamma(self):
        return (np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1())) / (self.s * self.iv * np.sqrt(self.t))
    
    def vega(self):
        return (self.s * np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * np.sqrt(self.t)) / 100 # Scales to a one percentage point change (ie 1%)

    def rho(self, type):
        type = type.upper()
        if type == 'CALL':
            if self.b == 0:
                return -self. t * self.call_px() / 100 # Scales to a one percentage point change (ie 1%)
            else:
                return self.t * self.k * np.exp(-self.r * self.t) * norm.cdf(self._d2()) / 100 # Scales to a one percentage point change (ie 1%)
        if type == 'PUT':
            if self.b == 0:
                return -self. t * self.put_px() / 100 # Scales to a one percentage point change (ie 1%)
            else:
                return -self.t * self.k * np.exp(-self.r * self.t) * norm.cdf(-self._d2()) / 100 # Scales to a one percentage point change (ie 1%)
    
    def theta(self, type):
        type = type.upper()
        term1 = -(self.s * np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * self.iv) / (2 * np.sqrt(self.t))
        if type == 'CALL':
            term2 = (self.b - self.r) * self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(self._d1()) - (self.r * self.k * np.exp(-self.r * self.t) * norm.cdf(self._d2()))
            return (term1 + term2) / 365 # Scaled to represent calendar day time-value 
        elif type == 'PUT':
            term2 = (self.b - self.r) * self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(-self._d1()) + (self.r * self.k * np.exp(-self.r * self.t) * norm.cdf(-self._d2()))
            return (term1 + term2) / 365 # Scaled to represent calendar day time-value 
        
    def vanna(self):
        return -np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * (self._d2() / self.iv)

    def charm(self, type):
        type = type.upper()
        term1 = norm.pdf(self._d1()) * ((self.b / (self.iv*np.sqrt(self.t))) - (self._d2() / (2 * self.t)))
        term2 = (self.b-self.r) * norm.cdf(self._d1())
        if type == 'CALL':
            return -np.exp((self.b-self.r) * self.t) * (term1 + term2) / 252 # Scaled to represent trading calendar
        elif type == 'PUT':
            return -np.exp((self.b-self.r) * self.t) * (term1 - term2) / 252 # Scaled to represent trading calendar