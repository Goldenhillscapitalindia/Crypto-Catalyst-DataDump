from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
import pandas as pd


# Database credentials for PostgreSQL
pg_db_name = 'CRYPTO DEVELOPMENT'
pg_user = 'postgres'
pg_password = 'GhcHyd_2025$'
pg_host = '192.168.1.68'
pg_port = 5432

# SQL Server credentials
sql_server_db_name = '72PI'
sql_server_user = '72pi'
sql_server_password = '72Pi_2023$'
sql_server_host = '192.168.1.5'
sql_server_port = 1433
sql_server_driver = 'ODBC Driver 13 for SQL Server'




def latest_dates_calc():

    # Dictionary to store latest dates
    latest_dates = {}
    
    # Loop through each table and retrieve the latest date from PostgreSQL
    for table in append_tables:
    
        table=table
        # table="test_"+table
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

#Code for appending the data
def append_table_code(pg_engine,sql_server_engine,latest_dates,delta,append_tables):
    for table in append_tables:
        
        # pg_table="test_"+table
        pg_table=table
        table_exists_query = pd.read_sql(f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = '{table}'", sql_server_engine)
            
        if not table_exists_query.empty:
            # Assuming 'Date' is the column to compare; replace with actual column if different
            date_column = 'Date'
            
            latest_date=latest_dates[pg_table]
            # Run the query to get data where date is greater than latest_date
            sql_server_query = pd.read_sql(f"SELECT * FROM {table} WHERE {date_column} > '{latest_date}'", sql_server_engine)
            data = sql_server_query.drop(columns=['id'])
            
            latest_date=latest_date-timedelta(days=delta)
            sql_delete_query = text(f"DELETE FROM {pg_table} WHERE \"{date_column}\" > '{latest_date}'")
            with pg_engine.begin() as conn:
                conn.execute(sql_delete_query)
            
            max_id = pd.read_sql(f"SELECT MAX(id) FROM {pg_table}", pg_engine)
            max_id = max_id.iloc[0, 0]
            if max_id is None:
                max_id=1
            data['id'] = range(max_id+1, max_id + len(data)+1)
            data.columns = data.columns.str.replace(' ', '_')
            data.to_sql(name = pg_table, con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)
            print(f"{table}-> table data inserted")
        else:
            print(f"Table '{table}' does not exist in the SQL Server database.")
    



#Truncate and insert tables code
def truncate_table_append(pg_engine,sql_server_engine,truncate_tables):
    for table in truncate_tables:
    
        # pg_table="test_"+table
        pg_table=table
        
        data = pd.read_sql(f"SELECT * FROM {table}", sql_server_engine)
        
        with pg_engine.begin() as conn:
            conn.execute(text(f'TRUNCATE TABLE {pg_table}'))
        data.to_sql(name = pg_table, con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)

        print(f"{pg_table}  --> Truncated and inserted!!")



def ma_ema_macd_table_append(pg_engine,sql_server_engine,latest_dates,delta):
    ma_ema_macd_table="crypto_ma_ema_macd"
    
    query_ema = 'SELECT * FROM Crypto_Exponential_Moving_Average ORDER BY FS_Ticker, Date'
    query_ma = 'SELECT * FROM Crypto_Moving_Average ORDER BY FS_Ticker, Date'
    query_macd = 'SELECT * FROM Crypto_Moving_Average_Convergence_Divergence ORDER BY FS_Ticker, Date'
    
    
    df_ema = pd.read_sql_query(query_ema, sql_server_engine)
    df_ma = pd.read_sql_query(query_ma, sql_server_engine)
    df_macd = pd.read_sql_query(query_macd, sql_server_engine)
    df_ema=df_ema[['Company', 'FS_Ticker', 'Date', 'Price', 'EMA9', 'EMA12', 'EMA',
       'EMA26', 'EMA50', 'EMA200']]
    df_ma=df_ma[['Date','FS_Ticker', '9MA', '20MA', '26MA', '50MA','100MA', '200MA']]
    df_macd=df_macd[['Date', 'FS_Ticker',  'MACD Line', 'Signal Line','MACD Histogram']]
    
    
    # Merging the DataFrames on FS_Ticker and Date
    merged_df = df_ema.merge(df_ma, on=['FS_Ticker', 'Date']).merge(df_macd, on=['FS_Ticker', 'Date'])
    
    ma_ema_macd_latest_date = pd.read_sql(f"SELECT MAX(\"Date\") FROM {ma_ema_macd_table}", pg_engine)
    ma_ema_macd_latest_date = ma_ema_macd_latest_date.iloc[0, 0]
    if ma_ema_macd_latest_date is None:
        ma_ema_macd_latest_date= pd.to_datetime('1900-01-01')
    
    ma_ema_macd_latest_date=ma_ema_macd_latest_date-timedelta(days=delta)
    ma_ema_macd_df=merged_df[merged_df["Date"]>ma_ema_macd_latest_date]
    
    ma_ema_macd_df.columns = ma_ema_macd_df.columns.str.replace(' ', '_')
    ma_ema_macd_df["created_at"]=datetime.now().date()
    ma_ema_macd_df["updated_at"]=datetime.now().date()
    ma_ema_macd_df.to_sql(name = ma_ema_macd_table, con = pg_engine,chunksize=10, method='multi', if_exists='append', index = False)
    

def main():
    
    delta=0
    # Create connection strings
    pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_name}"
    sql_server_connection_string = f"mssql+pyodbc://{sql_server_user}:{sql_server_password}@{sql_server_host}:{sql_server_port}/{sql_server_db_name}?driver={sql_server_driver}"
    
    
    # Create SQLAlchemy engines
    pg_engine = create_engine(pg_connection_string, pool_pre_ping=True)
    print(f"Connected to PostgreSQL database '{pg_db_name}'")
    
    sql_server_engine = create_engine(sql_server_connection_string, pool_pre_ping=True)
    print(f"Connected to SQL Server database '{sql_server_db_name}'")
    
    # List of table names
    
    # append_tables = [
    #     'crypto_average_true_range', 'crypto_daily_beta', 'crypto_exponential_moving_average', 
    #     'crypto_moving_average', 'crypto_moving_average_convergence_divergence', 'crypto_prices_main'
    #     , 'crypto_volume_20_data', 'crypto_volume_data'
    # ]
    append_tables = [
        'crypto_average_true_range', 'crypto_daily_beta', 'crypto_prices_main'
        , 'crypto_volume_20_data', 'crypto_volume_data'
    ]
    
    truncate_tables=['crypto_master','crypto_technical_indicators_daily','crypto_performance','crypto_target_prices']
    
    merge_tables={"crypto_ma_ema_macd":['crypto_exponential_moving_average', 
        'crypto_moving_average', 'crypto_moving_average_convergence_divergence']}

    print("----------Retieving latest dates")
    latest_dates=latest_dates_calc()
    
    print("----------Append tables insertion")
    append_table_code(pg_engine,sql_server_engine,latest_dates,delta,append_tables)
    
    print("-----------Truncate tables insertion")
    truncate_table_append(pg_engine,sql_server_engine,truncate_tables)

    print("-----------ma_ema_macd_table_append")
    ma_ema_macd_table_append(pg_engine,sql_server_engine,latest_dates,delta)
    
    pg_engine.dispose()
    sql_server_engine.dispose()
    print("Success!!!")
    
    

if __name__ == "__main__":
    main()
