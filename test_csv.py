# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 16:08:46 2024

@author: rbala
"""

import matplotlib.colors as mcolors
import matplotlib
import pandas as pd
#from src.preprocessing.location import Location
from src .preprocessing.conversion import investment_parameter,COP_calculation, load_profile_scaling,  Utility_demand_breakdown
from src.preprocessing.files import read_input_files
from src.postprocessing.export_results import export_csv_region, grid_energy_map, export_csv
from src.preprocessing.location import Location
import numpy as np
import matplotlib.image as mpimg
from oemof.tools import economics
from oemof import network, solph
#import pandas as pd
import os
workdir = os.getcwd()
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

co2_max = scalars['System_configurations_2024']['System']['CO2_Grenze_'+str(YEAR)]
co2_min = 0
if pareto_optimization:
    co2_range = np.linspace(co2_min, co2_max, 15)
else:
    co2_range =[co2_max]
# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
# %%

my_path = os.path.abspath(os.path.dirname(__file__))

energysystem = solph.EnergySystem()
#energysystem.restore(my_path, os.path.join(workdir,
 #                                          'dumps', '2030_BS0001', 'Basic_example_zorro_1_2030_BS0001_005.dump'))
YEAR = 2030
model_ID = 'BS0006'
model_name = "BS"
# model_name '_' years '_' variations '.dump'
# img_path = os.path.abspath(os.path.join(os.getcwd(),
# 'figures','Thuringia_karte_mit_Landkreisen_dull.png'))
# img=mpimg.imread(img_path)
# plt.show()
sequences = read_input_files(
    folder_name='data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name='data/scalars', sub_folder_name=None)
demand = load_profile_scaling(scalars,sequences,YEAR,model_name, region = False)
#demand = zorro_1_loadprofile_scaling(YEAR, new_profile=True)


demands = ['space_heating_household', 'space_heating_industry', 'space_heating_ghd',
           'process_heating_industry', 'process_heating_ghd',
           'cooling_household', 'cooling_industry', 'cooling_ghd',
           'electrical_household', 'electrical_ghd', 'electrical_industry',
           'mobility_person', 'mobility_goods', 'material_usage_industry', 'rechnenzentrum'
           ]
demand_ne = {}
for d in demands:
    demand_ne[d] = Utility_demand_breakdown(scalars, sequences, YEAR,model_ID, demand_type= d, region= False)
epc_costs = investment_parameter(scalars, YEAR, model_ID)
#results = energysystem.results["main"]
year = [2030, 2040, 2050]

Weather_dir = os.path.abspath(os.path.join(workdir, 'data','weatherdata'))
middle = Location(os.path.join(Weather_dir,'Erfurt_Binderslebn-hour.csv'), os.path.join(Weather_dir,'Erfurt_Binderslebn-min.dat'))
north = Location(os.path.join(Weather_dir,'Nordhausen-hour.csv'), os.path.join(Weather_dir,'Nordhausen-min.dat'))
swest= Location(os.path.join(Weather_dir,'Hildburghausen-hour.csv'), os.path.join(Weather_dir,'Hildburghausen-min.dat'))
east = Location(os.path.join(Weather_dir,'Gera-Leumnitz-hour.csv'), os.path.join(Weather_dir,'Gera-Leumnitz-min.dat'))
Ta_avg = ((north.weather_data_hour[' Ta'] + east.weather_data_hour[' Ta'] + middle.weather_data_hour[' Ta'] + swest.weather_data_hour[' Ta'])/4)
fixed_losses_absolute_seasonal_storage = 1656.2*(85 - Ta_avg )+ 74.7 *(10-11)
Planing_region = [middle, north, swest, east]
""" Simulate Wind feed-in profile for the desired location """
for L in Planing_region:
    L.Wind_feed_in_profile(YEAR)
    L.PV_feed_in_profile(YEAR)


COP_avg, T_VL_avg = COP_calculation(scalars, Ta_avg, model_ID, YEAR)
fixed_losses_absolute_seasonal_storage_avg = 1656.2*(85 - Ta_avg )+ 74.7 *(10-11)

COP_n = COP_m = COP_e = COP_s = COP_avg
T_VL_e = T_VL_m = T_VL_n = T_VL_s = T_VL_avg

#%%
# sum_2 =[]
# for sector, data in demand.items():
#     for name, data_dict in data.items():
#         for region, data_info in data_dict.items():
#             if name == 'demand_data':
#                 sum_2.append({
#                     'Sector': sector,
#                     'Region': region,
#                     'Sum': data_info['total_value']/1000000
#                 })
#             else:
#                 continue
            
                
# sum_df = pd.DataFrame(sum_2)

sum_ne= (demand_ne['cooling_ghd']['demand_data']['total_value']+
             demand_ne['cooling_household']['demand_data']['total_value']+
             demand_ne['cooling_industry']['demand_data']['total_value']+
             demand_ne['electrical_ghd']['demand_data']['total_value']+
             demand_ne['electrical_household']['demand_data']['total_value']+
             demand_ne['electrical_industry']['demand_data']['total_value']+
             demand_ne['material_usage_industry']['demand_data']['total_value']+
             demand_ne['process_heating_ghd']['demand_data']['total_value']+
             demand_ne['process_heating_industry']['demand_data']['total_value']+
             demand_ne['space_heating_ghd']['demand_data']['total_value']+
             demand_ne['space_heating_household']['demand_data']['total_value']+
             demand_ne['space_heating_industry']['demand_data']['total_value'])/1000000
             #demand_ne['mobility_goods']['demand_data']['total_value']+
             #demand_ne['mobility_person']['demand_data']['total_value']
             
    #%%
ph_ghd = demand_ne['process_heating_ghd']['technology_data']['Waermeuebergabestation']['series']
ph_ind = demand_ne['process_heating_industry']['technology_data']['Waermeuebergabestation']['series']
sh_hh  = demand_ne['space_heating_household']['technology_data']['Waermeuebergabestation']['series']
sh_ghd = demand_ne['space_heating_ghd']['technology_data']['Waermeuebergabestation']['series']
sh_ind = demand_ne['space_heating_industry']['technology_data']['Waermeuebergabestation']['series']

dist_heat = demand['dist_heating'] * 0.91

# Time index
t = range(len(ph_ghd))

# Stackplot
plt.figure(figsize=(10, 6))
plt.stackplot(
    t,
    ph_ghd,
    ph_ind,
    sh_hh,
    sh_ghd,
    sh_ind,
    labels=[
        'Process heat GHD',
        'Process heat Industry',
        'Space heat Household',
        'Space heat GHD',
        'Space heat Industry'
    ],
    alpha=0.8
)

# Overlay district heating demand
plt.plot(t, dist_heat, linewidth=2, label='District heating demand (×0.91)')

plt.legend(loc='upper right')
plt.xlabel('Time')
plt.ylabel('Heat demand')
plt.title('District heating demand')
plt.tight_layout()
plt.show()
#%%
plt.figure(figsize=(10, 4))
plt.plot(dist_heat - (ph_ghd + ph_ind + sh_hh + sh_ghd + sh_ind))
plt.title('District heating margin (positive = feasible)')
plt.show()