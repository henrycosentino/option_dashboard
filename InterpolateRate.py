import requests
import numpy as np

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

rates_value_dict = {}
time_lst = [30, 90, 180, 365, 730, 1095, 1825, 2555, 3650, 7300, 10950]

count = 0
for value in rates_series_dict.values():
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id={value}&api_key={fred_key}&file_type=json'
    data = requests.get(url).json()
    rate = float(data['observations'][-1]['value']) / 100

    rates_value_dict[time_lst[count]] = rate
    count += 1

def get_rates_value_dict() -> dict:
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