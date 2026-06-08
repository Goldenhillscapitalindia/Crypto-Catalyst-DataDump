# -*- coding: utf-8 -*-
"""
Created on Tue Jul 23 18:04:07 2024

@author: nookaraju.c
"""

import requests
import pandas as pd
from datetime import datetime,timedelta
from sqlalchemy import create_engine, text
import os
import numpy as np
import sys
sys.path.insert(0, r'I:\72PI Daily Data\Crypto Catalyst')
import repeated_functions
# # from . import repeated_functionsnctions
# # # 
# import numpy as np
# top=10
# Today_date=datetime.today().date()
# Yesterday_date=Today_date-timedelta(1)
# desired_timezone = 'Asia/Kolkata'

# pg_db_name = 'Testing'
# pg_user = 'postgres'
# pg_password = 'GhcHyd_2024$'
# pg_host = '192.168.1.57'
# pg_port = 5432


# pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_name}"
# pg_engine = create_engine(pg_connection_string, pool_pre_ping=True)


# all_tickers_url='https://eodhistoricaldata.com/api/exchange-symbol-list/CC?api_token=612f4f7f3906a3.86934021&fmt=json'

# resp = requests.get(all_tickers_url)

# crypto_all_tickers= resp.json()
# crypto_all_tickers = pd.DataFrame(crypto_all_tickers)
# crypto_all_tickers['Date'] = datetime.today().strftime('%Y-%m-%d')

# # data = pd.read_sql(f"SELECT * FROM crypto_all_tickers", pg_engine)

# crypto_all_tickers=repeated_functions.adding_creat_update_dt(crypto_all_tickers)
# pg_engine.execute(text(f'truncate table crypto_all_tickers').execution_options(autocommit=True))
# crypto_all_tickers.to_sql(name = "crypto_all_tickers", con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)

# crypto_all_tickers.to_excel(r'output_file\All_tickers_data\crypto_all_tickers.xlsx',index=False)

# crypto_all_tickers['Tickers']=crypto_all_tickers['Code']+ '.CC'

# crypto_all_tickers_list=crypto_all_tickers['Tickers'].to_list()

# # crypto_all_tickers_list=crypto_all_tickers_list[:4]

# # if 'BTC-USD.CC' in crypto_all_tickers_list:
# #     crypto_all_tickers_list.remove('BTC-USD.CC')
    
# crypto_all_tickers_string=','.join(crypto_all_tickers_list)

# #Live data download
# #--------------------------------------------------
# #Check if data is already exists
# live_download=False
# crypto_live_max_date='select max("Downloaded_Date") from crypto_live_data'
# crypto_live_max_date = pd.read_sql_query(crypto_live_max_date, pg_engine)
# crypto_live_max_date=crypto_live_max_date.iloc[0,0]
# crypto_live_max_date=crypto_live_max_date.date() if crypto_live_max_date is not None else crypto_live_max_date
# if crypto_live_max_date is None or crypto_live_max_date!=Today_date:
#     live_download=True

# #--------------------------------------------------

# all_data = []
# def fetch_crypto_data(crypto_all_tickers_list, api_token='612f4f7f3906a3.86934021', chunk_size=15):
#     base_url = 'https://eodhd.com/api/real-time/'
#     # headers = {'Content-Type': 'application/json'}
#     global all_data
#     print("Downloading Live crypto data-------")
#     tickers_list = crypto_all_tickers_list.copy()
#     for i in range(0, len(tickers_list), chunk_size):
#         tickers_chunk = ','.join(tickers_list[i+1:i + chunk_size])
#         print(i)
#         url = f'{base_url}{tickers_list[i]}?s={tickers_chunk}&api_token={api_token}&fmt=json'
#         resp = requests.get(url)
        
#         if resp.status_code == 200:
#             try:
#                 data = resp.json()
#                 if isinstance(data, dict):
#                     data = [data]
#                 all_data.extend(data)
#             except requests.exceptions.JSONDecodeError as e:
#                 print(f"Error decoding JSON for chunk {i // chunk_size}: {e}")
#                 print("Response content:", resp.text)
#         else:
#             print(f"Failed to fetch data for chunk {i // chunk_size}. Status code:", resp.status_code)
#             print("Response content:", resp.text)

#     if all_data:
#         return pd.DataFrame(all_data)
#     else:
#         return pd.DataFrame()  # Return an empty DataFrame if no data was fetched



# if live_download:
#     # url = f'https://eodhd.com/api/real-time/BTC-USD.CC?s={crypto_all_tickers_string}&api_token=612f4f7f3906a3.86934021&fmt=json'
#     # resp = requests.get(url)
    
#     # live_data = resp.json()
    
#     # Convert JSON data to DataFrame
#     # live_crypto_data_df = pd.DataFrame(live_data)
#     # crypto_all_tickers_list=crypto_all_tickers_list[0:100]
#     live_crypto_data_df=fetch_crypto_data(crypto_all_tickers_list)

#     live_crypto_data_df['timestamp'] = live_crypto_data_df['timestamp'].replace('NA', np.nan)
    
#     if "change_p" in list(live_crypto_data_df.columns):
#         live_crypto_data_df.rename(columns={
#             "change_p":"ChangeP"
#             },inplace=True)
    
#     live_crypto_data_df['ChangeP'] = live_crypto_data_df['ChangeP'].replace('NA', 0)

#     live_crypto_data_df = live_crypto_data_df.dropna(subset=['timestamp'])
    
#     live_crypto_data_df['Date'] = pd.to_datetime(live_crypto_data_df['timestamp'], unit='s', utc=True).dt.tz_convert('Asia/Kolkata')    # Print the DataFrame to verify the changes
#     live_crypto_data_df['Downloaded_Date'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    
#     live_crypto_data_df['Date'] = live_crypto_data_df['Date'].dt.tz_localize(None)
    
#     live_crypto_data_df.rename(columns={
#         'code': 'Code',
#         'timestamp': 'Timestamp',
#         'gmtoffset': 'GmtOffset',
#         'open': 'Open',
#          'high':'High',
#          'low':'Low',
#          'close':'Close',
#            'volume':'Volume',
#            'previousClose':'PreviousClose', 
#            'change':'Change',
#            'change_p':'ChangeP',
#            'Date':'Date',
#            'Downloaded_Date':'Downloaded_Date'
#     }, inplace=True)
#     live_crypto_data_df.to_excel(r"output_file\All_tickers_data\live_crypto_data.xlsx",index=False)
#     pg_engine.execute(text(f'truncate table crypto_live_data').execution_options(autocommit=True))
#     live_crypto_data_df = live_crypto_data_df.drop('Timestamp', axis=1)
#     columns_to_check = ['Open', 'High', 'Low', 'Close', 'Volume', 'PreviousClose', 'Change', 'ChangeP']
#     live_crypto_data_df[columns_to_check] = live_crypto_data_df[columns_to_check].replace('NA', np.nan)

#     live_crypto_data_df = live_crypto_data_df.dropna()
#     live_crypto_data_df=repeated_functions.adding_creat_update_dt(live_crypto_data_df)
#     live_crypto_data_df.to_sql(name = "crypto_live_data", con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)
    
    
    

# else:
#     print("Live prices already there --Skipped Live prices downloading!!!!!!!")
#     live_crypto_query='select * from crypto_live_data'
#     live_crypto_data_df = pd.read_sql_query(live_crypto_query, pg_engine)
#     live_crypto_data_df = live_crypto_data_df.drop('id', axis=1)
#     live_crypto_data_df['Date'] = pd.to_datetime(live_crypto_data_df['Date'], utc=True)
#     live_crypto_data_df['Date'] = live_crypto_data_df['Date'].dt.tz_convert(desired_timezone)
#     live_crypto_data_df['Downloaded_Date'] = pd.to_datetime(live_crypto_data_df['Downloaded_Date'], utc=True)
#     live_crypto_data_df['Downloaded_Date'] = live_crypto_data_df['Downloaded_Date'].dt.tz_convert(desired_timezone)
#     live_crypto_data_df=repeated_functions.exclude_creat_update_dt(live_crypto_data_df)


# # crypto_all_tickers_list.insert(0,"BTC-USD.CC")
# #--------------------------------------------------
# #Check if data is already exists
# hist_download=False
# crypto_hist_max_date='select max("Downloaded_Date") from crypto_historical_data'
# crypto_hist_max_date = pd.read_sql_query(crypto_hist_max_date, pg_engine)
# crypto_hist_max_date=crypto_hist_max_date.iloc[0,0]
# crypto_hist_max_date=crypto_hist_max_date.date() if crypto_hist_max_date is not None else crypto_hist_max_date
# if crypto_hist_max_date is None or crypto_hist_max_date!=Yesterday_date:
#     hist_download=True

# #--------------------------------------------------
# if hist_download:
#     print("-------Historical Prices downloading------------\n")
#     hist_df_list=[]
#     hist_issues_df_list=[]
#     i=0
#     for ticker in crypto_all_tickers_list:
#         print(f'{i}-->{ticker}')
#         i+=1
#         try:
#             hist_ticker_url= f'https://eodhistoricaldata.com/api/eod/{ticker}?api_token=612f4f7f3906a3.86934021&fmt=json'
#             resp = requests.get(hist_ticker_url)
#             hist_data = resp.json()
#             df=pd.DataFrame(hist_data)
#             df['Ticker']=ticker.replace('.CC','')
#             df.sort_values('date',ascending=True,inplace=True)
#             df=df[df['date']>='2017-01-01']
#             df['date'] = pd.to_datetime(df['date'])
#             df=df[df['date'].dt.date!=Today_date]
            
#             hist_df_list.append(df)
            
#         except:
#             hist_issues_df_list.append(ticker)
#             # result_df = pd.concat(hist_df_list, ignore_index=True)
#             # result_df['Downloaded_Date'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
#             # result_df.to_excel(r"C:\Users\nookaraju.c\Desktop\72PI_CRYPTO\Crypto_historical_data_failed.xlsx",index=False)
    
#     concat_df = pd.concat(hist_df_list, ignore_index=True)
#     concat_df['Downloaded_Date'] = datetime.today().strftime('%Y-%m-%d')
#     # concat_df.to_excel(r"C:\Users\nookaraju.c\Desktop\72PI_CRYPTO\Crypto_historical_data_Today.xlsx",index=False)
#     concat_df.rename(columns={
#         'date':'Date',
#         'open':'Open',
#         'high':'High',
#         'low':'Low',
#         'close':'Close',
#         'adjusted_close':'Adjusted_Close',
#         'volume':'Volume',
#        'Ticker':'Ticker',
#        'Downloaded_Date':'Downloaded_Date'
#     }, inplace=True)
#     concat_df=concat_df[['Date', 'Open', 'High', 'Low', 'Close', 'Adjusted_Close', 'Volume',
#        'Ticker', 'Downloaded_Date']]
    
    
#     concat_df=repeated_functions.adding_creat_update_dt(concat_df)

#     pg_engine.execute(text(f'truncate table crypto_historical_data').execution_options(autocommit=True))
#     concat_df.to_sql(name = "crypto_historical_data", con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)
#     print("Done with the Crypto Live prices download")
# else:
#     print("Historical prices already there --Historical Prices download skipped!!!!!!!!!")
#     hist_crypto_query='select * from crypto_historical_data'
#     concat_df = pd.read_sql_query(hist_crypto_query, pg_engine)
#     concat_df = concat_df.drop('id', axis=1)
#     concat_df['Date'] = pd.to_datetime(concat_df['Date'], utc=True)
#     concat_df['Date'] = concat_df['Date'].dt.tz_convert(desired_timezone)
#     concat_df['Downloaded_Date'] = pd.to_datetime(concat_df['Downloaded_Date'], utc=True)
#     concat_df['Downloaded_Date'] = concat_df['Downloaded_Date'].dt.tz_convert(desired_timezone)
#     concat_df=repeated_functions.exclude_creat_update_dt(concat_df)



# concat_df['Date'] = concat_df['Date'].dt.date
# concat_df=concat_df[concat_df['Date']<=Yesterday_date]

# concat_df['Date'] = pd.to_datetime(concat_df['Date'])

# #Checking 
# result_index = concat_df.groupby('Ticker')['Date'].apply(lambda x: Yesterday_date in x.dt.date.values)

# hist_filtered_df = concat_df[concat_df['Ticker'].isin(result_index[result_index].index)]


# live_crypto_data_df['Code'] = live_crypto_data_df['Code'].str.replace('.CC', '', regex=False)
# live_filterd_df=live_crypto_data_df[live_crypto_data_df['Code'].isin(result_index[result_index].index)]


# hist_filtered_df=hist_filtered_df[['Ticker','Date', 'Adjusted_Close', 'Volume']]
# hist_filtered_df.rename(columns={
#     'Adjusted_Close': 'Price'
# }, inplace=True)

# live_filterd_df=live_filterd_df[['Code','Downloaded_Date','Close','Volume']]
# live_filterd_df.rename(columns={
#     'Code': 'Ticker',
#     'Downloaded_Date': 'Date',
#     'Close': 'Price',
# }, inplace=True)

# final_df = pd.concat([hist_filtered_df, live_filterd_df], ignore_index=True)


# final_df['Date'] = pd.to_datetime(final_df['Date'], utc=True)

# filter_date=Today_date - timedelta(days=100)
# final_df['Date']=final_df['Date'].dt.date

# final_df=final_df[final_df['Date']>=filter_date]
# final_df = final_df.sort_values(by=['Ticker', 'Date'], ascending=[True, True])

# final_df['Volume_diff'] = final_df.groupby('Ticker')['Volume'].diff()

# volume_df = final_df.groupby('Ticker').tail(1)
# volume_df_sorted = volume_df.sort_values(by='Volume_diff', ascending=False)

# top_10_volume_df = volume_df_sorted.head(top)


# final_df = final_df.sort_values(by=['Ticker', 'Date'], ascending=[True, True])

# final_df['50_day_MA'] = final_df.groupby('Ticker')['Price'].rolling(window=50).mean().reset_index(level=0, drop=True)

# final_df = final_df.reset_index(drop=True)

# final_df['price_ma_diff']=final_df['Price']-final_df['50_day_MA']
# final_df['price_gt_ma'] = final_df.apply(lambda row: 1 if row['Price'] > row['50_day_MA'] else 0, axis=1)
# final_df['prev_price_gt_ma'] = final_df.groupby('Ticker')['price_gt_ma'].shift(1)

# final_df = final_df.sort_values(by=['Ticker', 'Date'], ascending=[True, True])


# ma_50_df = final_df.groupby('Ticker').tail(1)
# #ma_50_df.loc[ma_50_df['Ticker'].isin(['BTC-USD', '0xBTC-USD']), 'prev_price_gt_ma'] = 0

# filtered_ma_50_df = ma_50_df[(ma_50_df['price_gt_ma'] == 1) & (ma_50_df['prev_price_gt_ma'] == 0)]

# ma_50_df_sorted = filtered_ma_50_df.sort_values(by='price_ma_diff', ascending=False)

# top_10_ma_50_df = ma_50_df_sorted.head(top)


# final_df = final_df.sort_values(by=['Ticker', 'Date'], ascending=[True, True])
# Latet_date_df = final_df.groupby('Ticker').tail(1)


# original_file = r'output_file\All_tickers_historical_data\crypto_all_tickers.xlsx'

# # Generate today's date in YYYY-MM-DD format
# today_date = datetime.now().strftime('%Y-%m-%d')

# # Construct the new filename
# directory, original_filename = os.path.split(original_file)
# filename, file_extension = os.path.splitext(original_filename)
# new_filename = f"Volume_50MA_Daily_Summary_{today_date}{file_extension}"
# new_file_path = os.path.join(directory, new_filename)

# # final_df.to_excel(r"C:\Users\nookaraju.c\Desktop\72PI_CRYPTO\final.xlsx",index=False)
# with pd.ExcelWriter(new_file_path, engine='xlsxwriter') as writer:

#     final_df.to_excel(writer, sheet_name='Historical_data', index=False)
#     Latet_date_df.to_excel(writer, sheet_name='Today_Summary', index=False)
#     top_10_volume_df.to_excel(writer, sheet_name='Volume_Top_10', index=False)
#     top_10_ma_50_df.to_excel(writer, sheet_name='50MA_Crossed_Top_10', index=False)



# def truncate_and_insert(pg_engine, df, table_name):
#     # Truncate the table
#     pg_engine.execute(text(f'TRUNCATE TABLE {table_name}').execution_options(autocommit=True))
    
#     # Insert the DataFrame into the table
#     df.to_sql(name=table_name, con=pg_engine, chunksize=10, method='multi', if_exists='append', index=False)
    
#     print(f"{table_name} --> Truncated and inserted!!")

# # Call the function to truncate and insert final_df into the crypto_all_ticker_historical_data table
# truncate_and_insert(pg_engine, final_df, 'crypto_all_ticker_historical_data')


def main(pg_user, pg_password, pg_host, pg_port, pg_db_name):
    os.chdir(r'I:\72PI Daily Data\Crypto Catalyst')
    
    top = 10
    Today_date = datetime.today().date()
    Yesterday_date = Today_date - timedelta(1)
    desired_timezone = 'Asia/Kolkata'

    pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_name}"
    pg_engine = create_engine(pg_connection_string, pool_pre_ping=True)

    all_tickers_url = 'https://eodhistoricaldata.com/api/exchange-symbol-list/CC?api_token=612f4f7f3906a3.86934021&fmt=json'
    resp = requests.get(all_tickers_url)

    crypto_all_tickers = resp.json()
    crypto_all_tickers = pd.DataFrame(crypto_all_tickers)
    crypto_all_tickers['Date'] = datetime.today().strftime('%Y-%m-%d')

    crypto_all_tickers = repeated_functions.adding_creat_update_dt(crypto_all_tickers)
    with pg_engine.begin() as conn:
        conn.execute(text('TRUNCATE TABLE crypto_all_tickers'))
    crypto_all_tickers.to_sql(name="crypto_all_tickers", con=pg_engine, chunksize=10, method='multi', if_exists='append', index=False)

    crypto_all_tickers.to_excel(r"output_file\All_tickers_data\crypto_all_tickers.xlsx", index=False)
    crypto_all_tickers['Tickers'] = crypto_all_tickers['Code'] + '.CC'
    crypto_all_tickers_list = crypto_all_tickers['Tickers'].to_list()
    
    # Live data download
    live_download = False
    crypto_live_max_date = 'select max("Downloaded_Date") from crypto_live_data'
    crypto_live_max_date = pd.read_sql_query(crypto_live_max_date, pg_engine)
    crypto_live_max_date = crypto_live_max_date.iloc[0, 0]
    crypto_live_max_date = crypto_live_max_date.date() if crypto_live_max_date is not None else crypto_live_max_date
    
    if crypto_live_max_date is None or crypto_live_max_date != Today_date:
        live_download = True

    all_data = []
    def fetch_crypto_data(crypto_all_tickers_list, api_token='612f4f7f3906a3.86934021', chunk_size=15):
        global all_data
        print("Downloading Live crypto data-------")
        tickers_list = crypto_all_tickers_list.copy()
        for i in range(0, len(tickers_list), chunk_size):
            tickers_chunk = ','.join(tickers_list[i+1:i + chunk_size])
            url = f'https://eodhd.com/api/real-time/{tickers_list[i]}?s={tickers_chunk}&api_token={api_token}&fmt=json'
            resp = requests.get(url)

            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, dict):
                        data = [data]
                    all_data.extend(data)
                except requests.exceptions.JSONDecodeError as e:
                    print(f"Error decoding JSON for chunk {i // chunk_size}: {e}")
                    print("Response content:", resp.text)
            else:
                print(f"Failed to fetch data for chunk {i // chunk_size}. Status code:", resp.status_code)
                print("Response content:", resp.text)

        if all_data:
            return pd.DataFrame(all_data)
        else:
            return pd.DataFrame()

    if live_download:
        live_crypto_data_df = fetch_crypto_data(crypto_all_tickers_list)
        live_crypto_data_df['timestamp'] = live_crypto_data_df['timestamp'].replace('NA', np.nan)

        if "change_p" in list(live_crypto_data_df.columns):
            live_crypto_data_df.rename(columns={"change_p": "ChangeP"}, inplace=True)

        live_crypto_data_df['ChangeP'] = live_crypto_data_df['ChangeP'].replace('NA', 0)
        live_crypto_data_df = live_crypto_data_df.dropna(subset=['timestamp'])
        live_crypto_data_df['Date'] = pd.to_datetime(live_crypto_data_df['timestamp'], unit='s', utc=True).dt.tz_convert('Asia/Kolkata')
        live_crypto_data_df['Downloaded_Date'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        live_crypto_data_df['Date'] = live_crypto_data_df['Date'].dt.tz_localize(None)
        
        live_crypto_data_df.rename(columns={
            'code': 'Code',
            'timestamp': 'Timestamp',
            'gmtoffset': 'GmtOffset',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume',
            'previousClose': 'PreviousClose',
            'change': 'Change',
            'change_p': 'ChangeP',
            'Date': 'Date',
            'Downloaded_Date': 'Downloaded_Date'
        }, inplace=True)
        
        live_crypto_data_df.to_excel(r"output_file\All_tickers_data\live_crypto_data.xlsx", index=False)
        with pg_engine.begin() as conn:
            conn.execute(text('TRUNCATE TABLE crypto_live_data'))
        live_crypto_data_df = live_crypto_data_df.drop('Timestamp', axis=1)
        columns_to_check = ['Open', 'High', 'Low', 'Close', 'Volume', 'PreviousClose', 'Change', 'ChangeP']
        live_crypto_data_df[columns_to_check] = live_crypto_data_df[columns_to_check].replace('NA', np.nan)
        live_crypto_data_df = live_crypto_data_df.dropna()
        live_crypto_data_df = repeated_functions.adding_creat_update_dt(live_crypto_data_df)
        live_crypto_data_df.to_sql(name="crypto_live_data", con=pg_engine, chunksize=10, method='multi', if_exists='append', index=False)

    else:
        print("Live prices already there --Skipped Live prices downloading!!!!!!!")
        live_crypto_query = 'select * from crypto_live_data'
        live_crypto_data_df = pd.read_sql_query(live_crypto_query, pg_engine)
        live_crypto_data_df = live_crypto_data_df.drop('id', axis=1)
        live_crypto_data_df['Date'] = pd.to_datetime(live_crypto_data_df['Date'], utc=True)
        live_crypto_data_df['Date'] = live_crypto_data_df['Date'].dt.tz_convert(desired_timezone)
        live_crypto_data_df['Downloaded_Date'] = pd.to_datetime(live_crypto_data_df['Downloaded_Date'], utc=True)
        live_crypto_data_df['Downloaded_Date'] = live_crypto_data_df['Downloaded_Date'].dt.tz_convert(desired_timezone)
        live_crypto_data_df = repeated_functions.exclude_creat_update_dt(live_crypto_data_df)

    # Historical data download
    hist_download = False
    crypto_hist_max_date = 'select max("Downloaded_Date") from crypto_historical_data'
    crypto_hist_max_date = pd.read_sql_query(crypto_hist_max_date, pg_engine)
    crypto_hist_max_date = crypto_hist_max_date.iloc[0, 0]
    crypto_hist_max_date = crypto_hist_max_date.date() if crypto_hist_max_date is not None else crypto_hist_max_date
    if crypto_hist_max_date is None or crypto_hist_max_date != Yesterday_date:
        hist_download = True

    if hist_download:
        print("-------Historical Prices downloading------------\n")
        hist_df_list = []
        hist_issues_df_list = []
        i = 0
        for ticker in crypto_all_tickers_list:
            print(f'{i}-->{ticker}')
            i += 1
            try:
                hist_ticker_url = f'https://eodhistoricaldata.com/api/eod/{ticker}?api_token=612f4f7f3906a3.86934021&fmt=json'
                resp = requests.get(hist_ticker_url)
                hist_data = resp.json()
                df = pd.DataFrame(hist_data)
                df['Ticker'] = ticker.replace('.CC', '')
                df.sort_values('date', ascending=True, inplace=True)
                df = df[df['date'] >= '2017-01-01']
                df['date'] = pd.to_datetime(df['date'])
                df = df[df['date'].dt.date != Today_date]
                hist_df_list.append(df)

            except:
                hist_issues_df_list.append(ticker)

        concat_df = pd.concat(hist_df_list, ignore_index=True)
        concat_df['Downloaded_Date'] = datetime.today().strftime('%Y-%m-%d')
        concat_df.rename(columns={
            'date': 'Date',
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'adjusted_close': 'Adjusted_Close',
            'volume': 'Volume',
            'Ticker': 'Ticker',
            'Downloaded_Date': 'Downloaded_Date'
        }, inplace=True)
        concat_df = concat_df[['Date', 'Open', 'High', 'Low', 'Close', 'Adjusted_Close', 'Volume', 'Ticker', 'Downloaded_Date']]
        concat_df = repeated_functions.adding_creat_update_dt(concat_df)

        with pg_engine.begin() as conn:
            conn.execute(text('TRUNCATE TABLE crypto_historical_data'))
        concat_df.to_sql(name='crypto_historical_data', con=pg_engine, chunksize=10, method='multi', if_exists='append', index=False)

        print("Downloading finished!!!\n")
        if hist_issues_df_list:
            print("Issues with following tickers:")
            print(hist_issues_df_list)

    else:
        print("Historical prices already there --Skipped historical prices downloading!!!!!!!")
        historical_query = 'select * from crypto_historical_data'
        historical_data_df = pd.read_sql_query(historical_query, pg_engine)
        historical_data_df = historical_data_df.drop('id', axis=1)
        historical_data_df['Date'] = pd.to_datetime(historical_data_df['Date'], utc=True)
        historical_data_df['Downloaded_Date'] = pd.to_datetime(historical_data_df['Downloaded_Date'], utc=True)

        historical_data_df['Date'] = historical_data_df['Date'].dt.tz_convert(desired_timezone)
        historical_data_df['Downloaded_Date'] = historical_data_df['Downloaded_Date'].dt.tz_convert(desired_timezone)
        historical_data_df = repeated_functions.exclude_creat_update_dt(historical_data_df)

if __name__ == "__main__":
    # Retrieve PostgreSQL connection parameters from environment variables
    pg_user = os.getenv('PG_USER')
    pg_password = os.getenv('PG_PASSWORD')
    pg_host = os.getenv('PG_HOST')
    pg_port = os.getenv('PG_PORT')
    pg_db_name = os.getenv('PG_DB_NAME')

    main(pg_user, pg_password, pg_host, pg_port, pg_db_name)
