import csv
import os
import json
import requests
import pandas as pd
import tech_indicators as ti
from pandas.io.json import json_normalize

PATH = os.getcwd() + '/data'

# alpha vantage
API_key = '3T6KRZSKKLGLUFOL'
TEMPLATE_URL = 'https://www.alphavantage.co/query?'


def get_stockInfo(*args):
    """
    *args:        'NASDAQ'
                  'NYSE'
                  'ASX'
    """
    stocks = []
    for market in args:
        file = PATH + '/' + market.upper() + '.csv'
        with open(file) as f:
            reader = csv.DictReader(f)  # read rows into a dictionary format
            for row in reader:
                row['market'] = market
                stocks.append(row)
    return stocks


def get_realtimeData(symbol, interval = 1):
    """
    Intraday Data
    
    interval(minutes) = 1, 5, 15, 30, 60
    
    
    Example output:
    
    {'1. Information': 'Intraday (1min) prices and volumes', '2. Symbol': 'MSFT', '3. Last Refreshed': '2018-04-16 16:00:00', 
    '4. Interval': '1min', '5. Output Size': 'Compact', '6. Time Zone': 'US/Eastern', '1. open': '94.2500', 
    '2. high': '94.2999', '3. low': '94.1200', '4. close': '94.1700', '5. volume': '2233922'}
    
    """
    '''
    ['Last Refreshed'], ['Time Zone'], ['open'], ['high'], ['low'], ['close'], ['volume'], ['change'], ['percent_change'], ['desc'], ['sector']
    '''
        
    try:
        json_data = get_stockData(symbol, interval)
    except:
        empty_output = {'Symbol' : symbol, 'Last Refreshed' : 'Error', 'Time Zone' : '', 'open' : '0.0000', 'high' : '0.0000', 'low' : '0.0000', 'close' : '0.0000', 'volume' : '0.0000', 'change' : '0.0000', 'percent_change' : '0.0000', 'desc' : 'Error', 'sector' : 'Symbol does not exist or API Error (Please try again or use another symbol)'}
        return empty_output
    
    OHLCV_key = "Time Series (" + str(interval) + "min)"
    
    #print(json_data)
    if "Meta Data" not in json_data:
    	empty_output = {'Symbol' : symbol, 'Last Refreshed' : 'Error', 'Time Zone' : '', 'open' : '0.0000', 'high' : '0.0000', 'low' : '0.0000', 'close' : '0.0000', 'volume' : '0.0000', 'change' : '0.0000', 'percent_change' : '0.0000', 'desc' : 'Error', 'sector' : 'Symbol does not exist or API Error (Please try again or use another symbol)'}
    	return empty_output
    	
    meta = json_data["Meta Data"]
    OHLCV = json_data[OHLCV_key]
    OHLCV_realtime = next(iter(OHLCV.values()))
    
    meta_OHLCV = {**meta, **OHLCV_realtime}
    # change format of keys, in order to make it more clear and decent
    for key in (iter(meta_OHLCV.keys())):
        new_key = key[3:]
        meta_OHLCV[new_key] = meta_OHLCV.pop(key)
    
    # calculate change and % of change
    yesterday_data = iter(hist_data(symbol).values())
    next(yesterday_data)
    yesterday_close = next(yesterday_data)['4. close']
    current_close = OHLCV_realtime['4. close']
    change = float(current_close) - float(yesterday_close)
    percent_change = change / float(yesterday_close) * 100
    change = format(change, '.2f')
    percent_change = format(percent_change, '.2f')
    # add it to the result dictionary
    meta_OHLCV['change'] = change
    meta_OHLCV['percent_change'] = percent_change
    
    meta_OHLCV.pop('Information')
    meta_OHLCV.pop('Interval')
    meta_OHLCV.pop('Output Size')
    
    return meta_OHLCV


# intra-day data
def get_stockData(symbol, interval = 1):
    """
    Intraday Data
    
    interval(minutes) = 1, 5, 15, 30, 60
    """
    function = 'TIME_SERIES_INTRADAY'
    interval = str(interval) + 'min'
    
    source_url = TEMPLATE_URL + 'function=' + function + '&symbol=' + symbol + '&interval=' + interval + '&apikey=' + API_key
    response = requests.get(source_url) # JSONDecodeError ????
    txt = response.text
    
    json_data = json.loads(txt)
    #print("ASSdDSD##########################")
    #print(json_data)
    return json_data

def hist_data(symbol, start_date=None, end_date=None, outputsize="compact", datatype="json", adjusted=False):
    """
    :param outputsize: "compact" 100 days / "full" all historical data
    :param datatype: "json" / "csv" output format
    :return: 100 days of daily stock data
    
    Example URL:
    https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&outputsize=full&apikey=demo
    https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo&datatype=csv
    """
    function = 'TIME_SERIES_DAILY'
    
    source_url = TEMPLATE_URL + 'function=' + function + '&symbol='+ symbol + '&apikey=' + API_key
    response = requests.get(source_url)
    txt = response.text
    json_data = json.loads(txt)
    #print(json_data)
    try:
        test = json_data['Time Series (Daily)']
    except:
        return {}
    return json_data['Time Series (Daily)']
    

# daily historical close price data
# default parameters will return 100 days of historical data
def chart_data(symbol, start_date=None, end_date=None, outputsize="compact", datatype="json", adjusted=False):
    """
    :param outputsize: "compact" 100 days / "full" all historical data
    :param datatype: "json" / "csv" output format
    :return: 100 days of daily stock data
    
    Example URL:
    https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&outputsize=full&apikey=demo
    https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=MSFT&apikey=demo&datatype=csv
    """
    function = 'TIME_SERIES_DAILY'
    
    source_url = TEMPLATE_URL + 'function=' + function + '&symbol='+ symbol + '&apikey=' + API_key
    response = requests.get(source_url)
    txt = response.text
    json_data = json.loads(txt)
    
    #print(json_data)
    #for key in json_data.items():
    #	print (key)
    if 'Time Series (Daily)' not in json_data:
    	output = []
    	return output
    	
    hist_data = iter(json_data['Time Series (Daily)'])
    data = []
    
    for date, OHLCV in json_data['Time Series (Daily)'].items():
        temp_dict = {}
        temp_dict["date"] = str(date)
        temp_dict["value"] = float(OHLCV["4. close"])
        data.append(temp_dict)
    
    #print(data)
    return data[::-1]


def chart_data_ti(symbol):
    # df format
    try:
        hist_data = chart_data(symbol)
    except:
        return [], [], [], []
    df = json_normalize(hist_data)
    df = df.sort_values(by='date')

    # MA
    df_ma = ti.MA(df, n=10)

    #EMA
    df_ema = ti.EMA(df, n=10)

    #MACD
    df_macd = ti.MACD(df, n_fast=12, n_slow=26)

    #Momentum
    df_momentum = ti.MOM(df, n=10)

    # json format
    ma = df_ma.to_json(orient='records')
    ema = df_ema.to_json(orient='records')
    macd = df_macd.to_json(orient='records')
    mom = df_momentum.to_json(orient='records')

    return ma, ema, macd, mom

# def MA(df, n):
#     """
#     Moving Average
#     :param json_data: str, json-style data
#     :param n: int, size of the window
#     :return:
#     """
#     # Original version
#     # MA = pd.Series(pd.rolling_mean(df['Close'], n), name = 'MA_' + str(n))
#     MA = pd.Series.rolling(df['value'], n).mean()
#     MA = pd.Series(MA, name = 'MA_' + str(n))
#     df = df.join(MA)
#
#     return df

#Exponential Moving Average
def EMA(df, n):
    # Orignial version
    # EMA = pd.Series(pd.ewma(df['Close'], span = n, min_periods = n - 1), name = 'EMA_' + str(n))
    EMA = pd.Series.ewm(df['value'], span = n, min_periods = n - 1).mean()
    EMA = pd.Series(EMA, name = 'EMA_' + str(n))
    df = df.join(EMA)
    return df

def _json_to_pd(hist_data):
    df = json_normalize(hist_data)
    df = df.sort_values(by='date')
    return df


# def print_dict(dic):
#    for key, value in dic.items():
#        print(key, ":",value)
    
if __name__ == '__main__':
    # rd = get_stockInfo('nasdaq', 'asx', 'nyse')
    # data = get_realtimeData('AAPL')
    # print_dict(data)
    # data = hist_data('AAPL')
    # print(data)

    ma, ema, macd, mom = chart_data_ti('AAPL')
    print(ma)
    print(ema)
    print(macd)
    print(mom)
