# import os
# from dotenv import load_dotenv
# import Crypto_Daily_Top_Performers_Live
# import Noo_Crypto_dumping
# import us_market_index
# import Crypto_Super_Screener

# # PostgreSQL credentials
# pg_user = os.getenv('PG_USER')
# pg_password = os.getenv('PG_PASSWORD')
# pg_host = os.getenv('PG_HOST')
# pg_port = os.getenv('PG_PORT')
# pg_db_name = os.getenv('PG_DB_NAME')

# # SQL Server credentials
# sql_server_user = os.getenv('SQL_SERVER_USER')
# sql_server_password = os.getenv('SQL_SERVER_PASSWORD')
# sql_server_host = os.getenv('SQL_SERVER_HOST')
# sql_server_port = os.getenv('SQL_SERVER_PORT')
# sql_server_db_name = os.getenv('SQL_SERVER_DB_NAME')
# sql_server_driver = os.getenv('SQL_SERVER_DRIVER')

# def main():
#     # Load environment variables
#     load_dotenv()

#     # Run each script
#     print("Starting Crypto Daily Top Performers Live...")
#     Crypto_Daily_Top_Performers_Live.main()  # Ensure there's a main function in the script

#     print("Running Noo Crypto Dumping...")
#     Noo_Crypto_dumping.main()  # Ensure there's a main function in the script

#     print("Executing US Market Index...")
#     us_market_index.main()  # Ensure there's a main function in the script

#     print("Running Crypto Super Screener...")
#     Crypto_Super_Screener.main()  # Ensure there's a main function in the script

# if __name__ == "__main__":
#     main()


import requests
import pandas as pd
from datetime import datetime,timedelta
from sqlalchemy import create_engine, text
import os
os.chdir(r'I:\72PI Daily Data\Crypto Catalyst')
import repeated_functions
import numpy as np
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
top=10
Today_date=datetime.today().date()
Yesterday_date=Today_date-timedelta(1)
desired_timezone = 'Asia/Kolkata'

pg_db_name = 'CRYPTO DEVELOPMENT'
pg_user = 'postgres'
pg_password = 'GhcHyd_2025$'
pg_host = '192.168.1.68'
pg_port = 5432

#crypto_migration.py 
sql_server_db_name = '72PI'
sql_server_user = '72pi'
sql_server_password = '72Pi_2023$'
sql_server_host = '192.168.1.5'
sql_server_port = 1433
sql_server_driver = 'ODBC Driver 13 for SQL Server'

def latest_dates_calc(append_tables, pg_engine):
    # Dictionary to store latest dates
    latest_dates = {}
    
    # Loop through each table and retrieve the latest date from PostgreSQL
    for table in append_tables:
        if table == 'crypto_master':
            latest_date_query = pd.read_sql(f'SELECT MAX(downloaded_date) FROM {table}', pg_engine)
        else:
            latest_date_query = pd.read_sql(f"SELECT MAX(\"Date\") FROM {table}", pg_engine)
        
        latest_date = latest_date_query.iloc[0, 0]
        
        # Convert latest_date to a datetime object, handling None
        if latest_date is None:
            latest_date = pd.to_datetime('1900-01-01')
        else:
            latest_date = pd.to_datetime(latest_date)
        
        latest_dates[table] = latest_date
        
    return latest_dates

# Code for appending the data
def append_table_code(pg_engine, sql_server_engine, latest_dates, delta, append_tables):
    for table in append_tables:
        pg_table = table
        table_exists_query = pd.read_sql(f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table}'", sql_server_engine)
        
        if not table_exists_query.empty:
            # Assuming 'Date' is the column to compare; replace with actual column if different
            date_column = 'Date'
            
            latest_date = latest_dates[pg_table]
            # Run the query to get data where date is greater than latest_date
            sql_server_query = pd.read_sql(f"SELECT * FROM {table} WHERE {date_column} > '{latest_date}'", sql_server_engine)
            data = sql_server_query.drop(columns=['id'])
            
            latest_date = latest_date - timedelta(days=delta)
            sql_delete_query = text(f"DELETE FROM {pg_table} WHERE \"{date_column}\" > '{latest_date}'")
            with pg_engine.begin() as conn:
                conn.execute(sql_delete_query)
            
            max_id = pd.read_sql(f"SELECT MAX(id) FROM {pg_table}", pg_engine)
            max_id = max_id.iloc[0, 0]
            if max_id is None:
                max_id = 1
            data['id'] = range(max_id + 1, max_id + len(data) + 1)
            data.columns = data.columns.str.replace(' ', '_')
            data.to_sql(name=pg_table, con=pg_engine, chunksize=10, method='multi', if_exists='append', index=False)
            print(f"{table} -> table data inserted")
        else:
            print(f"Table '{table}' does not exist in the SQL Server database.")

# Truncate and insert tables code
def truncate_table_append(pg_engine, sql_server_engine, truncate_tables):
    for table in truncate_tables:
        pg_table = table
        
        data = pd.read_sql(f"SELECT * FROM {table}", sql_server_engine)
        
        with pg_engine.begin() as conn:
            conn.execute(text(f'TRUNCATE TABLE {pg_table}'))
        data.to_sql(name=pg_table, con=pg_engine, chunksize=10, method='multi', if_exists='append', index=False)

        print(f"{pg_table}  --> Truncated and inserted!!")

def ma_ema_macd_table_append(pg_engine, sql_server_engine, latest_dates, delta):
    ma_ema_macd_table = "crypto_ma_ema_macd"
    
    query_ema = 'SELECT * FROM Crypto_Exponential_Moving_Average ORDER BY FS_Ticker, Date'
    query_ma = 'SELECT * FROM Crypto_Moving_Average ORDER BY FS_Ticker, Date'
    query_macd = 'SELECT * FROM Crypto_Moving_Average_Convergence_Divergence ORDER BY FS_Ticker, Date'
    
    df_ema = pd.read_sql_query(query_ema, sql_server_engine)
    df_ma = pd.read_sql_query(query_ma, sql_server_engine)
    df_macd = pd.read_sql_query(query_macd, sql_server_engine)
    
    df_ema = df_ema[['Company', 'FS_Ticker', 'Date', 'Price', 'EMA9', 'EMA12', 'EMA', 'EMA26', 'EMA50', 'EMA200']]
    df_ma = df_ma[['Date', 'FS_Ticker', '9MA', '20MA', '26MA', '50MA', '100MA', '200MA']]
    df_macd = df_macd[['Date', 'FS_Ticker', 'MACD Line', 'Signal Line', 'MACD Histogram']]
    
    # Merging the DataFrames on FS_Ticker and Date
    merged_df = df_ema.merge(df_ma, on=['FS_Ticker', 'Date']).merge(df_macd, on=['FS_Ticker', 'Date'])
    
    ma_ema_macd_latest_date = pd.read_sql(f"SELECT MAX(\"Date\") FROM {ma_ema_macd_table}", pg_engine)
    ma_ema_macd_latest_date = ma_ema_macd_latest_date.iloc[0, 0]
    if ma_ema_macd_latest_date is None:
        ma_ema_macd_latest_date = pd.to_datetime('1900-01-01')
    
    ma_ema_macd_latest_date = ma_ema_macd_latest_date - timedelta(days=delta)
    ma_ema_macd_df = merged_df[merged_df["Date"] > ma_ema_macd_latest_date]
    
    ma_ema_macd_df.columns = ma_ema_macd_df.columns.str.replace(' ', '_')
    ma_ema_macd_df["created_at"] = datetime.now().date()
    ma_ema_macd_df["updated_at"] = datetime.now().date()
    ma_ema_macd_df.to_sql(name=ma_ema_macd_table, con=pg_engine, chunksize=10, method='multi', if_exists='append', index=False)

def main():
    delta = 0
    # Create connection strings
    pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_name}"
    sql_server_connection_string = f"mssql+pyodbc://{sql_server_user}:{sql_server_password}@{sql_server_host}:{sql_server_port}/{sql_server_db_name}?driver={sql_server_driver}"
    
    # Create SQLAlchemy engines
    pg_engine = create_engine(pg_connection_string, pool_pre_ping=True)
    print(f"Connected to PostgreSQL database '{pg_db_name}'")
    
    sql_server_engine = create_engine(sql_server_connection_string, pool_pre_ping=True)
    print(f"Connected to SQL Server database '{sql_server_db_name}'")
    
    # List of table names
    append_tables = [
        'crypto_average_true_range', 'crypto_daily_beta', 'crypto_prices_main',
        'crypto_volume_20_data', 'crypto_volume_data'
    ]
    
    truncate_tables = ['crypto_master', 'crypto_technical_indicators_daily', 'crypto_performance', 'crypto_target_prices']
    
    merge_tables = {
        "crypto_ma_ema_macd": ['crypto_exponential_moving_average', 
        'crypto_moving_average', 'crypto_moving_average_convergence_divergence']
    }

    print("----------Retrieving latest dates")
    latest_dates = latest_dates_calc(append_tables, pg_engine)
    
    print("----------Append tables insertion")
    append_table_code(pg_engine, sql_server_engine, latest_dates, delta, append_tables)
    
    print("-----------Truncate tables insertion")
    truncate_table_append(pg_engine, sql_server_engine, truncate_tables)

    print("-----------ma_ema_macd_table_append")
    ma_ema_macd_table_append(pg_engine, sql_server_engine, latest_dates, delta)
    
    pg_engine.dispose()
    sql_server_engine.dispose()
    print("Success!!!")

if __name__ == "__main__":
    main()


#Crypto_Daily_Top_Performers_Live

pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_name}"
pg_engine = create_engine(pg_connection_string, pool_pre_ping=True)


all_tickers_url='https://eodhistoricaldata.com/api/exchange-symbol-list/CC?api_token=612f4f7f3906a3.86934021&fmt=json'

resp = requests.get(all_tickers_url)

crypto_all_tickers= resp.json()
crypto_all_tickers = pd.DataFrame(crypto_all_tickers)
crypto_all_tickers['Date'] = datetime.today().strftime('%Y-%m-%d')

# data = pd.read_sql(f"SELECT * FROM crypto_all_tickers", pg_engine)

crypto_all_tickers=repeated_functions.adding_creat_update_dt(crypto_all_tickers)
with pg_engine.begin() as conn:
    conn.execute(text('TRUNCATE TABLE crypto_all_tickers'))
crypto_all_tickers.to_sql(name = "crypto_all_tickers", con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)

crypto_all_tickers.to_excel(r"I:\72PI Daily Data\Crypto Catalyst\output_file\All_tickers_data\crypto_all_tickers.xlsx",index=False)

# crypto_all_tickers=pd.read_excel(r"C:\Users\nookaraju.c\Desktop\72PI_CRYPTO\Crypto_All_tickers_Symbols.xlsx")


crypto_all_tickers['Tickers']=crypto_all_tickers['Code']+ '.CC'

crypto_all_tickers_list=crypto_all_tickers['Tickers'].to_list()

# crypto_all_tickers_list=crypto_all_tickers_list[:4]

# if 'BTC-USD.CC' in crypto_all_tickers_list:
#     crypto_all_tickers_list.remove('BTC-USD.CC')
    
crypto_all_tickers_string=','.join(crypto_all_tickers_list)

#Live data download
#--------------------------------------------------
#Check if data is already exists
live_download=False
crypto_live_max_date='select max("Downloaded_Date") from crypto_live_data'
crypto_live_max_date = pd.read_sql_query(crypto_live_max_date, pg_engine)
crypto_live_max_date=crypto_live_max_date.iloc[0,0]
crypto_live_max_date=crypto_live_max_date.date() if crypto_live_max_date is not None else crypto_live_max_date
if crypto_live_max_date is None or crypto_live_max_date!=Today_date:
    live_download=True

#--------------------------------------------------

all_data = []
def fetch_crypto_data(crypto_all_tickers_list, api_token='612f4f7f3906a3.86934021', chunk_size=15):
    base_url = 'https://eodhd.com/api/real-time/'
    # headers = {'Content-Type': 'application/json'}
    global all_data
    print("Downloading Live crypto data-------")
    tickers_list = crypto_all_tickers_list.copy()
    for i in range(0, len(tickers_list), chunk_size):
        tickers_chunk = ','.join(tickers_list[i+1:i + chunk_size])
        print(i)
        url = f'{base_url}{tickers_list[i]}?s={tickers_chunk}&api_token={api_token}&fmt=json'
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
        return pd.DataFrame()  # Return an empty DataFrame if no data was fetched



if live_download:
    # url = f'https://eodhd.com/api/real-time/BTC-USD.CC?s={crypto_all_tickers_string}&api_token=612f4f7f3906a3.86934021&fmt=json'
    # resp = requests.get(url)
    
    # live_data = resp.json()
    
    # Convert JSON data to DataFrame
    # live_crypto_data_df = pd.DataFrame(live_data)
    # crypto_all_tickers_list=crypto_all_tickers_list[0:100]
    live_crypto_data_df=fetch_crypto_data(crypto_all_tickers_list)

    live_crypto_data_df['timestamp'] = live_crypto_data_df['timestamp'].replace('NA', np.nan)
    
    if "change_p" in list(live_crypto_data_df.columns):
        live_crypto_data_df.rename(columns={
            "change_p":"ChangeP"
            },inplace=True)
    
    live_crypto_data_df['ChangeP'] = live_crypto_data_df['ChangeP'].replace('NA', 0)

    live_crypto_data_df = live_crypto_data_df.dropna(subset=['timestamp'])
    
    live_crypto_data_df['Date'] = pd.to_datetime(live_crypto_data_df['timestamp'], unit='s', utc=True).dt.tz_convert('Asia/Kolkata')    # Print the DataFrame to verify the changes
    live_crypto_data_df['Downloaded_Date'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    
    live_crypto_data_df['Date'] = live_crypto_data_df['Date'].dt.tz_localize(None)
    
    live_crypto_data_df.rename(columns={
        'code': 'Code',
        'timestamp': 'Timestamp',
        'gmtoffset': 'GmtOffset',
        'open': 'Open',
         'high':'High',
         'low':'Low',
         'close':'Close',
           'volume':'Volume',
           'previousClose':'PreviousClose', 
           'change':'Change',
           'change_p':'ChangeP',
           'Date':'Date',
           'Downloaded_Date':'Downloaded_Date'
    }, inplace=True)
    live_crypto_data_df.to_excel(r"I:\72PI Daily Data\Crypto Catalyst\output_file\All_tickers_data\live_crypto_data.xlsx",index=False)
    with pg_engine.begin() as conn:
        conn.execute(text('TRUNCATE TABLE crypto_live_data'))
    live_crypto_data_df = live_crypto_data_df.drop('Timestamp', axis=1)
    columns_to_check = ['Open', 'High', 'Low', 'Close', 'Volume', 'PreviousClose', 'Change', 'ChangeP']
    live_crypto_data_df[columns_to_check] = live_crypto_data_df[columns_to_check].replace('NA', np.nan)

    live_crypto_data_df = live_crypto_data_df.dropna()
    live_crypto_data_df=repeated_functions.adding_creat_update_dt(live_crypto_data_df)
    live_crypto_data_df.to_sql(name = "crypto_live_data", con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)
    
    
    

else:
    print("Live prices already there --Skipped Live prices downloading!!!!!!!")
    live_crypto_query='select * from crypto_live_data'
    live_crypto_data_df = pd.read_sql_query(live_crypto_query, pg_engine)
    live_crypto_data_df = live_crypto_data_df.drop('id', axis=1)
    live_crypto_data_df['Date'] = pd.to_datetime(live_crypto_data_df['Date'], utc=True)
    live_crypto_data_df['Date'] = live_crypto_data_df['Date'].dt.tz_convert(desired_timezone)
    live_crypto_data_df['Downloaded_Date'] = pd.to_datetime(live_crypto_data_df['Downloaded_Date'], utc=True)
    live_crypto_data_df['Downloaded_Date'] = live_crypto_data_df['Downloaded_Date'].dt.tz_convert(desired_timezone)
    live_crypto_data_df=repeated_functions.exclude_creat_update_dt(live_crypto_data_df)


# crypto_all_tickers_list.insert(0,"BTC-USD.CC")
#--------------------------------------------------
#Check if data is already exists
hist_download=False
crypto_hist_max_date='select max("Downloaded_Date") from crypto_historical_data'
crypto_hist_max_date = pd.read_sql_query(crypto_hist_max_date, pg_engine)
crypto_hist_max_date=crypto_hist_max_date.iloc[0,0]
crypto_hist_max_date=crypto_hist_max_date.date() if crypto_hist_max_date is not None else crypto_hist_max_date
if crypto_hist_max_date is None or crypto_hist_max_date!=Yesterday_date:
    hist_download=True

#--------------------------------------------------
if hist_download:
    print("-------Historical Prices downloading------------\n")
    hist_df_list=[]
    hist_issues_df_list=[]
    i=0
    for ticker in crypto_all_tickers_list:
        print(f'{i}-->{ticker}')
        i+=1
        try:
            hist_ticker_url= f'https://eodhistoricaldata.com/api/eod/{ticker}?api_token=612f4f7f3906a3.86934021&fmt=json'
            resp = requests.get(hist_ticker_url)
            hist_data = resp.json()
            df=pd.DataFrame(hist_data)
            df['Ticker']=ticker.replace('.CC','')
            df.sort_values('date',ascending=True,inplace=True)
            df=df[df['date']>='2017-01-01']
            df['date'] = pd.to_datetime(df['date'])
            df=df[df['date'].dt.date!=Today_date]
            
            hist_df_list.append(df)
            
        except:
            hist_issues_df_list.append(ticker)
            # result_df = pd.concat(hist_df_list, ignore_index=True)
            # result_df['Downloaded_Date'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            # result_df.to_excel(r"C:\Users\nookaraju.c\Desktop\72PI_CRYPTO\Crypto_historical_data_failed.xlsx",index=False)
    
    concat_df = pd.concat(hist_df_list, ignore_index=True)
    concat_df['Downloaded_Date'] = datetime.today().strftime('%Y-%m-%d')
    # concat_df.to_excel(r"C:\Users\nookaraju.c\Desktop\72PI_CRYPTO\Crypto_historical_data_Today.xlsx",index=False)
    concat_df.rename(columns={
        'date':'Date',
        'open':'Open',
        'high':'High',
        'low':'Low',
        'close':'Close',
        'adjusted_close':'Adjusted_Close',
        'volume':'Volume',
       'Ticker':'Ticker',
       'Downloaded_Date':'Downloaded_Date'
    }, inplace=True)
    concat_df=concat_df[['Date', 'Open', 'High', 'Low', 'Close', 'Adjusted_Close', 'Volume',
       'Ticker', 'Downloaded_Date']]
    
    
    concat_df=repeated_functions.adding_creat_update_dt(concat_df)

    with pg_engine.begin() as conn:
        conn.execute(text('TRUNCATE TABLE crypto_historical_data'))
    concat_df.to_sql(name = "crypto_historical_data", con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)
    print("Done with the Crypto Live prices download")
else:
    print("Historical prices already there --Historical Prices download skipped!!!!!!!!!")
    hist_crypto_query='select * from crypto_historical_data'
    concat_df = pd.read_sql_query(hist_crypto_query, pg_engine)
    concat_df = concat_df.drop('id', axis=1)
    concat_df['Date'] = pd.to_datetime(concat_df['Date'], utc=True)
    concat_df['Date'] = concat_df['Date'].dt.tz_convert(desired_timezone)
    concat_df['Downloaded_Date'] = pd.to_datetime(concat_df['Downloaded_Date'], utc=True)
    concat_df['Downloaded_Date'] = concat_df['Downloaded_Date'].dt.tz_convert(desired_timezone)
    concat_df=repeated_functions.exclude_creat_update_dt(concat_df)



concat_df['Date'] = concat_df['Date'].dt.date
concat_df=concat_df[concat_df['Date']<=Yesterday_date]

concat_df['Date'] = pd.to_datetime(concat_df['Date'])

#Checking 
result_index = concat_df.groupby('Ticker')['Date'].apply(lambda x: Yesterday_date in x.dt.date.values)

hist_filtered_df = concat_df[concat_df['Ticker'].isin(result_index[result_index].index)]


live_crypto_data_df['Code'] = live_crypto_data_df['Code'].str.replace('.CC', '', regex=False)
live_filterd_df=live_crypto_data_df[live_crypto_data_df['Code'].isin(result_index[result_index].index)]


hist_filtered_df=hist_filtered_df[['Ticker','Date', 'Adjusted_Close', 'Volume']]
hist_filtered_df.rename(columns={
    'Adjusted_Close': 'Price'
}, inplace=True)

live_filterd_df=live_filterd_df[['Code','Downloaded_Date','Close','Volume']]
live_filterd_df.rename(columns={
    'Code': 'Ticker',
    'Downloaded_Date': 'Date',
    'Close': 'Price',
}, inplace=True)

final_df = pd.concat([hist_filtered_df, live_filterd_df], ignore_index=True)


final_df['Date'] = pd.to_datetime(final_df['Date'], utc=True)

filter_date=Today_date - timedelta(days=100)
final_df['Date']=final_df['Date'].dt.date

final_df=final_df[final_df['Date']>=filter_date]
final_df = final_df.sort_values(by=['Ticker', 'Date'], ascending=[True, True])

final_df['Volume_diff'] = final_df.groupby('Ticker')['Volume'].diff()

volume_df = final_df.groupby('Ticker').tail(1)
volume_df_sorted = volume_df.sort_values(by='Volume_diff', ascending=False)

top_10_volume_df = volume_df_sorted.head(top)


final_df = final_df.sort_values(by=['Ticker', 'Date'], ascending=[True, True])

final_df['50_day_MA'] = final_df.groupby('Ticker')['Price'].rolling(window=50).mean().reset_index(level=0, drop=True)

final_df = final_df.reset_index(drop=True)

final_df['price_ma_diff']=final_df['Price']-final_df['50_day_MA']
final_df['price_gt_ma'] = final_df.apply(lambda row: 1 if row['Price'] > row['50_day_MA'] else 0, axis=1)
final_df['prev_price_gt_ma'] = final_df.groupby('Ticker')['price_gt_ma'].shift(1)

final_df = final_df.sort_values(by=['Ticker', 'Date'], ascending=[True, True])


ma_50_df = final_df.groupby('Ticker').tail(1)
#ma_50_df.loc[ma_50_df['Ticker'].isin(['BTC-USD', '0xBTC-USD']), 'prev_price_gt_ma'] = 0

filtered_ma_50_df = ma_50_df[(ma_50_df['price_gt_ma'] == 1) & (ma_50_df['prev_price_gt_ma'] == 0)]

ma_50_df_sorted = filtered_ma_50_df.sort_values(by='price_ma_diff', ascending=False)

top_10_ma_50_df = ma_50_df_sorted.head(top)


final_df = final_df.sort_values(by=['Ticker', 'Date'], ascending=[True, True])
Latet_date_df = final_df.groupby('Ticker').tail(1)


original_file = r"I:\72PI Daily Data\Crypto Catalyst\output_file\All_tickers_historical_data\Volume_50MA_Daily_Summary_2024-10-16.xlsx"

# Generate today's date in YYYY-MM-DD format
today_date = datetime.now().strftime('%Y-%m-%d')

# Construct the new filename
directory, original_filename = os.path.split(original_file)
filename, file_extension = os.path.splitext(original_filename)
new_filename = f"Volume_50MA_Daily_Summary_{today_date}{file_extension}"
new_file_path = os.path.join(directory, new_filename)

# final_df.to_excel(r"C:\Users\nookaraju.c\Desktop\72PI_CRYPTO\final.xlsx",index=False)
with pd.ExcelWriter(new_file_path, engine='xlsxwriter') as writer:

    final_df.to_excel(writer, sheet_name='Historical_data', index=False)
    Latet_date_df.to_excel(writer, sheet_name='Today_Summary', index=False)
    top_10_volume_df.to_excel(writer, sheet_name='Volume_Top_10', index=False)
    top_10_ma_50_df.to_excel(writer, sheet_name='50MA_Crossed_Top_10', index=False)


print("Data processing complete!")






#us_market_index
import pyodbc

sql_server_connection_string = f'DRIVER={sql_server_driver};SERVER={sql_server_host},{sql_server_port};DATABASE={sql_server_db_name};UID={sql_server_user};PWD={sql_server_password}'
sql_server_conn = pyodbc.connect(sql_server_connection_string)


query = 'SELECT * FROM US_Market_Index'
us_market_data_df = pd.read_sql(query, sql_server_conn)

# Close SQL Server connection
sql_server_conn.close()

# Add created_at and updated_at columns with the current timestamp
now = datetime.now()
us_market_data_df['created_at'] = now
us_market_data_df['updated_at'] = now

# Connect to Crypto PostgreSQL database using SQLAlchemy
pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_name}"
pg_engine = create_engine(pg_connection_string, pool_pre_ping=True)

with pg_engine.begin() as connection:
    connection.execute(text("TRUNCATE TABLE us_market_index"))
    
# Append data into the us_market_index table in PostgreSQL
us_market_data_df.to_sql('us_market_index', con=pg_engine, if_exists='append', index=False, method='multi', chunksize=1000)

# Close PostgreSQL connection
pg_engine.dispose()

print("Data migration from 72PI to Crypto is completed.")

# Email notification function
def sendMail(SUBJECT, BODY, TO, FROM):
    MESSAGE = MIMEMultipart()
    MESSAGE['subject'] = SUBJECT
    MESSAGE['To'] = ', '.join(TO)
    MESSAGE['From'] = FROM
    HTML_BODY = MIMEText(BODY, 'html')
    MESSAGE.attach(HTML_BODY)
    server = smtplib.SMTP('smtp.gmail.com:587')
    password = "Afsadmin2023$$$$$$$"
    server.starttls()
    server.login(FROM, password)
    for mailID in TO:
        server.sendmail(FROM, mailID, MESSAGE.as_string())
    server.quit()

def mailOut(mail_bit, BODY):
    TO = ['vasanthi.g@goldenhillsindia.com', 'charan.d@goldenhillsindia.com', 'ranjith.a@goldenhillsindia.com']
    FROM = 'ghcit@goldenhillsindia.com'
    if mail_bit == 0:
        SUBJECT = 'Crypto_Catalyst: Dump Failed!'
    else:
        SUBJECT = 'Crypto_Catalyst: Data Dump is completed!'
    sendMail(SUBJECT, BODY, TO, FROM)

# Send success email
BODY = "<p>The data migration from 72PI to Crypto has been successfully completed.</p>"
mailOut(1, BODY)
#Crypto_Super_Screener




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

