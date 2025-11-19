# -*- coding: utf-8 -*-
"""
Created on Tue Aug 19 12:07:29 2025

@author: treinhardt01
"""

from oemof import solph
import pandas as pd
import numpy as np
import seaborn
import colorcet as cc
import os 

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
    
# name = "2050_BS0005"


number_of_time_steps = 8760
date_time_index = pd.date_range(
    "1/1/2045", # change year
    periods=number_of_time_steps, freq="h"
)


my_path = os.path.abspath(os.path.dirname(__file__))

colors = seaborn.color_palette("bright", 30)
palette = seaborn.color_palette(cc.glasbey, n_colors=30)


res_Elec = {}
res_Elec_hoes = {}
res_battery = {}
res_li_ion_battery = {}
res_h2 = {}
res_dis_heat = {}
dict_costs_ = {}
res_Pumped_hydro_storage = {}
dict_costs_storages = {}
res_Natrium_Battery = {}
res_Heat_storage_dist_heat = {}
res_Heat_storage_seasonal = {}
res_Gas_storage = {}
res_H2_storage = {}
res_gas = {}
res_oil_fuel = {}
res_solid_fuel = {}


for x in range(0, 11):
    energysystem = solph.EnergySystem()
    energysystem.restore(dpath='2045_BS0006/', 
                         filename='BS_2045_BS0006_Bilanz_1_Wind_P'+str(x)+'0.dump')
    
    results = energysystem.results["main"]
    
    res_Elec[f'var{x+1}'] = solph.views.node(results, "Electricity")
    res_Elec_hoes[f'var{x+1}'] = solph.views.node(results, "Electricity_Hös")
    
    res_battery[f'var{x+1}'] = solph.views.node(results, "Battery")
    res_li_ion_battery[f'var{x+1}'] = solph.views.node(results, "Li-Ion_Battery")
    res_Natrium_Battery[f'var{x+1}'] = solph.views.node(results, "Natrium_Battery")
    
    res_Heat_storage_dist_heat[f'var{x+1}'] = solph.views.node(results, "Heat storage_dist_heat")
    res_Heat_storage_seasonal[f'var{x+1}'] = solph.views.node(results, "Heat storage_seasonal")
    
    res_Pumped_hydro_storage[f'var{x+1}'] = solph.views.node(results, "Pumped_hydro_storage")
    
    res_Gas_storage[f'var{x+1}'] = solph.views.node(results, "Gas_storage")
    res_H2_storage[f'var{x+1}'] = solph.views.node(results, "H2_storage")
    
    res_h2[f'var{x+1}'] = solph.views.node(results, "Hydrogen")
    res_dis_heat[f'var{x+1}'] = solph.views.node(results, "District heating")
    
    res_gas[f'var{x+1}'] = solph.views.node(results, "Gas") 
    res_oil_fuel[f'var{x+1}'] = solph.views.node(results, "Oil_fuel")
    
    res_solid_fuel[f'var{x+1}'] = solph.views.node(results, "Solidfuel")
    
    
#%%


sum_load = (res_gas['var1']["sequences"][
    ('Gas', 'Gas_demand_total'), 'flow'].sum() + 

res_Elec['var1']["sequences"][
    ('Electricity', 'Electricity_demand_total'), 'flow'].sum() +

res_oil_fuel['var1']["sequences"][
    ('Oil_fuel', 'Oil & fuel_demand_total'), 'flow'].sum() +

res_dis_heat['var1']["sequences"][
    ('District heating', 'Heat_demand_total'), 'flow'].sum() +

res_h2['var1']["sequences"][
    ('Hydrogen', 'Hydrogen_demand_total'), 'flow'].sum()
)


#%%


ee_erzeugung_1 = (res_Elec['var1']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var1']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var1']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var1']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var1']["sequences"][('PV_rooftop_north', 'Electricity'), 'flow'].sum()+
res_Elec['var1']["sequences"][('PV_rooftop_east', 'Electricity'), 'flow'].sum()+
res_Elec['var1']["sequences"][('PV_rooftop_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var1']["sequences"][('PV_rooftop_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var1']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var1']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var1']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var1']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var1']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var1']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var1']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var1']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var1']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var1']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var1']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var1']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var1']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_1 = ee_erzeugung_1/sum_load



ee_erzeugung_2 = (res_Elec['var2']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var2']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var2']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var2']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var2']["sequences"][('PV_rooftop_north', 'Electricity'), 'flow'].sum()+
res_Elec['var2']["sequences"][('PV_rooftop_east', 'Electricity'), 'flow'].sum()+
res_Elec['var2']["sequences"][('PV_rooftop_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var2']["sequences"][('PV_rooftop_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var2']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var2']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var2']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var2']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var2']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var2']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var2']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var2']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var2']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var2']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var2']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var2']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var2']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_2 = ee_erzeugung_2/sum_load


ee_erzeugung_3 = (res_Elec['var3']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var3']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var3']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var3']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var3']["sequences"][('PV_rooftop_north', 'Electricity'), 'flow'].sum()+
res_Elec['var3']["sequences"][('PV_rooftop_east', 'Electricity'), 'flow'].sum()+
res_Elec['var3']["sequences"][('PV_rooftop_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var3']["sequences"][('PV_rooftop_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var3']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var3']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var3']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var3']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var3']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var3']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var3']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var3']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var3']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var3']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var3']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var3']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var3']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_3 = ee_erzeugung_3/sum_load



ee_erzeugung_4 = (res_Elec['var4']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var4']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var4']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var4']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var4']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var4']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var4']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var4']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var4']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var4']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var4']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var4']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var4']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var4']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var4']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var4']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var4']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_4 = ee_erzeugung_4/sum_load




ee_erzeugung_5 = (res_Elec['var5']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var5']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var5']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var5']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var5']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var5']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var5']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var5']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var5']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var5']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var5']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var5']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var5']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var5']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var5']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var5']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var5']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_5 = ee_erzeugung_5/sum_load



ee_erzeugung_6 = (res_Elec['var6']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var6']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var6']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var6']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var6']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var6']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var6']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var6']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var6']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var6']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var6']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var6']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var6']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var6']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var6']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var6']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var6']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_6 = ee_erzeugung_6/sum_load


ee_erzeugung_7 = (res_Elec['var7']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var7']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var7']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var7']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var7']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var7']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var7']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var7']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var7']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var7']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var7']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var7']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var7']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var7']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var7']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var7']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var7']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_7 = ee_erzeugung_7/sum_load


ee_erzeugung_8 = (res_Elec['var8']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var8']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var8']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var8']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var8']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var8']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var8']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var8']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var8']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var8']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var8']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var8']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var8']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var8']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var8']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var8']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var8']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_8 = ee_erzeugung_8/sum_load


ee_erzeugung_9 = (res_Elec['var9']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var9']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var9']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var9']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var9']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var9']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var9']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var9']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var9']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var9']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var9']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var9']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var9']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var9']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var9']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var9']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var9']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_9 = ee_erzeugung_9/sum_load


ee_erzeugung_10 = (res_Elec['var10']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var10']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var10']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var10']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var10']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+

res_dis_heat['var10']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var10']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var10']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var10']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var10']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var10']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var10']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var10']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var10']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var10']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var10']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var10']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_10 = ee_erzeugung_10/sum_load


ee_erzeugung_11 = (res_Elec['var11']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Elec['var11']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Elec['var11']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var11']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Elec['var11']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+
res_Elec['var11']["sequences"][('Wind_east', 'Electricity'), 'flow'].sum()+
res_Elec['var11']["sequences"][('Wind_middle', 'Electricity'), 'flow'].sum()+
res_Elec['var11']["sequences"][('Wind_swest', 'Electricity'), 'flow'].sum()+

res_dis_heat['var11']["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Elec['var11']["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas['var11']["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas['var11']["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Elec['var11']["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat['var11']["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat['var11']["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Elec['var11']["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat['var11']["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Elec['var11']["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel['var11']["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel['var11']["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

bilanz_11 = ee_erzeugung_11/sum_load


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([bilanz_1,
    
    bilanz_2, bilanz_3, bilanz_4, bilanz_5, bilanz_6, bilanz_7, bilanz_8,
    bilanz_9, bilanz_10, bilanz_11
              
              ])

plt.ylabel('')
plt.bar(x, y, label='Bilanziell erneuerbar')
plt.legend(fontsize = 20)
plt.show()
