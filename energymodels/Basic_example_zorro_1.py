# -*- coding: utf-8 -*-
"""
Created on Fri Nov 15 13:27:56 2024

@author: rbala
"""

import os
workdir= os.getcwd()
import pandas as pd
from oemof import network, solph
from src.preprocessing.files import read_input_files
from src.preprocessing.conversion import investment_parameter, CO2_price_addition, load_profile_scaling, COP_calculation
from src.preprocessing.zorro_1_load_profile import zorro_1_loadprofile_scaling 
from src.preprocessing.location import Location

def Basisszenario_1(PERMUATION: str) -> solph.EnergySystem:
    YEAR, model_ID = PERMUATION.split("_")
    YEAR = int(YEAR)
    
    sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    demand = load_profile_scaling(scalars,sequences, YEAR, model_ID, region=False)
    #demand = zorro_1_loadprofile_scaling(YEAR, new_profile=True)
    epc_costs = investment_parameter(scalars, YEAR, model_ID)
    import_price = CO2_price_addition(scalars,sequences, YEAR,'Energy_price_brainpool_2024')
    feed_in_profile_new = False
    
    Weather_dir = os.path.abspath(os.path.join(workdir, 'data','weatherdata'))
    middle = Location(os.path.join(Weather_dir,'Erfurt_Binderslebn-hour.csv'), os.path.join(Weather_dir,'Erfurt_Binderslebn-min.dat'))
    north = Location(os.path.join(Weather_dir,'Nordhausen-hour.csv'), os.path.join(Weather_dir,'Nordhausen-min.dat'))
    swest= Location(os.path.join(Weather_dir,'Hildburghausen-hour.csv'), os.path.join(Weather_dir,'Hildburghausen-min.dat'))
    east = Location(os.path.join(Weather_dir,'Gera-Leumnitz-hour.csv'), os.path.join(Weather_dir,'Gera-Leumnitz-min.dat'))
    
    Ta_avg = ((north.weather_data_hour[' Ta'] + east.weather_data_hour[' Ta'] + middle.weather_data_hour[' Ta'] + swest.weather_data_hour[' Ta'])/4)
    COP = COP_calculation(scalars, Ta_avg, model_ID, YEAR)
    fixed_losses_absolute_seasonal_storage = 1656.2*(85 - Ta_avg )+ 74.7 *(10-11) # 11°C- Bodentemp
    Planing_region = [middle, north, swest, east]
    """ Simulate Wind feed-in profile for the desired location """
    for L in Planing_region:
        L.Wind_feed_in_profile(YEAR)
        L.PV_feed_in_profile(YEAR)
    
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
    # Höchstespannung netz                                                                                      # Class Bus sind jetzt in module buses verschoben (solph.buses.Bus)
    #------------------------------------------------------------------------------
    b_hös = solph.buses.Bus(label="Electricity_Hös")
    
    #------------------------------------------------------------------------------
    # Electricity Bus                                                                                      # Class Bus sind jetzt in module buses verschoben (solph.buses.Bus)
    #------------------------------------------------------------------------------
    b_el = solph.buses.Bus(label="Electricity")

    #------------------------------------------------------------------------------
    # Gas Bus
    #------------------------------------------------------------------------------
    b_gas = solph.buses.Bus(label="Gas")

    #------------------------------------------------------------------------------
    # Oil/fuel Bus
    #------------------------------------------------------------------------------
    b_oil_fuel = solph.buses.Bus(label="Oil_fuel")

    #------------------------------------------------------------------------------
    # Biomasse Bus
    #------------------------------------------------------------------------------
    b_bio = solph.buses.Bus(label="Biomass")

    #------------------------------------------------------------------------------
    # Solid Biomass Bus
    #------------------------------------------------------------------------------
    b_bioWood = solph.buses.Bus(label="BioWood")

    #------------------------------------------------------------------------------
    # District heating Bus
    #------------------------------------------------------------------------------
    b_dist_heat = solph.buses.Bus(label="District heating")

    #------------------------------------------------------------------------------
    # Hydrogen Bus
    #------------------------------------------------------------------------------
    b_H2 = solph.buses.Bus(label="Hydrogen")

    #------------------------------------------------------------------------------
    # Solidfuel Bus
    #------------------------------------------------------------------------------
    b_solidf = solph.buses.Bus(label="Solidfuel")
       
    #------------------------------------------------------------------------------
    # Abwärme Bus
    #------------------------------------------------------------------------------
    b_abwaerme = solph.buses.Bus(label="Recovery heat")
    
    #------------------------------------------------------------------------------
    # Umweltwaerme
    #------------------------------------------------------------------------------
    b_uw = solph.buses.Bus(label="Environmental heat")
    
    #------------------------------------------------------------------------------
    # Preheat
    #------------------------------------------------------------------------------
    b_preheat = solph.buses.Bus(label="Pre-heating")
    
    #------------------------------------------------------------------------------
    # Pumpspeicher
    #------------------------------------------------------------------------------
    b_pumps = solph.buses.Bus(label="Pumped-Hydro")
        
    # Hinzufügen der Busse zum Energiesystem-Modell 
    energysystem.add(b_el, b_gas, b_oil_fuel, b_bio, b_bioWood, b_dist_heat, b_H2, b_solidf, b_abwaerme, b_uw, b_hös, b_preheat, b_pumps)


    """
    Renewable Energy sources
    """
    if feed_in_profile_new:
        #------------------------------------------------------------------------------
        # Wind power plants
        #------------------------------------------------------------------------------
        energysystem.add(solph.components.Source(
            label='Wind_north', 
            outputs={b_el: solph.Flow(fix=north.Wind_feed_in_profile['Wind_feed_in'],#sequences['feed_in_profile']['Wind_north'],
                                            custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                        #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_north_min'][model_ID],
                                                                        maximum=scalars['Parameter_onshore_wind_power_plant']['potential_north_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='Wind_east', 
            outputs={b_el: solph.Flow(fix=east.Wind_feed_in_profile['Wind_feed_in'],#sequences['feed_in_profile']['Wind_east'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                        #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_east_min'][model_ID],
                                                                        maximum=scalars['Parameter_onshore_wind_power_plant']['potential_east_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='Wind_middle', 
            outputs={b_el: solph.Flow(fix=middle.Wind_feed_in_profile['Wind_feed_in'],#sequences['feed_in_profile']['Wind_middle'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                        #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_middle_min'][model_ID],
                                                                        maximum=scalars['Parameter_onshore_wind_power_plant']['potential_middle_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='Wind_swest', 
            outputs={b_el: solph.Flow(fix=swest.Wind_feed_in_profile['Wind_feed_in'],#sequences['feed_in_profile']['Wind_swest'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                        #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_swest_min'][model_ID],
                                                                        maximum=scalars['Parameter_onshore_wind_power_plant']['potential_swest_max'][model_ID])
            )}))
        #------------------------------------------------------------------------------
        # Photovoltaic Rooftop systems
        #------------------------------------------------------------------------------
        energysystem.add(solph.components.Source(
            label='PV_rooftop_north', 
            outputs={b_el: solph.Flow(fix=north.PV_feed_in_profile_rooftop['AC_Power'],#sequences['feed_in_profile']['PV_rooftop_north'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                        maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_rooftop_east', 
            outputs={b_el: solph.Flow(fix=east.PV_feed_in_profile_rooftop['AC_Power'],#sequences['feed_in_profile']['PV_rooftop_east'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_east_min'][model_ID],
                                                                        maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_east_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_rooftop_middle', 
            outputs={b_el: solph.Flow(fix=middle.PV_feed_in_profile_rooftop['AC_Power'],#sequences['feed_in_profile']['PV_rooftop_middle'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_middle_min'][model_ID],
                                                                        maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_middle_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_rooftop_swest', 
            outputs={b_el: solph.Flow(fix=swest.PV_feed_in_profile_rooftop['AC_Power'],#sequences['feed_in_profile']['PV_rooftop_swest'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_swest_min'][model_ID],
                                                                        maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_swest_max'][model_ID])
            )}))
        #------------------------------------------------------------------------------
        # Photovoltaic Openfield systems
        #------------------------------------------------------------------------------
        energysystem.add(solph.components.Source(
            label='PV_open_north', 
            outputs={b_el: solph.Flow(fix=north.PV_feed_in_profile_openfield['AC_Power'],#sequences['feed_in_profile']['PV_openfield_north'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                        maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_open_east', 
            outputs={b_el: solph.Flow(fix=east.PV_feed_in_profile_openfield['AC_Power'],#sequences['feed_in_profile']['PV_openfield_east'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_east_min'][model_ID],
                                                                        maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_east_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_open_middle', 
            outputs={b_el: solph.Flow(fix=middle.PV_feed_in_profile_openfield['AC_Power'],#sequences['feed_in_profile']['PV_openfield_middle'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_middle_min'][model_ID],
                                                                        maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_middle_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_open_swest', 
            outputs={b_el: solph.Flow(fix=swest.PV_feed_in_profile_openfield['AC_Power'],#sequences['feed_in_profile']['PV_openfield_swest'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_swest_min'][model_ID],
                                                                        maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_swest_max'][model_ID])
            )}))
    
    else:
        #------------------------------------------------------------------------------
        # Wind power plants
        #------------------------------------------------------------------------------
        energysystem.add(solph.components.Source(
            label='Wind_north', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['Wind_north'],
                                            custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                        #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_north_min'][model_ID],
                                                                        maximum=scalars['Parameter_onshore_wind_power_plant']['potential_north_max_'+ str(YEAR)][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='Wind_east', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['Wind_east'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                        #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_east_min'][model_ID],
                                                                        maximum=scalars['Parameter_onshore_wind_power_plant']['potential_east_max_'+ str(YEAR)][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='Wind_middle', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['Wind_middle'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                        #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_middle_min'][model_ID],
                                                                        maximum=scalars['Parameter_onshore_wind_power_plant']['potential_middle_max_'+ str(YEAR)][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='Wind_swest', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['Wind_swest'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                        #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_swest_min'][model_ID],
                                                                        maximum=scalars['Parameter_onshore_wind_power_plant']['potential_swest_max_'+ str(YEAR)][model_ID])
            )}))
        #------------------------------------------------------------------------------
        # Photovoltaic Rooftop systems
        #------------------------------------------------------------------------------
        energysystem.add(solph.components.Source(
            label='PV_rooftop_north', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_north'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                        maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_rooftop_east', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_east'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_east_min'][model_ID],
                                                                        maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_east_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_rooftop_middle', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_middle'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_middle_min'][model_ID],
                                                                        maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_middle_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_rooftop_swest', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_swest'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_swest_min'][model_ID],
                                                                        maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_swest_max'][model_ID])
            )}))
        #------------------------------------------------------------------------------
        # Photovoltaic Openfield systems
        #------------------------------------------------------------------------------
        energysystem.add(solph.components.Source(
            label='PV_open_north', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_north'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                        maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_open_east', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_east'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_east_min'][model_ID],
                                                                        maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_east_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_open_middle', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_middle'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_middle_min'][model_ID],
                                                                        maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_middle_max'][model_ID])
            )}))
        
        energysystem.add(solph.components.Source(
            label='PV_open_swest', 
            outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_swest'],#
                                            custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                            investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                        #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_swest_min'][model_ID],
                                                                        maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_swest_max'][model_ID])
            )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant', 
        outputs={b_el: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                        custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                    minimum= scalars['Parameter_run_river_power_plant']['potential_total'][model_ID], 
                                                                    maximum = scalars['Parameter_run_river_power_plant']['potential_total'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST', 
        outputs={b_dist_heat: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                      # maximum=scalars['Parameter_solar_thermal_power_plant']['potential_total'][model_ID]
                                                                      )
        )}))
    
    #------------------------------------------------------------------------------
    # Environmental heat
    #------------------------------------------------------------------------------
    
    Load_profile_uw = ((north.weather_data_hour[' Ta'] + east.weather_data_hour[' Ta'] + middle.weather_data_hour[' Ta'] + swest.weather_data_hour[' Ta'])/4)
    Load_profile_uw[Load_profile_uw<0]=0
    Load_profile_uw = Load_profile_uw / sum(Load_profile_uw)    # developed with environmental temperature as fix for teh source block
    
    energysystem.add(solph.components.Source(
        label='UW', 
        outputs={b_uw: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          nominal_value = scalars['System_configurations_2024']['System']['Potential_Umweltwärme']
        )}))
    
    #------------------------------------------------------------------------------
    # Recovery heat
    #------------------------------------------------------------------------------
           
    energysystem.add(solph.components.Source(
        label='AW', 
        outputs={b_abwaerme: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          nominal_value = scalars['System_configurations_2024']['System']['Potential_Abwärme']) 
                  }))
    
    """ Imports """
    #------------------------------------------------------------------------------
    # Electricity grid interconnection
    #------------------------------------------------------------------------------
    
    energysystem.add(solph.components.Source(
       label='Import_Electricity',
       outputs={b_hös: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power'],
                                 variable_costs = import_price['import_electricity_price']+ import_price['grid_operating_fee_HöS<2500h'],
                                 custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Strom_'+ str(YEAR)]},
                                 
           )}))
   
    """Link between HöS & HS""" 
    energysystem.add(solph.components.Link(
        label='Hös<->HS',
        inputs= {b_hös: solph.Flow(),
                 b_el: solph.Flow()},
        outputs= {b_el: solph.Flow(variable_costs= import_price['grid_operating_fee_HS<2500h']),
                  b_hös: solph.Flow(variable_costs= import_price['grid_operating_fee_HS<2500h'])},
        conversion_factors = {(b_hös,b_el): 1, (b_el,b_hös):1}
        ))
      
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel',
        outputs={b_bio: solph.Flow(variable_costs = import_price['import_biomass_price'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood',
        outputs={b_bioWood: solph.Flow(variable_costs =import_price['import_biomass_price'],
                                       #fix=sequences['Base_demand_profile']['base_load'],
                                       # nominal_value = 1,
                                       investment = solph.Investment(ep_costs=0),
                                       summed_max= scalars['System_configurations_2024']['System']['Holzpotential_tot'],
                                       # custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
    
    if YEAR == 2020:
        energysystem.add(solph.components.Source(
            label='Import_brown_coal',
            outputs={b_solidf: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                        fix=sequences['Base_demand_profile']['base_load'], 
                                        #nominal_value = 1,
                                        investment = solph.Investment(ep_costs=0),
                                        summed_max=(scalars['System_configurations_2024']['System']['Menge_Braunkohle'] )*len(import_price['import_brown_coal_price']),
                                        custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Braunkohle']},
            )}))
        
        #------------------------------------------------------------------------------
        # Import hard coal
        #------------------------------------------------------------------------------
        # energysystem.add(solph.components.Source(
        #     label='Import_hard_coal',
        #     outputs={b_solidf: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
        #                                 fix=sequences['Base_demand_profile']['base_load'], 
        #                                 #nominal_value = 1,
        #                                 investment = solph.Investment(ep_costs=0),
        #                                 summed_max=(scalars['System_configurations_2024']['System']['Menge_Steinkohle'])*len(import_price['import_brown_coal_price']),
        #                                 custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Steinkohle']},
                                        
        #     )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas',
        outputs={b_gas: solph.Flow(variable_costs = import_price['import_gas_price'],
                                         custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Erdgas']},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil',
        outputs={b_oil_fuel: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                     custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Oel']}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel',
        outputs={b_oil_fuel: solph.Flow(variable_costs = import_price['import_synt_fuel_price'],
            )}))
    
    #------------------------------------------------------------------------------
    # Import Hydrogen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Hydrogen',
        outputs={b_H2: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                  variable_costs = import_price['import_hydrogen_price'],
            )}))
    
       
    """
    Transformers
    """
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing",
        inputs={b_bio: solph.Flow(#custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_upgrading_plant']['existing_factor'][model_ID]},
                                  fix=sequences['Base_demand_profile']['base_load'],
                                  investment = solph.Investment(ep_costs=0)
                                  #nominal_value = 1
                                  )},
        outputs={b_gas: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(
                                       ep_costs=epc_costs['biogas_upgrading_plant']['epc'],
                                       maximum=scalars['Parameter_biogas_upgrading_plant']['potential'][model_ID]
                                       ),
                                   custom_attributes={'emission_factor': scalars['Parameter_biogas_upgrading_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas: scalars['Parameter_biogas_upgrading_plant']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_new",
        inputs={b_bio: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biomethane_injection_plant']['epc']),
                                   custom_attributes={'emission_factor': scalars['Parameter_biomethane_injection_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas: scalars['Parameter_biomethane_injection_plant']['efficiency_'+str(YEAR)][model_ID]/100}                                    
        ))
    
    #------------------------------------------------------------------------------
    # Biogas BHKW
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas- BHKW',
        inputs={b_bio: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['existing_factor'][model_ID]})},
                                  
        outputs={b_el: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['biogas_combined_heat_and_power_plant']['epc']), 
                                        custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load']),
                  b_dist_heat: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                          fix=sequences['Base_demand_profile']['base_load'],
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL",
        inputs={b_bio: solph.Flow()},
        outputs={b_oil_fuel: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_holz']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                        custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_holz']['EE_factor'][model_ID]}
                                        )},
        conversion_factors={b_oil_fuel: scalars['Parameter_biomass_to_liquid_system_holz']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell",
        inputs={b_H2: solph.Flow()},
        outputs={b_el: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                                # maximum=scalars['Parameter_fuel_cells']['potential_total'][model_ID]
                                                                ))},
        conversion_factors={b_el: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation",
        inputs={b_H2: solph.Flow()},
        outputs={b_gas: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                                 # maximum=scalars['Parameter_methanation']['potential_total'][model_ID]
                                                                 ))},
        conversion_factors={b_gas: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]/100}  
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid (with elec source)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL",
        inputs={b_H2: solph.Flow(),
                b_el: solph.Flow()},
        outputs={b_oil_fuel: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                      # maximum=scalars['Parameter_power_to_liquid_system']['potential_total'][model_ID]
                                                                      ))},
        conversion_factors={b_oil_fuel: scalars['Parameter_power_to_liquid_system']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD',
        inputs={b_gas: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                              maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential_total'][model_ID])),
                 b_dist_heat: solph.Flow()},
        conversion_factors={b_el: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec',
        inputs={b_bioWood: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_power_plant']['EE_factor'][model_ID]}),
                 
                 },
        conversion_factors={b_el: scalars['Parameter_biomass_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            
                            }
        ))  
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat',
        inputs={b_bioWood: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                           #nominal_value = 1
                                           investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                    investment=solph.Investment(ep_costs=epc_costs['biomass_heating_plant']['epc']),
                                    custom_attributes={'emission_factor': scalars['Parameter_biomass_heating_plant']['EE_factor'][model_ID]})},
        conversion_factors={b_dist_heat: scalars['Parameter_biomass_heating_plant']['efficiency_th_' +str(YEAR)][model_ID]/100}
        ))
    
   
    #------------------------------------------------------------------------------
    # Biomasse (for electricty  and heatproduction)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_heat',
        inputs={b_bioWood: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_combined_heat_and_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]}),
                 
                  b_dist_heat: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                            fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value= 1
                                            investment = solph.Investment(ep_costs=0)
                                            )
                  },
        conversion_factors={b_el: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            b_dist_heat: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_th_' +str(YEAR)][model_ID]/100
                            }
        ))     
    
    #------------------------------------------------------------------------------
    # Solid biomass in the same bus as coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BioTransformer",
        inputs={b_bioWood: solph.Flow()},
        outputs={b_solidf: solph.Flow(custom_attributes={'emission_factor': -1})},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler",
        inputs={b_el: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
        conversion_factors={b_dist_heat: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]/100}    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Air heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air",
        inputs={b_el: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(
            ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
            # maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]
            ))},
        conversion_factors={b_dist_heat: COP},
        #conversion_factors={b_dist_heat: scalars['Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water",
        inputs={b_el: solph.Flow(),
                b_uw: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(
            ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
            # maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential_total'][model_ID]
            ))},
        conversion_factors={b_dist_heat: COP},
        #conversion_factors={b_dist_heat: scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},    
        ))
      
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_recovery_heat",
        inputs={b_el: solph.Flow(),
                b_abwaerme: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(
            ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
            # maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]
            ))},
        # conversion_factors={b_dist_heat: COP},
        conversion_factors={b_dist_heat: scalars['Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]},    
        ))
    
    #------------------------------------------------------------------------------
    # Elektrolysis
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electrolysis",
        inputs={b_el: solph.Flow()},
        outputs={b_H2: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc'], 
                                                                # maximum=scalars['Parameter_electrolysis']['potential_total'][model_ID]
                                                                 ))},
        conversion_factors={b_H2: scalars['Parameter_electrolysis']['efficiency_'+str(YEAR)][model_ID]/100},
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung- WP
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- WP",
        inputs={b_el: solph.Flow(),
                b_preheat: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_dist_heat: COP},
        #conversion_factors={b_dist_heat: scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]/100
         #                   },
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung - Boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- Electric boiler",
        inputs={b_el: solph.Flow(),
                b_preheat: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['electrical_heater']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_dist_heat: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]/100
                            },
        ))
    
    # #------------------------------------------------------------------------------
    # # Pumped hydro storge technology
    # #------------------------------------------------------------------------------
    # energysystem.add(solph.components.Converter(
    #     label="Pumped-Hydro_technology(feed-in)",
    #     inputs={b_el: solph.Flow(),
    #             },
    #     outputs={b_pumps: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'], 
    #                                                               #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
    #                                                               ))},
    #     conversion_factors={b_pumps: scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_in_' +str(YEAR)][model_ID]/100
    #                         },
    #     ))
    # #------------------------------------------------------------------------------
    # # Pumped hydro storge technology
    # #------------------------------------------------------------------------------
    # energysystem.add(solph.components.Converter(
    #     label="Pumped-Hydro_technology(feed-out)",
    #     inputs={b_pumps: solph.Flow(),
    #             },
    #     outputs={b_el: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'], 
    #                                                               #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
    #                                                               ))},
    #     conversion_factors={b_el: scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['efficiency_out_' +str(YEAR)][model_ID]/100
    #                         },
    #     ))
    
    """Link between Pumped storage & Electricity bus""" 
    energysystem.add(solph.components.Link(
        label='Pumped_hydro_technology',
        inputs= {b_pumps: solph.Flow(),
                 b_hös: solph.Flow()},
        outputs= {b_hös: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                                                                  minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Technology)']['potential_min'][model_ID],
                                                                  maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Technology)']['potential_neu'][model_ID])),
                  b_pumps: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                                                                    minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Technology)']['potential_min'][model_ID],
                                                                    maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Technology)']['potential_neu'][model_ID]))},
        conversion_factors = {(b_pumps,b_hös):scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Technology)']['efficiency_out_' +str(YEAR)][model_ID]/100 ,
                              (b_hös,b_pumps):scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Technology)']['efficiency_in_' +str(YEAR)][model_ID]/100}
        ))
   
    """
    Energy storage
    """
    
    #------------------------------------------------------------------------------
    # Electricity storage (Großbatterie-speicher)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Battery',
        inputs={b_el: solph.Flow()},
        outputs={b_el: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                        maximum=scalars['Parameter_storage_electricity']['potential_total'][model_ID],
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Electricity storage (Li-Ion)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Li-Ion_Battery',
        inputs={b_el: solph.Flow()},
        outputs={b_el: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_Li-Ion']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_electricity_Li-Ion']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_Li-Ion']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_Li-Ion']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_Li-Ion']['epc'], 
                                        #maximum=scalars['Parameter_storage_electricity_Li-Ion']['potential_total'][model_ID],
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Electricity storage (Natrium)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Natrium_Battery',
        inputs={b_el: solph.Flow()},
        outputs={b_el: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_Natrium']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_electricity_Natrium']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_Natrium']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_Natrium']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_Natrium']['epc'], 
                                        #maximum=scalars['Parameter_storage_electricity_Natrium']['potential_total'][model_ID],
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Electricity storage (Red-OX)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Red-OX_Battery',
        inputs={b_el: solph.Flow()},
        outputs={b_el: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_Red-OX']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_electricity_Red-OX']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_Red-OX']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_Red-OX']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_Red-OX']['epc'], 
                                        #maximum=scalars['Parameter_storage_electricity_Red-OX']['potential_total'][model_ID],
                                        )
        ))
    #------------------------------------------------------------------------------
    # Dist heating storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Heat storage_dist_heat',
        inputs={b_dist_heat: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float(scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()    
                                    )},
        outputs={b_dist_heat: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float(scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_district_heating']['loss_rate'][model_ID]/24),
        inflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_heat_district_heating']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_heat_district_heating']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat_district_heating']['epc'], 
                                       )
        ))
    
    #------------------------------------------------------------------------------
    # Seasonal Heat storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Heat storage_seasonal',
        inputs={b_dist_heat: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float(scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_preheat: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float(scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_seasonal']['loss_rate'][model_ID]),
        fixed_losses_relative=float(scalars['Parameter_storage_heat_seasonal']['fixed_losses_relative'][model_ID]),
        #fixed_losses_absolute= fixed_losses_absolute_seasonal_storage,
        inflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_heat_seasonal']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_heat_seasonal']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat_seasonal']['epc'], 
                                      
                                      )
                                      
        ))
      
    
    #------------------------------------------------------------------------------
    # Pumped hydro storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label="Pumped_hydro_storage",
        inputs={b_pumps: solph.Flow()},
        outputs={b_pumps: solph.Flow()},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['initial_storage_level'][model_ID],
        # invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        # invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Becken)']['epc'],
                                      minimum = (scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_min'][model_ID]),#+scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology']['potential_Hös_min'][model_ID]), # excluding goldistal
                                      maximum = (scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_neu'][model_ID]))
        ))
    
    #------------------------------------------------------------------------------
    # Pumped hydro storage (Bestand) HochSpannungnetz verbunden
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label="Pumped_hydro_storage_bestand",
        inputs={b_el: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                                          minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID],
                                          maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID])
            )},
        outputs={b_el: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                              minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID],
                              maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID])
            )},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['initial_storage_level'][model_ID],
        # invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        # invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Becken)']['epc'],
                                      minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID],
                                      maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID])
        ))
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas_storage",
        inputs={b_gas: solph.Flow()},
        outputs={b_gas: solph.Flow()},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                      maximum = scalars['Parameter_storage_gas']['potential_total'][model_ID])  # is the same value for all region in the csv file, that's why as Potential_north, the capacity is not yet regionalised
        ))
    
    #------------------------------------------------------------------------------
    # H2 Storage
    #------------------------------------------------------------------------------    
    energysystem.add(solph.components.GenericStorage(
        label="H2_storage",
        inputs={b_H2: solph.Flow()},
        outputs={b_H2: solph.Flow()},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_hydrogen']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                      maximum = scalars['Parameter_storage_hydrogen']['potential_total'][model_ID])  
        ))
    
    """
    Export block
    """
    #------------------------------------------------------------------------------  
    # Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Electricity', 
        inputs={b_el: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_power'],
                                  variable_costs = import_price['export_electricity_price'],
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen', 
        inputs={b_H2: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                 variable_costs = import_price['export_hydrogen_price']
                                  
        )}))
    
    """
    End-Energy demands
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total', 
        inputs={b_el: solph.Flow(fix=demand['electricity'], 
                                 nominal_value=1,
        )}))
    #------------------------------------------------------------------------------
    # Biomass demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Biomass_demand_total', 
        inputs={b_solidf: solph.Flow(fix=demand['biomass'], 
                                     nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Gas demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Gas_demand_total', 
        inputs={b_gas: solph.Flow(fix=demand['gas'], 
                                  nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Material demand: Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Gas', 
        inputs={b_gas: solph.Flow(fix=demand['material_usage_gas'], 
                                  nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Oil and Fuel demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil & fuel_demand_total', 
        inputs={b_oil_fuel: solph.Flow(fix=demand['oil'] + demand['fuel'], 
                                       nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Material demand: Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Oil', 
        inputs={b_oil_fuel: solph.Flow(fix=demand['material_usage_oil'], 
                                       nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Heat demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Heat_demand_total', 
        inputs={b_dist_heat: solph.Flow(fix=demand['dist_heating'], 
                                        nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Hydrogen_demand_total', 
        inputs={b_H2: solph.Flow(fix=demand['H2'], 
                                 nominal_value=1,
        )}))
    
    """
    Excess energy capture sinks 
    """
    #------------------------------------------------------------------------------
    # Überschuss Senke für Strom
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_el', 
        inputs={b_el: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_gas', 
        inputs={b_gas: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Oel/Kraftstoffe
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_oil_fuel', 
        inputs={b_oil_fuel: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_bio', 
        inputs={b_bio: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Waerme
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_distheat', 
        inputs={b_dist_heat: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Wasserstoff
    #-----------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_H2', 
        inputs={b_H2: solph.Flow(variable_costs = 10000000
        )}))
    
    # Prepare a dataset for exporting, to have access after the simulation 
    sim_data = {'Timeseries': sequences,
                'Parameter': scalars,
                'Loadprofiles':demand,
                'epc_costs':epc_costs,
                'North': north,
                'East': east,
                'Swest': swest,
                'Middle': middle,
                'Import_prices': import_price}
    
    return energysystem, sim_data