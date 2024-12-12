# -*- coding: utf-8 -*-
"""
Created on Thu Dec 12 15:24:16 2024

@author: rbala
"""

from src.preprocessing.files import read_input_files
import pandas as pd
from oemof.tools import economics


scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)

Model_ID = 'BS0001'

if Model_ID == 'BS0001':
    simulation_year = [2030,2040,2050]
else:
    simulation_year = [2020,2025,2030,2035,2040,2045]

data = scalars
T_list = []             # Technology list will be automatically generated based on the file name
for i in data:
    if i.startswith('Parameter'):
        i = i[10:]
        #i = i[:-5]
        T_list.append(i) 

my_dict={}
df = {}
for name in T_list:
    df[name]= {}

for y in simulation_year:
    for name in T_list:
        n = "Parameter_"+ name 
        my_dict[name] = {}
        my_dict[name]['investk'] = economics.annuity(capex=data[n]['investment_costs_'+str(y)][Model_ID], n=data[n]['lifetime_'+str(y)][Model_ID], wacc=data['System_configurations']['System']['Zinssatz']/100)
        my_dict[name]['betriebsk'] = data[n]['investment_costs_'+str(y)][Model_ID] * (data[n]['operating_costs_'+str(y)][Model_ID]/100)
        my_dict[name]['epc'] = my_dict[name]['investk'] + my_dict[name]['betriebsk']
        df[name][str(y)]= my_dict[name]['epc']