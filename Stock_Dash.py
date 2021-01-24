from mysql.connector import Error
import warnings

warnings.filterwarnings('ignore')
import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import requests
import database as db
import Stock_Predict as predict
import matplotlib.pyplot as plt
from datetime import date, datetime
from dash.dependencies import Input, Output
from bs4 import BeautifulSoup
from plotly.tools import mpl_to_plotly

# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
app.config.suppress_callback_exceptions = True


def get_stock_code():
    r = requests.get('https://www.twse.com.tw/zh/page/trading/exchange/MI_INDEX.html')
    sp = BeautifulSoup(r.text, 'html.parser')
    options = [y.text for y in sp.select('option')][19:]
    options.remove('綜合')
    options.remove('存託憑證')
    return options


def get_options(list_stocks):
    dict_list = []
    for i in list_stocks:
        dict_list.append({'label': i, 'value': i})
    return dict_list


all_category = get_stock_code()

df_STOCK = pd.read_sql('SELECT * FROM tw_stock.{}'.format(all_category[0]), con=db.connection).sort_values(by='date')
df_STOCK.index = df_STOCK['date'].map(lambda x: x[:4] + '-' + x[4:6] + '-' + x[6:]).map(lambda x: datetime.strptime(x, "%Y-%m-%d"))

stock_data = {
    'category': None,
    'code': None,
    'min_date': df_STOCK['date'][0],
    'max_date': df_STOCK['date'][-1],
    'cur_min_date': df_STOCK['date'][0],
    'cur_max_date': df_STOCK['date'][-1],
}

app.layout = html.Div([
    dbc.Row([
        dbc.Col(
            html.Div(
                children=[
                    dbc.Col(html.H2('DASH - STOCK PRICES'), width="auto"),
                    dbc.Col(html.P('Visualising time series with Plotly - Dash.'), width="auto"),
                    dbc.Col(html.P('Pick one or more stocks from the dropdown below.'), width="auto"),
                    dbc.Row([
                        dbc.Col(html.H4('Category'), width=4),
                        # dbc.DropdownMenu(get_options(all_category), label="Category"),
                        dbc.Col(dcc.Dropdown(
                            id='category-selector',
                            options=get_options(all_category),
                            multi=False,
                            value=all_category[0],
                            style={'backgroundColor': '#1E1E1E'},
                            className='category-selector'
                        ), width=6, style={'color': '#1E1E1E'})
                    ]),
                    dbc.Col(html.H2(' '), width="auto"),
                    dbc.Row([
                        dbc.Col(html.H4('Code'), width=4),
                        dbc.Col(dcc.Dropdown(
                            id='code-selector',
                            multi=True,
                            style={'backgroundColor': '#1E1E1E'},
                            className='code-selector'
                        ), width=6, style={'color': '#1E1E1E'}),
                    ]),
                    dbc.Row([
                        dbc.Col(html.H4('Date'), width=4),
                        dcc.DatePickerRange(
                            id='date-picker-range',
                            min_date_allowed=date(int(stock_data['min_date'][:4]),
                                                  int(stock_data['min_date'][4:6]),
                                                  int(stock_data['min_date'][6:])),
                            max_date_allowed=date(int(stock_data['max_date'][:4]),
                                                  int(stock_data['max_date'][4:6]),
                                                  int(stock_data['max_date'][6:])),
                            start_date=date(int(stock_data['cur_min_date'][:4]),
                                            int(stock_data['cur_min_date'][4:6]),
                                            int(stock_data['cur_min_date'][6:])),
                            end_date=date(int(stock_data['cur_max_date'][:4]),
                                          int(stock_data['cur_max_date'][4:6]),
                                          int(stock_data['cur_max_date'][6:])),
                            display_format='Y/M/D',
                            style={'backgroundColor': '#1E1E1E'}
                        ),
                    ]),
                    dbc.Button("Predict", id="predict_button", size="lg", color="success", className="mr-1", disabled=True),
                ]
            ), width="auto"
        ),
        dbc.Col(
            html.Div(
                children=[dcc.Graph(id='dbGraph', config={'displayModeBar': False}, animate=True)]
            )
        ),
        dbc.Col(
            html.Div(
                children=[dcc.Graph(id='predictGraph', config={'displayModeBar': False}, animate=True)]
            )
        )
    ]),
])


@app.callback(
    [
        Output('code-selector', 'options'),
        Output('code-selector', 'value')
    ],
    Input('category-selector', 'value'))
def update_df_stock(dropdown_category):
    global df_STOCK
    df_STOCK = pd.read_sql('SELECT * FROM {}.{}'.format(db.db_settings['database'], dropdown_category), con=db.connection).sort_values(by='date')
    df_STOCK['cate_code'] = df_STOCK['證券代號'] + '_' + df_STOCK['證券名稱']
    df_STOCK['date_int'] = df_STOCK['date'].map(lambda x: int(x))
    df_STOCK.index = df_STOCK['date'].map(lambda x: x[:4] + '-' + x[4:6] + '-' + x[6:]).map(
        lambda x: datetime.strptime(x, "%Y-%m-%d"))
    options = get_options(df_STOCK['cate_code'].sort_values().unique())
    return options, None


@app.callback(
    [
        Output('dbGraph', 'figure'),
        Output('predict_button', 'disabled')
    ], [
        Input('category-selector', 'value'),
        Input('code-selector', 'value'),
        Input('date-picker-range', 'start_date'),
        Input('date-picker-range', 'end_date')
    ]
)
def update_db_figure(category, code, start_date, end_date):
    update_stock_data(category, code, start_date, end_date)
    traces = []
    df_sub = df_STOCK[int(stock_data['cur_min_date']) <= df_STOCK['date_int']]
    df_sub = df_sub[df_sub['date_int'] <= int(stock_data['cur_max_date'])]
    if code:
        for stock in code:
            traces.append(new_scatter(
                x=df_sub[df_sub['cate_code'] == stock].index,
                y=df_sub[df_sub['cate_code'] == stock]['收盤價'],
                name=stock)
            )
    data = [val for sublist in [traces] for val in sublist]
    figure = {
        'data': data,
        'layout': new_layout(range=[df_sub.index.min(), df_sub.index.max()], name='Stock Prices')
    }
    return figure, code is None


@app.callback(
    Output('predictGraph', 'figure'),
    Input('predict_button', 'n_clicks')
)
def update_predict_figure(n):
    traces = []
    range = [df_STOCK.index.min(), df_STOCK.index.max()]
    if n is not None:
        valid, train = predict.LSTM_STOCK(stock_data['category'], stock_data['code'], 7, False, batch_size=1, epochs=5, verbose=1)
        traces.append(new_scatter(x=valid.index, y=valid['收盤價'], name=stock_data['code'] + 'Real'))
        traces.append(new_scatter(x=valid.index, y=valid['Predictions'], name=stock_data['code'] + 'Predict'))
        traces.append(new_scatter(x=train.index, y=train['收盤價'], name=stock_data['code'] + 'Train'))
        range = [train.index.min(), valid.index.max()]
    data = [val for sublist in [traces] for val in sublist]
    figure = {
        'data': data,
        'layout': new_layout(range=range, name='Predict Prices')
    }
    return figure


def update_stock_data(category, code, start, end):
    stock_data['category'] = category
    if code:
        stock_data['code'] = code[0].split('_')[0]
    stock_data['cur_min_date'] = start.replace('-', '')
    stock_data['cur_max_date'] = end.replace('-', '')


def new_scatter(x, y, name):
    scatter = go.Scatter(
        x=x,
        y=y,
        mode='lines',
        opacity=0.7,
        name=name,
        textposition='bottom center',
    )
    return scatter


def new_layout(range, name):
    layout = go.Layout(
        colorway=["#5E0DAC", '#FF4F00', '#375CB1', '#FF7400', '#FFF400', '#FF0056'],
        template='plotly_dark',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        margin={'b': 15},
        hovermode='x',
        autosize=True,
        title={'text': name, 'font': {'color': 'white'}, 'x': 0.5},
        xaxis={'range': range},
    )
    return layout


if __name__ == '__main__':
    app.run_server(debug=True)
