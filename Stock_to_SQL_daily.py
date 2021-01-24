# -*- coding: utf-8 -*-
"""
Created on Thu Dec  3 21:21:49 2020

@author: Xiang
"""

import warnings
warnings.filterwarnings('ignore')
import mysql.connector
from mysql.connector import Error
from tqdm import tqdm
from datetime import datetime
from Stock_Crawl_daily import Crawl
import pandas as pd
import logging
import argparse
import database as db


class STORE_TO_SQL:
    def __init__(self):
        self.logger = logging.getLogger('SQL')
        
    def start(self, start_date, end_date):
        try:
            if db.connection.is_connected():    
                # Show version of SQL
                db_Info = db.connection.get_server_info()
                self.logger.info('資料庫版本：{}'.format(db_Info))
        
                # Show the current database
                db.cursor.execute('SELECT DATABASE();')
                record = db.cursor.fetchone()
                self.logger.info('目前使用的資料庫：{}'.format(record))
        
        except Error as e:
            self.logger.warning('資料庫連接失敗：{}'.format(e))
        
        finally:
            if (db.connection.is_connected()):
                # get stock code
                stock_code = Crawl().get_stock_code()
                time_period_weekday = Crawl().get_time_period(start = start_date, end = end_date)
                for name, code in tqdm(stock_code.items()):
                    df = Crawl().TW_stock(date_periods = time_period_weekday, code = code)
                    df = df.where(pd.notnull(df), None)
                    stock_name = name
                    db.cursor.execute("""
                                   CREATE TABLE IF NOT EXISTS {} (
                                   證券代號 VARCHAR(255), 證券名稱 VARCHAR(255), 成交股數 FLOAT(65,2),
                                   成交筆數 INTEGER(255), 成交金額 FLOAT(65,2), 開盤價 FLOAT(65,2),
                                   最高價 FLOAT(65,2), 最低價 FLOAT(65,2), 收盤價 FLOAT(65,2),
                                   `漲跌(+/-)` INTEGER(255), 漲跌價差 FLOAT(65,2), 最後揭示買價 FLOAT(65,2),
                                   最後揭示買量 INTEGER(255), 最後揭示賣價 FLOAT(65,2), 最後揭示賣量 INTEGER(255),
                                   本益比 FLOAT(65,2), date VARCHAR(255)
                                   ) 
                                   """.format(stock_name))
                    for index, row in df.iterrows():
                        command = """INSERT INTO {} (證券代號, 證券名稱, 成交股數, 成交筆數, 成交金額,
                                       開盤價, 最高價, 最低價, 收盤價, `漲跌(+/-)`,
                                       漲跌價差, 最後揭示買價, 最後揭示買量, 最後揭示賣價,
                                       最後揭示賣量, 本益比, date) values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""".format(stock_name)
                        db.cursor.execute(command, (row['證券代號'], row['證券名稱'], row['成交股數'], row['成交筆數'], row['成交金額'],
                                                 row['開盤價'], row['最高價'], row['最低價'], row['收盤價'], row['漲跌(+/-)'],
                                                 row['漲跌價差'], row['最後揭示買價'], row['最後揭示買量'], row['最後揭示賣價'],
                                                 row['最後揭示賣量'],row['本益比'], row['date']))          
                    self.logger.info('*--Now {} has been stored into SQL--*'.format(stock_name))
                    db.connection.commit()
                self.logger.info('*--Now all stock from {} to {} has been stored into SQL--*'.format(start_date, end_date))
                # commit and close
#                connection.commit()
                db.cursor.close()
                db.connection.close()
                self.logger.info('資料庫連線已關閉')
            
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
    today = datetime.today().strftime('%Y-%m-%d')
    STORE_TO_SQL().start(start_date  = '2021-01-09', end_date = '2021-01-23')