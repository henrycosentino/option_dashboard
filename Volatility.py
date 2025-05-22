import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

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

    def spot_iv(self) -> tuple[list[float], list[float]]:
        """Returns two lists (call and put) of spot IV for each expiration date"""
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


### TESTING ###
def testing():
    vol = Volatility('AAPL')

    options_df = vol.spot_iv_surface('CALL')
    options_df = options_df[(options_df['expiryDays'] >= 10) & (options_df['expiryDays'] <= 100)].copy()
    options_df = options_df[(options_df['strike'] >= 180) & (options_df['strike'] <= 220)].copy()
    print(options_df)

# if __name__ == '__main__':
#     testing()