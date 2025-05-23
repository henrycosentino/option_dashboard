import numpy as np
from scipy.stats import norm


class BlackScholes:

    def __init__(self, k, s, r, t, iv, b):
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

    def delta(self, optionType: str) -> float:
        optionType = optionType.upper()
        if optionType == 'CALL':
            return np.exp((self.b-self.r) * self.t) * norm.cdf(self._d1())
        if optionType == 'PUT':
            return -np.exp((self.b-self.r) * self.t) * norm.cdf(-self._d1())
        
    def gamma(self) -> float:
        return (np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1())) / (self.s * self.iv * np.sqrt(self.t))
    
    def vega(self) -> float:
        return (self.s * np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * np.sqrt(self.t)) / 100 # Scales to a one percentage point change (ie 1%)

    def rho(self, optionType: str) -> float:
        optionType = optionType.upper()
        if optionType == 'CALL':
            if self.b == 0:
                return -self. t * self.call_px() / 100 # Scales to a one percentage point change (ie 1%)
            else:
                return self.t * self.k * np.exp(-self.r * self.t) * norm.cdf(self._d2()) / 100 # Scales to a one percentage point change (ie 1%)
        if optionType == 'PUT':
            if self.b == 0:
                return -self. t * self.put_px() / 100 # Scales to a one percentage point change (ie 1%)
            else:
                return -self.t * self.k * np.exp(-self.r * self.t) * norm.cdf(-self._d2()) / 100 # Scales to a one percentage point change (ie 1%)
    
    def theta(self, optionType: str) -> float:
        optionType = optionType.upper()
        term1 = -(self.s * np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * self.iv) / (2 * np.sqrt(self.t))
        if optionType == 'CALL':
            term2 = (self.b - self.r) * self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(self._d1()) - (self.r * self.k * np.exp(-self.r * self.t) * norm.cdf(self._d2()))
            return (term1 + term2) / 365 # Scaled to represent calendar day time-value 
        elif optionType == 'PUT':
            term2 = (self.b - self.r) * self.s * np.exp((self.b-self.r) * self.t) * norm.cdf(-self._d1()) + (self.r * self.k * np.exp(-self.r * self.t) * norm.cdf(-self._d2()))
            return (term1 + term2) / 365 # Scaled to represent calendar day time-value 
        
    def vanna(self) -> float:
        return -np.exp((self.b-self.r) * self.t) * norm.pdf(self._d1()) * (self._d2() / self.iv)

    def charm(self, optionType: str) -> float:
        optionType = optionType.upper()
        term1 = norm.pdf(self._d1()) * ((self.b / (self.iv*np.sqrt(self.t))) - (self._d2() / (2 * self.t)))
        term2 = ((self.b-self.r) * norm.cdf(self._d1()))
        if optionType == 'CALL':
            return -np.exp((self.b-self.r) * self.t) * (term1 + term2) / 252 # Scaled to represent trading calendar
        elif optionType == 'PUT':
            return -np.exp((self.b-self.r) * self.t) * (term1 - term2) / 252 # Scaled to represent trading calendar
        
    def charm(self, optionType: str) -> float:
        optionType = optionType.upper()
        term1 = norm.pdf(self._d1()) * ((self.b / (self.iv * np.sqrt(self.t))) - (self._d2() / (2 * self.t)))
        term2 = (self.b - self.r) * norm.cdf(self._d1())
        if optionType == 'CALL':
            return -np.exp((self.b - self.r) * self.t) * (term1 + term2) / 252
        elif optionType == 'PUT':
            return -np.exp((self.b - self.r) * self.t) * (term1 - (self.b - self.r) * norm.cdf(-self._d1())) / 252
        
    def volga(self) -> float:
        return self.vega() * (self._d1() * self._d2() / self.iv) / 100
