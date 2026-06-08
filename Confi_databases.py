# -*- coding: utf-8 -*-
"""
Created on Fri Sep 27 17:40:28 2024

@author: vasanthi.g
"""

from sqlalchemy import create_engine

pg_db_name = 'CRYPTO DEVELOPMENT'
pg_user = 'postgres'
pg_password = 'GhcHyd_2025$'
pg_host = '192.168.1.68'
pg_port = 5432

sql_server_db_name = '72PI'
sql_server_user = '72pi'
sql_server_password = '72Pi_2023$'
sql_server_host = '192.168.1.5'
sql_server_port = 1433
sql_server_driver = 'ODBC Driver 13 for SQL Server'


pg_connection_string = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db_name}"
pg_engine = create_engine(pg_connection_string, pool_pre_ping=True)