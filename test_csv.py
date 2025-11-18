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


# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
# %%

my_path = os.path.abspath(os.path.dirname(__file__))

energysystem = solph.EnergySystem()
#energysystem.restore(my_path, os.path.join(workdir,
 #                                          'dumps', '2030_BS0001', 'Basic_example_zorro_1_2030_BS0001_005.dump'))
YEAR = 2030
model_ID = 'BS0005'
# model_name '_' years '_' variations '.dump'
# img_path = os.path.abspath(os.path.join(os.getcwd(),
# 'figures','Thuringia_karte_mit_Landkreisen_dull.png'))
# img=mpimg.imread(img_path)
# plt.show()
sequences = read_input_files(
    folder_name='data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name='data/scalars', sub_folder_name=None)
#demand = load_profile_scaling(scalars,sequences, YEAR, region=False)
#demand = zorro_1_loadprofile_scaling(YEAR, new_profile=True)


demands = ['space_heating_household', 'space_heating_industry', 'space_heating_ghd',
           'process_heating_industry', 'process_heating_ghd',
           'cooling_household', 'cooling_industry', 'cooling_ghd',
           'electrical_household', 'electrical_ghd', 'electrical_industry',
           'mobility_person', 'mobility_goods', 'material_usage_industry'
           ]
demand = {}
for d in demands:
    demand[d] = Utility_demand_breakdown(scalars, sequences, YEAR, demand_type= d, region= False)
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

COP = COP_calculation(scalars, Ta_avg, model_ID, YEAR)



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

    #%%
# AC_power_nom_1_n = north.PV_feed_in_profile_openfield['AC_Power']  # Random normalized power values for openfield
# AC_power_nom_1_e = east.PV_feed_in_profile_openfield['AC_Power']  # Random normalized power values for rooftop
# AC_power_nom_1_w = swest.PV_feed_in_profile_openfield['AC_Power']  # Random normalized power values for openfield
# AC_power_nom_1_m = middle.PV_feed_in_profile_openfield['AC_Power']
# # Sort the data to create the duration curve (highest values first)
# sorted_n = np.sort(AC_power_nom_1_n)[::-1]
# sorted_e = np.sort(AC_power_nom_1_e)[::-1]
# sorted_w = np.sort(AC_power_nom_1_w)[::-1]
# sorted_m = np.sort(AC_power_nom_1_m)[::-1]

# # Plotting the duration curves for both Openfield and Rooftop
# plt.figure(figsize=(10, 6))
# plt.plot(AC_power_nom_1_n, label='north', color='blue')
# plt.plot(AC_power_nom_1_e, label='east', color='green')
# plt.plot(AC_power_nom_1_w, label='w', color='orange')
# plt.plot(AC_power_nom_1_m, label='m', color='red')

# # Adding titles and labels
# plt.title("Year Duration Curve", fontsize=16)
# plt.xlabel("Hours of the Year", fontsize=14)
# plt.ylabel("Normalized Power Output (kW)", fontsize=14)
# plt.legend()
# plt.grid(True)
#%%


