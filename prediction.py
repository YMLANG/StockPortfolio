import ti
import pandas as pd
import quandl as qd
import os
import sys
import warnings
import numpy as np
import time
from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn import svm
"""
What is our 1-Day stock prediction based on?
We use Support Vector Machine to do the classification of historical prices.
"""
# ignore future warnings for pandas
if not sys.warnoptions:
    warnings.simplefilter("ignore")


class MarketDataProvider:
    local_store_dir = os.getcwd() + '/marketstore/'

    def __init__(self, source, symbol, start=None, end=None, interval='1d'):
        """
        initialize source data, start downloading data for the time range
        interval: e.g. 1d, 1w, 1m
        if not in local data store, download from source, then persist to local store
        with key: source_symbol_start_end_interval, otherwise load local file.
        """

        self.symbol = symbol
        self.source = source
        self.start = start
        self.end = end
        self.interval = interval
        if start is None or end is None:
            self.local_store_file = (MarketDataProvider.local_store_dir + self.source + '_' + self.symbol +
                                     '_' + self.interval + '.csv')
        else:
            self.local_store_file = (MarketDataProvider.local_store_dir + self.source + '_' + self.symbol + '_'
                                 + self.start + '_' + self.end + '_' + self.interval + '.csv')

        if self.is_existing_df():
            # if there is a same dataframe downloaded before, use it
            self.data = pd.read_csv(self.local_store_file)
        else:
            # if there is no same dataframe, then download and store it to local store
            if source == 'quandl':
                qd.ApiConfig.api_key = 'Uk8aW7H-x7bvsqD2wH98'
                if start is None or end is None:
                    self.data = qd.get('WIKI/' + symbol)
                else:
                    self.data = qd.get('WIKI/' + symbol, start_date=start, end_date=end)
                self.data.to_csv(self.local_store_file, index=False)  # store new data to local store
            else:
                raise ValueError('unknown source: ' + source)

        print('Loading done.')

    def is_existing_df(self):
        """
        1. check the existence of local store, if no then create one.
        2. check if the data file already exists, return True if file already exists, return False otherwise
        """

        if not os.path.exists(MarketDataProvider.local_store_dir):
            print('Local store does not exist, creating directory ' + MarketDataProvider.local_store_dir)
            os.makedirs(MarketDataProvider.local_store_dir)

        if os.path.isfile(self.local_store_file):
            print('There exists a same file in the local store, loading data from ' + self.local_store_file)
            return True
        else:
            print('There is NO same file in the local store, retrieving from {} ...'.format(self.source.upper()))
            return False

def get_matrix(symbol):
    # make sure the data is loading from local
    for i in range(2):
        datafile = MarketDataProvider('quandl', symbol)
    df = datafile.data

    # get price column
    data = df[['Close', 'Low', 'High', 'Volume']]
    df = data.rename(columns={'Close': 'value'})

    # get indicators columns
    # 5, 10 MA
    df = ti.MA(df, 5)
    df = ti.MA(df, 7)
    df = ti.MA(df, 10)
    # 12, 26 EMA
    df = ti.EMA(df, 5)
    df = ti.EMA(df, 12)
    df = ti.EMA(df, 26)
    # MOM
    df = ti.MOM(df, 1)
    df = ti.MOM(df, 4)
    # # ROC
    # df = ti.ROC(df, 12)
    # MACD
    df = ti.MACD(df, n_fast=12, n_slow=26)
    # # RSI
    # df = ti.RSI(df, 7)
    # TSI
    df = ti.TSI(df, 7, 4)
    # Bollinger Bands
    df = ti.BBANDS(df, 5)
    # Volume: On-Balance Volume
    df = ti.OBV(df, 1)
    # Mass Index
    df = ti.MassI(df)
    # # Vortex Indicator: http://www.vortexindicator.com/VFX_VORTEX.PDF
    # df = ti.Vortex(df, 7)
    # Force Index
    df = ti.FORCE(df, 1)
    # Stochastic oscillator %K
    df = ti.STOK(df)
    # Stochastic oscillator %D
    df = ti.STO(df, 3)
    # # AD
    # df = ti.ACCDIST(df, 1)
    # Chaikin Oscillator
    df = ti.Chaikin(df)
    # Disparity
    df = ti.DIS(df, 5)
    df = ti.DIS(df, 10)
    # Standard Deviation
    # df = ti.STDDEV(df, 7)
    # add Y
    df = get_Y(df)
    return df

def get_Y(df):
    i = 0
    Y = []
    mom = df['Momentum_1']
    while i <= df.index[-1]:
        if mom[i] >= 0:
            y = 1
            Y.append(y)
        elif mom[i] < 0:
            y = 0
            Y.append(y)
        else:
            # this PASS IS VERY IMPORTANT!
            # Since only the first row of df['Momentum_1'] is NaN
            # I use this pass to shift the Y one row above
            # e.g. df['Momentum_1'][1] decides df['Y'][0]
            #      df['Momentum_1'][2] decides df['Y'][1]
            pass
        i += 1
    # last day doesn't have a prediction
    # also make the len(Y) == len(df)
    Y.append(np.NaN)

    Y_col = pd.Series(Y)
    df['Y'] = Y_col.values
    return df

def preprocess(df):
    # drop all the rows with any missing NaN values
    df_dropedNAN = df.dropna(axis=0, how='any')
    # print(df_dropedNAN.columns)
    # df_dropedNAN = df_dropedNAN.sample(frac=1) # shuffle all the rows
    # test y labeling, 8 is the index of Momentum_1
    # df_np = df_dropedNAN.values
    # print(df_np[-10:, 0])
    # print(df_np[-10:, 8])

    # get y
    y_df = df_dropedNAN['Y']
    y = y_df.values
    y = y[:, np.newaxis]

    # get X
    print(df.columns)
    X_df = df_dropedNAN.loc[:, 'MA_5':'Disparity_10']
    # print(X_df.shape)
    pred_X_all = df.loc[len(df) - 1, 'MA_5':'Disparity_10']
    X_df = X_df.append(pred_X_all)
    # print(X_df.shape)
    # print(X_df.columns)
    # print(len(X_df.columns))
    X_all = X_df.values # numpy representation
    X_all = preprocessing.scale(X_all)

    X = X_all[0:-1, :]
    pred_X = X_all[-1, :]
    pred_X = pred_X.reshape(1, len(pred_X))
    # print(X.shape)
    # print(pred_X.shape)
    # print(pred_X)

    return X, pred_X, y

def train_svm(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = 12)
    # analysis of variance
    # anova_filter = SelectKBest(f_regression, k=10)

    # cross validation to tune hyper-parameters
    # C_values = np.linspace(0.5, 10, 15)
    # gamma_values = np.logspace(-8, 3, 10)
    # print(C_values)
    # print(gamma_values)

    # parameters = {'kernel': ('linear',), 'C': C_values}
    clf = svm.SVC()

    # estimator = RFE(clf, n_features_to_select=7)
    estimator = clf.fit(X, y)
    accuracy = clf.score(X, y)
    accuracy = np.around(accuracy, decimals=4) * 100
    # print(type(accuracy))
    # accuracy = round(a, 4)
    # print(accuracy)
    # print(len(estimator.ranking_))
    # print(estimator.support_)
    # print(estimator.ranking_)

    # clf = GridSearchCV(svc, parameters)
    # print(estimator.score(X_train, y_train))
    # print(estimator.score(X_test, y_test))
    print("hahaha", accuracy)
    return estimator, X.shape[0], accuracy

def predict(symbol):
    raw_data = get_matrix(symbol)
    X, pred_X, y = preprocess(raw_data) 
    clf, data_size, acc = train_svm(X, y)
    pred_Y = clf.predict(pred_X)

    if pred_Y[0] == 1:
        pred = 'RISE'
    elif pred_Y[0] == 0:
        pred = 'FALL'
    else:
        pred = 'N/A'

    return pred, data_size, acc


def run(symbol):
    try:
    	pred, data_size, acc = predict(symbol)
    except:
        pred, data_size, acc = 'N/A', 0, 0.00
    return pred, data_size, acc

# output the exact format for the front end
def run_time(symbol):
    start = time.time()
    pred, data_size, acc = run(symbol)
    end = time.time()
    time_it = end - start
    time_it = round(time_it, 4)
    
    return pred, data_size, time_it, acc
    
# pred, size, time, acc = run_time('FB')
# print(type(pred), type(size), type(time), type(acc))
# print(pred, size, time, acc)



