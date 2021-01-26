import numpy as np
import plotly.graph_objs as go
import pandas_datareader as pdr
import datetime as datetime
import talib


def update_candlestick(cate_code, min, max):
    if cate_code is None:
        return go.Figure()
    [code, stock] = cate_code.split('_')
    start = datetime.datetime(int(min[:4]), int(min[4:6]), int(min[6:]))
    end = datetime.datetime(int(max[:4]), int(max[4:6]), int(max[6:]))
    df = pdr.DataReader('{}.TW'.format(code), 'yahoo', start=start, end=end)

    fig = go.Figure(
        data=[go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name=stock,
                             increasing_line_color='red', decreasing_line_color='green')])
    fig.add_trace(
        go.Scatter(x=df.index, y=talib.SMA(np.array(df['Close'], dtype='float'), 5), marker_color='#fae823', name='5 MA', hovertemplate=[]))
    fig.add_trace(
        go.Scatter(x=df.index, y=talib.SMA(np.array(df['Close'], dtype='float'), 10), marker_color='#16e6f5', name='10 MA', hovertemplate=[]))
    fig.add_trace(
        go.Scatter(x=df.index, y=talib.SMA(np.array(df['Close'], dtype='float'), 20), marker_color='#7e04cf', name='20 MA', hovertemplate=[]))
    fig.update_layout({'plot_bgcolor': "#21201f", 'paper_bgcolor': "#21201f", 'legend_orientation': "h"},
                      legend=dict(y=1, x=0),
                      font=dict(color='#dedddc'), hovermode='x unified',
                      margin=dict(b=20, t=0, l=0, r=40))
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=True,
                     showspikes=True, spikemode='across', showline=False, spikedash='dash', color='pink')
    # 加上spikesnap='cursor'可無間隔移動
    fig.update_xaxes(showgrid=False, zeroline=False, rangeslider_visible=True, showticklabels=True,
                     showspikes=True, spikemode='across', showline=False, spikedash='dash', color='pink')
    # fig.update_layout(hoverdistance=100)
    # fig.update_traces(xaxis='x', hoverinfo='x unified')
    return fig
