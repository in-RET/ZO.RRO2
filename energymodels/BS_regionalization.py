# -*- coding: utf-8 -*-
"""
Created on Wed Sep  4 13:18:19 2024

@author: rbala
"""

import os
workdir= os.getcwd()
import pandas as pd
from oemof import network, solph
from oemof.tools import economics

from src.preprocessing.create_input_dataframe import createDataFrames
from src.preprocessing.files import read_input_files
from src.preprocessing.conversion import investment_parameter, load_profile_scaling, CO2_price_addition
from src.preprocessing.location import Location


def BS_regionalization(PERMUATION: str) -> solph.EnergySystem:
    YEAR, VARIATION = PERMUATION.split("_")
    YEAR = int(YEAR)
    model_ID = 'BS0001'
    
    sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    demand = load_profile_scaling(scalars,sequences,YEAR)
    epc_costs = investment_parameter(scalars, YEAR, model_ID)
    import_price = CO2_price_addition(scalars,sequences, YEAR)
    
    Weather_dir = os.path.abspath(os.path.join(workdir,'./', 'data','weatherdata'))
    middle = Location(os.path.join(Weather_dir,'Erfurt_Binderslebn-hour.csv'), os.path.join(Weather_dir,'Erfurt_Binderslebn-min.dat'))
    north = Location(os.path.join(Weather_dir,'Nordhausen-hour.csv'), os.path.join(Weather_dir,'Nordhausen-min.dat'))
    swest= Location(os.path.join(Weather_dir,'Hildburghausen-hour.csv'), os.path.join(Weather_dir,'Hildburghausen-min.dat'))
    east = Location(os.path.join(Weather_dir,'Gera-Leumnitz-hour.csv'), os.path.join(Weather_dir,'Gera-Leumnitz-min.dat'))
  
    Planing_region = [middle, north, swest, east]
    """ Simulate Wind feed-in profile for the desired location """
    for L in Planing_region:
        L.Wind_feed_in_profile(YEAR)
        #L.PV_feed_in_profile(YEAR)
    
    
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
        outputs={b_hös: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power'],
                                  variable_costs = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee'] for i in sequences['Energy_price']['Strompreis_brain_'+str(YEAR)]],
                                  custom_attributes={'CO2_factor': scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]},
                                  
            )}))
    """Link between HöS & HS""" 
    energysystem.add(solph.components.Link(
        label='HöS<->HS',
        inputs= {b_hös: solph.Flow(),
                 b_hs: solph.Flow()},
        outputs= {b_hs: solph.Flow(),
                 b_hös: solph.Flow()},
        conversion_factors = {(b_hös,b_hs): 1, (b_hs,b_hös):1}
        
        ))
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
    #------------------------------------------------------------------------------  
    # Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Electricity_n', 
        inputs={b_el_north: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power_north'],
                                  variable_costs = [i *(-1) for i in sequences['Energy_price']['Strompreis_brain_'+str(YEAR)]],
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
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
        outputs={b_el_north: solph.Flow(fix=north.Wind_feed_in_profiel['Wind_feed_in'],
                                        custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_Factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=investment_parameter['onshore_wind_power_plant']['epc'], 
                                                                    maximum=scalars['Parameter_onshore_wind_power_plant']['potential_nord'][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_Nordhausen', 
        outputs={b_el_north: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_north'],
                                        custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_Factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=investment_parameter['rooftop_photovoltaic_power_plant']['epc'], 
                                                                    maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_nord'][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_Freifeld_Nordhausen', 
        outputs={b_el_north: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_north'],
                                        custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_Factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=investment_parameter['field_photovoltaic_power_plant']['epc'], 
                                                                    maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_nord'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant_n', 
        outputs={b_el_north: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                        custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_Factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=investment_parameter['run_river_power_plant']['epc'], 
                                                                    minimum=scalars['Parameter_run_river_power_plant']['potential_nord'][model_ID], 
                                                                    maximum = scalars['Parameter_run_river_power_plant']['potential_nord'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST_n', 
        outputs={b_dist_heat_n: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_Factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=investment_parameter['solar_thermal_power_plant']['epc'], 
                                                                      maximum=scalars['Parameter_solar_thermal_power_plant']['potential_nord'][model_ID])
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
                                    fix=sequences['base_demand_load']['base_load'], 
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
                                    fix=sequences['base_demand_load']['base_load'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=scalars['System_configurations']['System']['Menge_Steinkohle']*len(import_price['import_brown_coal_price']),
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
        inflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Natriumspeicher, 
                                        maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Potential'],
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Heat storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Heat storage_n',
        inputs={b_dist_heat_n: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_dist_heat_n: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(Parameter_Waermespeicher_2030['Waermespeicher']['Verlustrate']/24),
        inflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Waermespeicher_2030['Waermespeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Waermespeicher_2030['Waermespeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_Waermespeicher, 
                                     )
        ))
    
    
    #------------------------------------------------------------------------------
    # Pumped hydro storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label="Pumped_hydro_storage_n",
        inputs={b_el_north: solph.Flow()},
        outputs={b_el_north: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['balanced']),
        inflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Pumpspeicherkraftwerk,
                                      minimum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential_min'],
                                      maximum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential'])
        ))
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas storage_n",
        inputs={b_gas_n: solph.Flow()},
        outputs={b_gas_n: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Erdgasspeicher, 
                                      maximum = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Potential'])    
        ))
    
    #------------------------------------------------------------------------------
    # H2 Storage
    #------------------------------------------------------------------------------    
    energysystem.add(solph.components.GenericStorage(
        label="H2_storage_n",
        inputs={b_H2_n: solph.Flow()},
        outputs={b_H2_n: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Wasserstoffspeicher, 
                                      maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Potential'])    
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
        outputs={b_H2_n: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrolyse, 
                                                                 maximum=Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Potential']))},
        conversion_factors={b_H2_n: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Wirkungsgrad']},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler_n",
        inputs={b_el_north: solph.Flow()},
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrodenheizkessel))},
        conversion_factors={b_dist_heat_n: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['Wirkungsgrad']}    
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD_n',
        inputs={b_gas_n: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el_north: solph.Flow(investment=solph.Investment(ep_costs=epc_GuD,
                                                              maximum =Parameter_GuD_2030['GuD']['Potential'])),
                 b_dist_heat_n: solph.Flow()},
        conversion_factors={b_el_north: Parameter_GuD_2030['GuD']['Wirkungsgrad_el'], 
                            b_dist_heat_n: Parameter_GuD_2030['GuD']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell_n",
        inputs={b_H2_n: solph.Flow()},
        outputs={b_el_north: solph.Flow(investment = solph.Investment(ep_costs=epc_Brennstoffzelle, 
                                                                maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Potential']))},
        conversion_factors={b_el_north: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Wirkungsgrad']}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation_n",
        inputs={b_H2_n: solph.Flow()},
        outputs={b_gas_n: solph.Flow(investment = solph.Investment(ep_costs=epc_Methanisierung, 
                                                                 maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Potential']))},
        conversion_factors={b_gas_n: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Wirkungsgrad']}  
        ))
    
    #------------------------------------------------------------------------------
    # Biogas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas_n',
        inputs={b_bio_n: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': Parameter_Biomasse_Biogas_2030['Biogas']['BiogasBestand']})},
                                  
        outputs={b_el_north: solph.Flow(investment=solph.Investment(ep_costs=epc_Biogas), 
                                        custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast']),
                 b_dist_heat_n: solph.Flow(custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                          fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el_north: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_el'], 
                            b_dist_heat_n: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_n',
        inputs={b_bioWood_n: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                            #nominal_value = 1
                                            investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_north: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                  investment=solph.Investment(ep_costs=epc_Biomasse),
                                  custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_el_north: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_el']}
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat_n',
        inputs={b_bioWood_n: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                           #nominal_value = 1
                                           investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat_n: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                    investment=solph.Investment(ep_costs=epc_Biomasse),
                                    custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_dist_heat_n: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing_n",
        inputs={b_bio_n: solph.Flow(custom_attributes={'BiogasBestand_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['BiogasBestand']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas_n: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Bestandsanlagen),
                                   )},
        conversion_factors={b_gas_n: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['EE_Faktor']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feed_in_new_n",
        inputs={b_bio_n: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas_n: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Neuanlagen),
                                   )},
        conversion_factors={b_gas_n: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['EE_Faktor']}
                                    
        ))
    
    # -----------------------------------------------------------------------------
    # Hydroden feed-in
    # -----------------------------------------------------------------------------
    maximale_Wasserstoffeinspeisung_Lastgang_n = [None] * len(Last_Gas_Zusammen)
    maximale_Wasserstoffeinspeisung_n=0
    for a in range(0, len(Last_Gas_Zusammen)):
        maximale_Wasserstoffeinspeisung_Lastgang_n[a]=(Last_Gas_Zusammen[a]*(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Potential']))/(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Wirkungsgrad'])
        if maximale_Wasserstoffeinspeisung_Lastgang_n[a] > maximale_Wasserstoffeinspeisung_n:
            maximale_Wasserstoffeinspeisung_n = maximale_Wasserstoffeinspeisung_Lastgang_n[a]
    
    energysystem.add(solph.components.Converter(
        label='Hydrogen_feedin_n',
        inputs={b_H2_n: solph.Flow()},
        outputs={b_gas_n: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang_n,
                                   investment=solph.Investment(ep_costs=epc_Wasserstoffeinspeisung, 
                                                               maximum=max(maximale_Wasserstoffeinspeisung_Lastgang_n)))}
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water_n",
        inputs={b_el_north: solph.Flow()},
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Fluss, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['Potential']))},
        conversion_factors={b_dist_heat_n: Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air_n",
        inputs={b_el_north: solph.Flow()},
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Abwaerme, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['Potential']))},
        conversion_factors={b_dist_heat_n: Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL_n",
        inputs={b_H2_n: solph.Flow()},
        outputs={b_oil_fuel_n: solph.Flow(investment = solph.Investment(ep_costs=epc_PtL, 
                                                                             maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Potential']))},
        conversion_factors={b_oil_fuel_n: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Wirkungsgrad']}
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
    """ Defining energy system for North region"""
    
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
        inputs={b_el_east: solph.Flow(nominal_value = scalars['Parameter_Stromnetz_' + str(YEAR)]['Strom']['Max_Bezugsleistung'],
                                 variable_costs = [i*(-1) for i in sequences['Preise_2030_Stundenwerte']['Strompreis_2030']]
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen_e', 
        inputs={b_H2_e: solph.Flow(nominal_value = scalars['Parameter_Wasserstoffnetz_'+ str(YEAR)]['Wasserstoff']['Max_Bezugsleistung'],
                                 variable_costs = [i*(-1) for i in sequences['Preise_2030_Stundenwerte']['Wasserstoffpreis_2030']]
                                  
        )}))
    
    """
    Defining final energy demand as Sinks
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total_e', 
        inputs={b_el_east: solph.Flow(fix=Last_Strom_Zusammen, 
                                 nominal_value=1,
        )}))
    #------------------------------------------------------------------------------
    # Biomass demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Biomass_demand_total_e', 
        inputs={b_solidf_e: solph.Flow(fix=Last_Bio_Zusammen, 
                                   nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Gas demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Gas_demand_total_e', 
        inputs={b_gas_e: solph.Flow(fix=Last_Gas_Zusammen, 
                                  nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Material demand: Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Gas_e', 
        inputs={b_gas_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                  nominal_value=P_nom_Gas_Grundlast_Materialnutzung,
        )}))

    #------------------------------------------------------------------------------
    # Oil demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil_demand_total_e', 
        inputs={b_oil_fuel_e: solph.Flow(fix=Last_Oel_Zusammen, 
                                              nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Mobility demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Mobility_demand_total_e', 
        inputs={b_oil_fuel_e: solph.Flow(fix=Last_Verbrenner_Zusammen, 
                                              nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Material demand: Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Oil_e', 
        inputs={b_oil_fuel_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                              nominal_value=P_nom_Oel_Grundlast_Materialnutzung,
        )}))

    #------------------------------------------------------------------------------
    # Heat demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Heat_demand_total_e', 
        inputs={b_dist_heat_e: solph.Flow(fix=Last_Fernw_Zusammen, 
                                   nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Hydrogen_demand_total_e', 
        inputs={b_H2_e: solph.Flow(fix=Last_H2_Zusammen, 
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
        outputs={b_el_east: solph.Flow(fix=data_Wind_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wind, 
                                                                    maximum=Parameter_PV_Wind_2030['Wind']['Potential_Nordhausen_Nord'])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_Gera', 
        outputs={b_el_east: solph.Flow(fix=data_PV_Aufdach_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Nordhausen_Nord'])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_Freifeld_Gera', 
        outputs={b_el_east: solph.Flow(fix=data_PV_Freifeld_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Nordhausen_Nord'])
        )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant_e', 
        outputs={b_el_east: solph.Flow(fix=data_Wasserkraft,
                                        custom_attributes={'emission_factor': Parameter_Wasserkraft_2030['Wasserkraft']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wasserkraft, 
                                                                    minimum=Parameter_Wasserkraft_2030['Wasserkraft']['Potential'], 
                                                                    maximum = Parameter_Wasserkraft_2030['Wasserkraft']['Potential'])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST_e', 
        outputs={b_dist_heat_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Solarthermie'], 
                                          custom_attributes={'emission_factor': Parameter_ST_2030['Solarthermie']['EE_Faktor']},
                                          investment=solph.Investment(ep_costs=epc_ST, 
                                                                      maximum=Parameter_ST_2030['Solarthermie']['Potential'])
        )}))
    
    """ Imports """
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel_e',
        outputs={b_bio_e: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood_e',
        outputs={b_bioWood_e: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                             custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_brown_coal_e',
        outputs={b_solidf_e: solph.Flow(variable_costs = Import_Braunkohlepreis_2030,
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=data_Systemeigenschaften['System']['Menge_Braunkohle']*number_of_time_steps,
                                    custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Braunkohle']},
        )}))
    
    #------------------------------------------------------------------------------
    # Import hard coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_hard_coal_e',
        outputs={b_solidf_e: solph.Flow(variable_costs = Import_Steinkohlepreis_2030,
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=data_Systemeigenschaften['System']['Menge_Steinkohle']*number_of_time_steps,
                                    custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Steinkohle']},
                                    
        )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas_e',
        outputs={b_gas_e: solph.Flow(variable_costs = Import_Erdgaspreis_2030,
                                         custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Erdgas']},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil_e',
        outputs={b_oil_fuel_e: solph.Flow(variable_costs = Import_Oelpreis_2030,
                                                     custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Oel']}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel_e',
        outputs={b_oil_fuel_e: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Synthetische_Kraftstoffe_2030'],
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
        inflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Natriumspeicher, 
                                        maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Potential'],
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Heat storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Heat storage_e',
        inputs={b_dist_heat_e: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_dist_heat_e: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(Parameter_Waermespeicher_2030['Waermespeicher']['Verlustrate']/24),
        inflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Waermespeicher_2030['Waermespeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Waermespeicher_2030['Waermespeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_Waermespeicher, 
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
        balanced=bool(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['balanced']),
        inflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Pumpspeicherkraftwerk,
                                      minimum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential_min'],
                                      maximum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential'])
        ))
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas storage_e",
        inputs={b_gas_e: solph.Flow()},
        outputs={b_gas_e: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Erdgasspeicher, 
                                      maximum = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Potential'])    
        ))
    
    #------------------------------------------------------------------------------
    # H2 Storage
    #------------------------------------------------------------------------------    
    energysystem.add(solph.components.GenericStorage(
        label="H2_storage_e",
        inputs={b_H2_e: solph.Flow()},
        outputs={b_H2_e: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Wasserstoffspeicher, 
                                      maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Potential'])    
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
        outputs={b_H2_e: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrolyse, 
                                                                 maximum=Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Potential']))},
        conversion_factors={b_H2_e: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Wirkungsgrad']},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler_e",
        inputs={b_el_east: solph.Flow()},
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrodenheizkessel))},
        conversion_factors={b_dist_heat_e: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['Wirkungsgrad']}    
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD_e',
        inputs={b_gas_e: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el_east: solph.Flow(investment=solph.Investment(ep_costs=epc_GuD,
                                                              maximum =Parameter_GuD_2030['GuD']['Potential'])),
                 b_dist_heat_e: solph.Flow()},
        conversion_factors={b_el_east: Parameter_GuD_2030['GuD']['Wirkungsgrad_el'], 
                            b_dist_heat_e: Parameter_GuD_2030['GuD']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell_e",
        inputs={b_H2_e: solph.Flow()},
        outputs={b_el_east: solph.Flow(investment = solph.Investment(ep_costs=epc_Brennstoffzelle, 
                                                                maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Potential']))},
        conversion_factors={b_el_east: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Wirkungsgrad']}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation_e",
        inputs={b_H2_e: solph.Flow()},
        outputs={b_gas_e: solph.Flow(investment = solph.Investment(ep_costs=epc_Methanisierung, 
                                                                 maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Potential']))},
        conversion_factors={b_gas_e: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Wirkungsgrad']}  
        ))
    
    #------------------------------------------------------------------------------
    # Biogas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas_e',
        inputs={b_bio_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': Parameter_Biomasse_Biogas_2030['Biogas']['BiogasBestand']})},
                                  
        outputs={b_el_east: solph.Flow(investment=solph.Investment(ep_costs=epc_Biogas), 
                                        custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast']),
                 b_dist_heat_n: solph.Flow(custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                          fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el_east: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_el'], 
                            b_dist_heat_e: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_e',
        inputs={b_bioWood_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                            #nominal_value = 1
                                            investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_east: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                  investment=solph.Investment(ep_costs=epc_Biomasse),
                                  custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_el_east: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_el']}
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat_e',
        inputs={b_bioWood_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                           #nominal_value = 1
                                           investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                    investment=solph.Investment(ep_costs=epc_Biomasse),
                                    custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_dist_heat_e: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing_e",
        inputs={b_bio_e: solph.Flow(custom_attributes={'BiogasBestand_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['BiogasBestand']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Bestandsanlagen),
                                   )},
        conversion_factors={b_gas_e: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['EE_Faktor']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feed_in_new_e",
        inputs={b_bio_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas_e: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Neuanlagen),
                                   )},
        conversion_factors={b_gas_e: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['EE_Faktor']}
                                    
        ))
    
    # -----------------------------------------------------------------------------
    # Hydroden feed-in
    # -----------------------------------------------------------------------------
    maximale_Wasserstoffeinspeisung_Lastgang_e = [None] * len(Last_Gas_Zusammen)
    maximale_Wasserstoffeinspeisung_e=0
    for a in range(0, len(Last_Gas_Zusammen)):
        maximale_Wasserstoffeinspeisung_Lastgang_e[a]=(Last_Gas_Zusammen[a]*(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Potential']))/(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Wirkungsgrad'])
        if maximale_Wasserstoffeinspeisung_Lastgang_e[a] > maximale_Wasserstoffeinspeisung_e:
            maximale_Wasserstoffeinspeisung_e = maximale_Wasserstoffeinspeisung_Lastgang_e[a]
    
    energysystem.add(solph.components.Converter(
        label='Hydrogen_feedin_e',
        inputs={b_H2_e: solph.Flow()},
        outputs={b_gas_e: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang_e,
                                   investment=solph.Investment(ep_costs=epc_Wasserstoffeinspeisung, 
                                                               maximum=max(maximale_Wasserstoffeinspeisung_Lastgang_e)))}
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water_e",
        inputs={b_el_east: solph.Flow()},
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Fluss, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['Potential']))},
        conversion_factors={b_dist_heat_e: Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air_e",
        inputs={b_el_east: solph.Flow()},
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Abwaerme, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['Potential']))},
        conversion_factors={b_dist_heat_e: Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL_e",
        inputs={b_H2_e: solph.Flow()},
        outputs={b_oil_fuel_e: solph.Flow(investment = solph.Investment(ep_costs=epc_PtL, 
                                                                             maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Potential']))},
        conversion_factors={b_oil_fuel_e: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Wirkungsgrad']}
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
        inputs={b_el_middle: solph.Flow(nominal_value = scalars['Parameter_Stromnetz_' + str(YEAR)]['Strom']['Max_Bezugsleistung'],
                                 variable_costs = [i*(-1) for i in sequences['Preise_2030_Stundenwerte']['Strompreis_2030']]
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen_m', 
        inputs={b_H2_m: solph.Flow(nominal_value = scalars['Parameter_Wasserstoffnetz_'+ str(YEAR)]['Wasserstoff']['Max_Bezugsleistung'],
                                 variable_costs = [i*(-1) for i in sequences['Preise_2030_Stundenwerte']['Wasserstoffpreis_2030']]
                                  
        )}))
    
    """
    Defining final energy demand as Sinks
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total_m', 
        inputs={b_el_middle: solph.Flow(fix=Last_Strom_Zusammen, 
                                 nominal_value=1,
        )}))
    #------------------------------------------------------------------------------
    # Biomass demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Biomass_demand_total_m', 
        inputs={b_solidf_m: solph.Flow(fix=Last_Bio_Zusammen, 
                                   nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Gas demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Gas_demand_total_m', 
        inputs={b_gas_m: solph.Flow(fix=Last_Gas_Zusammen, 
                                  nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Material demand: Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Gas_m', 
        inputs={b_gas_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                  nominal_value=P_nom_Gas_Grundlast_Materialnutzung,
        )}))

    #------------------------------------------------------------------------------
    # Oil demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil_demand_total_m', 
        inputs={b_oil_fuel_m: solph.Flow(fix=Last_Oel_Zusammen, 
                                              nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Mobility demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Mobility_demand_total_m', 
        inputs={b_oil_fuel_m: solph.Flow(fix=Last_Verbrenner_Zusammen, 
                                              nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Material demand: Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Oil_m', 
        inputs={b_oil_fuel_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                              nominal_value=P_nom_Oel_Grundlast_Materialnutzung,
        )}))

    #------------------------------------------------------------------------------
    # Heat demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Heat_demand_total_m', 
        inputs={b_dist_heat_m: solph.Flow(fix=Last_Fernw_Zusammen, 
                                   nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Hydrogen_demand_total_m', 
        inputs={b_H2_m: solph.Flow(fix=Last_H2_Zusammen, 
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
        outputs={b_el_middle: solph.Flow(fix=data_Wind_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wind, 
                                                                    maximum=Parameter_PV_Wind_2030['Wind']['Potential_Nordhausen_Nord'])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_Erfurt', 
        outputs={b_el_middle: solph.Flow(fix=data_PV_Aufdach_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Nordhausen_Nord'])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_Freifeld_Erfurt', 
        outputs={b_el_middle: solph.Flow(fix=data_PV_Freifeld_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Nordhausen_Nord'])
        )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant_m', 
        outputs={b_el_middle: solph.Flow(fix=data_Wasserkraft,
                                        custom_attributes={'emission_factor': Parameter_Wasserkraft_2030['Wasserkraft']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wasserkraft, 
                                                                    minimum=Parameter_Wasserkraft_2030['Wasserkraft']['Potential'], 
                                                                    maximum = Parameter_Wasserkraft_2030['Wasserkraft']['Potential'])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST_m', 
        outputs={b_dist_heat_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Solarthermie'], 
                                          custom_attributes={'emission_factor': Parameter_ST_2030['Solarthermie']['EE_Faktor']},
                                          investment=solph.Investment(ep_costs=epc_ST, 
                                                                      maximum=Parameter_ST_2030['Solarthermie']['Potential'])
        )}))
    
    """ Imports """
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel_m',
        outputs={b_bio_m: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood_m',
        outputs={b_bioWood_m: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                             custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_brown_coal_m',
        outputs={b_solidf_m: solph.Flow(variable_costs = Import_Braunkohlepreis_2030,
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=data_Systemeigenschaften['System']['Menge_Braunkohle']*number_of_time_steps,
                                    custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Braunkohle']},
        )}))
    
    #------------------------------------------------------------------------------
    # Import hard coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_hard_coal_m',
        outputs={b_solidf_m: solph.Flow(variable_costs = Import_Steinkohlepreis_2030,
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=data_Systemeigenschaften['System']['Menge_Steinkohle']*number_of_time_steps,
                                    custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Steinkohle']},
                                    
        )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas_m',
        outputs={b_gas_m: solph.Flow(variable_costs = Import_Erdgaspreis_2030,
                                         custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Erdgas']},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil_m',
        outputs={b_oil_fuel_m: solph.Flow(variable_costs = Import_Oelpreis_2030,
                                                     custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Oel']}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel_m',
        outputs={b_oil_fuel_m: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Synthetische_Kraftstoffe_2030'],
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
        inflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Natriumspeicher, 
                                        maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Potential'],
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Heat storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Heat storage_m',
        inputs={b_dist_heat_m: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_dist_heat_m: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(Parameter_Waermespeicher_2030['Waermespeicher']['Verlustrate']/24),
        inflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Waermespeicher_2030['Waermespeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Waermespeicher_2030['Waermespeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_Waermespeicher, 
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
        balanced=bool(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['balanced']),
        inflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Pumpspeicherkraftwerk,
                                      minimum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential_min'],
                                      maximum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential'])
        ))
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas storage_m",
        inputs={b_gas_m: solph.Flow()},
        outputs={b_gas_m: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Erdgasspeicher, 
                                      maximum = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Potential'])    
        ))
    
    #------------------------------------------------------------------------------
    # H2 Storage
    #------------------------------------------------------------------------------    
    energysystem.add(solph.components.GenericStorage(
        label="H2_storage_m",
        inputs={b_H2_m: solph.Flow()},
        outputs={b_H2_m: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Wasserstoffspeicher, 
                                      maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Potential'])    
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
        outputs={b_H2_m: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrolyse, 
                                                                 maximum=Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Potential']))},
        conversion_factors={b_H2_m: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Wirkungsgrad']},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler_m",
        inputs={b_el_middle: solph.Flow()},
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrodenheizkessel))},
        conversion_factors={b_dist_heat_m: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['Wirkungsgrad']}    
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD_m',
        inputs={b_gas_m: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el_middle: solph.Flow(investment=solph.Investment(ep_costs=epc_GuD,
                                                              maximum =Parameter_GuD_2030['GuD']['Potential'])),
                 b_dist_heat_m: solph.Flow()},
        conversion_factors={b_el_middle: Parameter_GuD_2030['GuD']['Wirkungsgrad_el'], 
                            b_dist_heat_m: Parameter_GuD_2030['GuD']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell_m",
        inputs={b_H2_m: solph.Flow()},
        outputs={b_el_middle: solph.Flow(investment = solph.Investment(ep_costs=epc_Brennstoffzelle, 
                                                                maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Potential']))},
        conversion_factors={b_el_middle: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Wirkungsgrad']}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation_m",
        inputs={b_H2_m: solph.Flow()},
        outputs={b_gas_m: solph.Flow(investment = solph.Investment(ep_costs=epc_Methanisierung, 
                                                                 maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Potential']))},
        conversion_factors={b_gas_m: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Wirkungsgrad']}  
        ))
    
    #------------------------------------------------------------------------------
    # Biogas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas_m',
        inputs={b_bio_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': Parameter_Biomasse_Biogas_2030['Biogas']['BiogasBestand']})},
                                  
        outputs={b_el_middle: solph.Flow(investment=solph.Investment(ep_costs=epc_Biogas), 
                                        custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast']),
                 b_dist_heat_n: solph.Flow(custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                          fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el_middle: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_el'], 
                            b_dist_heat_m: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_m',
        inputs={b_bioWood_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                            #nominal_value = 1
                                            investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_middle: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                  investment=solph.Investment(ep_costs=epc_Biomasse),
                                  custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_el_middle: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_el']}
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat_m',
        inputs={b_bioWood_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                           #nominal_value = 1
                                           investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                    investment=solph.Investment(ep_costs=epc_Biomasse),
                                    custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_dist_heat_m: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing_m",
        inputs={b_bio_m: solph.Flow(custom_attributes={'BiogasBestand_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['BiogasBestand']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Bestandsanlagen),
                                   )},
        conversion_factors={b_gas_m: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['EE_Faktor']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feed_in_new_m",
        inputs={b_bio_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas_m: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Neuanlagen),
                                   )},
        conversion_factors={b_gas_m: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['EE_Faktor']}
                                    
        ))
    
    # -----------------------------------------------------------------------------
    # Hydroden feed-in
    # -----------------------------------------------------------------------------
    maximale_Wasserstoffeinspeisung_Lastgang_m = [None] * len(Last_Gas_Zusammen)
    maximale_Wasserstoffeinspeisung_m=0
    for a in range(0, len(Last_Gas_Zusammen)):
        maximale_Wasserstoffeinspeisung_Lastgang_m[a]=(Last_Gas_Zusammen[a]*(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Potential']))/(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Wirkungsgrad'])
        if maximale_Wasserstoffeinspeisung_Lastgang_m[a] > maximale_Wasserstoffeinspeisung_m:
            maximale_Wasserstoffeinspeisung_m = maximale_Wasserstoffeinspeisung_Lastgang_m[a]
    
    energysystem.add(solph.components.Converter(
        label='Hydrogen_feedin_m',
        inputs={b_H2_m: solph.Flow()},
        outputs={b_gas_m: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang_m,
                                   investment=solph.Investment(ep_costs=epc_Wasserstoffeinspeisung, 
                                                               maximum=max(maximale_Wasserstoffeinspeisung_Lastgang_m)))}
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water_m",
        inputs={b_el_middle: solph.Flow()},
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Fluss, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['Potential']))},
        conversion_factors={b_dist_heat_m: Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air_m",
        inputs={b_el_middle: solph.Flow()},
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Abwaerme, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['Potential']))},
        conversion_factors={b_dist_heat_m: Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL_m",
        inputs={b_H2_m: solph.Flow()},
        outputs={b_oil_fuel_m: solph.Flow(investment = solph.Investment(ep_costs=epc_PtL, 
                                                                             maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Potential']))},
        conversion_factors={b_oil_fuel_m: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Wirkungsgrad']}
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
        inputs={b_el_swest: solph.Flow(nominal_value = scalars['Parameter_Stromnetz_' + str(YEAR)]['Strom']['Max_Bezugsleistung'],
                                 variable_costs = [i*(-1) for i in sequences['Preise_2030_Stundenwerte']['Strompreis_2030']]
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen_s', 
        inputs={b_H2_s: solph.Flow(nominal_value = scalars['Parameter_Wasserstoffnetz_'+ str(YEAR)]['Wasserstoff']['Max_Bezugsleistung'],
                                 variable_costs = [i*(-1) for i in sequences['Preise_2030_Stundenwerte']['Wasserstoffpreis_2030']]
                                  
        )}))
    
    """
    Defining final energy demand as Sinks
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total_s', 
        inputs={b_el_swest: solph.Flow(fix=Last_Strom_Zusammen, 
                                 nominal_value=1,
        )}))
    #------------------------------------------------------------------------------
    # Biomass demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Biomass_demand_total_s', 
        inputs={b_solidf_s: solph.Flow(fix=Last_Bio_Zusammen, 
                                   nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Gas demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Gas_demand_total_s', 
        inputs={b_gas_s: solph.Flow(fix=Last_Gas_Zusammen, 
                                  nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Material demand: Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Gas_s', 
        inputs={b_gas_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                  nominal_value=P_nom_Gas_Grundlast_Materialnutzung,
        )}))

    #------------------------------------------------------------------------------
    # Oil demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil_demand_total_s', 
        inputs={b_oil_fuel_s: solph.Flow(fix=Last_Oel_Zusammen, 
                                              nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Mobility demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Mobility_demand_total_s', 
        inputs={b_oil_fuel_s: solph.Flow(fix=Last_Verbrenner_Zusammen, 
                                              nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Material demand: Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Oil_s', 
        inputs={b_oil_fuel_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                              nominal_value=P_nom_Oel_Grundlast_Materialnutzung,
        )}))

    #------------------------------------------------------------------------------
    # Heat demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Heat_demand_total_s', 
        inputs={b_dist_heat_s: solph.Flow(fix=Last_Fernw_Zusammen, 
                                   nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Hydrogen_demand_total_s', 
        inputs={b_H2_s: solph.Flow(fix=Last_H2_Zusammen, 
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
        outputs={b_el_swest: solph.Flow(fix=data_Wind_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wind, 
                                                                    maximum=Parameter_PV_Wind_2030['Wind']['Potential_Nordhausen_Nord'])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_Erfurt', 
        outputs={b_el_swest: solph.Flow(fix=data_PV_Aufdach_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Nordhausen_Nord'])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_Freifeld_Erfurt', 
        outputs={b_el_swest: solph.Flow(fix=data_PV_Freifeld_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Nordhausen_Nord'])
        )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant_s', 
        outputs={b_el_swest: solph.Flow(fix=data_Wasserkraft,
                                        custom_attributes={'emission_factor': Parameter_Wasserkraft_2030['Wasserkraft']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wasserkraft, 
                                                                    minimum=Parameter_Wasserkraft_2030['Wasserkraft']['Potential'], 
                                                                    maximum = Parameter_Wasserkraft_2030['Wasserkraft']['Potential'])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST_s', 
        outputs={b_dist_heat_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Solarthermie'], 
                                          custom_attributes={'emission_factor': Parameter_ST_2030['Solarthermie']['EE_Faktor']},
                                          investment=solph.Investment(ep_costs=epc_ST, 
                                                                      maximum=Parameter_ST_2030['Solarthermie']['Potential'])
        )}))
    
    """ Imports """
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel_s',
        outputs={b_bio_s: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood_s',
        outputs={b_bioWood_s: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                             custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_brown_coal_s',
        outputs={b_solidf_s: solph.Flow(variable_costs = Import_Braunkohlepreis_2030,
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=data_Systemeigenschaften['System']['Menge_Braunkohle']*number_of_time_steps,
                                    custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Braunkohle']},
        )}))
    
    #------------------------------------------------------------------------------
    # Import hard coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_hard_coal_s',
        outputs={b_solidf_s: solph.Flow(variable_costs = Import_Steinkohlepreis_2030,
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=data_Systemeigenschaften['System']['Menge_Steinkohle']*number_of_time_steps,
                                    custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Steinkohle']},
                                    
        )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas_s',
        outputs={b_gas_s: solph.Flow(variable_costs = Import_Erdgaspreis_2030,
                                         custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Erdgas']},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil_s',
        outputs={b_oil_fuel_s: solph.Flow(variable_costs = Import_Oelpreis_2030,
                                                     custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Oel']}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel_s',
        outputs={b_oil_fuel_s: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Synthetische_Kraftstoffe_2030'],
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
        inflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Natriumspeicher, 
                                        maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Potential'],
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Heat storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Heat storage_s',
        inputs={b_dist_heat_s: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_dist_heat_s: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(Parameter_Waermespeicher_2030['Waermespeicher']['Verlustrate']/24),
        inflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Waermespeicher_2030['Waermespeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Waermespeicher_2030['Waermespeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_Waermespeicher, 
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
        balanced=bool(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['balanced']),
        inflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Pumpspeicherkraftwerk,
                                      minimum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential_min'],
                                      maximum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential'])
        ))
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas storage_s",
        inputs={b_gas_s: solph.Flow()},
        outputs={b_gas_s: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Erdgasspeicher, 
                                      maximum = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Potential'])    
        ))
    
    #------------------------------------------------------------------------------
    # H2 Storage
    #------------------------------------------------------------------------------    
    energysystem.add(solph.components.GenericStorage(
        label="H2_storage_s",
        inputs={b_H2_s: solph.Flow()},
        outputs={b_H2_s: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Wasserstoffspeicher, 
                                      maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Potential'])    
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
        outputs={b_H2_s: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrolyse, 
                                                                 maximum=Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Potential']))},
        conversion_factors={b_H2_s: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Wirkungsgrad']},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler_s",
        inputs={b_el_swest: solph.Flow()},
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrodenheizkessel))},
        conversion_factors={b_dist_heat_s: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['Wirkungsgrad']}    
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD_s',
        inputs={b_gas_s: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el_swest: solph.Flow(investment=solph.Investment(ep_costs=epc_GuD,
                                                              maximum =Parameter_GuD_2030['GuD']['Potential'])),
                 b_dist_heat_s: solph.Flow()},
        conversion_factors={b_el_swest: Parameter_GuD_2030['GuD']['Wirkungsgrad_el'], 
                            b_dist_heat_s: Parameter_GuD_2030['GuD']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell_s",
        inputs={b_H2_s: solph.Flow()},
        outputs={b_el_swest: solph.Flow(investment = solph.Investment(ep_costs=epc_Brennstoffzelle, 
                                                                maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Potential']))},
        conversion_factors={b_el_swest: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Wirkungsgrad']}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation_s",
        inputs={b_H2_s: solph.Flow()},
        outputs={b_gas_s: solph.Flow(investment = solph.Investment(ep_costs=epc_Methanisierung, 
                                                                 maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Potential']))},
        conversion_factors={b_gas_s: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Wirkungsgrad']}  
        ))
    
    #------------------------------------------------------------------------------
    # Biogas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas_s',
        inputs={b_bio_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': Parameter_Biomasse_Biogas_2030['Biogas']['BiogasBestand']})},
                                  
        outputs={b_el_swest: solph.Flow(investment=solph.Investment(ep_costs=epc_Biogas), 
                                        custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast']),
                 b_dist_heat_n: solph.Flow(custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                          fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el_swest: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_el'], 
                            b_dist_heat_s: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_s',
        inputs={b_bioWood_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                            #nominal_value = 1
                                            investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_swest: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                  investment=solph.Investment(ep_costs=epc_Biomasse),
                                  custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_el_swest: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_el']}
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat_s',
        inputs={b_bioWood_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                           #nominal_value = 1
                                           investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                    investment=solph.Investment(ep_costs=epc_Biomasse),
                                    custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_dist_heat_s: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing_s",
        inputs={b_bio_s: solph.Flow(custom_attributes={'BiogasBestand_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['BiogasBestand']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Bestandsanlagen),
                                   )},
        conversion_factors={b_gas_s: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['EE_Faktor']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feed_in_new_s",
        inputs={b_bio_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas_s: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Neuanlagen),
                                   )},
        conversion_factors={b_gas_s: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['EE_Faktor']}
                                    
        ))
    
    # -----------------------------------------------------------------------------
    # Hydroden feed-in
    # -----------------------------------------------------------------------------
    maximale_Wasserstoffeinspeisung_Lastgang_s = [None] * len(Last_Gas_Zusammen)
    maximale_Wasserstoffeinspeisung_s=0
    for a in range(0, len(Last_Gas_Zusammen)):
        maximale_Wasserstoffeinspeisung_Lastgang_s[a]=(Last_Gas_Zusammen[a]*(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Potential']))/(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Wirkungsgrad'])
        if maximale_Wasserstoffeinspeisung_Lastgang_s[a] > maximale_Wasserstoffeinspeisung_s:
            maximale_Wasserstoffeinspeisung_s = maximale_Wasserstoffeinspeisung_Lastgang_s[a]
    
    energysystem.add(solph.components.Converter(
        label='Hydrogen_feedin_s',
        inputs={b_H2_s: solph.Flow()},
        outputs={b_gas_s: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang_s,
                                   investment=solph.Investment(ep_costs=epc_Wasserstoffeinspeisung, 
                                                               maximum=max(maximale_Wasserstoffeinspeisung_Lastgang_s)))}
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water_s",
        inputs={b_el_swest: solph.Flow()},
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Fluss, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['Potential']))},
        conversion_factors={b_dist_heat_s: Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air_s",
        inputs={b_el_swest: solph.Flow()},
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Abwaerme, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['Potential']))},
        conversion_factors={b_dist_heat_s: Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL_s",
        inputs={b_H2_s: solph.Flow()},
        outputs={b_oil_fuel_s: solph.Flow(investment = solph.Investment(ep_costs=epc_PtL, 
                                                                             maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Potential']))},
        conversion_factors={b_oil_fuel_s: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Wirkungsgrad']}
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
    
    return energysystem