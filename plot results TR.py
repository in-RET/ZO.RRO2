# -*- coding: utf-8 -*-
"""
Created on Wed Jul 23 13:29:43 2025

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

name = "2045_BS0006"

'''Plot default settings'''
fontsizenr=20
# dpi_nr = 600
# plt.rc('xtick', labelsize=fontsizenr) 
# plt.rc('legend', fontsize=fontsizenr-2) 
# plt.rc('ytick', labelsize=fontsizenr) 
# plt.rc('font', size=fontsizenr) 
# plt.rc('axes', titlesize=fontsizenr, labelsize=fontsizenr, axisbelow=True) # fontsize of the axes title #axisbelow=Netz hinter den Säulen
# # plt.rc('axes', labelsize=fontsizenr)    # fontsize of the x and y labels
# plt.rcParams.update({'axes.titlesize': fontsizenr})
# plt.rcParams.update({'font.size': fontsizenr})
# plt.rcParams.update({'axes.titlepad': 10})
# plt.rcParams['font.family'] = ['sans-serif']
# plt.rcParams['font.sans-serif'] = ['News Gothic MT']

# cm = 1/2.54  # centimeters in inche
# m=100*cm
# mm=10**(-3)*m
# plt.rcParams.update({'figure.subplot.right':0.975})
# plt.rcParams.update({'figure.subplot.left':0.3})
# plt.rcParams.update({'figure.subplot.top':0.977})
# plt.rcParams.update({'figure.subplot.bottom':0.35})

number_of_time_steps = 8760
date_time_index = pd.date_range(
    "1/1/2045", # change year
    periods=number_of_time_steps, freq="h"
)


my_path = os.path.abspath(os.path.dirname(__file__))

colors = seaborn.color_palette("bright", 30)
palette = seaborn.color_palette(cc.glasbey, n_colors=30)

energysystem = solph.EnergySystem()
energysystem.restore(dpath='dumps/'+ name+ '/', 
                     filename='BS_2045_BS0006_Original.dump')

results = energysystem.results["main"]

res_Electricity = solph.views.node(results, "Electricity")
res_Pumped_hydro_storage_bestand = solph.views.node(results, 
                                                    "Pumped_hydro_storage_bestand")
res_Pumped_hydro_storage = solph.views.node(results, "Pumped_hydro_storage")
res_Heat_storage_seasonal = solph.views.node(results, "Heat storage_seasonal")
res_Heat_storage_dist_heat = solph.views.node(results, "Heat storage_dist_heat")
res_Elec_hoes = solph.views.node(results, "Electricity_Hös")

res_dis_heat = solph.views.node(results, "District heating")

res_battery = solph.views.node(results, "Battery")
res_li_ion_battery = solph.views.node(results, "Li-Ion_Battery")
res_Natrium_Battery = solph.views.node(results, "Natrium_Battery")

res_Gas_storage = solph.views.node(results, "Gas_storage")
res_H2_storage = solph.views.node(results, "H2_storage")

res_h2 = solph.views.node(results, "Hydrogen")
res_gas = solph.views.node(results, "Gas")
res_oil_fuel = solph.views.node(results, "Oil_fuel")
res_solid_fuel = solph.views.node(results, "Solidfuel")


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

text = ['PV_open_north',
        'PV_open_east',
        'PV_open_middle',
        'PV_open_swest',
        
        'Wind_north',
        # 'Wind_east',
        # 'Wind_middle',
        # 'Wind_swest'
        
        ]
data = [
        res_Electricity["scalars"][('PV_open_north', 'Electricity'), 'invest'],
        res_Electricity["scalars"][('PV_open_east', 'Electricity'), 'invest'],
        res_Electricity["scalars"][('PV_open_middle', 'Electricity'), 'invest'],
        res_Electricity["scalars"][('PV_open_swest', 'Electricity'), 'invest'],
        
        res_Electricity["scalars"][('Wind_north', 'Electricity'), 'invest'],
        # res_Electricity["scalars"][('Wind_east', 'Electricity'), 'invest'],
        # res_Electricity["scalars"][('Wind_middle', 'Electricity'), 'invest'],
        # res_Electricity["scalars"][('Wind_swest', 'Electricity'), 'invest'],
                 ]
bars = plt.bar(text, data, color=['#2E74B5'] #"So gehts"-blau
)
xlocs, xlabs = plt.xticks()               
for i, v in enumerate(data):
    plt.text(xlocs[i] -0.25, v + 0.1, str(round(v)))
    
plt.xticks(
            # xticks_pos,
            fontsize=fontsizenr,
           ha='right',
           rotation=45)

plt.grid(axis = 'y')
plt.show()
plt.ylabel('Leistung in MW')



fig, ax = plt.subplots(figsize=(19.1, 10.5))

text = ['PV_open_north',
        'PV_open_east',
        'PV_open_middle',
        'PV_open_swest',
        
        'Wind_north',
        # 'Wind_east',
        # 'Wind_middle',
        # 'Wind_swest'
        
        ]
data = [
        res_Electricity["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum(),
        res_Electricity["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum(),
        res_Electricity["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum(),
        res_Electricity["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum(),
        
        res_Electricity["sequences"][('Wind_north', 'Electricity'), 'flow'].sum(),
        # res_Electricity["sequences"][('Wind_east', 'Electricity'), 'flow'].sum(),
        # res_Electricity["sequences"][('Wind_middle', 'Electricity'), 'flow'].sum(),
        # res_Electricity["sequences"][('Wind_swest', 'Electricity'), 'flow'].sum(),
                 ]
bars = plt.bar(text, data, color=['#2E74B5'] #"So gehts"-blau
)
xlocs, xlabs = plt.xticks()               
for i, v in enumerate(data):
    plt.text(xlocs[i] -0.25, v + 0.1, str(round(v)))
    
plt.xticks(
            # xticks_pos,
            fontsize=fontsizenr,
           ha='right',
           rotation=45)

plt.grid(axis = 'y')
plt.show()
plt.ylabel('MWh')


#%%

# (res_Electricity["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

# res_Electricity["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('Wind_east', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('Wind_middle', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('Wind_swest', 'Electricity'), 'flow'].sum())

#%%

fig = plt.figure(figsize=(19.1, 10.5))
plt.plot(date_time_index,
         res_Heat_storage_dist_heat['sequences'][
             ('Heat storage_dist_heat','None'),'storage_content'][:8760], 
         label='District Heat Storage')

plt.plot(date_time_index,
          res_Heat_storage_seasonal['sequences'][
              ('Heat storage_seasonal','None'),'storage_content'][:8760], 
          label='Seasonal Heat Storage')
# plt.ylim(-3,103)
plt.grid()
plt.legend()
plt.ylabel('Speicherfüllstand in MWh')
plt.xlabel('Zeit')

#%%

fig = plt.figure(figsize=(19.1, 10.5))
plt.plot(date_time_index,
         res_Pumped_hydro_storage['sequences'][
             ('Pumped_hydro_storage','None'),'storage_content'][:8760], 
         label='Pumped Hydro Storage')

plt.plot(date_time_index,
          res_Pumped_hydro_storage_bestand['sequences'][
              ('Pumped_hydro_storage_bestand','None'),'storage_content'][:8760], 
          label='Pumped Hydro Storage Bestand')
# plt.ylim(-3,103)
plt.grid()
plt.legend()
plt.ylabel('Speicherfüllstand in MWh')
plt.xlabel('Zeit')

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["Import_Electricity", "Export_Electricity"
              ])

y = np.array([res_Elec_hoes["sequences"][
    ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Electricity["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
              
              ])

plt.ylabel('MWh')
plt.bar(x, y)
plt.legend(fontsize = 20)
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["GuD", "Biomasse_elec", "Biomasse_elec_heat"])

y = np.array([res_Electricity["scalars"][('GuD', 'Electricity'), 'invest'],
               
              res_Electricity["scalars"][
                  ('Biomasse_elec', 'Electricity'), 'invest'],
              
              res_Electricity["scalars"][
                  ('Biomasse_elec_heat', 'Electricity'), 'invest'],
              
              ])

plt.ylabel('MW el')
plt.bar(x, y)
plt.legend(fontsize = 20)
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["Biogas BHKW", "Biomasse Heat", "Electric boiler",
              "Heatpump air", "Heatpump_water", "Heatpump_recovery_heat"])

y = np.array([
               res_dis_heat["scalars"][
                   ('Biogas- BHKW', 'District heating'), 'invest'],
               
               res_dis_heat["scalars"][
                   ('Biomasse_heat', 'District heating'), 'invest'],
               
               res_dis_heat["scalars"][
                   ('Electric boiler', 'District heating'), 'invest'],
               
               res_dis_heat["scalars"][
                   ('Heatpump_air', 'District heating'), 'invest'],
               
               res_dis_heat["scalars"][
                   ('Heatpump_water', 'District heating'), 'invest'],
               
               res_dis_heat["scalars"][
                   ('Heatpump_recovery_heat', 'District heating'), 'invest']
    
    ])

plt.ylabel('MW th')
plt.bar(x, y)
plt.legend(fontsize = 20)
plt.show()


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["Biogas_feedin_existing", "Biogas_feedin_new"])

y = np.array([
               
    res_gas["scalars"][('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas["scalars"][('Biogas_feedin_new', 'Gas'), 'invest'].sum()
              
              ])

plt.ylabel('MW')
plt.bar(x, y)
plt.legend(fontsize = 20)
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["Battery", "Li-Ion_Battery", "Natrium_Battery"])

y = np.array([
               
    res_battery["scalars"][('Battery', 'None'), 'invest'],
    
    res_li_ion_battery["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery["scalars"][('Natrium_Battery', 'None'), 'invest']
              
              ])

plt.ylabel('MWh')
plt.bar(x, y)
plt.legend(fontsize = 20)
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["Electrolysis"])

y = np.array([res_h2["scalars"][('Electrolysis', 'Hydrogen'), 'invest'],
              ])

plt.ylabel('MW')
plt.bar(x, y)
plt.legend(fontsize = 20)
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_h2['sequences'].plot(ax=ax, kind='line',
                               drawstyle='steps-post', color=palette, linewidth=2.5)
plt.legend(res_h2['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2, fontsize=15)
fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_gas['sequences'].plot(ax=ax, kind='line',
                               drawstyle='steps-post', color=palette, linewidth=2.5)
plt.legend(res_gas['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2, fontsize=15)
fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

emissionen_erdgas = (sum(
    res_gas['sequences'][('Import_Gas','Gas'),'flow'][:8760])
    * 202)

#%%

fig = plt.figure(figsize=(19.1, 10.5))
plt.plot(date_time_index,
         res_Gas_storage['sequences'][
             ('Gas_storage','None'),'storage_content'][:8760], 
         label='Gas_storage')

plt.plot(date_time_index,
          res_H2_storage['sequences'][
              ('H2_storage','None'),'storage_content'][:8760], 
          label='H2_storage')
# plt.ylim(-3,103)
plt.grid()
plt.legend()
plt.ylabel('Speicherfüllstand in MWh')
plt.xlabel('Zeit')

#%%

def cost_calculation_for_esm(energysystem, results):
    sum_investcosts=0
    sum_variablecosts=0
    sum_erloese=0
    
    dict_costs = {"investment costs":{},
                  "variable costs": {},
                  "profits": {}
                  }

    
    for key, value in energysystem.node.items():
        for item in energysystem.node[key].outputs.data.values():
            if type(energysystem.node[key]) is not solph.components.GenericStorage:
                if item.investment: 
                    # Speicher wird zweimal aufgeführt, weil invest nicht im Flow() steht 
                    # jetzt nur noch einmal 
                    investcosts = (item.investment.ep_costs[0] * 
                                   solph.views.node(results, item.input)["scalars"].iloc[0])
                    if (item.investment.offset and 
                        solph.views.node(results, item.input)["scalars"].iloc[0] > 0):
                        investcosts += item.investment.offset[0]
                    dict_costs["investment costs"].update( 
                        {str(item.input) + ' to ' + str(item.output) : investcosts} )
                    sum_investcosts += investcosts
                
            if len(item.variable_costs) != 0:
                    if not all(v == 0 for v in item.variable_costs):
                        if (all(val <= 0 for val in item.variable_costs) 
                            # or 
                            # sum(i > 0 for i in item.variable_costs) <= 10
                            ):
                            erloese = np.multiply(
                                np.array(solph.views.node(results, 
                                                          item.output)["sequences"]
                                          [(item.input, item.output), 'flow'][:8759]),
                                np.array(item.variable_costs[:8759])
                                )
                            dict_costs["profits"].update( 
                                {str(item.input) + ' to ' + str(item.output) : sum(erloese)} )
                            sum_erloese += sum(erloese)
                            
                        else:
                            line = np.multiply(
                                np.array(solph.views.node(results, 
                                                          item.output)["sequences"]
                                          [(item.input, item.output), 'flow'])[:8759],
                                np.array(item.variable_costs)[:8759]
                                )
                            dict_costs["variable costs"].update( 
                                {str(item.input) + ' to ' + str(item.output) : sum(line)} )
                            sum_variablecosts += sum(line)
                            
    
    dict_costs["profits"].update( {"sum profits" : sum_erloese} )
    dict_costs["variable costs"].update( {"sum variable costs" : sum_variablecosts} )
    dict_costs["investment costs"].update( {"sum investment costs" : sum_investcosts} )
    return dict_costs


dict_costs_ = cost_calculation_for_esm(energysystem, results)

df_costs = pd.DataFrame(dict_costs_)

#%%

fig = plt.figure(figsize=(19.1, 10.5))
df_costs["variable costs"].dropna().plot(kind="barh", stacked=True, 
                                         title='variable Kosten',
                                         figsize=(19, 11), fontsize=15, color=palette)
# plt.legend(fontsize = 20)
plt.xlabel('Kosten in €/a')
plt.show()

#%%

df_costs["investment costs"].dropna().plot(kind="barh", stacked=True, 
                                            title='Investionskosten',
                                            fontsize=20, color=palette)
# plt.legend(fontsize = 20)
plt.xlabel('Kosten in €/a')
plt.show()

#%%

fig = plt.figure(figsize=(19.1, 10.5))
df_costs["profits"].dropna().plot(kind="barh", stacked=True, 
                                  title='Erlöse aus Stromeinspeisung',
                                  figsize=(19, 11), fontsize=15, color=palette)
# plt.legend(fontsize = 20)
plt.xlabel('Kosten in €/a')
plt.show()


#%%

def cost_calculation_for_esm_storage(energysystem, results):
    sum_investcosts=0
    # sum_variablecosts=0
    
    dict_costs = {"investment costs":{},
                  # "variable costs": {}
                  }

    
    for key, value in energysystem.node.items():
        for item in energysystem.node[key].outputs.data.values():
            if type(energysystem.node[key]) is solph.components.GenericStorage:
                if item.investment:
                    # print(energysystem.node[key], 
                          # energysystem.node[key].investment.ep_costs[0],
                          # solph.views.node(results, item.input)["scalars"].iloc[0])

                    # print(key, energysystem.node[key].investment.ep_costs[0])
                    investcosts = (
                        energysystem.node[key].investment.ep_costs[0] * 
                        solph.views.node(results, item.input)["scalars"].iloc[4] #init_content
                         )
                    
                    dict_costs["investment costs"].update( 
                        {str(item.input) + ' to ' + str(item.output) : investcosts} )
                    sum_investcosts += investcosts
                            
    
    # dict_costs["variable costs"].update( {"sum variable costs" : sum_variablecosts} )
    dict_costs["investment costs"].update( 
        {"sum investment costs storages" : sum_investcosts} )
    return dict_costs

dict_costs_storages = cost_calculation_for_esm_storage(energysystem, results)

df_costs_storages = pd.DataFrame(dict_costs_storages)

#%%

gesamtkosten = (df_costs["variable costs"]["sum variable costs"] 
                + df_costs["investment costs"]["sum investment costs"]
                + df_costs["profits"]["sum profits"]
                + df_costs_storages["investment costs"][
                    "sum investment costs storages"]
                )

import locale
locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
print(locale.format_string('%.2f', gesamtkosten, grouping=True))

#%%

# energiemenge_1=(
#     (res_Electricity["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+
#     res_Electricity["sequences"][('Wind_east', 'Electricity'), 'flow'].sum()+
#     res_Electricity["sequences"][('Wind_middle', 'Electricity'), 'flow'].sum()+
#     res_Electricity["sequences"][('Wind_swest', 'Electricity'), 'flow'].sum())+
    
#     (res_Electricity["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
#     res_Electricity["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
#     res_Electricity["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
#     res_Electricity["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()))

# print(energiemenge_1)


#%%

sum_load = (res_gas["sequences"][
    ('Gas', 'Gas_demand_total'), 'flow'].sum() + 

res_Electricity["sequences"][
    ('Electricity', 'Electricity_demand_total'), 'flow'].sum() +

res_oil_fuel["sequences"][
    ('Oil_fuel', 'Oil & fuel_demand_total'), 'flow'].sum() +

res_dis_heat["sequences"][
    ('District heating', 'Heat_demand_total'), 'flow'].sum() +

res_h2["sequences"][
    ('Hydrogen', 'Hydrogen_demand_total'), 'flow'].sum()
)

bilanz = sum_load * 1

ee_erzeugung = (res_Electricity["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
res_Electricity["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
res_Electricity["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
res_Electricity["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()+

res_Electricity["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('Wind_east', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('Wind_middle', 'Electricity'), 'flow'].sum()+
# res_Electricity["sequences"][('Wind_swest', 'Electricity'), 'flow'].sum()+

res_dis_heat["sequences"][('Biogas- BHKW', 'District heating'), 'flow'].sum()+
res_Electricity["sequences"][('Biogas- BHKW', 'Electricity'), 'flow'].sum()+

res_gas["sequences"][
    ('Biogas_feedin_new', 'Gas'), 'flow'].sum()+
res_gas["sequences"][
    ('Biogas_feedin_existing', 'Gas'), 'flow'].sum()+

res_Electricity["sequences"][('Hydro power plant', 'Electricity'), 'flow'].sum()+

res_dis_heat["sequences"][('ST', 'District heating'), 'flow'].sum()+

res_dis_heat["sequences"][('Biomasse_heat', 'District heating'), 'flow'].sum()+
res_Electricity["sequences"][('Biomasse_elec', 'Electricity'), 'flow'].sum()+

res_dis_heat["sequences"][('Biomasse_elec_heat', 'District heating'), 'flow'].sum()+
res_Electricity["sequences"][('Biomasse_elec_heat', 'Electricity'), 'flow'].sum()+

res_solid_fuel["sequences"][('BioTransformer', 'Solidfuel'), 'flow'].sum()+
res_oil_fuel["sequences"][('BtL', 'Oil_fuel'), 'flow'].sum()
)

print(ee_erzeugung/sum_load)

#%%

(res_Electricity["scalars"][('PV_rooftop_north', 'Electricity'), 'invest'].sum()+
res_Electricity["scalars"][('PV_rooftop_east', 'Electricity'), 'invest'].sum()+
res_Electricity["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest'].sum()+
res_Electricity["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest'].sum())


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_Pumped_hydro_storage_bestand['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_Pumped_hydro_storage_bestand['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_Electricity['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_Electricity['sequences'].keys(), 
           loc='upper center', prop={'size': 8},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
# fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_dis_heat['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_dis_heat['sequences'].keys(), 
           loc='best', prop={'size': 8},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
# fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["BtL", "Fuelcell", "PtL", "Methanisation"])

y = np.array([(res_oil_fuel["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_Electricity["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_oil_fuel["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              res_gas["scalars"][
                  ('Methanisation', 'Gas'), 'invest'].sum()
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='')
plt.legend(fontsize = 20)
plt.show()
