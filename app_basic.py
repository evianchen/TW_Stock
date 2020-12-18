import mysql.connector
from mysql.connector import Error
import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from dash.dependencies import Input, Output

# Initialize the app
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

# 資料庫設定
db_settings = {
    'host': '127.0.0.1', # 主機名稱
    'port': 3306,
    'user': 'root', # 帳號
    'password': 'evian', # 密碼
    'database' : 'tw_stock'
}
connection = mysql.connector.connect(**db_settings)
cursor = connection.cursor()
df_STOCK = pd.read_sql('SELECT * FROM tw_stock.半導體業', con=connection).sort_values(by='date')
df_STOCK['date'] = df_STOCK['date'].map(lambda x: x[:4] + '-' + x[4:6] + '-' + x[6:]).map(lambda x: datetime.strptime(x, "%Y-%m-%d"))
df_STOCK.index = df_STOCK['date']
df_STOCK['cate_code'] = df_STOCK['證券代號'] + '_' + df_STOCK['證券名稱']
cursor.close()
connection.close()

def get_options(list_stocks):
    dict_list = []
    for i in list_stocks:
        dict_list.append({'label': i, 'value': i})
    return dict_list

cate_code = df_STOCK['證券代號'] + '_' + df_STOCK['證券名稱']
app.layout = html.Div(
    children=[
        html.Div(className='row',
                 children=[
                    html.Div(className='four columns div-user-controls',
                             children=[
                                 html.H2('DASH - STOCK PRICES'),
                                 html.P('Visualising time series with Plotly - Dash.'),
                                 html.P('Pick one or more stocks from the dropdown below.'),
                                 html.Div(
                                     className='div-for-dropdown',
                                     children=[
                                         dcc.Dropdown(id='stockselector', options=get_options(cate_code.sort_values().unique()),
                                                      multi=True, value=[cate_code.sort_values()[0]],
                                                      style={'backgroundColor': '#1E1E1E'},
                                                      className='stockselector'
                                                      ),
                                     ],
                                     style={'color': '#1E1E1E'})
                                ]
                             ),
                    html.Div(className='eight columns div-for-charts bg-grey',
                             children=[
                                 dcc.Graph(id='timeseries', config={'displayModeBar': False}, animate=True)
                             ])
                              ])
        ]

)


# Callback for timeseries price
@app.callback(Output('timeseries', 'figure'),
              [Input('stockselector', 'value')])
def update_graph(selected_dropdown_value):
    trace1 = []
    df_sub = df_STOCK
    for stock in selected_dropdown_value:
        trace1.append(go.Scatter(x=df_sub[df_sub['cate_code'] == stock].index,
                                 y=df_sub[df_sub['cate_code'] == stock]['收盤價'],
                                 mode='lines',
                                 opacity=0.7,
                                 name=stock,
                                 textposition='bottom center'))
    traces = [trace1]
    data = [val for sublist in traces for val in sublist]
    figure = {'data': data,
              'layout': go.Layout(
                  colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
                  template='plotly_dark',
                  paper_bgcolor='rgba(0, 0, 0, 0)',
                  plot_bgcolor='rgba(0, 0, 0, 0)',
                  margin={'b': 15},
                  hovermode='x',
                  autosize=True,
                  title={'text': 'Stock Prices', 'font': {'color': 'white'}, 'x': 0.5},
                  xaxis={'range': [df_sub.index.min(), df_sub.index.max()]},
              ),

              }

    return figure


if __name__ == '__main__':
    app.run_server()