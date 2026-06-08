# -*- coding: utf-8 -*-
"""
Main file to run Crypto Migration, Crypto Super Screener, and Crypto Daily Top Performers Live
"""
import warnings
warnings.filterwarnings("ignore")
import os
os.chdir(r'I:\72PI Daily Data\Crypto Catalyst')

# Import your separate crypto files
import Crpyto_migration
import Crypto_Super_Screener
import Crypto_Daily_Top_Performers_Live
import US_Market_Index_Migration 
import Confi_databases

# Configurations (can be placed in a config file if necessary)
from configurations import pg_engine  # Assuming configurations.py holds the database connection
from configurations import today_date, crypto_config  # Other relevant settings

def main():
    # Running Crypto Migration
    print("Running Crypto Migration script...")
    migration_flag = Crpyto_migration.main()  # Call the main function in the migration file

    if migration_flag:
        print("Crypto Migration completed successfully.")
        
        # Running US Market Index Migration
        print("Running US Market Index Migration script...")
        us_market_flag = US_Market_Index_Migration.main()  # Call the main function in the us_market_index migration file

        if us_market_flag:
            print("US Market Index Migration completed successfully.")
            
            # Running Crypto Super Screener
            print("Running Crypto Super Screener script...")
            screener_flag = Crypto_Super_Screener.main()  # Call the main function in the screener file

            if screener_flag:
                print("Crypto Super Screener completed successfully.")
                
                # Running Crypto Daily Top Performers Live
                print("Running Crypto Daily Top Performers Live script...")
                performers_flag = Crypto_Daily_Top_Performers_Live.main()  # Call the main function in the performers file

                if performers_flag:
                    print("Crypto Daily Top Performers Live completed successfully.")
                    print("All scripts executed successfully.")
                    print("Success")
                else:
                    print("Crypto Daily Top Performers Live failed.")
            else:
                print("Crypto Super Screener failed.")
        else:
            print("US Market Index Migration failed.")
    else:
        print("Crypto Migration failed.")

if __name__ == '__main__':
    main()

    
    
    
    
    

