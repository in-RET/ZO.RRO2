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
    - function to calculate the investment, operating and equivalent periodic costs 
        
"""
import pandas as pd
from oemof.tools import economics

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
        

def investment_parameter(data,simulation_year, Model_ID):

    '''
    data : dictionary with all the techno-economical parameters (csv file)
    simulationyear: to choose the specific parameter for the respective simulation year
    
    Function to calculate epc costs and store it as a variable for all technologies
    
    Note: Fix a standard file name format for technology parameters.
    '''   
    T_list = []             # Technology list will be automatically generated based on the file name
    for i in data:
        if i.startswith('Parameter'):
            i = i[10:]
            #i = i[:-5]
            T_list.append(i) 

    my_dict={}
    for name in T_list:
        n = "Parameter_"+ name 
        my_dict[name]= {}
        my_dict[name]['investk'] = economics.annuity(capex=data[n]['investment_costs_'+str(simulation_year)][Model_ID], n=data[n]['lifetime_'+str(simulation_year)][Model_ID], wacc=data['System_configurations']['System']['Zinssatz']/100)
        my_dict[name]['betriebsk'] = data[n]['investment_costs_'+str(simulation_year)][Model_ID] * (data[n]['operating_costs_'+str(simulation_year)][Model_ID]/100)
        my_dict[name]['epc'] = my_dict[name]['investk'] + my_dict[name]['betriebsk']
        
    return(my_dict)