# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 17:28:44 2024

@author: rbala

TEST: 
    Script to test whether the funtions work as specified
    
"""

import sys,os
sys.path.append('../')
from preprocessing import files,conversion
from preprocessing.location import Location
from oemof.tools import economics

workdir= os.getcwd()


simulation_year = [2030]
#%% 
"""   Define Location by importing weather data as input file  """

Weather_dir = os.path.abspath(os.path.join(workdir,'../..', 'data','weatherdata'))

Erfurt = Location(os.path.join(Weather_dir,'Erfurt_Binderslebn-hour.csv'), os.path.join(Weather_dir,'Erfurt_Binderslebn-min.dat'))
Nordhausen= Location(os.path.join(Weather_dir,'Nordhausen-hour.csv'), os.path.join(Weather_dir,'Nordhausen-min.dat'))
Hildburghausen= Location(os.path.join(Weather_dir,'Hildburghausen-hour.csv'), os.path.join(Weather_dir,'Hildburghausen-min.dat'))
Gera = Location(os.path.join(Weather_dir,'Gera-Leumnitz-hour.csv'), os.path.join(Weather_dir,'Gera-Leumnitz-min.dat'))

Planing_region = [Erfurt, Nordhausen, Hildburghausen, Gera]

""" Simulate Wind feed-in profile for the desired location """

for year in simulation_year:
    for L in Planing_region:
        L.Wind_feed_in_profile(year)
        L.PV_feed_in_profile(year)
#%%
Timeseries = files.read_input_files(folder_name = 'data/sequences', sub_folder_name='00_ZORRO_I_old_sequences')
Eingangsdaten = files.read_input_files(folder_name = 'data/scalars', sub_folder_name='00_ZORRO_I_old_scalars')
#%%
'''
Function to calculate epc costs and store it as a variable for all technologies
'''

T_list = ['Waermespeicher']
# for i in Eingangsdaten:
#     if i.startswith('Parameter'):
#         i = i[10:]
#         i = i[:-5]
#         T_list.append(i) 

my_dict={}
for name in T_list:
    n = "Parameter_"+ name +'_' + "2030"
    my_dict[name]= {}
    my_dict[name]['investk'] = economics.annuity(capex=Eingangsdaten[n][name]['CAPEX'], n=Eingangsdaten[n][name]['Amortisierungszeit'], wacc=Eingangsdaten['Systemeigenschaften']['System']['Zinssatz']/100)
    my_dict[name]['betriebsk'] = Eingangsdaten[n][name]['CAPEX'] * (Eingangsdaten[n][name]['OPEX']/100)
    my_dict[name]['epc'] = investk + betriebsk
    a=pd.DataFrame.from_dict(my_dict[name])
    

