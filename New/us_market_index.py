# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 15:36:42 2024

@author: vasanthi.g
"""

import pandas as pd
import pyodbc
from sqlalchemy import create_engine
from datetime import datetime
from sqlalchemy import text
# 72PI Database (SQL Server) connection details
sql_server_db_name = '72PI'
sql_server_user = '72pi'
sql_server_password = '72Pi_2023$'
sql_server_host = '192.168.1.5'
sql_server_port = 1433
sql_server_driver = 'ODBC Driver 13 for SQL Server'

# Crypto Database (PostgreSQL) connection details
pg_db_name = 'CRYPTO DEVELOPMENT'
pg_user = 'postgres'
pg_password = 'GhcHyd_2025$'
pg_host = '192.168.1.68'
pg_port = 5432

# Connect to 72PI SQL Server database using pyodbc
sql_server_connection_string = f'DRIVER={sql_server_driver};SERVER={sql_server_host},{sql_server_port};DATABASE={sql_server_db_name};UID={sql_server_user};PWD={sql_server_password}'
sql_server_conn = pyodbc.connect(sql_server_connection_string)

# Fetch data from US_Market_Index table in SQL Server (72PI DB)
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



