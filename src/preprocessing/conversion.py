# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 18:22:48 2024

@author: rbala
!!!!!!!!!!!!!!!!!!!!!!!!!!!

CAUTION: 
    
    The script is written to calculate/ process some datas from simulation.
    Please consult the author before altering the script.


!!!!!!!!!!!!!!!!!!!!!!!!!!!
this script consists:
    - function to convert timeseries from any resolution to hourly values, does'nt matter which type of data is given to the funtion (can be a series/DF/list/etc.)' 
        
"""
import pandas as pd

def convert_into_hourly_values (data, simulation_year, existing_res = '15min'):
    
    # existing_res --> 15min /H/1min
    # data can be provies as a list of series or as a dataframe
           
    if type(data) == list:
        df = pd.DataFrame()
        for y in simulation_year:
            for s in data:
                d_t_index = pd.date_range('1/1/' +str(y), periods = len(data), freq = existing_res)
                df = df.append(s)
            a = df.T
            a = a.set_index(d_t_index)
            a = a.resample('H').mean()
            return(a)
    
    elif type(data) == pd.core.frame.DataFrame:
        for y in simulation_year:
            d_t_index = pd.date_range('1/1/' +str(y), periods = len(data), freq = existing_res)
            data= data.set_index(d_t_index)
            data = data.resample('H').mean()
            return(data)