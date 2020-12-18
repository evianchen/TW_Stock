# -*- coding: utf-8 -*-
"""
Created on Thu Dec  3 21:07:57 2020

@author: Xiang
"""

import time
import logging
import argparse
import requests
import pandas as pd
import numpy as np
from io import StringIO
from datetime import datetime
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
   
class Crawl:
    def __init__(self):
        self.logger = logging.getLogger('stock')
        
    def get_time_period(self, start, **kwargs):
        """
        definition of weekday: Monday ~ Friday
        start: start_date
        **kwargs: end_date
        create from start_date to end_date(if exists)
        """
        time_period = pd.date_range(start = start, **kwargs)
        time_period_weekday = time_period[np.where(time_period.map(lambda x: x.isoweekday() < 6))]
        time_period_weekday = pd.Series(time_period_weekday).apply(lambda x: datetime.strftime(x, '%Y-%m-%d').replace('-', ''))
        self.logger.info('Create {} weekdays'.format(len(time_period_weekday)))
        return time_period_weekday    
    
    def set_header_user_agent(self):
        """
        Creat fake Useragent
        """
        user_agent = UserAgent()
        return user_agent.random
    
    def daily_crawler_stock(self, datestr, code):
        requests.adapters.DEFAULT_RETRIES = 5
        r = requests.session()
        r.keep_alive = False
        # fake agent 
        user_agent = self.set_header_user_agent()
        # download
        r = r.get('https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + datestr + '&type=' + code,
                          headers={'user-agent': user_agent, 'Connection': 'close'})
        # preprocessing
        df = pd.read_csv(StringIO(r.text.replace("=", "")), 
                    header=["證券代號" in l for l in r.text.split("\n")].index(True)-1).iloc[:,:-1].iloc[:-6,:]
        df.columns = df.iloc[0,:]
        df = df.iloc[1:,:]
        # replace word
        for col in df.columns[2:]:
            if col == '漲跌(+/-)': #漲+1跌-1無資訊nan
                df[col] = df[col].apply(lambda x: np.nan if x == ' ' else x).apply(lambda x: 1 if x== '+' else -1)
            else:
                df[col] = df[col].astype(str).str.replace(',', '').replace('--', np.nan).astype(float)
        return df
    
    def get_stock_code(self):
        r = requests.get('https://www.twse.com.tw/zh/page/trading/exchange/MI_INDEX.html')
        sp = BeautifulSoup(r.text, 'html.parser')
        options = sp.select('option')
        options1 = [y.text for y in options]
        values = [o.get("value") for o in options]
        stock_code = dict(zip(options1[19:], values[19:]))
        stock_code.update({'ETF':'0099P'})
        del stock_code['綜合']
        del stock_code['存託憑證']
        return stock_code

    def TW_stock(self, date_periods, code):
        stock_list, count_good, count_bad = [], 0, 0
        for value in date_periods.values:
            try:
                if (count_good + count_bad) % 50 ==0:
                    self.logger.info('Now crawler total days= {}'.format(count_good + count_bad))
                df = self.daily_crawler_stock(datestr = value, code = code)
                count_good += 1
                df['date'] = value
                stock_list.append(df)
                time.sleep(10)
            except ValueError:
                count_bad += 1
                self.logger.warning('Crawler faild on: {}, it is a holiday.'.format(value))
                continue
        self.logger.info('Crawler success total = {}'.format(count_good))
        self.logger.info('Crawler faild total = {}'.format(count_bad))
        stock_list = pd.concat(stock_list)
        return stock_list
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d","--debug", help="getall ruten result", action = "store_true")
    parser.add_argument("--return_counts", type=bool, default=True)
    parser.add_argument("--mode", default='client')
    parser.add_argument("--port", default=52162)
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level = logging.DEBUG)
    else:
        logging.basicConfig(level = logging.INFO)