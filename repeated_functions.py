# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 14:54:36 2024

@author: nookaraju.c
"""

import pandas as pd
from datetime import datetime

def adding_creat_update_dt(df,created_at_dt=datetime.now().date(),updated_at_dt=datetime.now().date()):
    
    df['created_at'] = created_at_dt
    df['updated_at'] = updated_at_dt
    return df


def exclude_creat_update_dt(df,columns_to_exclude= ['created_at', 'updated_at']):
    return df.drop(columns=columns_to_exclude)








