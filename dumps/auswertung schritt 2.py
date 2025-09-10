# -*- coding: utf-8 -*-
"""
Created on Thu Jul 24 12:06:49 2025

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
    "1/1/2050", # change year
    periods=number_of_time_steps, freq="h"
)


my_path = os.path.abspath(os.path.dirname(__file__))

colors = seaborn.color_palette("bright", 30)
palette = seaborn.color_palette(cc.glasbey, n_colors=30)

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
res_Pumped_hydro_storage_bestand = {}


for x in range(0, 11):
    energysystem = solph.EnergySystem()
    energysystem.restore(dpath='2045_BS0006/', 
                         filename='BS_2045_BS0006_Wind_P'+str(x)+'0.dump')
    
    results = energysystem.results["main"]
    
    dict_costs_[f'var{x+1}'] = cost_calculation_for_esm(energysystem, results)
    dict_costs_storages[f'var{x+1}'] = cost_calculation_for_esm_storage(energysystem,
                                                                        results)
    
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
    
    res_Pumped_hydro_storage_bestand[f'var{x+1}'] = solph.views.node(results, 
                                                                     "Pumped_hydro_storage_bestand")
     
     
#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["00", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"])

y = np.array([(res_Elec['var1']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var1']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var1']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var1']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var2']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var2']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var2']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var2']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var3']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var3']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var3']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var3']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var4']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var4']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var4']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var4']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var5']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var5']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var5']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var5']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var6']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var6']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var6']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var6']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var7']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var7']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var7']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var7']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var8']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var8']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var8']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var8']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var9']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var9']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var9']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var9']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var10']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var10']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var10']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var10']["scalars"][('PV_open_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var11']["scalars"][('PV_open_north', 'Electricity'), 'invest']+
              res_Elec['var11']["scalars"][('PV_open_east', 'Electricity'), 'invest']+
              res_Elec['var11']["scalars"][('PV_open_middle', 'Electricity'), 'invest']+
              res_Elec['var11']["scalars"][('PV_open_swest', 'Electricity'), 'invest'])
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='PV')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)


combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='PV open', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["00", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"])

y = np.array([(res_Elec['var1']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var1']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var1']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var1']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var2']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var2']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var2']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var2']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var3']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var3']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var3']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var3']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var4']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var4']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var4']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var4']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var5']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var5']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var5']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var5']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var6']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var6']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var6']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var6']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var7']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var7']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var7']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var7']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var8']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var8']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var8']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var8']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var9']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var9']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var9']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var9']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var10']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var10']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var10']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var10']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest']),
              
              (res_Elec['var11']["scalars"][('PV_rooftop_north', 'Electricity'), 'invest']+
              res_Elec['var11']["scalars"][('PV_rooftop_east', 'Electricity'), 'invest']+
              res_Elec['var11']["scalars"][('PV_rooftop_middle', 'Electricity'), 'invest']+
              res_Elec['var11']["scalars"][('PV_rooftop_swest', 'Electricity'), 'invest'])
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='PV rooftop')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='PV rooftop', index=False)


#%%

# fig, ax = plt.subplots(figsize=(19.1, 10.5))

# x = np.array(["00", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"])

# y = np.array([(res_Elec['var1']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var1']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var1']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var1']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var2']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var2']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var2']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var2']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var3']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var3']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var3']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var3']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var4']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var4']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var4']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var4']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var5']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var5']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var5']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var5']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var6']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var6']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var6']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var6']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var7']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var7']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var7']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var7']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var8']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var8']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var8']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var8']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var9']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var9']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var9']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var9']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var10']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var10']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var10']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var10']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
              
#               (res_Elec['var11']["scalars"][('Wind_north', 'Electricity'), 'invest']+
#               res_Elec['var11']["scalars"][('Wind_east', 'Electricity'), 'invest']+
#               res_Elec['var11']["scalars"][('Wind_middle', 'Electricity'), 'invest']+
#               res_Elec['var11']["scalars"][('Wind_swest', 'Electricity'), 'invest']),
#               ])

# plt.ylabel('Leistung in MW')
# # plt.title("installierte Wind Leistung")
# plt.bar(x, y, label='Wind')
# plt.legend(fontsize = 20)
# plt.show()


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["00", "10", "20", "30", "40", "50", "60", "70", "80", "90", "100"])

y = np.array([(res_Elec['var1']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var2']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var3']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var4']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var5']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var6']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var7']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var8']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var9']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var10']["scalars"][('Wind_north', 'Electricity'), 'invest']),
              
              (res_Elec['var11']["scalars"][('Wind_north', 'Electricity'), 'invest'])
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='Wind')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Wind', index=False)

#%%

energiemenge_1=(
    (res_Elec['var1']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()
    # res_Elec['var1']["sequences"][('Wind_east', 'Electricity'), 'flow'].sum()+
    # res_Elec['var1']["sequences"][('Wind_middle', 'Electricity'), 'flow'].sum()+
    # res_Elec['var1']["sequences"][('Wind_swest', 'Electricity'), 'flow'].sum()
    )+
    
    (res_Elec['var1']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
    res_Elec['var1']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
    res_Elec['var1']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
    res_Elec['var1']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()))


energiemenge_11=(
    (res_Elec['var11']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum()
    # res_Elec['var11']["sequences"][('Wind_east', 'Electricity'), 'flow'].sum()+
    # res_Elec['var11']["sequences"][('Wind_middle', 'Electricity'), 'flow'].sum()+
    # res_Elec['var11']["sequences"][('Wind_swest', 'Electricity'), 'flow'].sum()
    )+
    
    (res_Elec['var11']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum()+
    res_Elec['var11']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum()+
    res_Elec['var11']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum()+
    res_Elec['var11']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum()))

print(energiemenge_1)
print(energiemenge_11)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_dis_heat['var1']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var2']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var3']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var4']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var5']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var6']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var7']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var8']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var9']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var10']["scalars"][('Biogas- BHKW', 'District heating'), 'invest']),
              
              (res_dis_heat['var11']["scalars"][('Biogas- BHKW', 'District heating'), 'invest'])
              ])

plt.ylabel('Leistung in MW th')
plt.bar(x, y, label='Biogas- BHKW')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Biogas- BHKW', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_Elec_hoes['var1']["sequences"][
    ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var2']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var3']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var4']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var5']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var6']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var7']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var8']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var9']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var10']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
    
    res_Elec_hoes['var11']["sequences"][
        ('Import_Electricity', 'Electricity_Hös'), 'flow'].sum(),
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Import_Electricity')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Import Electricity', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_battery['var1']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var2']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var3']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var4']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var5']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var6']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var7']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var8']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var9']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var10']["scalars"][('Battery', 'None'), 'invest'],
    
    res_battery['var11']["scalars"][('Battery', 'None'), 'invest'],
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Battery')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Battery', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_li_ion_battery['var1']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var2']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var3']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var4']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var5']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var6']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var7']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var8']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var9']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var10']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
    
    res_li_ion_battery['var11']["scalars"][('Li-Ion_Battery', 'None'), 'invest'],
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Li-Ion_Battery')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Li-Ion_Battery', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_Natrium_Battery['var1']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var2']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var3']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var4']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var5']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var6']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var7']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var8']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var9']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var10']["scalars"][('Natrium_Battery', 'None'), 'invest'],
    
    res_Natrium_Battery['var11']["scalars"][('Natrium_Battery', 'None'), 'invest'],
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Natrium_Battery')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Natrium Battery', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_Gas_storage['var1']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var2']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var3']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var4']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var5']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var6']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var7']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var8']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var9']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var10']["scalars"][('Gas_storage', 'None'), 'invest'],
    
    res_Gas_storage['var11']["scalars"][('Gas_storage', 'None'), 'invest'],
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Gas_storage')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Gas storage', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_H2_storage['var1']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var2']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var3']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var4']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var5']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var6']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var7']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var8']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var9']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var10']["scalars"][('H2_storage', 'None'), 'invest'],
    
    res_H2_storage['var11']["scalars"][('H2_storage', 'None'), 'invest'],
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='H2_storage')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='H2 Storage', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([
    res_Heat_storage_dist_heat['var1']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var2']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var3']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var4']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var5']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var6']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var7']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var8']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var9']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var10']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
    
    res_Heat_storage_dist_heat['var11']["scalars"][('Heat storage_dist_heat', 'None'), 'invest'],
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Heat storage_dist_heat')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Heat storage_dist_heat', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([
    res_Heat_storage_seasonal['var1']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var2']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var3']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var4']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var5']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var6']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var7']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var8']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var9']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var10']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
    
    res_Heat_storage_seasonal['var11']["scalars"][('Heat storage_seasonal', 'None'), 'invest'],
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Heat storage_seasonal')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Heat storage_seasonal', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_Pumped_hydro_storage['var1']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var2']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var3']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var4']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var5']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var6']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var7']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var8']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var9']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var10']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
    
    res_Pumped_hydro_storage['var11']["scalars"][('Pumped_hydro_storage', 'None'), 'invest'],
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Pumped_hydro_storage')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Pumped_hydro_storage', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_Elec['var1']["sequences"][
    ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var2']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var3']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var4']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var5']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var6']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var7']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var8']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var9']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var10']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
    
    res_Elec['var11']["sequences"][
        ('Electricity', 'Export_Electricity'), 'flow'].sum(),
              
              ])

plt.ylabel('MWh')
plt.bar(x, y, label='Export_Electricity')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Export_Electricity', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_h2['var1']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var2']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var3']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var4']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var5']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var6']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var7']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var8']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var9']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var10']["scalars"][('Electrolysis', 'Hydrogen'), 'invest']),
              
              (res_h2['var11']["scalars"][('Electrolysis', 'Hydrogen'), 'invest'])
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='Electrolysis')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Electrolysis', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_dis_heat['var1']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var2']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var3']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var4']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var5']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var6']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var7']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var8']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var9']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var10']["scalars"][('Electric boiler', 'District heating'), 'invest']),
              
              (res_dis_heat['var11']["scalars"][('Electric boiler', 'District heating'), 'invest'])
              ])

plt.ylabel('Leistung in MW th')
plt.bar(x, y, label='Electric boiler')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Electric boiler', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_dis_heat['var1']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var2']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var3']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var4']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var5']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var6']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var7']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var8']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var9']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var10']["scalars"][('Heatpump_air', 'District heating'), 'invest']),
              
              (res_dis_heat['var11']["scalars"][('Heatpump_air', 'District heating'), 'invest'])
              ])

plt.ylabel('Leistung in MW th')
plt.bar(x, y, label='Heatpump_air')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Heatpump_air', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_dis_heat['var1']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var2']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var3']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var4']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var5']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var6']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var7']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var8']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var9']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var10']["scalars"][('Heatpump_water', 'District heating'), 'invest']),
              
              (res_dis_heat['var11']["scalars"][('Heatpump_water', 'District heating'), 'invest'])
              ])

plt.ylabel('Leistung in MW th')
plt.bar(x, y, label='Heatpump_water')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Heatpump_water', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_dis_heat['var1']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var2']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var3']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var4']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var5']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var6']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var7']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var8']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var9']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var10']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var11']["scalars"][('Heatpump_recovery_heat', 'District heating'), 'invest'])
              ])

plt.ylabel('Leistung in MW th')
plt.bar(x, y, label='Heatpump_recovery_heat')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Heatpump_recovery', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_dis_heat['var1']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var2']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var3']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var4']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var5']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var6']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var7']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var8']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var9']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var10']["scalars"][('Biomasse_heat', 'District heating'), 'invest']),
              
              (res_dis_heat['var11']["scalars"][('Biomasse_heat', 'District heating'), 'invest'])
              ])

plt.ylabel('Leistung in MW th')
plt.bar(x, y, label='Biomasse_heat')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Biomasse_heat', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_Elec['var1']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var2']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var3']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var4']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var5']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var6']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var7']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var8']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var9']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var10']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest']),
              
              (res_Elec['var11']["scalars"][('Biomasse_elec_heat', 'Electricity'), 'invest'])
              ])

plt.ylabel('Leistung in MW el')
plt.bar(x, y, label='Biomasse_elec_heat')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Biomasse_elec_heat MWel', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_Elec['var1']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var2']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var3']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var4']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var5']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var6']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var7']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var8']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var9']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var10']["scalars"][('GuD', 'Electricity'), 'invest']),
              
              (res_Elec['var11']["scalars"][('GuD', 'Electricity'), 'invest'])
              ])

plt.ylabel('Leistung in MW el')
plt.bar(x, y, label='GuD')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='GuD', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_Elec['var1']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var2']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var3']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var4']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var5']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var6']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var7']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var8']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var9']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var10']["scalars"][('Biomasse_elec', 'Electricity'), 'invest']),
              
              (res_Elec['var11']["scalars"][('Biomasse_elec', 'Electricity'), 'invest'])
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='Biomasse_elec')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Biomasse_elec', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(dict_costs_['var1']["variable costs"]["sum variable costs"]
                + dict_costs_['var1']["profits"]["sum profits"]
               + dict_costs_['var1']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var1']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var2']["variable costs"]["sum variable costs"]
                + dict_costs_['var2']["profits"]["sum profits"]
               + dict_costs_['var2']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var2']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var3']["variable costs"]["sum variable costs"]
                + dict_costs_['var3']["profits"]["sum profits"]
               + dict_costs_['var3']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var3']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var4']["variable costs"]["sum variable costs"]
                + dict_costs_['var4']["profits"]["sum profits"]
               + dict_costs_['var4']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var4']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var5']["variable costs"]["sum variable costs"] 
                + dict_costs_['var5']["profits"]["sum profits"]
               + dict_costs_['var5']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var5']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var6']["variable costs"]["sum variable costs"] 
                + dict_costs_['var6']["profits"]["sum profits"]
               + dict_costs_['var6']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var6']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var7']["variable costs"]["sum variable costs"]
                + dict_costs_['var7']["profits"]["sum profits"]
               + dict_costs_['var7']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var7']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var8']["variable costs"]["sum variable costs"]
                + dict_costs_['var8']["profits"]["sum profits"]
               + dict_costs_['var8']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var8']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var9']["variable costs"]["sum variable costs"]
                + dict_costs_['var9']["profits"]["sum profits"]
               + dict_costs_['var9']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var9']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var10']["variable costs"]["sum variable costs"]
                + dict_costs_['var10']["profits"]["sum profits"]
               + dict_costs_['var10']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var10']["investment costs"][
                   "sum investment costs storages"]),
              
              (dict_costs_['var11']["variable costs"]["sum variable costs"] 
                + dict_costs_['var11']["profits"]["sum profits"]
               + dict_costs_['var11']["investment costs"]["sum investment costs"]
               + dict_costs_storages['var11']["investment costs"][
                   "sum investment costs storages"]),
              ])

plt.ylabel('EUR')
plt.bar(x, y, label='Gesamtkosten')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Gesamtkosten', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_gas['var1']["scalars"][
    ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var2']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var3']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var4']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var5']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var6']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var7']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var8']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var9']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var10']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
    
    res_gas['var11']["scalars"][
        ('Biogas_feedin_existing', 'Gas'), 'invest'].sum(),
              
              ])

plt.ylabel('MW')
plt.bar(x, y, label='Biogas feedin existing')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Bio feedin existing', index=False)

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_gas['var1']["scalars"][
    ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var2']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var3']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var4']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var5']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var6']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var7']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var8']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var9']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var10']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
    
    res_gas['var11']["scalars"][
        ('Biogas_feedin_new', 'Gas'), 'invest'].sum(),
              
              ])

plt.ylabel('MW')
plt.bar(x, y, label='Biogas feedin new')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Bio feedin new', index=False)


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_gas['var11']['sequences'].plot(ax=ax, kind='line',
                                   drawstyle='steps-post', 
                                   color=palette, linewidth=2.5)
plt.legend(res_gas['var11']['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
fig.subplots_adjust(top=0.8)
plt.title('Gasbus')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_gas['var11']['sequences'].plot(ax=ax, kind='line',
                                   drawstyle='steps-post', 
                                   color=palette, linewidth=2.5)
plt.legend(res_gas['var11']['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
fig.subplots_adjust(top=0.8)
plt.title('Gasbus')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_h2['var11']['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_h2['var11']['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
fig.subplots_adjust(top=0.8)
plt.title('Wasserstoffbus')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_Pumped_hydro_storage_bestand['var11']['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_Pumped_hydro_storage_bestand['var11']['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_Elec['var11']['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_Elec['var11']['sequences'].keys(), 
           loc='upper center', prop={'size': 8},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
# fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_dis_heat['var11']['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_dis_heat['var11']['sequences'].keys(), 
           loc='upper center', prop={'size': 8},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
# fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

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
        res_Elec['var11']["sequences"][('PV_open_north', 'Electricity'), 'flow'].sum(),
        res_Elec['var11']["sequences"][('PV_open_east', 'Electricity'), 'flow'].sum(),
        res_Elec['var11']["sequences"][('PV_open_middle', 'Electricity'), 'flow'].sum(),
        res_Elec['var11']["sequences"][('PV_open_swest', 'Electricity'), 'flow'].sum(),
        
        res_Elec['var11']["sequences"][('Wind_north', 'Electricity'), 'flow'].sum(),
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
            # fontsize=fontsizenr,
           ha='right',
           rotation=45)

plt.grid(axis = 'y')
plt.show()
plt.ylabel('MWh')

#%%

fig = plt.figure(figsize=(19.1, 10.5))
plt.plot(date_time_index,
         res_Heat_storage_dist_heat['var11']['sequences'][
             ('Heat storage_dist_heat','None'),'storage_content'][:8760], 
         label='District Heat Storage')

plt.plot(date_time_index,
          res_Heat_storage_seasonal['var11']['sequences'][
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
         res_Gas_storage['var11']['sequences'][
             ('Gas_storage','None'),'storage_content'][:8760], 
         label='Gas_storage')

plt.plot(date_time_index,
          res_H2_storage['var11']['sequences'][
              ('H2_storage','None'),'storage_content'][:8760], 
          label='H2_storage')
# plt.ylim(-3,103)
plt.grid()
plt.legend()
plt.ylabel('Speicherfüllstand in MWh')
plt.xlabel('Zeit')


#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_oil_fuel['var1']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var2']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var3']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var4']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var5']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var6']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var7']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var8']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var9']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var10']["scalars"][('BtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var11']["scalars"][('BtL', 'Oil_fuel'), 'invest'])
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='BtL')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='BtL', index=False)
    
#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_Elec['var1']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var2']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var3']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var4']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var5']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var6']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var7']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var8']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var9']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var10']["scalars"][('Fuelcell', 'Electricity'), 'invest']),
              
              (res_Elec['var11']["scalars"][('Fuelcell', 'Electricity'), 'invest'])
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='Fuelcell')
plt.legend(fontsize = 20)
plt.show()

df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Fuelcell', index=False)
    
#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([(res_oil_fuel['var1']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var2']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var3']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var4']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var5']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var6']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var7']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var8']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var9']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var10']["scalars"][('PtL', 'Oil_fuel'), 'invest']),
              
              (res_oil_fuel['var11']["scalars"][('PtL', 'Oil_fuel'), 'invest'])
              ])

plt.ylabel('Leistung in MW')
plt.bar(x, y, label='PtL')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='PtL', index=False)
    
#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))

x = np.array(["kein Wind", "10", "20", "30", "40", "50", "60", "70", "80", "90", "viel Wind"])

y = np.array([res_gas['var1']["scalars"][
    ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var2']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var3']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var4']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var5']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var6']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var7']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var8']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var9']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var10']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
    
    res_gas['var11']["scalars"][
        ('Methanisation', 'Gas'), 'invest'].sum(),
              
              ])

plt.ylabel('MW')
plt.bar(x, y, label='Methanisation')
plt.legend(fontsize = 20)
plt.show()


df1 = pd.DataFrame(x)
df2 = pd.DataFrame(y)
combined = pd.concat([df1, df2], axis=1)

with pd.ExcelWriter('Auswertung Windpotential neu.xlsx', engine='openpyxl', mode='a') as writer:
    pd.DataFrame(combined).to_excel(writer, sheet_name='Methanisation', index=False)
    
#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_gas['var1']['sequences'].plot(ax=ax, kind='line',
                                   drawstyle='steps-post', 
                                   color=palette, linewidth=2.5)
plt.legend(res_gas['var1']['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
fig.subplots_adjust(top=0.8)
plt.title('Gasbus')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_h2['var1']['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_h2['var1']['sequences'].keys(), 
           loc='upper center', prop={'size': 18},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
fig.subplots_adjust(top=0.8)
plt.title('Wasserstoffbus')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_Elec['var1']['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_Elec['var1']['sequences'].keys(), 
           loc='upper center', prop={'size': 8},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
# fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()

#%%

fig, ax = plt.subplots(figsize=(19.1, 10.5))
res_dis_heat['var1']['sequences'].plot(ax=ax, kind='line',
                                 drawstyle='steps-post', 
                                 color=palette, linewidth=2.5)
plt.legend(res_dis_heat['var1']['sequences'].keys(), 
           loc='upper center', prop={'size': 8},
           bbox_to_anchor=(0.5, 1.25), ncol=2)
# fig.subplots_adjust(top=0.8)
plt.title('')
plt.ylabel('Leistung in MW')
plt.grid()
plt.show()
