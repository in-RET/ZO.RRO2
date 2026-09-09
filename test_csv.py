# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 16:08:46 2024

@author: rbala
"""

import matplotlib.colors as mcolors
import matplotlib
import pandas as pd
#from src.preprocessing.location import Location
from src .preprocessing.conversion import investment_parameter,COP_calculation, load_profile_scaling,  Utility_demand_breakdown, CO2_price_addition
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

# co2_max = scalars['System_configurations_2024']['System']['CO2_Grenze_'+str(YEAR)]
# co2_min = 0
# if pareto_optimization:
#     co2_range = np.linspace(co2_min, co2_max, 15)
# else:
#     co2_range =[co2_max]
# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
# %%

my_path = os.path.abspath(os.path.dirname(__file__))

energysystem = solph.EnergySystem()
#energysystem.restore(my_path, os.path.join(workdir,
 #                                          'dumps', '2030_BS0001', 'Basic_example_zorro_1_2030_BS0001_005.dump'))
YEAR = 2045
model_ID = 'BS0006'
model_name = "BS_regionalization"
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
import_price_2021 = CO2_price_addition(scalars,sequences, YEAR, 'Energy_price_brainpool_2021')
import_price_2023 = CO2_price_addition(scalars,sequences, YEAR, 'Energy_price_brainpool_2023')
import_price_2026 = CO2_price_addition(scalars,sequences, YEAR, 'Energy_price_brainpool_2026')

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
cool_HH = demand_ne['cooling_household']['demand_data']['series']*0
cool_ind = demand_ne['cooling_industry']['demand_data']['series']    
cool_ghd = demand_ne['cooling_ghd']['demand_data']['series']*0


space_cool = (cool_HH+cool_ind+cool_ghd)/3.7
print(space_cool.sum())
# Time index
t = range(len(cool_HH))

# Stackplot
plt.figure(figsize=(10, 6))
plt.stackplot(
    t,
    cool_HH,
    cool_ind,
    cool_ghd,
    labels=[
        'Space cool Household',
        'Space cool Industry',
        'Space cool GHD',
    ],
    alpha=0.8
)

# Overlay district heating demand
plt.plot(t, space_cool, linewidth=2, label='Space cooling demand (endenergy)')

plt.legend(loc='upper right')
plt.xlabel('Time')
plt.ylabel('Cooling demand')
plt.title('Space cooling demand')
plt.tight_layout()
plt.show()
#%%

plt.figure(figsize=(10, 6))
plt.plot(t, demand['electricity'], linewidth=2, label='Electricity')
plt.legend(loc='upper right')
plt.xlabel('Time')
plt.ylabel('Cooling demand')
plt.title('Space cooling demand')
plt.tight_layout()
plt.show()

#%% PKW Emob share calc

s = scalars['Demand_Transport_nutzenergie_east_b']['NE_Personenverkehr_2045']

exclude = ["Summe_EE ", "Summe_NE"]
base = s.drop(index=exclude, errors="ignore")

# baseline total electrified vs combustion if needed
total = base.sum()

electric = [
    "PKW - Batterie",
    "Busse - Batterie",
    "Schiene - Elektrisch",
]

combustion = [
    "PKW - Verbrenner",
    "PKW - Verbrenner CNG",
    "Busse - Verbrenner",
    "Schiene - Verbrenner",
]

elec_base = base.loc[electric]
comb_base = base.loc[combustion]

elec_share = elec_base / elec_base.sum()
comb_share = comb_base / comb_base.sum()

alpha = 1
total_demand = base.sum()
elec_total = total_demand * (elec_base.sum()/total_demand + alpha*(1 - elec_base.sum()/total_demand))

comb_total = total_demand - elec_total
new = pd.Series(index=base.index, dtype=float)

new.loc[electric] = elec_share * elec_total
new.loc[combustion] = comb_share * comb_total


#%%