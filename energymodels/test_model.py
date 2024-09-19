# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 11:18:34 2024

@author: rbala
"""

import os

import pandas as pd
from oemof import network, solph
from oemof.tools import economics

from src.preprocessing.create_input_dataframe import createDataFrames
from src.preprocessing.files import read_input_files
from src.preprocessing.conversion import investment_parameter


YEAR = 2030
Model_ID = 'BS0001'
sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)




profile = []             # Sorting only the timeseies from the list of all files in the sequences folder
for i in sequences: 
    if i.endswith('profile'):
        profile.append(i)

load_profile_nom = {}
for name in profile:
    load_profile_nom[name]= sequences[name]/sequences[name].sum() # Normalising the timeseries to scale the profile to respective energy demand.

sector = ['electricity', 'gas', 'dist_heating', 'biomass', 'oil&fuel', 'material_usage_gas', 'material_usage_oil_fuel']
region = ['north', 'middle', 'east', 'swest']
demand_profile_dict={}
#%%

for s in sector:
    demand_profile_dict[s] = {}
    for r in region:
           
        if s == 'electricity':
                # Load profile * (total demand * (percentage share/100)/ EER) 
            demand_profile_dict[s][r]= ((load_profile_nom['other_demand_profile']['G3'] * (float(scalars['Demand_Industry_' + r + '_b']['Strom_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Strom_' + str(YEAR)]['Elektrogeraete'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Elektrogeraete'])))+
                                            (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Heizstab'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                            (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                            (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                            (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Heizstab'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                            (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                            (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                            (load_profile_nom['Electricity_household_demand_profile'][r +'_'+ str(YEAR)] *(float(scalars['Demand_Household_' + r + '_b']['Strom_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Strom_' + str(YEAR)]['Elektrogeraete'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Elektrogeraete'])))+
                                            (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Heizstab'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                            (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                            (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                            (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_Household_' + r + '_b']['Klima- und Prozesskaelte_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Kompressionskaelte'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Kompressionskaelte'])))+
                                            (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_Household_' + r + '_b']['Klima- und Prozesskaelte_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Sorptionskaelte'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Sorptionskaelte'])))+
                                            (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_Industry_' + r + '_b']['Klima- und Prozesskaelte_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Kompressionskaelte'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Kompressionskaelte'])))
                                            )*1000000 # TWh to MWh noch GHD und Verkehr
        elif s == 'gas':
            if YEAR == 2030:
                demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                           (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                              (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))
                                              *1000000)
            else:
                demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                           (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                              (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas_1'])))
                                              *1000000)
                
        elif s== 'biomass':
            if YEAR == 2030:
                demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                        (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel_1'])))+
                                        (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))
                                        *1000000)
            else:
                demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel_1'])))+
                                            (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel_1'])))+
                                            (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel_1'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel_1'])))
                                            *1000000)
        elif s== 'oil&fuel':
            
            demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Oel'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Oel'])))
                                        *1000000)
            
#             demand_dict[name]['Middle']= scalars[name][16:29].fillna(0)
#             demand_dict[name]['East']= scalars[name][31:45].fillna(0)
#             demand_dict[name]['Swest']= scalars[name][48:62].fillna(0)
#         if name.endswith('Industry_b'):
#             demand_dict[name]['North']= scalars[name][0:16].fillna(0)
#             demand_dict[name]['Middle']= scalars[name][20:36].fillna(0)
#             demand_dict[name]['East']= scalars[name][40:56].fillna(0)
#             demand_dict[name]['Swest']= scalars[name][60:76].fillna(0)
        
        

#investment_parameter = investment_parameter(scalars, YEAR, Model_ID)
#%%
# ------------------------------------------------------------------------------
# Modellbildung
# ------------------------------------------------------------------------------
date_time_index = pd.date_range("1/1/"+ str(YEAR), periods=8760, freq="h")
energysystem = solph.EnergySystem(
    timeindex=date_time_index, infer_last_interval=False
)

"""
Defining connecting lines/buses for balancing energy quantities
"""
#------------------------------------------------------------------------------
# Electricity Bus                                                                                      # Class Bus sind jetzt in module buses verschoben (solph.buses.Bus)
#------------------------------------------------------------------------------
b_hös = solph.buses.Bus(label = "Electricity_HöS") 
b_hs = solph.buses.Bus(label = "Electricity_HS")

b_el_north = solph.buses.Bus(label="Electricity_north")
b_el_middle = solph.buses.Bus(label="Electricity_middle")
b_el_east = solph.buses.Bus(label="Electricity_east")
b_el_swest = solph.buses.Bus(label="Electricity_swest")

energysystem.add(b_hös, b_hs, b_el_east, b_el_middle, b_el_north, b_el_swest)

#------------------------------------------------------------------------------
# Electricity grid interconnection
#------------------------------------------------------------------------------
# Unrestricted electricity import from german grid
energysystem.add(solph.components.Source(
    label='Import_electricity',
    outputs={b_hös: solph.Flow(nominal_value=Parameter_Stromnetz_2030['Strom']['Max_Bezugsleistung'],
                              variable_costs = [i+Parameter_Stromnetz_2030['Strom']['Netzentgelt_Arbeitspreis'] for i in Preise_2030_Stundenwerte['Strompreis_2030']],
                              custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Strom_2030']},
                              
        )}))
# define links between grids and regions
"""Link between HS & North""" 
energysystem.add(solph.components.Link(
    label='HS<->North',
    inputs= {b_hs: solph.Flow()},
    outputs= {b_el_north: solph.Flow()},
    conversion_factors = {(b_hs,b_el_north): 1}
    ))

"""Link between HS & East""" 
energysystem.add(solph.components.Link(
    label='HS<->East',
    inputs= {b_hs: solph.Flow()},
    outputs= {b_el_east: solph.Flow()},
    conversion_factors = {(b_hs,b_el_east): 1}
    ))

"""Link between HS & Middle""" 
energysystem.add(solph.components.Link(
    label='HS<->Middle',
    inputs= {b_hs: solph.Flow()},
    outputs= {b_el_middle: solph.Flow()},
    conversion_factors = {(b_hs,b_el_middle): 1}
    ))

"""Link between HS & Swest""" 
energysystem.add(solph.components.Link(
    label='HS<->Swest',
    inputs= {b_hs: solph.Flow()},
    outputs= {b_el_swest: solph.Flow()},
    conversion_factors = {(b_hs,b_el_swest): 1}
    ))

"""Link between HöS & HS""" 
energysystem.add(solph.components.Link(
    label='HöS<->HS',
    inputs= {b_hös: solph.Flow(nominal_value = 640),
             b_hs: solph.Flow(nominal_value = 640)},
    outputs= {b_hs: solph.Flow(),
             b_hös: solph.Flow()},
    conversion_factors = {(b_hös,b_hs): 1, (b_hs,b_hös):1}
    
    ))

"""Link between HS & different regions""" 
energysystem.add(solph.components.Link(
    label='North<->Middel',
    inputs= {b_el_north: solph.Flow(nominal_value = 0),
             b_el_middle: solph.Flow(nominal_value = 0)},
    outputs= {b_el_middle: solph.Flow(),
             b_el_north: solph.Flow()},
    conversion_factors = {(b_el_north,b_el_middle): 1, (b_el_middle,b_el_north):1}
    
    ))

energysystem.add(solph.components.Link(
    label='Middel<->Swest',
    inputs= {b_el_middle: solph.Flow(nominal_value = 0),
             b_el_swest: solph.Flow(nominal_value = 0)},
    outputs= {b_el_swest: solph.Flow(),
             b_el_middle: solph.Flow()},
    conversion_factors = {(b_el_middle,b_el_swest): 1, (b_el_swest,b_el_middle):1}
    
    ))

energysystem.add(solph.components.Link(
     label='East<->Middel',
     inputs= {b_el_east: solph.Flow(nominal_value = 0),
              b_el_middle: solph.Flow(nominal_value = 0)},
     outputs= {b_el_middle: solph.Flow(),
              b_el_east: solph.Flow()},
     conversion_factors = {(b_el_east,b_el_middle): 1, (b_el_middle,b_el_east):1}
     
     ))   

##############################################################       North region         #################################################################
""" Defining energy system for North region"""

#------------------------------------------------------------------------------
# Gas Bus
#------------------------------------------------------------------------------
b_gas_n = solph.buses.Bus(label="Gas_n")
#------------------------------------------------------------------------------
# Oil/fuel Bus
#------------------------------------------------------------------------------
b_oil_fuel_n = solph.buses.Bus(label="Oil_fuel_n")
#------------------------------------------------------------------------------
# Biomass Bus
#------------------------------------------------------------------------------
b_bio_n = solph.buses.Bus(label="Biomass_n")
#------------------------------------------------------------------------------
# Solid Biomass Bus
#------------------------------------------------------------------------------
b_bioWood_n = solph.buses.Bus(label="BioWood_n")
#------------------------------------------------------------------------------
# District heating Bus
#------------------------------------------------------------------------------
b_dist_heat_n = solph.buses.Bus(label="District heating_n")
#------------------------------------------------------------------------------
# Hydrogen Bus
#------------------------------------------------------------------------------
b_H2_n = solph.buses.Bus(label="Hydrogen_n")
#------------------------------------------------------------------------------
# Solidfuel Bus
#------------------------------------------------------------------------------
b_solidf_n = solph.buses.Bus(label="Solidfuel_n")

# Hinzufügen der Busse zum Energiesystem-Modell 
energysystem.add(b_gas_n, b_oil_fuel_n, b_bio_n, b_bioWood_n, b_dist_heat_n, b_H2_n, b_solidf_n)
