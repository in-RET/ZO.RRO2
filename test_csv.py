# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 16:08:46 2024

@author: rbala
"""

import matplotlib.colors as mcolors
import matplotlib
#from src.preprocessing.location import Location
from src .preprocessing.conversion import investment_parameter
from src.preprocessing.files import read_input_files
from src.postprocessing.export_results import export_csv_region, grid_energy_map, export_csv
import numpy as np
import matplotlib.image as mpimg
from oemof.tools import economics
from oemof import network, solph
import pandas as pd
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
energysystem.restore(my_path, os.path.join(workdir,
                                           'dumps', '2030_BS0001', 'Basic_example_zorro_1_2030_BS0001_005.dump'))
YEAR = 2030
model_ID = 'BS0001'
# model_name '_' years '_' variations '.dump'
# img_path = os.path.abspath(os.path.join(os.getcwd(),
# 'figures','Thuringia_karte_mit_Landkreisen_dull.png'))
# img=mpimg.imread(img_path)
# plt.show()
sequences = read_input_files(
    folder_name='data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name='data/scalars', sub_folder_name='parameter')
#demand = load_profile_scaling(scalars,sequences, YEAR, region=False)
#demand = zorro_1_loadprofile_scaling(YEAR, new_profile=True)
epc_costs = investment_parameter(scalars, YEAR, model_ID)
results = energysystem.results["main"]
year = [2030, 2040, 2050]
#sim_data = sim_data
#csv=export_csv(results, 2030, '2030_BS0001', 'Basic_example_zorro_1_2030_BS0001', '005', sim_data)
#export = export_csv_region(results, 2030 , '2030_BS0001', 'BS_regionalization_2030_BS0001')
#grid_energy_map(results,'2030_BS0001', 'BS_regionalization_2030_BS0001')

# b_el = solph.views.node(results, 'Electricity')
# b_gas = solph.views.node(results, 'Gas')
# b_oil = solph.views.node(results, 'Oil_fuel')
# b_bio = solph.views.node(results, 'Biomass')
# b_bioWood = solph.views.node(results, 'BioWood')
# b_solidf = solph.views.node(results, 'Solidfuel')
# b_dist_heat = solph.views.node(results, 'District heating')
# b_H2 = solph.views.node(results, 'Hydrogen')
# #Syntbus = solph.views.node(results, 'Synthetische_Kraftstoffe')
# Battery = solph.views.node(results, 'Battery')
# Heat_storage = solph.views.node(results, 'Heat storage')
# Pumped_hydro_storage = solph.views.node(results, 'Pumped_hydro_storage')
# Gas_storage = solph.views.node(results, 'Gas_storage')
# H2_storage = solph.views.node(results, 'H2_storage')
#%%
import pickle
dump_file_path =os.path.join(workdir,'dumps', '2030_BS0001', 'Basic_example_zorro_1_2030_BS0001_001.dump')

with open(dump_file_path, "rb") as file:
    results = pickle.load(file)

# Extract flow results
if "Main" in results and "flows" in results["Main"]:
    flows = results["Main"]["flows"]
    
    # Convert to a structured DataFrame
    data = []
    for (source, target), flow_data in flows.items():
        if hasattr(flow_data, "values"):  # Check if values exist
            for time_index, value in enumerate(flow_data.values):
                data.append([time_index, source.label, target.label, value])
    
    df = pd.DataFrame(data, columns=["Time", "Source", "Target", "Flow Value"])

#%%

def COP(scalars, T_a, model_ID, YEAR):

    T_VL = [None]*8760
    COP = [None]*8760
    T_VL_L = scalars['Temperature_dist_heat']['T_VL_L_' + str(YEAR)][model_ID]
    T_VL_U = scalars['Temperature_dist_heat']['T_VL_U_' + str(YEAR)][model_ID]
    T_RL = scalars['Temperature_dist_heat']['T_RL_' + str(YEAR)][model_ID]
    T_L = scalars['Temperature_dist_heat']['T_L'][model_ID]
    T_U = scalars['Temperature_dist_heat']['T_U'][model_ID]
    
    for i in range(len(T_a)):
        if T_a[i] > T_L and T_a[i] < T_U:
            T_VL[i] = T_VL_L - ((T_VL_L - T_VL_U)/(T_U - T_L)) * (T_a[i] - T_L)
        elif T_a[i] <= T_L:
            T_VL[i] = T_VL_L
        elif T_a[i] >= T_U:
            T_VL[i] = T_VL_U
        nu_H = 0.36
        COP[i] = nu_H*(T_VL[i]+273.15) / (T_VL[i]-T_RL)
    return pd.Series(COP)
    
COP = COP(scalars, T_a, model_ID, YEAR)