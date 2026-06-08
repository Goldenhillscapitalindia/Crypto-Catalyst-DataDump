# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 11:05:31 2024

@author: nookaraju.c
"""

from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import pandas as pd


pg_db_name = 'CRYPTO DEVELOPMENT'
pg_user = 'postgres'
pg_password = 'GhcHyd_2025$'
pg_host = '192.168.1.68'
pg_port = 5432

pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_name}"
pg_engine = create_engine(pg_connection_string, pool_pre_ping=True)


def df_filter(df,FS_Ticker="FS_Ticker",Date="Date"):
    df['Date'] = pd.to_datetime(df['Date'])

    df = df.sort_values('Date').groupby('FS_Ticker').tail(1)
    df = df.drop(columns=['Date'])
    
    return df

crypto_tech_indi_df='select "Date","FS_Ticker","Symbol","Company","Price","Return","Net_Change","MA9_MA20_Value","MA20_MA50_Value","MA50_MA200_Value","RSI_Value","CCI_Value","Williams_Value","StochRSI_Value","Stochastics_Value","MACD_Value","ATR_Value","ADX_Value","Super_Trend_Value","MFI_Value","PVO_Value","CMF_Value","Moving_Average_Rating","Momentum_Rating","Trend_Rating","Volume_Rating","Final_Rating"\
    from crypto_technical_indicators_daily'

crypto_tech_indi_df = pd.read_sql_query(crypto_tech_indi_df, pg_engine)
crypto_tech_indi_df['Date'] = crypto_tech_indi_df['Date'].dt.tz_localize('UTC')
crypto_tech_indi_df['Date'] = crypto_tech_indi_df['Date'].dt.tz_convert('Asia/Kolkata')

crypto_master_df='select "FS_Ticker","Security_Code","MarketCapDominance","MarketCapitalization","MaxSupply","TotalSupply","Beta_1Y" \
from crypto_master'
crypto_master_df = pd.read_sql_query(crypto_master_df, pg_engine)

crypto_ma_ema_macd_df='select "FS_Ticker","Date","EMA9","EMA12","EMA","EMA26","EMA50","EMA200","9MA","20MA","26MA","50MA","100MA","200MA" \
  from crypto_ma_ema_macd'
crypto_ma_ema_macd_df = pd.read_sql_query(crypto_ma_ema_macd_df, pg_engine)

crypto_ma_ema_macd_df=df_filter(crypto_ma_ema_macd_df,"FS_Ticker","Date")


crypto_ATR_df='select "FS_Ticker","Date","Volume" from crypto_average_true_range'
crypto_ATR_df = pd.read_sql_query(crypto_ATR_df, pg_engine)
crypto_ATR_df=df_filter(crypto_ATR_df,"FS_Ticker","Date")


crypto_target_prices_df='select "FS_Ticker","52_Week_High","52_Week_Low","1M_High","1M_Low" from crypto_target_prices'
crypto_target_prices_df = pd.read_sql_query(crypto_target_prices_df, pg_engine)


crypto_performance_df='select "FS_Ticker","2017toDate","YTD","MTD","1Y" from crypto_performance'
crypto_performance_df = pd.read_sql_query(crypto_performance_df, pg_engine)

dfs = [crypto_tech_indi_df, crypto_master_df, crypto_ma_ema_macd_df, crypto_ATR_df, crypto_target_prices_df, crypto_performance_df]

# Start with the first dataframe
merged_df = dfs[0]

# Iterate through the remaining dataframes and perform a left merge
for df in dfs[1:]:
    merged_df = merged_df.merge(df, on='FS_Ticker', how='left')



merged_df['Date'] = merged_df['Date'].dt.tz_localize(None)

merged_df_cols=list(merged_df.columns)
merged_df['id'] = range(1, len(merged_df)+1)
merged_df_cols.insert(0,'id')
merged_df=merged_df[merged_df_cols]


today_date = datetime.now().date()

# Add the 'created_at' and 'updated_at' columns with today's date
merged_df['created_at'] = today_date
merged_df['updated_at'] = today_date

with pg_engine.begin() as conn:
    conn.execute(text('TRUNCATE TABLE crypto_super_screener'))
merged_df.to_sql(name = 'crypto_super_screener', con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)

