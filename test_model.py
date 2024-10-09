# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 15:32:15 2024

@author: rbala

Infos zum Modell:
    Projekt: ZO.RRO
    Modell: Basisszenario 2030
    version:
        oemof: v0.5.2
        
Ändereungen von alte Basisszenario sind in Kommentaren beschrieben    
"""

__copyright__ = "oemof developer group"
__license__ = "GPLv3"

from oemof.tools import logger
from oemof import solph
import logging

import os
workdir= os.getcwd()
import pandas as pd
import matplotlib
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
from oemof.tools import economics
matplotlib.pyplot.margins
# from oemof.solph._plumbing import sequence            # _plumbing statt plumbing, war in neue version umbennant
# from oemof.solph import constraints
import pyomo.environ as po
from src.preprocessing.create_input_dataframe import createDataFrames
from src.preprocessing.files import read_input_files
from src.preprocessing.conversion import investment_parameter, load_profile_scaling, CO2_price_addition
from src.preprocessing.location import Location
from src.preprocessing.constraints import CO2_limit, BiogasBestand_limit, BiogasNeuanlagen_limit, Biomasse_limit, GuD_time

YEAR = 2030
model_ID = 'BS0001'
name = os.path.basename(__file__)
name = 'BS030006'#name.replace(".py", "")
my_path = os.path.abspath(os.path.dirname(__file__))
results_path = os.path.abspath(os.path.join(my_path, '..', 'results', name))
if not os.path.isdir(results_path):
    os.makedirs(results_path)


sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
demand = load_profile_scaling(scalars,sequences,YEAR)
epc_costs = investment_parameter(scalars, YEAR, model_ID)
import_price = CO2_price_addition(scalars,sequences, YEAR)
#%%

Weather_dir = os.path.abspath(os.path.join(workdir, 'data','weatherdata'))
middle = Location(os.path.join(Weather_dir,'Erfurt_Binderslebn-hour.csv'), os.path.join(Weather_dir,'Erfurt_Binderslebn-min.dat'))
north = Location(os.path.join(Weather_dir,'Nordhausen-hour.csv'), os.path.join(Weather_dir,'Nordhausen-min.dat'))
swest= Location(os.path.join(Weather_dir,'Hildburghausen-hour.csv'), os.path.join(Weather_dir,'Hildburghausen-min.dat'))
east = Location(os.path.join(Weather_dir,'Gera-Leumnitz-hour.csv'), os.path.join(Weather_dir,'Gera-Leumnitz-min.dat'))

Planing_region = [middle, north, swest, east]
""" Simulate Wind feed-in profile for the desired location """
for L in Planing_region:
    L.Wind_feed_in_profile(YEAR)
    #L.PV_feed_in_profile(YEAR)

    
solver = 'gurobi'
debug = False  
solver_verbose = False

logger.define_logging(logfile='oemof_example.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.getLogger().setLevel(logging.INFO)
logging.info('Initialize the energy system')


# ------------------------------------------------------------------------------
# Modellbildung
# ------------------------------------------------------------------------------
date_time_index = pd.date_range("1/1/"+ str(YEAR), periods=8760, freq="h")
energysystem = solph.EnergySystem(
    timeindex=date_time_index, infer_last_interval=True
)
logging.info('Create oemof objects')

"""
Defining connecting lines/buses for balancing energy quantities
"""
#------------------------------------------------------------------------------
# Electricity Bus                                                                                      # Class Bus sind jetzt in module buses verschoben (solph.buses.Bus)
#------------------------------------------------------------------------------
#b_hös = solph.buses.Bus(label = "Electricity_HöS") 
b_hs = solph.buses.Bus(label = "Electricity_HS")

b_el_north = solph.buses.Bus(label="Electricity_north")
b_el_middle = solph.buses.Bus(label="Electricity_middle")
b_el_east = solph.buses.Bus(label="Electricity_east")
b_el_swest = solph.buses.Bus(label="Electricity_swest")

energysystem.add(b_hs, b_el_north, b_el_east, b_el_middle,  b_el_swest)

#------------------------------------------------------------------------------
# Electricity grid interconnection
#------------------------------------------------------------------------------
# Unrestricted electricity import from german grid
energysystem.add(solph.components.Source(
    label='Import_electricity',
    outputs={b_hs: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power'],
                              variable_costs = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee'] for i in sequences['Energy_price']['Strompreis_brain_'+str(YEAR)]],
                              custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]},
                              
        )}))
"""Link between HöS & HS""" 
# energysystem.add(solph.components.Link(
#     label='HöS<->HS',
#     inputs= {b_hös: solph.Flow(),
#              b_hs: solph.Flow()},
#     outputs= {b_hs: solph.Flow(),
#              b_hös: solph.Flow()},
#     conversion_factors = {(b_hös,b_hs): 1, (b_hs,b_hös):1}
    
#     ))
# define links between grids and regions
"""Link between HS & North""" 
energysystem.add(solph.components.Link(
    label='HS<->North',
    inputs= {b_hs: solph.Flow()},
    outputs= {b_el_north: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_north'])},
    conversion_factors = {(b_hs,b_el_north): 1}
    ))



"""Link between HS & East""" 
energysystem.add(solph.components.Link(
    label='HS<->East',
    inputs= {b_hs: solph.Flow()},
    outputs= {b_el_east: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_east'])},
    conversion_factors = {(b_hs,b_el_east): 1}
    ))

"""Link between HS & Middle""" 
energysystem.add(solph.components.Link(
    label='HS<->Middle',
    inputs= {b_hs: solph.Flow()},
    outputs= {b_el_middle: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_middle'])},
    conversion_factors = {(b_hs,b_el_middle): 1}
    ))

"""Link between HS & Swest""" 
energysystem.add(solph.components.Link(
    label='HS<->Swest',
    inputs= {b_hs: solph.Flow()},
    outputs= {b_el_swest: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_swest'])},
    conversion_factors = {(b_hs,b_el_swest): 1}
    ))


"""Link between HS & different regions""" 
energysystem.add(solph.components.Link(
    label='North<->Middel',
    inputs= {b_el_north: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['connection_north_middle']),
              b_el_middle: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['connection_north_middle'])},
    outputs= {b_el_middle: solph.Flow(),
              b_el_north: solph.Flow()},
    conversion_factors = {(b_el_north,b_el_middle): 1, (b_el_middle,b_el_north):1}
    
    ))

energysystem.add(solph.components.Link(
    label='Middel<->Swest',
    inputs= {b_el_middle: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['connection_middle_swest']),
              b_el_swest: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['connection_middle_swest'])},
    outputs= {b_el_swest: solph.Flow(),
              b_el_middle: solph.Flow()},
    conversion_factors = {(b_el_middle,b_el_swest): 1, (b_el_swest,b_el_middle):1}
    
    ))

energysystem.add(solph.components.Link(
      label='East<->Middel',
      inputs= {b_el_east: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['connection_east_middle']),
              b_el_middle: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['connection_east_middle'])},
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

"""
Export block
"""
# ------------------------------------------------------------------------------  
# Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
# ------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Electricity_n', 
    inputs={b_el_north: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_north'],
                              variable_costs = [i *(-1) for i in sequences['Energy_price']['Strompreis_brain_'+str(YEAR)]],
    )}))

# ------------------------------------------------------------------------------
# Hydrogen export
# ------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Hydrogen_n', 
    inputs={b_H2_n: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                              variable_costs = [i*(-1) for i in sequences['Energy_price']['Hydrogen_' + str(YEAR)]]
                              
    )}))

"""
Defining final energy demand as Sinks
"""
#------------------------------------------------------------------------------
# Electricity demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Electricity_demand_total_n', 
    inputs={b_el_north: solph.Flow(fix=demand['electricity']['north'], 
                             nominal_value=1,
    )}))
#------------------------------------------------------------------------------
# Biomass demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Biomass_demand_total_n', 
    inputs={b_solidf_n: solph.Flow(fix=demand['biomass']['north'], 
                                nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Gas demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Gas_demand_total_n', 
    inputs={b_gas_n: solph.Flow(fix=demand['gas']['north'], 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Material demand: Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Material_demand_Gas_n', 
    inputs={b_gas_n: solph.Flow(fix=demand['material_usage_gas']['north'], 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Oil demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Oil_demand_total_n', 
    inputs={b_oil_fuel_n: solph.Flow(fix=demand['oil']['north'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Mobility demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Mobility_demand_total_n', 
    inputs={b_oil_fuel_n: solph.Flow(fix=demand['fuel']['north'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Material demand: Oil
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Material_demand_Oil_n', 
    inputs={b_oil_fuel_n: solph.Flow(fix=demand['material_usage_oil']['north'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Heat demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Heat_demand_total_n', 
    inputs={b_dist_heat_n: solph.Flow(fix=demand['dist_heating']['north'], 
                                nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Hydrogen demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Hydrogen_demand_total_n', 
    inputs={b_H2_n: solph.Flow(fix=demand['H2']['north'], 
                              nominal_value=1,
    )}))


"""
Renewable Energy sources
"""
#------------------------------------------------------------------------------
# Wind power plants
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Wind_Nordhausen', 
    outputs={b_el_north: solph.Flow(fix=north.Wind_feed_in_profile['Wind_feed_in'],
                                    custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                minimum=scalars['Parameter_onshore_wind_power_plant']['potential_north'][model_ID]
                                                                )
    )}))
#------------------------------------------------------------------------------
# Photovoltaic Rooftop systems
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_rooftop_Nordhausen', 
    outputs={b_el_north: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_north'],
                                    custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north'][model_ID]
                                                                )
    )}))
# #------------------------------------------------------------------------------
# # Photovoltaic Openfield systems
# #------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_Freifeld_Nordhausen', 
    outputs={b_el_north: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_north'],
                                    custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north'][model_ID])
    )}))

#------------------------------------------------------------------------------
# Hydroenergy
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Hydro power plant_n', 
    outputs={b_el_north: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                    custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                minimum=scalars['Parameter_run_river_power_plant']['potential_north'][model_ID], 
                                                                maximum = scalars['Parameter_run_river_power_plant']['potential_north'][model_ID])
    )}))

# ------------------------------------------------------------------------------
# Solar thermal
# ------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='ST_n', 
    outputs={b_dist_heat_n: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                      custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                      investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                  maximum=scalars['Parameter_solar_thermal_power_plant']['potential_north'][model_ID])
    )}))

""" Imports """

#------------------------------------------------------------------------------
# Import Solid fuel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_solid_fuel_n',
    outputs={b_bio_n: solph.Flow(variable_costs = sequences['Energy_price']['Biomass_'+ str(YEAR)],
                                      custom_attributes={'BiogasNeuanlagen_factor': 1},
                               
    )}))

#------------------------------------------------------------------------------
# solid Biomass
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Wood_n',
    outputs={b_bioWood_n: solph.Flow(variable_costs =sequences['Energy_price']['Biomass_'+ str(YEAR)],
                                          custom_attributes={'Biomasse_factor': 1},
                                   
    )}))

#------------------------------------------------------------------------------
# Import Brown-coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_brown_coal_n',
    outputs={b_solidf_n: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                fix=sequences['Base_demand_profile']['base_load'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=scalars['System_configurations']['System']['Menge_Braunkohle']*len(import_price['import_brown_coal_price']),
                                custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Braunkohle']},
    )}))

#------------------------------------------------------------------------------
# Import hard coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_hard_coal_n',
    outputs={b_solidf_n: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
                                fix=sequences['Base_demand_profile']['base_load'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=scalars['System_configurations']['System']['Menge_Steinkohle']*len(import_price['import_hard_coal_price']),
                                custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Steinkohle']},
                                
    )}))

#------------------------------------------------------------------------------
# Import Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Gas_n',
    outputs={b_gas_n: solph.Flow(variable_costs = import_price['import_gas_price'],
                                      custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Erdgas']},
                               
    )}))

#------------------------------------------------------------------------------
# Import Oil
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Oil_n',
    outputs={b_oil_fuel_n: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                  custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Oel']}
                                           
        )}))

#------------------------------------------------------------------------------
# Import Synthetic fuel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Synthetic_fuel_n',
    outputs={b_oil_fuel_n: solph.Flow(variable_costs = sequences['Energy_price']['Synthetic_fuel_'+ str(YEAR)],
        )}))

"""
Energy storage
"""

#------------------------------------------------------------------------------
# Electricity storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Battery_n',
    inputs={b_el_north: solph.Flow()},
    outputs={b_el_north: solph.Flow()},
    loss_rate=0,
    inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
    balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                    maximum=scalars['Parameter_storage_electricity']['potential_north'][model_ID],
                                    )
    ))

#------------------------------------------------------------------------------
# Heat storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Heat storage_n',
    inputs={b_dist_heat_n: solph.Flow(
                              custom_attributes={'keywordWSP': 1},
                              nominal_value=float(scalars['Parameter_storage_heat']['potential'][model_ID]/scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
                              #nonconvex=solph.NonConvex()
                                )},
    outputs={b_dist_heat_n: solph.Flow(
                                custom_attributes={'keywordWSP': 1},
                                nominal_value=float(scalars['Parameter_storage_heat']['potential'][model_ID]/scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
                                #nonconvex=solph.NonConvex()
                                )},
    loss_rate=float(scalars['Parameter_storage_heat']['loss_rate'][model_ID]/24),
    inflow_conversion_factor=scalars['Parameter_storage_heat']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor=scalars['Parameter_storage_heat']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_heat']['initial_storage_level'][model_ID],
    balanced=bool(scalars['Parameter_storage_heat']['balanced'][model_ID]),
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
    nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat']['epc'], 
                                  )
    ))


# ------------------------------------------------------------------------------
# Pumped hydro storage
# ------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label="Pumped_hydro_storage_n",
    inputs={b_el_north: solph.Flow()},
    outputs={b_el_north: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology']['epc'],
                                  minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_min'][model_ID],
                                  maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_max'][model_ID])
    ))

#------------------------------------------------------------------------------
# Gas storage
#------------------------------------------------------------------------------ 
energysystem.add(solph.components.GenericStorage(
    label="Gas storage_n",
    inputs={b_gas_n: solph.Flow()},
    outputs={b_gas_n: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                  maximum = scalars['Parameter_storage_gas']['potential_north'][model_ID])  
    ))

#------------------------------------------------------------------------------
# H2 Storage
#------------------------------------------------------------------------------    
energysystem.add(solph.components.GenericStorage(
    label="H2_storage_n",
    inputs={b_H2_n: solph.Flow()},
    outputs={b_H2_n: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_hydrogen']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                  maximum = scalars['Parameter_storage_hydrogen']['potential_north'][model_ID])  
    ))

"""
Transformers
"""
#------------------------------------------------------------------------------
# Elektrolysis
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Elektrolysis_n",
    inputs={b_el_north: solph.Flow()},
    outputs={b_H2_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc'], 
                                                              maximum=scalars['Parameter_electrolysis']['potential'][model_ID]))},
    conversion_factors={b_H2_n: scalars['Parameter_electrolysis']['efficiency_'+str(YEAR)][model_ID]},
    ))

#------------------------------------------------------------------------------
# Electric boiler
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Electric boiler_n",
    inputs={b_el_north: solph.Flow()},
    outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
    conversion_factors={b_dist_heat_n: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]}    
    ))

#------------------------------------------------------------------------------
# Gas and Steam turbine
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='GuD_n',
    inputs={b_gas_n: solph.Flow(custom_attributes={'time_factor' :1})},
    outputs={b_el_north: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                          maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential'][model_ID])),
              b_dist_heat_n: solph.Flow()},
    conversion_factors={b_el_north: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID], 
                        b_dist_heat_n: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Fuel cells
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Fuelcell_n",
    inputs={b_H2_n: solph.Flow()},
    outputs={b_el_north: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                            maximum=scalars['Parameter_fuel_cells']['potential'][model_ID]))},
    conversion_factors={b_el_north: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Methanisation
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Methanisation_n",
    inputs={b_H2_n: solph.Flow()},
    outputs={b_gas_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                              maximum=scalars['Parameter_methanation']['potential'][model_ID]))},
    conversion_factors={b_gas_n: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]}  
    ))

#------------------------------------------------------------------------------
# Biogas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biogas_n',
    inputs={b_bio_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                    #nominal_value=1,
                                    investment = solph.Investment(ep_costs=0),
                                    custom_attributes={'BiogasBestand_factor': scalars['Parameter_bio_power_unit_Biogas']['existing_factor'][model_ID]})},
                              
    outputs={b_el_north: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogas']['epc']), 
                                    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogas']['EE_factor'][model_ID]},
                                    fix=sequences['Base_demand_profile']['base_load']),
              b_dist_heat_n: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogas']['EE_factor'][model_ID]},
                                      fix=sequences['Base_demand_profile']['base_load'],
                                      #nominal_value= 1
                                      investment = solph.Investment(ep_costs=0)
                                      )},
    conversion_factors={b_el_north: scalars['Parameter_bio_power_unit_Biogas']['efficiency_el_'+str(YEAR)][model_ID], 
                        b_dist_heat_n: scalars['Parameter_bio_power_unit_Biogas']['efficiency_th_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biomasse (for electricty production)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_elec_n',
    inputs={b_bioWood_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_el_north: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                              investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biomass']['epc']),
                              custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biomass']['EE_factor'][model_ID]})},
    conversion_factors={b_el_north: scalars['Parameter_bio_power_unit_Biomass']['efficiency_el_' +str(YEAR)][model_ID]}
    ))        

#------------------------------------------------------------------------------
# Biomasse (for heat production)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_heat_n',
    inputs={b_bioWood_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_dist_heat_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biomass']['epc']),
                                custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biomass']['EE_factor'][model_ID]})},
    conversion_factors={b_dist_heat_n: scalars['Parameter_bio_power_unit_Biomass']['efficiency_th_' +str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung mit bereits bestehenden Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogas_feedin_existing_n",
    inputs={b_bio_n: solph.Flow(custom_attributes={'BiogasBestand_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['existing_factor'][model_ID]},
                                    fix=sequences['Base_demand_profile']['base_load'],
                                    investment = solph.Investment(ep_costs=0)
                                    #nominal_value = 1
                                    )},
    outputs={b_gas_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment = solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogaseinspeisung_Bestand']['epc']),
                                )},
    conversion_factors={b_gas_n: scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['efficiency_'+str(YEAR)][model_ID]},
    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['EE_factor'][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung ohne bereits bestehende Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogas_feed_in_new_n",
    inputs={b_bio_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                    investment = solph.Investment(ep_costs=0)
                                    )},
    outputs={b_gas_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment = solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogaseinspeisung_Neu']['epc']),
                                )},
    conversion_factors={b_gas_n: scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['efficiency_'+str(YEAR)][model_ID]},
    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['EE_factor'][model_ID]}
                                
    ))

# -----------------------------------------------------------------------------
# Hydroden feed-in
# -----------------------------------------------------------------------------
maximale_Wasserstoffeinspeisung_Lastgang_n = [None] * len(demand['gas']['north'])
maximale_Wasserstoffeinspeisung_n=0
for a in range(0, len(demand['gas']['north'])):
    maximale_Wasserstoffeinspeisung_Lastgang_n[a]=(demand['gas']['north'][a]*(scalars['Parameter_hydrogen_feed_in']['potential'][model_ID]))/(scalars['Parameter_hydrogen_feed_in']['efficiency_'+str(YEAR)][model_ID])
    if maximale_Wasserstoffeinspeisung_Lastgang_n[a] > maximale_Wasserstoffeinspeisung_n:
        maximale_Wasserstoffeinspeisung_n = maximale_Wasserstoffeinspeisung_Lastgang_n[a]

energysystem.add(solph.components.Converter(
    label='Hydrogen_feedin_n',
    inputs={b_H2_n: solph.Flow()},
    outputs={b_gas_n: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang_n,
                                investment=solph.Investment(ep_costs=epc_costs['hydrogen_feed_in']['epc'], 
                                                            maximum=max(maximale_Wasserstoffeinspeisung_Lastgang_n)))}
    ))

#------------------------------------------------------------------------------
# Heatpump_river
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Heatpump_water_n",
    inputs={b_el_north: solph.Flow()},
    outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                              maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential'][model_ID]))},
    conversion_factors={b_dist_heat_n: scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},    
    ))

#------------------------------------------------------------------------------
# Heatpump: Recovery heat
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Heatpump_air_n",
    inputs={b_el_north: solph.Flow()},
    outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
                                                              maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential'][model_ID]))},
    conversion_factors={b_dist_heat_n: scalars['Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]},    
    ))

#------------------------------------------------------------------------------
# Power-to-Liquid
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="PtL_n",
    inputs={b_H2_n: solph.Flow()},
    outputs={b_oil_fuel_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                          maximum=scalars['Parameter_power_to_liquid_system']['potential'][model_ID]))},
    conversion_factors={b_oil_fuel_n: scalars['Parameter_power_to_liquid_system']['efficiency_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Solid biomass in the same bus as coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="BioTransformer_n",
    inputs={b_bioWood_n: solph.Flow()},
    outputs={b_solidf_n: solph.Flow()},
    ))

"""
Excess energy capture sinks 
"""
#------------------------------------------------------------------------------
# Überschuss Senke für Strom
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_el_n', 
    inputs={b_el_north: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_gas_n', 
    inputs={b_gas_n: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Oel/Kraftstoffe
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_oil_fuel_n', 
    inputs={b_oil_fuel_n: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Biomasse
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_bio_n', 
    inputs={b_bio_n: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Waerme
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_distheat_n', 
    inputs={b_dist_heat_n: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Wasserstoff
#-----------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_H2_n', 
    inputs={b_H2_n: solph.Flow(variable_costs = 10000000
    )}))

##############################################################       East region         #################################################################
# """ Defining energy system for North region"""

#------------------------------------------------------------------------------
# Gas Bus
#------------------------------------------------------------------------------
b_gas_e = solph.buses.Bus(label="Gas_e")
#------------------------------------------------------------------------------
# Oil/fuel Bus
#------------------------------------------------------------------------------
b_oil_fuel_e = solph.buses.Bus(label="Oil_fuel_e")
#------------------------------------------------------------------------------
# Biomass Bus
#------------------------------------------------------------------------------
b_bio_e = solph.buses.Bus(label="Biomass_e")
#------------------------------------------------------------------------------
# Solid Biomass Bus
#------------------------------------------------------------------------------
b_bioWood_e = solph.buses.Bus(label="BioWood_e")
#------------------------------------------------------------------------------
# District heating Bus
#------------------------------------------------------------------------------
b_dist_heat_e = solph.buses.Bus(label="District heating_e")
#------------------------------------------------------------------------------
# Hydrogen Bus
#------------------------------------------------------------------------------
b_H2_e = solph.buses.Bus(label="Hydrogen_e")
#------------------------------------------------------------------------------
# Solidfuel Bus
#------------------------------------------------------------------------------
b_solidf_e = solph.buses.Bus(label="Solidfuel_e")

# Hinzufügen der Busse zum Energiesystem-Modell 
energysystem.add(b_gas_e, b_oil_fuel_e, b_bio_e, b_bioWood_e, b_dist_heat_e, b_H2_e, b_solidf_e)

"""
Export block
"""
#------------------------------------------------------------------------------  
# Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Electricity_e', 
    inputs={b_el_east: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_east'],
                              variable_costs = [i *(-1) for i in sequences['Energy_price']['Strompreis_brain_'+str(YEAR)]]
    )}))

#------------------------------------------------------------------------------
# Hydrogen export
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Hydrogen_e', 
    inputs={b_H2_e: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                              variable_costs = [i*(-1) for i in sequences['Energy_price']['Hydrogen_' + str(YEAR)]]
                              
    )}))

"""
Defining final energy demand as Sinks
"""
#------------------------------------------------------------------------------
# Electricity demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Electricity_demand_total_e', 
    inputs={b_el_east: solph.Flow(fix=demand['electricity']['east'], 
                              nominal_value=1,
    )}))
#------------------------------------------------------------------------------
# Biomass demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Biomass_demand_total_e', 
    inputs={b_solidf_e: solph.Flow(fix=demand['biomass']['east'], 
                                nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Gas demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Gas_demand_total_e', 
    inputs={b_gas_e: solph.Flow(fix=demand['gas']['east'], 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Material demand: Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Material_demand_Gas_e', 
    inputs={b_gas_e: solph.Flow(fix=demand['material_usage_gas']['east'], 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Oil demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Oil_demand_total_e', 
    inputs={b_oil_fuel_e: solph.Flow(fix=demand['oil']['east'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Mobility demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Mobility_demand_total_e', 
    inputs={b_oil_fuel_e: solph.Flow(fix=demand['fuel']['east'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Material demand: Oil
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Material_demand_Oil_e', 
    inputs={b_oil_fuel_e: solph.Flow(fix=demand['material_usage_oil']['east'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Heat demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Heat_demand_total_e', 
    inputs={b_dist_heat_e: solph.Flow(fix=demand['dist_heating']['east'], 
                                nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Hydrogen demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Hydrogen_demand_total_e', 
    inputs={b_H2_e: solph.Flow(fix=demand['H2']['east'], 
                              nominal_value=1,
    )}))


"""
Renewable Energy sources
"""
#------------------------------------------------------------------------------
# Wind power plants
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Wind_Gera', 
    outputs={b_el_east: solph.Flow(fix=east.Wind_feed_in_profile['Wind_feed_in'],
                                    custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_onshore_wind_power_plant']['potential_east'][model_ID])
    )}))
#------------------------------------------------------------------------------
# Photovoltaic Rooftop systems
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_rooftop_Gera', 
    outputs={b_el_east: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_east'],
                                    custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_east'][model_ID])
    )}))
#------------------------------------------------------------------------------
# Photovoltaic Openfield systems
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_Freifeld_Gera', 
    outputs={b_el_east: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_east'],
                                    custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_east'][model_ID])
    )}))

#------------------------------------------------------------------------------
# Hydroenergy
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Hydro power plant_e', 
    outputs={b_el_east: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                    custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                minimum=scalars['Parameter_run_river_power_plant']['potential_east'][model_ID], 
                                                                maximum = scalars['Parameter_run_river_power_plant']['potential_east'][model_ID])
    )}))

#------------------------------------------------------------------------------
# Solar thermal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='ST_e', 
    outputs={b_dist_heat_e: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                      custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                      investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                  maximum=scalars['Parameter_solar_thermal_power_plant']['potential_east'][model_ID])
    )}))

""" Imports """

#------------------------------------------------------------------------------
# Import Solid fuel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_solid_fuel_e',
    outputs={b_bio_e: solph.Flow(variable_costs = sequences['Energy_price']['Biomass_'+ str(YEAR)],
                                      custom_attributes={'BiogasNeuanlagen_factor': 1},
                               
    )}))

#------------------------------------------------------------------------------
# solid Biomass
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Wood_e',
    outputs={b_bioWood_e: solph.Flow(variable_costs =sequences['Energy_price']['Biomass_'+ str(YEAR)],
                                          custom_attributes={'Biomasse_factor': 1},
                                   
    )}))

#------------------------------------------------------------------------------
# Import Brown-coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_brown_coal_e',
    outputs={b_solidf_e: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                fix=sequences['Base_demand_profile']['base_load'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=scalars['System_configurations']['System']['Menge_Braunkohle']*len(import_price['import_brown_coal_price']),
                                custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Braunkohle']},
    )}))

#------------------------------------------------------------------------------
# Import hard coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_hard_coal_e',
    outputs={b_solidf_e: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
                                fix=sequences['Base_demand_profile']['base_load'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=scalars['System_configurations']['System']['Menge_Steinkohle']*len(import_price['import_brown_coal_price']),
                                custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Steinkohle']},
                                
    )}))

#------------------------------------------------------------------------------
# Import Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Gas_e',
    outputs={b_gas_e: solph.Flow(variable_costs = import_price['import_gas_price'],
                                      custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Erdgas']},
                               
    )}))

#------------------------------------------------------------------------------
# Import Oil
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Oil_e',
    outputs={b_oil_fuel_e: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                  custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Oel']}
                                           
        )}))

#------------------------------------------------------------------------------
# Import Synthetic fuel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Synthetic_fuel_e',
    outputs={b_oil_fuel_e: solph.Flow(variable_costs = sequences['Energy_price']['Synthetic_fuel_'+ str(YEAR)],
        )}))

"""
Energy storage
"""

#------------------------------------------------------------------------------
# Electricity storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Battery_e',
    inputs={b_el_east: solph.Flow()},
    outputs={b_el_east: solph.Flow()},
    loss_rate=0,
    inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
    balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                    maximum=scalars['Parameter_storage_electricity']['potential_east'][model_ID],
                                    )
    ))

#------------------------------------------------------------------------------
# Heat storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Heat storage_e',
    inputs={b_dist_heat_e: solph.Flow(
                              custom_attributes={'keywordWSP': 1},
                              nominal_value=float(scalars['Parameter_storage_heat']['potential'][model_ID]/scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
                              #nonconvex=solph.NonConvex()
                                )},
    outputs={b_dist_heat_e: solph.Flow(
                                custom_attributes={'keywordWSP': 1},
                                nominal_value=float(scalars['Parameter_storage_heat']['potential'][model_ID]/scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
                                #nonconvex=solph.NonConvex()
                                )},
    loss_rate=float(scalars['Parameter_storage_heat']['loss_rate'][model_ID]/24),
    inflow_conversion_factor=scalars['Parameter_storage_heat']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor=scalars['Parameter_storage_heat']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_heat']['initial_storage_level'][model_ID],
    balanced=bool(scalars['Parameter_storage_heat']['balanced'][model_ID]),
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
    nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat']['epc'], 
                                  )
    ))


#------------------------------------------------------------------------------
# Pumped hydro storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label="Pumped_hydro_storage_e",
    inputs={b_el_east: solph.Flow()},
    outputs={b_el_east: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology']['epc'],
                                  minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_min'][model_ID],
                                  maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_max'][model_ID])
    ))

#------------------------------------------------------------------------------
# Gas storage
#------------------------------------------------------------------------------ 
energysystem.add(solph.components.GenericStorage(
    label="Gas storage_e",
    inputs={b_gas_e: solph.Flow()},
    outputs={b_gas_e: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                  maximum = scalars['Parameter_storage_gas']['potential_east'][model_ID])     
    ))

#------------------------------------------------------------------------------
# H2 Storage
#------------------------------------------------------------------------------    
energysystem.add(solph.components.GenericStorage(
    label="H2_storage_e",
    inputs={b_H2_e: solph.Flow()},
    outputs={b_H2_e: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_hydrogen']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                  maximum = scalars['Parameter_storage_hydrogen']['potential_east'][model_ID])  
      
    ))

"""
Transformers
"""
#------------------------------------------------------------------------------
# Elektrolysis
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Elektrolysis_e",
    inputs={b_el_east: solph.Flow()},
    outputs={b_H2_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc'], 
                                                              maximum=scalars['Parameter_electrolysis']['potential'][model_ID]))},
    conversion_factors={b_H2_e: scalars['Parameter_electrolysis']['efficiency_'+str(YEAR)][model_ID]},
    ))

#------------------------------------------------------------------------------
# Electric boiler
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Electric boiler_e",
    inputs={b_el_east: solph.Flow()},
    outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
    conversion_factors={b_dist_heat_e: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]} 
    ))

#------------------------------------------------------------------------------
# Gas and Steam turbine
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='GuD_e',
    inputs={b_gas_e: solph.Flow(custom_attributes={'time_factor' :1})},
    outputs={b_el_east: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                          maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential'][model_ID])),
              b_dist_heat_e: solph.Flow()},
    conversion_factors={b_el_east: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID], 
                        b_dist_heat_e: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Fuel cells
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Fuelcell_e",
    inputs={b_H2_e: solph.Flow()},
    outputs={b_el_east: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                            maximum=scalars['Parameter_fuel_cells']['potential'][model_ID]))},
    conversion_factors={b_el_east: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Methanisation
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Methanisation_e",
    inputs={b_H2_e: solph.Flow()},
    outputs={b_gas_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                              maximum=scalars['Parameter_methanation']['potential'][model_ID]))},
    conversion_factors={b_gas_e: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]}    
    ))

#------------------------------------------------------------------------------
# Biogas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biogas_e',
    inputs={b_bio_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                    #nominal_value=1,
                                    investment = solph.Investment(ep_costs=0),
                                    custom_attributes={'BiogasBestand_factor': scalars['Parameter_bio_power_unit_Biogas']['existing_factor'][model_ID]})},
                              
    outputs={b_el_east: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogas']['epc']), 
                                    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogas']['EE_factor'][model_ID]},
                                    fix=sequences['Base_demand_profile']['base_load']),
              b_dist_heat_e: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogas']['EE_factor'][model_ID]},
                                      fix=sequences['Base_demand_profile']['base_load'],
                                      #nominal_value= 1
                                      investment = solph.Investment(ep_costs=0)
                                      )},
    conversion_factors={b_el_east: scalars['Parameter_bio_power_unit_Biogas']['efficiency_el_'+str(YEAR)][model_ID], 
                        b_dist_heat_e: scalars['Parameter_bio_power_unit_Biogas']['efficiency_th_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biomasse (for electricty production)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_elec_e',
    inputs={b_bioWood_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_el_east: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                              investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biomass']['epc']),
                              custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biomass']['EE_factor'][model_ID]})},
    conversion_factors={b_el_east: scalars['Parameter_bio_power_unit_Biomass']['efficiency_el_' +str(YEAR)][model_ID]}
    ))        

#------------------------------------------------------------------------------
# Biomasse (for heat production)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_heat_e',
    inputs={b_bioWood_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_dist_heat_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biomass']['epc']),
                                custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biomass']['EE_factor'][model_ID]})},
    conversion_factors={b_dist_heat_e: scalars['Parameter_bio_power_unit_Biomass']['efficiency_th_' +str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung mit bereits bestehenden Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogas_feedin_existing_e",
    inputs={b_bio_e: solph.Flow(custom_attributes={'BiogasBestand_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['existing_factor'][model_ID]},
                                    fix=sequences['Base_demand_profile']['base_load'],
                                    investment = solph.Investment(ep_costs=0)
                                    #nominal_value = 1
                                    )},
    outputs={b_gas_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment = solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogaseinspeisung_Bestand']['epc']),
                                )},
    conversion_factors={b_gas_e: scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['efficiency_'+str(YEAR)][model_ID]},
    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['EE_factor'][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung ohne bereits bestehende Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogas_feed_in_new_e",
    inputs={b_bio_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                    investment = solph.Investment(ep_costs=0)
                                    )},
    outputs={b_gas_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment = solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogaseinspeisung_Neu']['epc']),
                                )},
    conversion_factors={b_gas_e: scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['efficiency_'+str(YEAR)][model_ID]},
    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['EE_factor'][model_ID]}
                                
    ))

# -----------------------------------------------------------------------------
# Hydroden feed-in
# -----------------------------------------------------------------------------
maximale_Wasserstoffeinspeisung_Lastgang_e = [None] * len(demand['gas']['east'])
maximale_Wasserstoffeinspeisung_e=0
for a in range(0, len(demand['gas']['east'])):
    maximale_Wasserstoffeinspeisung_Lastgang_e[a]=(demand['gas']['east'][a]*(scalars['Parameter_hydrogen_feed_in']['potential'][model_ID]))/(scalars['Parameter_hydrogen_feed_in']['efficiency_'+str(YEAR)][model_ID])
    if maximale_Wasserstoffeinspeisung_Lastgang_e[a] > maximale_Wasserstoffeinspeisung_e:
        maximale_Wasserstoffeinspeisung_e = maximale_Wasserstoffeinspeisung_Lastgang_e[a]

energysystem.add(solph.components.Converter(
    label='Hydrogen_feedin_e',
    inputs={b_H2_e: solph.Flow()},
    outputs={b_gas_e: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang_e,
                                investment=solph.Investment(ep_costs=epc_costs['hydrogen_feed_in']['epc'], 
                                                            maximum=max(maximale_Wasserstoffeinspeisung_Lastgang_e)))}
    ))

#------------------------------------------------------------------------------
# Heatpump_river
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Heatpump_water_e",
    inputs={b_el_east: solph.Flow()},
    outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                              maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential'][model_ID]))},
    conversion_factors={b_dist_heat_e: scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},    
    ))

#------------------------------------------------------------------------------
# Heatpump: Recovery heat
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Heatpump_air_e",
    inputs={b_el_east: solph.Flow()},
    outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
                                                              maximum=scalars['Parameter_heat_pump_air_Abwärme']['potential'][model_ID]))},
    conversion_factors={b_dist_heat_e: scalars['Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]},    
    ))

#------------------------------------------------------------------------------
# Power-to-Liquid
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="PtL_e",
    inputs={b_H2_e: solph.Flow()},
    outputs={b_oil_fuel_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                          maximum=scalars['Parameter_power_to_liquid_system']['potential'][model_ID]))},
    conversion_factors={b_oil_fuel_e: scalars['Parameter_power_to_liquid_system']['efficiency_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Solid biomass in the same bus as coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="BioTransformer_e",
    inputs={b_bioWood_e: solph.Flow()},
    outputs={b_solidf_e: solph.Flow()},
    ))

"""
Excess energy capture sinks 
"""
#------------------------------------------------------------------------------
# Überschuss Senke für Strom
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_el_e', 
    inputs={b_el_east: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_gas_e', 
    inputs={b_gas_e: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Oel/Kraftstoffe
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_oil_fuel_e', 
    inputs={b_oil_fuel_e: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Biomasse
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_bio_e', 
    inputs={b_bio_e: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Waerme
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_distheat_e', 
    inputs={b_dist_heat_e: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Wasserstoff
#-----------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_H2_e', 
    inputs={b_H2_e: solph.Flow(variable_costs = 10000000
    )}))

##############################################################      Middle region         #################################################################
""" Defining energy system for Middle region"""

#------------------------------------------------------------------------------
# Gas Bus
#------------------------------------------------------------------------------
b_gas_m = solph.buses.Bus(label="Gas_m")
#------------------------------------------------------------------------------
# Oil/fuel Bus
#------------------------------------------------------------------------------
b_oil_fuel_m = solph.buses.Bus(label="Oil_fuel_m")
#------------------------------------------------------------------------------
# Biomass Bus
#------------------------------------------------------------------------------
b_bio_m = solph.buses.Bus(label="Biomass_m")
#------------------------------------------------------------------------------
# Solid Biomass Bus
#------------------------------------------------------------------------------
b_bioWood_m = solph.buses.Bus(label="BioWood_m")
#------------------------------------------------------------------------------
# District heating Bus
#------------------------------------------------------------------------------
b_dist_heat_m = solph.buses.Bus(label="District heating_m")
#------------------------------------------------------------------------------
# Hydrogen Bus
#------------------------------------------------------------------------------
b_H2_m = solph.buses.Bus(label="Hydrogen_m")
#------------------------------------------------------------------------------
# Solidfuel Bus
#------------------------------------------------------------------------------
b_solidf_m = solph.buses.Bus(label="Solidfuel_m")

# Hinzufügen der Busse zum Energiesystem-Modell 
energysystem.add(b_gas_m, b_oil_fuel_m, b_bio_m, b_bioWood_m, b_dist_heat_m, b_H2_m, b_solidf_m)

"""
Export block
"""
#------------------------------------------------------------------------------  
# Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Electricity_m', 
    inputs={b_el_middle: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_middle'],
                              variable_costs = [i *(-1) for i in sequences['Energy_price']['Strompreis_brain_'+str(YEAR)]]
    )}))

#------------------------------------------------------------------------------
# Hydrogen export
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Hydrogen_m', 
    inputs={b_H2_m: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                              variable_costs = [i*(-1) for i in sequences['Energy_price']['Hydrogen_' + str(YEAR)]]
                              
    )}))

"""
Defining final energy demand as Sinks
"""
#------------------------------------------------------------------------------
# Electricity demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Electricity_demand_total_m', 
    inputs={b_el_middle: solph.Flow(fix=demand['electricity']['middle'], 
                              nominal_value=1,
    )}))
#------------------------------------------------------------------------------
# Biomass demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Biomass_demand_total_m', 
    inputs={b_solidf_m: solph.Flow(fix=demand['biomass']['middle'], 
                                nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Gas demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Gas_demand_total_m', 
    inputs={b_gas_m: solph.Flow(fix=demand['gas']['middle'], 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Material demand: Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Material_demand_Gas_m', 
    inputs={b_gas_m: solph.Flow(fix=demand['material_usage_gas']['middle'], 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Oil demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Oil_demand_total_m', 
    inputs={b_oil_fuel_m: solph.Flow(fix=demand['oil']['middle'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Mobility demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Mobility_demand_total_m', 
    inputs={b_oil_fuel_m: solph.Flow(fix=demand['fuel']['middle'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Material demand: Oil
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Material_demand_Oil_m', 
    inputs={b_oil_fuel_m: solph.Flow(fix=demand['material_usage_oil']['middle'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Heat demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Heat_demand_total_m', 
    inputs={b_dist_heat_m: solph.Flow(fix=demand['dist_heating']['middle'], 
                                nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Hydrogen demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Hydrogen_demand_total_m', 
    inputs={b_H2_m: solph.Flow(fix=demand['H2']['middle'], 
                              nominal_value=1,
    )}))


"""
Renewable Energy sources
"""
#------------------------------------------------------------------------------
# Wind power plants
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Wind_Erfurt', 
    outputs={b_el_middle: solph.Flow(fix=middle.Wind_feed_in_profile['Wind_feed_in'],
                                    custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_onshore_wind_power_plant']['potential_middle'][model_ID])
    )}))
#------------------------------------------------------------------------------
# Photovoltaic Rooftop systems
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_rooftop_Erfurt', 
    outputs={b_el_middle: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_middle'],
                                    custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_middle'][model_ID])
    )}))
#------------------------------------------------------------------------------
# Photovoltaic Openfield systems
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_Freifeld_Erfurt', 
    outputs={b_el_middle: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_middle'],
                                    custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_middle'][model_ID])
    )}))

#------------------------------------------------------------------------------
# Hydroenergy
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Hydro power plant_m', 
    outputs={b_el_middle: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                    custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                minimum=scalars['Parameter_run_river_power_plant']['potential_middle'][model_ID], 
                                                                maximum = scalars['Parameter_run_river_power_plant']['potential_middle'][model_ID])
    )}))

#------------------------------------------------------------------------------
# Solar thermal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='ST_m', 
    outputs={b_dist_heat_m: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                      custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                      investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                  maximum=scalars['Parameter_solar_thermal_power_plant']['potential_middle'][model_ID])
    )}))

""" Imports """

#------------------------------------------------------------------------------
# Import Solid fuel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_solid_fuel_m',
    outputs={b_bio_m: solph.Flow(variable_costs = sequences['Energy_price']['Biomass_'+ str(YEAR)],
                                      custom_attributes={'BiogasNeuanlagen_factor': 1},
                               
    )}))

#------------------------------------------------------------------------------
# solid Biomass
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Wood_m',
    outputs={b_bioWood_m: solph.Flow(variable_costs =sequences['Energy_price']['Biomass_'+ str(YEAR)],
                                          custom_attributes={'Biomasse_factor': 1},
                                   
    )}))

#------------------------------------------------------------------------------
# Import Brown-coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_brown_coal_m',
    outputs={b_solidf_m: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                fix=sequences['Base_demand_profile']['base_load'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=scalars['System_configurations']['System']['Menge_Braunkohle']*len(import_price['import_brown_coal_price']),
                                custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Braunkohle']},
    )}))

#------------------------------------------------------------------------------
# Import hard coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_hard_coal_m',
    outputs={b_solidf_m: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
                                fix=sequences['Base_demand_profile']['base_load'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=scalars['System_configurations']['System']['Menge_Steinkohle']*len(import_price['import_brown_coal_price']),
                                custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Steinkohle']},
                                
    )}))

#------------------------------------------------------------------------------
# Import Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Gas_m',
    outputs={b_gas_m: solph.Flow(variable_costs = import_price['import_gas_price'],
                                      custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Erdgas']},
                               
    )}))

#------------------------------------------------------------------------------
# Import Oil
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Oil_m',
    outputs={b_oil_fuel_m: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                  custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Oel']}
                                           
        )}))

#------------------------------------------------------------------------------
# Import Synthetic fuel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Synthetic_fuel_m',
    outputs={b_oil_fuel_m: solph.Flow(variable_costs = sequences['Energy_price']['Synthetic_fuel_'+ str(YEAR)],
        )}))

"""
Energy storage
"""

#------------------------------------------------------------------------------
# Electricity storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Battery_m',
    inputs={b_el_middle: solph.Flow()},
    outputs={b_el_middle: solph.Flow()},
    loss_rate=0,
    inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
    balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                    maximum=scalars['Parameter_storage_electricity']['potential_middle'][model_ID],
                                    )
    ))

#------------------------------------------------------------------------------
# Heat storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Heat storage_m',
    inputs={b_dist_heat_m: solph.Flow(
                              custom_attributes={'keywordWSP': 1},
                              nominal_value=float(scalars['Parameter_storage_heat']['potential'][model_ID]/scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
                              #nonconvex=solph.NonConvex()
                                )},
    outputs={b_dist_heat_m: solph.Flow(
                                custom_attributes={'keywordWSP': 1},
                                nominal_value=float(scalars['Parameter_storage_heat']['potential'][model_ID]/scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
                                #nonconvex=solph.NonConvex()
                                )},
    loss_rate=float(scalars['Parameter_storage_heat']['loss_rate'][model_ID]/24),
    inflow_conversion_factor=scalars['Parameter_storage_heat']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor=scalars['Parameter_storage_heat']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_heat']['initial_storage_level'][model_ID],
    balanced=bool(scalars['Parameter_storage_heat']['balanced'][model_ID]),
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
    nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat']['epc'], 
                                  )
    ))


#------------------------------------------------------------------------------
# Pumped hydro storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label="Pumped_hydro_storage_m",
    inputs={b_el_middle: solph.Flow()},
    outputs={b_el_middle: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology']['epc'],
                                  minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_min'][model_ID],
                                  maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_max'][model_ID])
    ))

#------------------------------------------------------------------------------
# Gas storage
#------------------------------------------------------------------------------ 
energysystem.add(solph.components.GenericStorage(
    label="Gas storage_m",
    inputs={b_gas_m: solph.Flow()},
    outputs={b_gas_m: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                  maximum = scalars['Parameter_storage_gas']['potential_middle'][model_ID])      
    ))

#------------------------------------------------------------------------------
# H2 Storage
#------------------------------------------------------------------------------    
energysystem.add(solph.components.GenericStorage(
    label="H2_storage_m",
    inputs={b_H2_m: solph.Flow()},
    outputs={b_H2_m: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_hydrogen']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                  maximum = scalars['Parameter_storage_hydrogen']['potential_middle'][model_ID])  
    ))

"""
Transformers
"""
#------------------------------------------------------------------------------
# Elektrolysis
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Elektrolysis_m",
    inputs={b_el_middle: solph.Flow()},
    outputs={b_H2_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc'], 
                                                              maximum=scalars['Parameter_electrolysis']['potential'][model_ID]))},
    conversion_factors={b_H2_m: scalars['Parameter_electrolysis']['efficiency_'+str(YEAR)][model_ID]},
    ))

#------------------------------------------------------------------------------
# Electric boiler
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Electric boiler_m",
    inputs={b_el_middle: solph.Flow()},
    outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
    conversion_factors={b_dist_heat_m: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]}   
    ))

#------------------------------------------------------------------------------
# Gas and Steam turbine
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='GuD_m',
    inputs={b_gas_m: solph.Flow(custom_attributes={'time_factor' :1})},
    outputs={b_el_middle: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                          maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential'][model_ID])),
              b_dist_heat_m: solph.Flow()},
    conversion_factors={b_el_middle: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID], 
                        b_dist_heat_m: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Fuel cells
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Fuelcell_m",
    inputs={b_H2_m: solph.Flow()},
    outputs={b_el_middle: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                            maximum=scalars['Parameter_fuel_cells']['potential'][model_ID]))},
    conversion_factors={b_el_middle: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Methanisation
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Methanisation_m",
    inputs={b_H2_m: solph.Flow()},
    outputs={b_gas_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                              maximum=scalars['Parameter_methanation']['potential'][model_ID]))},
    conversion_factors={b_gas_m: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]}    
    ))

#------------------------------------------------------------------------------
# Biogas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biogas_m',
    inputs={b_bio_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                    #nominal_value=1,
                                    investment = solph.Investment(ep_costs=0),
                                    custom_attributes={'BiogasBestand_factor': scalars['Parameter_bio_power_unit_Biogas']['existing_factor'][model_ID]})},
                              
    outputs={b_el_middle: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogas']['epc']), 
                                    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogas']['EE_factor'][model_ID]},
                                    fix=sequences['Base_demand_profile']['base_load']),
              b_dist_heat_m: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogas']['EE_factor'][model_ID]},
                                      fix=sequences['Base_demand_profile']['base_load'],
                                      #nominal_value= 1
                                      investment = solph.Investment(ep_costs=0)
                                      )},
    conversion_factors={b_el_middle: scalars['Parameter_bio_power_unit_Biogas']['efficiency_el_'+str(YEAR)][model_ID], 
                        b_dist_heat_m: scalars['Parameter_bio_power_unit_Biogas']['efficiency_th_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biomasse (for electricty production)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_elec_m',
    inputs={b_bioWood_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_el_middle: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                              investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biomass']['epc']),
                              custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biomass']['EE_factor'][model_ID]})},
    conversion_factors={b_el_middle: scalars['Parameter_bio_power_unit_Biomass']['efficiency_el_' +str(YEAR)][model_ID]}
    ))        

#------------------------------------------------------------------------------
# Biomasse (for heat production)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_heat_m',
    inputs={b_bioWood_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_dist_heat_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biomass']['epc']),
                                custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biomass']['EE_factor'][model_ID]})},
    conversion_factors={b_dist_heat_m: scalars['Parameter_bio_power_unit_Biomass']['efficiency_th_' +str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung mit bereits bestehenden Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogas_feedin_existing_m",
    inputs={b_bio_m: solph.Flow(custom_attributes={'BiogasBestand_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['existing_factor'][model_ID]},
                                    fix=sequences['Base_demand_profile']['base_load'],
                                    investment = solph.Investment(ep_costs=0)
                                    #nominal_value = 1
                                    )},
    outputs={b_gas_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment = solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogaseinspeisung_Bestand']['epc']),
                                )},
    conversion_factors={b_gas_m: scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['efficiency_'+str(YEAR)][model_ID]},
    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['EE_factor'][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung ohne bereits bestehende Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogas_feed_in_new_m",
    inputs={b_bio_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                    investment = solph.Investment(ep_costs=0)
                                    )},
    outputs={b_gas_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment = solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogaseinspeisung_Neu']['epc']),
                                )},
    conversion_factors={b_gas_m: scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['efficiency_'+str(YEAR)][model_ID]},
    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['EE_factor'][model_ID]}
                                
    ))

# -----------------------------------------------------------------------------
# Hydroden feed-in
# -----------------------------------------------------------------------------
maximale_Wasserstoffeinspeisung_Lastgang_m = [None] * len(demand['gas']['middle'])
maximale_Wasserstoffeinspeisung_m=0
for a in range(0, len(demand['gas']['middle'])):
    maximale_Wasserstoffeinspeisung_Lastgang_m[a]=(demand['gas']['middle'][a]*(scalars['Parameter_hydrogen_feed_in']['potential'][model_ID]))/(scalars['Parameter_hydrogen_feed_in']['efficiency_'+str(YEAR)][model_ID])
    if maximale_Wasserstoffeinspeisung_Lastgang_m[a] > maximale_Wasserstoffeinspeisung_m:
        maximale_Wasserstoffeinspeisung_m = maximale_Wasserstoffeinspeisung_Lastgang_m[a]

energysystem.add(solph.components.Converter(
    label='Hydrogen_feedin_m',
    inputs={b_H2_m: solph.Flow()},
    outputs={b_gas_m: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang_m,
                                investment=solph.Investment(ep_costs=epc_costs['hydrogen_feed_in']['epc'], 
                                                            maximum=max(maximale_Wasserstoffeinspeisung_Lastgang_m)))}
    ))

#------------------------------------------------------------------------------
# Heatpump_river
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Heatpump_water_m",
    inputs={b_el_middle: solph.Flow()},
    outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                              maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential'][model_ID]))},
    conversion_factors={b_dist_heat_m: scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},    
    ))

#------------------------------------------------------------------------------
# Heatpump: Recovery heat
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Heatpump_air_m",
    inputs={b_el_middle: solph.Flow()},
    outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
                                                              maximum=scalars['Parameter_heat_pump_air_Abwärme']['potential'][model_ID]))},
    conversion_factors={b_dist_heat_m: scalars['Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]},    
    ))

#------------------------------------------------------------------------------
# Power-to-Liquid
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="PtL_m",
    inputs={b_H2_m: solph.Flow()},
    outputs={b_oil_fuel_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                          maximum=scalars['Parameter_power_to_liquid_system']['potential'][model_ID]))},
    conversion_factors={b_oil_fuel_m: scalars['Parameter_power_to_liquid_system']['efficiency_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Solid biomass in the same bus as coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="BioTransformer_m",
    inputs={b_bioWood_m: solph.Flow()},
    outputs={b_solidf_m: solph.Flow()},
    ))

"""
Excess energy capture sinks 
"""
#------------------------------------------------------------------------------
# Überschuss Senke für Strom
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_el_m', 
    inputs={b_el_middle: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_gas_m', 
    inputs={b_gas_m: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Oel/Kraftstoffe
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_oil_fuel_m', 
    inputs={b_oil_fuel_m: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Biomasse
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_bio_m', 
    inputs={b_bio_m: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Waerme
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_distheat_m', 
    inputs={b_dist_heat_m: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Wasserstoff
#-----------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_H2_m', 
    inputs={b_H2_m: solph.Flow(variable_costs = 10000000
    )}))


##############################################################      Southwest region         #################################################################
""" Defining energy system for Southwest region"""

#------------------------------------------------------------------------------
# Gas Bus
#------------------------------------------------------------------------------
b_gas_s = solph.buses.Bus(label="Gas_s")
#------------------------------------------------------------------------------
# Oil/fuel Bus
#------------------------------------------------------------------------------
b_oil_fuel_s = solph.buses.Bus(label="Oil_fuel_s")
#------------------------------------------------------------------------------
# Biomass Bus
#------------------------------------------------------------------------------
b_bio_s = solph.buses.Bus(label="Biomass_s")
#------------------------------------------------------------------------------
# Solid Biomass Bus
#------------------------------------------------------------------------------
b_bioWood_s = solph.buses.Bus(label="BioWood_s")
#------------------------------------------------------------------------------
# District heating Bus
#------------------------------------------------------------------------------
b_dist_heat_s = solph.buses.Bus(label="District heating_s")
#------------------------------------------------------------------------------
# Hydrogen Bus
#------------------------------------------------------------------------------
b_H2_s = solph.buses.Bus(label="Hydrogen_s")
#------------------------------------------------------------------------------
# Solidfuel Bus
#------------------------------------------------------------------------------
b_solidf_s = solph.buses.Bus(label="Solidfuel_s")

# Hinzufügen der Busse zum Energiesystem-Modell 
energysystem.add(b_gas_s, b_oil_fuel_s, b_bio_s, b_bioWood_s, b_dist_heat_s, b_H2_s, b_solidf_s)

"""
Export block
"""
#------------------------------------------------------------------------------  
# Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Electricity_s', 
    inputs={b_el_swest: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_swest'],
                              variable_costs = [i *(-1) for i in sequences['Energy_price']['Strompreis_brain_'+str(YEAR)]]
    )}))

#------------------------------------------------------------------------------
# Hydrogen export
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Hydrogen_s', 
    inputs={b_H2_s: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                              variable_costs = [i*(-1) for i in sequences['Energy_price']['Hydrogen_' + str(YEAR)]]
                              
    )}))

"""
Defining final energy demand as Sinks
"""
#------------------------------------------------------------------------------
# Electricity demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Electricity_demand_total_s', 
    inputs={b_el_swest: solph.Flow(fix=demand['electricity']['swest'], 
                              nominal_value=1,
    )}))
#------------------------------------------------------------------------------
# Biomass demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Biomass_demand_total_s', 
    inputs={b_solidf_s: solph.Flow(fix=demand['biomass']['swest'], 
                                nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Gas demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Gas_demand_total_s', 
    inputs={b_gas_s: solph.Flow(fix=demand['gas']['swest'], 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Material demand: Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Material_demand_Gas_s', 
    inputs={b_gas_s: solph.Flow(fix=demand['material_usage_gas']['swest'], 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Oil demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Oil_demand_total_s', 
    inputs={b_oil_fuel_s: solph.Flow(fix=demand['oil']['swest'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Mobility demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Mobility_demand_total_s', 
    inputs={b_oil_fuel_s: solph.Flow(fix=demand['fuel']['swest'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Material demand: Oil
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Material_demand_Oil_s', 
    inputs={b_oil_fuel_s: solph.Flow(fix=demand['material_usage_oil']['swest'], 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Heat demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Heat_demand_total_s', 
    inputs={b_dist_heat_s: solph.Flow(fix=demand['dist_heating']['swest'], 
                                nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Hydrogen demand
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Hydrogen_demand_total_s', 
    inputs={b_H2_s: solph.Flow(fix=demand['H2']['swest'], 
                              nominal_value=1,
    )}))


"""
Renewable Energy sources
"""
#------------------------------------------------------------------------------
# Wind power plants
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Wind_Hildburghausen', 
    outputs={b_el_swest: solph.Flow(fix=swest.Wind_feed_in_profile['Wind_feed_in'],
                                    custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_onshore_wind_power_plant']['potential_swest'][model_ID])
    )}))
#------------------------------------------------------------------------------
# Photovoltaic Rooftop systems
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_rooftop_Hildburghausen', 
    outputs={b_el_swest: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_swest'],
                                    custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_swest'][model_ID])
    )}))
#------------------------------------------------------------------------------
# Photovoltaic Openfield systems
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_Freifeld_Hildburghausen', 
    outputs={b_el_swest: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_swest'],
                                    custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_swest'][model_ID])
    )}))

#------------------------------------------------------------------------------
# Hydroenergy
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Hydro power plant_s', 
    outputs={b_el_swest: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                    custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                    investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                minimum=scalars['Parameter_run_river_power_plant']['potential_swest'][model_ID], 
                                                                maximum = scalars['Parameter_run_river_power_plant']['potential_swest'][model_ID])
    )}))

#------------------------------------------------------------------------------
# Solar thermal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='ST_s', 
    outputs={b_dist_heat_s: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                      custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                      investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                  maximum=scalars['Parameter_solar_thermal_power_plant']['potential_swest'][model_ID])
    )}))

""" Imports """

#------------------------------------------------------------------------------
# Import Solid fuel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_solid_fuel_s',
    outputs={b_bio_s: solph.Flow(variable_costs = sequences['Energy_price']['Biomass_'+ str(YEAR)],
                                      custom_attributes={'BiogasNeuanlagen_factor': 1},
                               
    )}))

#------------------------------------------------------------------------------
# solid Biomass
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Wood_s',
    outputs={b_bioWood_s: solph.Flow(variable_costs =sequences['Energy_price']['Biomass_'+ str(YEAR)],
                                          custom_attributes={'Biomasse_factor': 1},
                                   
    )}))

#------------------------------------------------------------------------------
# Import Brown-coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_brown_coal_s',
    outputs={b_solidf_s: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                fix=sequences['Base_demand_profile']['base_load'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=scalars['System_configurations']['System']['Menge_Braunkohle']*len(import_price['import_brown_coal_price']),
                                custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Braunkohle']},
    )}))

#------------------------------------------------------------------------------
# Import hard coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_hard_coal_s',
    outputs={b_solidf_s: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
                                fix=sequences['Base_demand_profile']['base_load'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=scalars['System_configurations']['System']['Menge_Steinkohle']*len(import_price['import_brown_coal_price']),
                                custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Steinkohle']},
                                
    )}))

#------------------------------------------------------------------------------
# Import Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Gas_s',
    outputs={b_gas_s: solph.Flow(variable_costs = import_price['import_gas_price'],
                                      custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Erdgas']},
                               
    )}))

#------------------------------------------------------------------------------
# Import Oil
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Oil_s',
    outputs={b_oil_fuel_s: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                  custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Oel']}
                                           
        )}))

#------------------------------------------------------------------------------
# Import Synthetic fuel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Synthetic_fuel_s',
    outputs={b_oil_fuel_s: solph.Flow(variable_costs = sequences['Energy_price']['Synthetic_fuel_'+ str(YEAR)],
        )}))

"""
Energy storage
"""

#------------------------------------------------------------------------------
# Electricity storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Battery_s',
    inputs={b_el_swest: solph.Flow()},
    outputs={b_el_swest: solph.Flow()},
    loss_rate=0,
    inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
    balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                    maximum=scalars['Parameter_storage_electricity']['potential_swest'][model_ID],
                                    )
    ))

#------------------------------------------------------------------------------
# Heat storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Heat storage_s',
    inputs={b_dist_heat_s: solph.Flow(
                              custom_attributes={'keywordWSP': 1},
                              nominal_value=float(scalars['Parameter_storage_heat']['potential'][model_ID]/scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
                              #nonconvex=solph.NonConvex()
                                )},
    outputs={b_dist_heat_s: solph.Flow(
                                custom_attributes={'keywordWSP': 1},
                                nominal_value=float(scalars['Parameter_storage_heat']['potential'][model_ID]/scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
                                #nonconvex=solph.NonConvex()
                                )},
    loss_rate=float(scalars['Parameter_storage_heat']['loss_rate'][model_ID]/24),
    inflow_conversion_factor=scalars['Parameter_storage_heat']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor=scalars['Parameter_storage_heat']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_heat']['initial_storage_level'][model_ID],
    balanced=bool(scalars['Parameter_storage_heat']['balanced'][model_ID]),
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat']['inverse_c_rate'][model_ID]),
    nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat']['epc'], 
                                  )
    ))


#------------------------------------------------------------------------------
# Pumped hydro storage
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label="Pumped_hydro_storage_s",
    inputs={b_el_swest: solph.Flow()},
    outputs={b_el_swest: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology']['epc'],
                                  minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_min'][model_ID],
                                  maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_max'][model_ID])
    ))

#------------------------------------------------------------------------------
# Gas storage
#------------------------------------------------------------------------------ 
energysystem.add(solph.components.GenericStorage(
    label="Gas storage_s",
    inputs={b_gas_s: solph.Flow()},
    outputs={b_gas_s: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                  maximum = scalars['Parameter_storage_gas']['potential_swest'][model_ID])     
    ))

#------------------------------------------------------------------------------
# H2 Storage
#------------------------------------------------------------------------------    
energysystem.add(solph.components.GenericStorage(
    label="H2_storage_s",
    inputs={b_H2_s: solph.Flow()},
    outputs={b_H2_s: solph.Flow()},
    loss_rate=0,
    balanced=bool(scalars['Parameter_storage_hydrogen']['balanced'][model_ID]),
    inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID],
    outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID],
    initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
    invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
    invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
    investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                  maximum = scalars['Parameter_storage_hydrogen']['potential_swest'][model_ID])  
    ))

"""
Transformers
"""
#------------------------------------------------------------------------------
# Elektrolysis
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Elektrolysis_s",
    inputs={b_el_swest: solph.Flow()},
    outputs={b_H2_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc']))},
    conversion_factors={b_dist_heat_s: scalars['Parameter_electrolysis']['efficiency_' +str(YEAR)][model_ID]} 
    ))

#------------------------------------------------------------------------------
# Electric boiler
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Electric boiler_s",
    inputs={b_el_swest: solph.Flow()},
    outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
    conversion_factors={b_dist_heat_s: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]}   
    ))

#------------------------------------------------------------------------------
# Gas and Steam turbine
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='GuD_s',
    inputs={b_gas_s: solph.Flow(custom_attributes={'time_factor' :1})},
    outputs={b_el_swest: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                          maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential'][model_ID])),
              b_dist_heat_s: solph.Flow()},
    conversion_factors={b_el_swest: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID], 
                        b_dist_heat_s: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Fuel cells
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Fuelcell_s",
    inputs={b_H2_s: solph.Flow()},
    outputs={b_el_swest: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                            maximum=scalars['Parameter_fuel_cells']['potential'][model_ID]))},
    conversion_factors={b_el_swest: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Methanisation
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Methanisation_s",
    inputs={b_H2_s: solph.Flow()},
    outputs={b_gas_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                              maximum=scalars['Parameter_methanation']['potential'][model_ID]))},
    conversion_factors={b_gas_s: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]}    
    ))

#------------------------------------------------------------------------------
# Biogas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biogas_s',
    inputs={b_bio_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                    #nominal_value=1,
                                    investment = solph.Investment(ep_costs=0),
                                    custom_attributes={'BiogasBestand_factor': scalars['Parameter_bio_power_unit_Biogas']['existing_factor'][model_ID]})},
                              
    outputs={b_el_swest: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogas']['epc']), 
                                    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogas']['EE_factor'][model_ID]},
                                    fix=sequences['Base_demand_profile']['base_load']),
              b_dist_heat_s: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogas']['EE_factor'][model_ID]},
                                      fix=sequences['Base_demand_profile']['base_load'],
                                      #nominal_value= 1
                                      investment = solph.Investment(ep_costs=0)
                                      )},
    conversion_factors={b_el_swest: scalars['Parameter_bio_power_unit_Biogas']['efficiency_el_'+str(YEAR)][model_ID], 
                        b_dist_heat_s: scalars['Parameter_bio_power_unit_Biogas']['efficiency_th_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biomasse (for electricty production)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_elec_s',
    inputs={b_bioWood_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_el_swest: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                              investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biomass']['epc']),
                              custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biomass']['EE_factor'][model_ID]})},
    conversion_factors={b_el_swest: scalars['Parameter_bio_power_unit_Biomass']['efficiency_el_' +str(YEAR)][model_ID]}
    ))        

#------------------------------------------------------------------------------
# Biomasse (for heat production)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_heat_s',
    inputs={b_bioWood_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_dist_heat_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment=solph.Investment(ep_costs=epc_costs['bio_power_unit_Biomass']['epc']),
                                custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biomass']['EE_factor'][model_ID]})},
    conversion_factors={b_dist_heat_s: scalars['Parameter_bio_power_unit_Biomass']['efficiency_th_' +str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung mit bereits bestehenden Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogas_feedin_existing_s",
    inputs={b_bio_s: solph.Flow(custom_attributes={'BiogasBestand_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['existing_factor'][model_ID]},
                                    fix=sequences['Base_demand_profile']['base_load'],
                                    investment = solph.Investment(ep_costs=0)
                                    #nominal_value = 1
                                    )},
    outputs={b_gas_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment = solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogaseinspeisung_Bestand']['epc']),
                                )},
    conversion_factors={b_gas_s: scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['efficiency_'+str(YEAR)][model_ID]},
    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['EE_factor'][model_ID]}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung ohne bereits bestehende Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogas_feed_in_new_s",
    inputs={b_bio_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                    investment = solph.Investment(ep_costs=0)
                                    )},
    outputs={b_gas_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                investment = solph.Investment(ep_costs=epc_costs['bio_power_unit_Biogaseinspeisung_Neu']['epc']),
                                )},
    conversion_factors={b_gas_s: scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['efficiency_'+str(YEAR)][model_ID]},
    custom_attributes={'emission_factor': scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['EE_factor'][model_ID]}
                                
    ))

# -----------------------------------------------------------------------------
# Hydroden feed-in
# -----------------------------------------------------------------------------
maximale_Wasserstoffeinspeisung_Lastgang_s = [None] * len(demand['gas']['swest'])
maximale_Wasserstoffeinspeisung_s=0
for a in range(0, len(demand['gas']['swest'])):
    maximale_Wasserstoffeinspeisung_Lastgang_s[a]=(demand['gas']['swest'][a]*(scalars['Parameter_hydrogen_feed_in']['potential'][model_ID]))/(scalars['Parameter_hydrogen_feed_in']['efficiency_'+str(YEAR)][model_ID])
    if maximale_Wasserstoffeinspeisung_Lastgang_s[a] > maximale_Wasserstoffeinspeisung_s:
        maximale_Wasserstoffeinspeisung_s = maximale_Wasserstoffeinspeisung_Lastgang_s[a]

energysystem.add(solph.components.Converter(
    label='Hydrogen_feedin_s',
    inputs={b_H2_s: solph.Flow()},
    outputs={b_gas_s: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang_s,
                                investment=solph.Investment(ep_costs=epc_costs['hydrogen_feed_in']['epc'], 
                                                            maximum=max(maximale_Wasserstoffeinspeisung_Lastgang_s)))}
    ))

#------------------------------------------------------------------------------
# Heatpump_river
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Heatpump_water_s",
    inputs={b_el_swest: solph.Flow()},
    outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                              maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential'][model_ID]))},
    conversion_factors={b_dist_heat_s: scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},    
    ))

#------------------------------------------------------------------------------
# Heatpump: Recovery heat
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Heatpump_air_s",
    inputs={b_el_swest: solph.Flow()},
    outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
                                                              maximum=scalars['Parameter_heat_pump_air_Abwärme']['potential'][model_ID]))},
    conversion_factors={b_dist_heat_s: scalars['Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]},    
    ))

#------------------------------------------------------------------------------
# Power-to-Liquid
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="PtL_s",
    inputs={b_H2_s: solph.Flow()},
    outputs={b_oil_fuel_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                        maximum=scalars['Parameter_power_to_liquid_system']['potential'][model_ID]))},
    conversion_factors={b_oil_fuel_s: scalars['Parameter_power_to_liquid_system']['efficiency_'+str(YEAR)][model_ID]}
    ))

#------------------------------------------------------------------------------
# Solid biomass in the same bus as coal
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="BioTransformer_s",
    inputs={b_bioWood_s: solph.Flow()},
    outputs={b_solidf_s: solph.Flow()},
    ))

"""
Excess energy capture sinks 
"""
#------------------------------------------------------------------------------
# Überschuss Senke für Strom
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_el_s', 
    inputs={b_el_swest: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_gas_s', 
    inputs={b_gas_s: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Oel/Kraftstoffe
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_oil_fuel_s', 
    inputs={b_oil_fuel_s: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Biomasse
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_bio_s', 
    inputs={b_bio_s: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Waerme
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_distheat_s', 
    inputs={b_dist_heat_s: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Wasserstoff
#-----------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_H2_s', 
    inputs={b_H2_s: solph.Flow(variable_costs = 10000000
    )}))

# Prepare a dataset for exporting, to have access after the simulation 
sim_data = {'Timeseries': sequences,
            'Parameter': scalars,
            'Loadprofiles':demand,
            'epc_costs':investment_parameter,
            'North': north,
            'East': east,
            'Swest': swest,
            'Middle': middle}

logging.info('Optimise the energy system')

# initialise the operational model
model = solph.Model(energysystem)

#------------------------------------------------------------------------------
# Bilanziell erneuerbar
#------------------------------------------------------------------------------

SummeLasten=(sum(demand['electricity']['north'])+ sum(demand['electricity']['east'])+sum(demand['electricity']['middle'])+sum(demand['electricity']['swest'])+
              sum(demand['gas']['north'])+ sum(demand['gas']['east'])+sum(demand['gas']['middle'])+sum(demand['gas']['swest'])+
              sum(demand['oil']['north'])+ sum(demand['oil']['east'])+sum(demand['oil']['middle'])+sum(demand['oil']['swest'])+
              sum(demand['fuel']['north'])+ sum(demand['fuel']['east'])+sum(demand['fuel']['middle'])+sum(demand['fuel']['swest'])+
              sum(demand['dist_heating']['north'])+ sum(demand['dist_heating']['east'])+sum(demand['dist_heating']['middle'])+sum(demand['dist_heating']['swest'])+
              sum(demand['H2']['north'])+ sum(demand['H2']['east'])+sum(demand['H2']['middle'])+sum(demand['H2']['swest']))
             


Anteilig_erneuerbar = True

if Anteilig_erneuerbar == True:
    constraints.emission_limit(model, limit=-SummeLasten*0.55)
    GuD_time(model, limit=0, Starttime=1777, Endtime=7656)
    
#------------------------------------------------------------------------------
# Aktivierung der Begrenzungen
#------------------------------------------------------------------------------
CO2_limit(model, limit=scalars['System_configurations']['System']['CO2_Grenze_2030'])
BiogasBestand_limit(model, limit=scalars['Parameter_bio_power_unit_Biogaseinspeisung_Bestand']['potential'][model_ID])
BiogasNeuanlagen_limit(model, limit=scalars['Parameter_bio_power_unit_Biogaseinspeisung_Neu']['potential'][model_ID])
Biomasse_limit(model, limit=scalars['Parameter_bio_power_unit_Biomass']['potential'][model_ID])

if debug:
    filename = os.path.join(
        solph.helpers.extend_basic_path('lp_files'), 'Energiesystemmodell_Thueringen_2030.lp')
    logging.info('Store lp-file in {0}.'.format(filename))
    model.write(filename, io_options={'symbolic_solver_labels': True})

logging.info('Solve the optimization problem')
model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})
logging.info('Store the energy system with the results.')

# The processing module of the outputlib can be used to extract the results
# from the model transfer them into a homogeneous structured dictionary.

# add results to the energy system to make it possible to store them.
energysystem.results['main'] = solph.processing.results(model)
energysystem.results['meta'] = solph.processing.meta_results(model)

# The default path is the '.oemof' folder in your $HOME directory.
# The default filename is 'es_dump.oemof'.
# You can omit the attributes (as None is the default value) for testing cases.
# You should use unique names/folders for valuable results to avoid
# overwriting.

# store energy system with results
energysystem.dump(dpath=None, filename=None)
