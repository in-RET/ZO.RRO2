# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 16:08:46 2024

@author: rbala
"""

from oemof.tools import economics
from oemof import network, solph
import pandas as pd
import os
workdir = os.getcwd()
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from src.postprocessing.export_results import export_csv_region, grid_energy_map


# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
# %%

my_path = os.path.abspath(os.path.dirname(__file__))

energysystem = solph.EnergySystem()
energysystem.restore(my_path, os.path.join(workdir, 
                     'dumps', '2030_BS0001', 'BS_regionalization_2030_BS0001.dump'))

# model_name '_' years '_' variations '.dump'
img_path = os.path.abspath(os.path.join(os.getcwd(), 
                     'figures','Thuringia_karte_mit_Landkreisen_dull.png'))
img=mpimg.imread(img_path)
plt.show()
results = energysystem.results["main"]
year = [2030,2040,2050]

export = export_csv_region(results, 2030 , '2030_BS0001', 'BS_regionalization_2030_BS0001')
grid_energy_map(results,'2030_BS0001', 'BS_regionalization_2030_BS0001')

region = ['n','s', 'e', 'm']
Region_csv = pd.DataFrame()
for r in region:
    b_el = solph.views.node(results, 'Electricity_'+ r)
    b_gas = solph.views.node(results, 'Gas_'+ r)
    b_oil = solph.views.node(results, 'Oil_fuel_'+ r)
    b_bio = solph.views.node(results, 'Biomass_'+ r)
    b_bioWood = solph.views.node(results, 'BioWood_'+ r)
    b_solidf = solph.views.node(results, 'Solidfuel_'+ r)
    b_dist_heat = solph.views.node(results, 'District heating_' + r)
    b_H2 = solph.views.node(results, 'Hydrogen_' + r)
    #Syntbus = solph.views.node(results, 'Synthetische_Kraftstoffe')
    Battery = solph.views.node(results, 'Battery_'+ r)
    Heat_storage = solph.views.node(results, 'Heat storage_'+ r)
    Pumped_hydro_storage = solph.views.node(results, 'Pumped_hydro_storage_' + r)
    Gas_storage = solph.views.node(results, 'Gas_storage_'+ r)
    H2_storage = solph.views.node(results, 'H2_storage_'+ r)
    
#%%


df = pd.DataFrame()
df_2 = pd.DataFrame()
df['Oil_2025'] = [57.18,56.92,56.68,56.44,56.21,55.97,55.73,55.50,55.27,55.06,54.83,54.61,54.61,0]
df_2['Gas_2025'] = [35.10 ,35.04,34.98,34.91,34.85,34.79,34.72,34.66,34.60 
,34.54 
,34.48 
,30.92 
,30.92
,0
]

df['Oil_2030'] = [62.51 
,62.77 
,63.04 
,63.31 
,63.59 
,63.86 
,63.99 
,63.97 
,63.96 
,63.94 
,63.92 
,63.91
,63.91
,0 
]

df_2['Gas_2030'] =[23.08 
,22.99 
,22.90 
,22.80 
,22.71 
,22.61 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56
,0
]
df['Oil_2035'] = [63.09 
,63.08 
,63.06 
,63.04 
,63.03 
,63.01 
,62.99 
,62.98 
,62.96 
,62.94 
,62.92 
,62.91 
,62.91
,0
]
df_2['Gas_2035'] =[22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56
,0]
df['Oil_2040'] =[62.09 
,62.08 
,62.06 
,62.04 
,62.03 
,62.01 
,61.99 
,61.97 
,61.96 
,61.94 
,61.92 
,61.91 
,61.91
,0]
df_2['Gas_2040'] =[22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.56 
,22.54 
,22.50 
,22.45 
,22.41 
,22.37 
,22.32
,22.32
,0 
]
df['Oil_2045'] = [61.09 
,61.07 
,61.06 
,61.04 
,61.03 
,61.01 
,60.99 
,60.97 
,60.96 
,60.94 
,60.92 
,60.91 
,60.91
,0]
df_2['Gas_2045'] =[20.20 
,20.16 
,20.11 
,20.07 
,20.03 
,19.98 
,19.94 
,19.90 
,19.85 
,19.81 
,19.77 
,19.72 
,19.72
,0]
df['Oil_2050'] = [60.09 
,60.07 
,60.06 
,60.04 
,60.03 
,60.01 
,60.00 
,59.99 
,59.98 
,59.97 
,59.96 
,59.95 
,59.95
,0]
df_2['Gas_2050'] =[17.60 
,17.56 
,17.52 
,17.47 
,17.43 
,17.38 
,17.35 
,17.32 
,17.30 
,17.27 
,17.25 
,17.22 
,17.22
,0]
df = df/(158.7579*11.86*0.86)*1000 # brainpool price / ((1bbl = 158.7579 l) *(Brennwert_oil = 11.86 kWh/kg) *(dicte_oil = 0.86 kg/l)) *1000 (kWh to MWh)
index = pd.date_range(start='2024-12-31' , end= '2026-01-31', freq= 'M')
df = df.set_index(index)
df = df.resample('H').ffill()
df = df['2025-01-01 00:00:00' : '2025-12-31 23:00:00']

df_2 = df_2.set_index(index)
df_2 = df_2.resample('H').ffill()
df_2 = df_2['2025-01-01 00:00:00' : '2025-12-31 23:00:00']

df.applymap(lambda x: str(x).replace('.', ',')).to_csv("dummy.csv", sep = ';')
df_2.applymap(lambda x: str(x).replace('.', ',')).to_csv("dummy_gas.csv", sep = ';')
print("Ende")