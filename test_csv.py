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
from src.postprocessing.export_results import export_csv_region

# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
# %%

my_path = os.path.abspath(os.path.dirname(__file__))

energysystem = solph.EnergySystem()
energysystem.restore(my_path, os.path.join(workdir, 
                     'dumps', '2030_BS0001', 'BS_regionalization_2030_BS0001.dump'))

# model_name '_' years '_' variations '.dump'

results = energysystem.results["main"]

export = export_csv_region(results, 2030, '2030_BS0001', 'BS_regionalization_2030_BS0001')

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
    


print("Ende")