# import warnings
# warnings.filterwarnings("ignore")

# # Import your separate crypto files
# import Crpyto_migration
# import Crypto_Super_Screener
# import Crypto_Daily_Top_Performers_Live
# # from . import repeated_functions


# # Configurations (can be placed in a config file if necessary)
# from configurations import pg_engine  # Assuming configurations.py holds the database connection
# from configurations import today_date, crypto_config  # Other relevant settings

# def main():
#     # Running Crypto Migration
#     print("Running Crypto Migration script...")
#     migration_flag = Crpyto_migration.main()  # Call the main function in the migration file

#     if migration_flag:
#         print("Crypto Migration completed successfully.")
        
#         # Running Crypto Super Screener
#         print("Running Crypto Super Screener script...")
#         screener_flag = Crypto_Super_Screener.main()  # Call the main function in the screener file

#         if screener_flag:
#             print("Crypto Super Screener completed successfully.")
            
#             # Running Crypto Daily Top Performers Live
#             print("Running Crypto Daily Top Performers Live script...")
#             performers_flag = Crypto_Daily_Top_Performers_Live.main()  # Call the main function in the performers file

#             if performers_flag:
#                 print("Crypto Daily Top Performers Live completed successfully.")
#                 print("All scripts executed successfully.")
#             else:
#                 print("Crypto Daily Top Performers Live failed.")
#         else:
#             print("Crypto Super Screener failed.")
#     else:
#         print("Crypto Migration failed.")

# if __name__ == '__main__':
#     main()
    

import os
import repeated_functions
import Crypto_Daily_Top_Performers_Live
import Crypto_migration
import us_market_index
import Crypto_Super_Screener

# PostgreSQL credentials
pg_user = 'postgres'  # Your actual PostgreSQL username
pg_password = 'GhcHyd_2025$'  # Your actual PostgreSQL password
pg_host = '192.168.1.68'  # Your actual PostgreSQL host
pg_port = '5432'  # Your actual PostgreSQL port
pg_db_name = 'CRYPTO DEVELOPMENT'  # Your actual PostgreSQL database name

# SQL Server credentials
sql_server_user = '72pi'  # Your actual SQL Server username
sql_server_password = '72Pi_2023$'  # Your actual SQL Server password
sql_server_host = '192.168.1.5'  # Your actual SQL Server host
sql_server_port = '1433'  # Your actual SQL Server port
sql_server_db_name = '72PI'  # Your actual SQL Server database name
sql_server_driver = 'ODBC Driver 13 for SQL Server'  # Your actual SQL Server driver

def main():
    # Run each script
    print("Starting Crypto Daily Top Performers Live...")
    Crypto_Daily_Top_Performers_Live.main(pg_user, pg_password, pg_host, pg_port, pg_db_name)

    print("Running Noo Crypto Dumping...")
    Noo_Crypto_dumping.main(pg_user, pg_password, pg_host, pg_port, pg_db_name, sql_server_user, sql_server_password, sql_server_host, sql_server_port, sql_server_db_name, sql_server_driver)

    print("Executing US Market Index...")
    us_market_index.main(pg_user, pg_password, pg_host, pg_port, pg_db_name)

    print("Running Crypto Super Screener...")
    Crypto_Super_Screener.main(pg_user, pg_password, pg_host, pg_port, pg_db_name, sql_server_user, sql_server_password, sql_server_host, sql_server_port, sql_server_db_name, sql_server_driver)

if __name__ == "__main__":
    main()
