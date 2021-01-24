# -*- coding: utf-8 -*-
"""
Created on Sun Nov 29 21:41:34 2020

@author: Xiang
"""

import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.preprocessing import MinMaxScaler
from tensorflow.python.keras.layers import Dense, LSTM, Conv1D, MaxPooling1D, TimeDistributed, Flatten
from tensorflow.python.keras import Sequential
import matplotlib.pyplot as plt
import database as db


def LSTM_STOCK(category, code, time_step, show, **kwargs):
    df_STOCK = pd.read_sql('SELECT * FROM tw_stock.{} WHERE 證券代號 = {}'.format(category, code), con=db.connection).sort_values(by='date')
    # db.cursor.close()
    # db.connection.close()
    df_STOCK['date'] = df_STOCK['date'].map(lambda x: x[:4] + '-' + x[4:6] + '-' + x[6:]).map(lambda x: datetime.strptime(x, "%Y-%m-%d"))
    df_STOCK.index = df_STOCK['date']

    # create a new df with only '收盤價'
    data = df_STOCK.filter(regex='收盤價')
    dataset = data.values
    training_data_len = int(np.ceil(len(dataset) * 0.8))

    # Scale
    MMS = MinMaxScaler(feature_range=(0, 1))
    scaled_data = MMS.fit_transform(dataset)
    # create the scaled training data set
    train_data = scaled_data[:training_data_len, :]
    # Split
    x_train, y_train = [], []
    for i in range(time_step, len(train_data)):
        x_train.append(train_data[i - time_step:i, 0])
        y_train.append(train_data[i, 0])
    # x_train.shape [batch-size, time steps]
    x_train, y_train = np.array(x_train), np.array(y_train)
    # x_train.reshape [batch-size, time steps, features]
    # x_train = x_train.reshape(x_train.shape[0], x_train.shape[1], 1)
    x_train = x_train.reshape(x_train.shape[0], 1, x_train.shape[1], 1)
    # LSTM
    model = Sequential()
    model.add(TimeDistributed(Conv1D(filters=16, kernel_size=3, strides=1,
                                     padding='same', activation='relu',
                                     input_shape=(None, x_train.shape[1], 1))))
    model.add(TimeDistributed(MaxPooling1D(pool_size=2)))
    model.add(TimeDistributed(Flatten()))
    model.add(LSTM(40, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(LSTM(40, return_sequences=True))
    model.add(LSTM(40, return_sequences=False))
    model.add(Dense(5))
    model.add(Dense(1))
    # Compile
    model.compile('adam', loss='mean_squared_error')
    model.fit(x_train, y_train, **kwargs)

    # Create the testing data
    test_data = scaled_data[training_data_len - time_step:, :]
    x_test = []
    y_test = dataset[training_data_len:, :]  # original value
    for i in range(time_step, len(test_data)):
        x_test.append(test_data[i - time_step:i, 0])
    x_test = np.array(x_test)
    # x_test = x_test.reshape(x_test.shape[0], x_test.shape[1], 1)
    x_test = x_test.reshape(x_test.shape[0], 1, x_test.shape[1], 1)

    # Predict
    y_pred = model.predict(x_test)
    y_pred = MMS.inverse_transform(y_pred)

    # Get RMSE
    rmse = np.sqrt(np.mean(y_pred - y_test) ** 2)
    print('*-----RMSE-----* : {:.4f}'.format(rmse))
    # Plot result
    train = data[:training_data_len]
    valid = data[training_data_len:]
    valid['Predictions'] = y_pred

    if show:
        plt.figure()
        plt.title('LSTM with stock: {} - {}'.format(df_STOCK['證券名稱'].unique()[0], code))
        plt.xlabel('Close Price NTD', fontsize=18)
        plt.plot(train['收盤價'])
        plt.plot(valid[['收盤價', 'Predictions']])
        plt.legend(['Train', 'Val', 'Predictions'], loc='lower right')
        plt.show()

    # predict new day
    # new_x = np.vstack((x_test[-1][1:], test_data[-1].reshape(-1,1)))
    new_x = np.vstack((x_test[-1][-1][1:], test_data[-1][-1].reshape(-1, 1)))
    # new_pred = MMS.inverse_transform(model.predict(new_x.reshape(1,-1,1)))[0][0]
    new_pred = MMS.inverse_transform(model.predict(new_x.reshape(1, 1, -1, 1)))[0][0]
    print('*-----今日收盤價為 "{:.2f}"-----*'.format(valid['收盤價'][-1]))
    print('*-----預測明日收盤價為 "{:.2f}"-----*'.format(new_pred))
    print('*-----預測明日漲跌為 "{}"-----*'.format(['漲' if (new_pred - valid['收盤價'][-1]) > 0 else '跌'][0]))
    return valid, train


if __name__ == '__main__':
    valid = LSTM_STOCK(category='半導體業', code='2330', time_step=7, show=True, batch_size=1, epochs=5, verbose=1)
