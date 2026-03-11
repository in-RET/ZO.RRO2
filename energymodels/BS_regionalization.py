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
from src.preprocessing.conversion import investment_parameter, load_profile_scaling, CO2_price_addition, COP_calculation
from src.preprocessing.location import Location


def BS_regionalization(PERMUATION: str, model_name: str) -> solph.EnergySystem:
    YEAR, model_ID = PERMUATION.split("_")
    YEAR = int(YEAR)
    
    # Daten Einlesung mit Hilfe von Hilfsfunktionen
    sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    demand = load_profile_scaling(scalars,sequences,YEAR,model_name, region = True)
    epc_costs = investment_parameter(scalars, YEAR, model_ID)
    import_price = CO2_price_addition(scalars,sequences, YEAR, 'Energy_price_brainpool_2024')
    strompreiszeitreihe = pd.Series([0 if x<0 else x for x in import_price['import_electricity_price']])
    
    # Wetterdaten für Einspeiseprofil Berechnung (aber momentan nicht im Simulation verwendet)
    Weather_dir = os.path.abspath(os.path.join(workdir, 'data','weatherdata'))
    middle = Location(os.path.join(Weather_dir,'Erfurt_Binderslebn-hour.csv'), os.path.join(Weather_dir,'Erfurt_Binderslebn-min.dat'))
    north = Location(os.path.join(Weather_dir,'Nordhausen-hour.csv'), os.path.join(Weather_dir,'Nordhausen-min.dat'))
    swest= Location(os.path.join(Weather_dir,'Hildburghausen-hour.csv'), os.path.join(Weather_dir,'Hildburghausen-min.dat'))
    east = Location(os.path.join(Weather_dir,'Gera-Leumnitz-hour.csv'), os.path.join(Weather_dir,'Gera-Leumnitz-min.dat'))
  
    COP_n, T_VL_n = COP_calculation(scalars, north.weather_data_hour[' Ta'], model_ID, YEAR)
    fixed_losses_absolute_seasonal_storage_n = 1656.2*(85 - north.weather_data_hour[' Ta'] )+ 74.7 *(10-11)
    COP_s,T_VL_s = COP_calculation(scalars, swest.weather_data_hour[' Ta'], model_ID, YEAR)
    fixed_losses_absolute_seasonal_storage_s = 1656.2*(85 - swest.weather_data_hour[' Ta'] )+ 74.7 *(10-11)
    COP_m, T_VL_m = COP_calculation(scalars, middle.weather_data_hour[' Ta'], model_ID, YEAR)
    fixed_losses_absolute_seasonal_storage_m = 1656.2*(85 - middle.weather_data_hour[' Ta'] )+ 74.7 *(10-11)
    COP_e, T_VL_e = COP_calculation(scalars, east.weather_data_hour[' Ta'], model_ID, YEAR)
    fixed_losses_absolute_seasonal_storage_e = 1656.2*(85 - east.weather_data_hour[' Ta'] )+ 74.7 *(10-11)
    
    Ta_avg = ((north.weather_data_hour[' Ta'] + east.weather_data_hour[' Ta'] + middle.weather_data_hour[' Ta'] + swest.weather_data_hour[' Ta'])/4)
    COP_avg, T_VL_avg = COP_calculation(scalars, Ta_avg, model_ID, YEAR)
    fixed_losses_absolute_seasonal_storage_avg = 1656.2*(85 - Ta_avg )+ 74.7 *(10-11)
    
    #COP_n = COP_m = COP_e = COP_s = COP_avg
    #T_VL_e = T_VL_m = T_VL_n = T_VL_s = T_VL_avg
    #fixed_losses_absolute_seasonal_storage_n = fixed_losses_absolute_seasonal_storage_m = fixed_losses_absolute_seasonal_storage_e = fixed_losses_absolute_seasonal_storage_s = fixed_losses_absolute_seasonal_storage_avg
    T_seas_storage =90
    for i in range(len(T_VL_n)):
        if T_VL_n[i]<T_seas_storage:
            T_VL_n[i]=T_seas_storage
        elif T_VL_s[i]<T_seas_storage:
            T_VL_s[i]=T_seas_storage
        elif T_VL_m[i]<T_seas_storage:
            T_VL_m[i]=T_seas_storage
        elif T_VL_e[i]<T_seas_storage:
            T_VL_e[i]=T_seas_storage
            
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
    # Electricity Bus                                                                                      # Class Bus sind jetzt in module buses verschoben (solph.buses.Bus)
    #------------------------------------------------------------------------------
    b_hös = solph.buses.Bus(label = "Electricity_Hös") 
    
    b_el_n_in = solph.Bus(label="ElectricityIn_n")
    b_el_n_out = solph.Bus(label="ElectricityOut_n")

    b_el_m_in = solph.Bus(label="ElectricityIn_m")
    b_el_m_out = solph.Bus(label="ElectricityOut_m")
    
    b_el_e_in = solph.Bus(label="ElectricityIn_e")
    b_el_e_out= solph.Bus(label="ElectricityOut_e")
    
    b_el_s_in = solph.Bus(label="ElectricityIn_s")
    b_el_s_out = solph.Bus(label="ElectricityOut_s")
    
    b_pumps = solph.buses.Bus(label="Pumped-Hydro")
    
    energysystem.add(b_hös, b_el_n_in, b_el_n_out, b_el_e_in, b_el_e_out, b_el_m_in, b_el_m_out, b_el_s_in, b_el_s_out, b_pumps)
    
    #------------------------------------------------------------------------------
    # Electricity grid interconnection
    #------------------------------------------------------------------------------
    # Unrestricted electricity import from german grid
    energysystem.add(solph.components.Source(
       label='Import_Electricity',
       outputs={b_hös: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_Bezug_'+str(YEAR)],#['max_power'],
                                 variable_costs = strompreiszeitreihe+ import_price['grid_operating_fee_HöS<2500h'],
                                 custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Strom_'+ str(YEAR)],
                                                    'import_bilanz': -1},
                                 
           )}))
    
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
            
    
    
    
    # define links between grids and regions
    """Link between HS & North""" 
    energysystem.add(solph.components.Link(
        label='HS<->North',
        inputs= {b_hös: solph.Flow(),
                 b_el_n_in: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['max_import_power_north_'+str(YEAR)])
                     },
        outputs= {b_el_n_in: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['max_import_power_north_'+str(YEAR)],
                                        variable_costs= import_price['grid_operating_fee_HS<2500h']),
                  b_hös: solph.Flow(variable_costs= import_price['grid_operating_fee_HS<2500h'])
                  },
        conversion_factors = {(b_hös,b_el_n_in): 1, (b_el_n_in,b_hös):1}
        ))

    """Link between HS & East""" 
    energysystem.add(solph.components.Link(
        label='HS<->East',
        inputs= {b_hös: solph.Flow(),
                 b_el_e_in: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_import_power_east_'+str(YEAR)])
                 },
        outputs= {b_el_e_in: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['max_import_power_east_'+str(YEAR)],
                                        variable_costs= import_price['grid_operating_fee_HS<2500h']),
                  b_hös: solph.Flow(variable_costs= import_price['grid_operating_fee_HS<2500h'])
                  },
        conversion_factors = {(b_hös,b_el_e_in): 1, (b_el_e_in,b_hös):1}
        ))

    """Link between HS & Middle""" 
    energysystem.add(solph.components.Link(
        label='HS<->Middle',
        inputs= {b_hös: solph.Flow(),
                 b_el_m_in: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['max_import_power_middle_'+str(YEAR)])
                 },
        outputs= {b_el_m_in: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['max_import_power_middle_'+str(YEAR)],
                                          variable_costs= import_price['grid_operating_fee_HS<2500h']),
                  b_hös: solph.Flow(variable_costs= import_price['grid_operating_fee_HS<2500h'])
                  },
        conversion_factors = {(b_hös,b_el_m_in): 1, (b_el_m_in, b_hös): 1}
        ))

    """Link between HS & Swest""" 
    energysystem.add(solph.components.Link(
        label='HS<->Swest',
        inputs= {b_hös: solph.Flow(),
                 b_el_s_in: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['max_import_power_swest_'+str(YEAR)])
                 },
        outputs= {b_el_s_in: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_import_power_swest_'+str(YEAR)],
                                         variable_costs= import_price['grid_operating_fee_HS<2500h']),
                  b_hös: solph.Flow(variable_costs= import_price['grid_operating_fee_HS<2500h'])
                  },
        conversion_factors = {(b_hös,b_el_s_in): 1, (b_el_s_in, b_hös):1}
        ))


    """Link between HS & different regions""" 
    energysystem.add(solph.components.Link(
        label='North<->Middle',
        inputs= {b_el_n_in: solph.Flow(),
                 b_el_m_in: solph.Flow()},
        outputs= {b_el_m_in: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['connection_north_middle'],
                                          variable_costs= import_price['grid_operating_fee_HS<2500h']),
                 b_el_n_in: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['connection_north_middle'],
                                        variable_costs= import_price['grid_operating_fee_HS<2500h'])
                                        },
        conversion_factors = {(b_el_n_in, b_el_m_in): 1, (b_el_m_in, b_el_n_in):1}
        
        ))

    energysystem.add(solph.components.Link(
        label='Middle<->Swest',
        inputs= {b_el_m_in: solph.Flow(),
                 b_el_s_in: solph.Flow()},
        outputs= {b_el_s_in: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['connection_middle_swest'],
                                         variable_costs= import_price['grid_operating_fee_HS<2500h']),
                 b_el_m_in: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['connection_middle_swest'],
                                         variable_costs= import_price['grid_operating_fee_HS<2500h'])
                  },
        conversion_factors = {(b_el_m_in,b_el_s_in): 1, (b_el_s_in,b_el_m_in):1}
        
        ))

    energysystem.add(solph.components.Link(
         label='East<->Middle',
         inputs= {b_el_e_in: solph.Flow(),
                  b_el_m_in: solph.Flow()},
         outputs= {b_el_m_in: solph.Flow(nominal_value = scalars['Electricity_grid']['electricity']['connection_east_middle'],
                                           variable_costs= import_price['grid_operating_fee_HS<2500h']),
                  b_el_e_in: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['connection_east_middle'],
                                        variable_costs= import_price['grid_operating_fee_HS<2500h'])
                   },
         conversion_factors = {(b_el_e_in, b_el_m_in): 1, (b_el_m_in, b_el_e_in):1}
         
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
    #------------------------------------------------------------------------------
    # Umweltwaerme
    #------------------------------------------------------------------------------
    b_uw_n = solph.buses.Bus(label="Environmental heat_n")
    #------------------------------------------------------------------------------
    # Abwaerme
    #------------------------------------------------------------------------------
    b_abwaerme_n = solph.buses.Bus(label="Recovery heat_n")
    #------------------------------------------------------------------------------
    # Preheat
    #------------------------------------------------------------------------------
    b_preheat_n = solph.buses.Bus(label="Preheater_n")
    #------------------------------------------------------------------------------
    
    b_umgebungsluft_n = solph.buses.Bus(label="Umgebungsluftbus_n")

    # Hinzufügen der Busse zum Energiesystem-Modell 
    energysystem.add(b_gas_n, b_oil_fuel_n, b_bio_n, b_bioWood_n, b_dist_heat_n, b_H2_n, b_solidf_n,b_uw_n, b_abwaerme_n, b_preheat_n,b_umgebungsluft_n)
    
   


    """
    Renewable Energy sources
    """
    #------------------------------------------------------------------------------
    # Wind power plants
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Wind_n', 
        outputs={b_el_n_in: solph.Flow(fix=sequences['feed_in_profile']['Wind_north'],
                                        custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                    #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_onshore_wind_power_plant']['potential_north_max_'+str(YEAR)][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_n', 
        outputs={b_el_n_in: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_north'],
                                        custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                    #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_max'][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_open_n', 
        outputs={b_el_n_in: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_north'],
                                        custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                    #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_max'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant_n', 
        outputs={b_el_n_in: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                        custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                    minimum= scalars['Parameter_run_river_power_plant']['potential_north_min'][model_ID], 
                                                                    maximum = scalars['Parameter_run_river_power_plant']['potential_north_min'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST_n', 
        outputs={b_dist_heat_n: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                      #maximum=scalars['Parameter_solar_thermal_power_plant']['potential_total'][model_ID]/4)
        ))}))
    
    #------------------------------------------------------------------------------
    # Environmental heat
    #------------------------------------------------------------------------------
      
    energysystem.add(solph.components.Source(
        label='UW_n', 
        outputs={b_uw_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=0, 
                                                                      maximum=scalars['System_configurations_2024']['System']['Potential_Umweltwärme']/4
                                                                    )
        )}))
    #------------------------------------------------------------------------------
    # Umgebungsluft
    #------------------------------------------------------------------------------
    
    energysystem.add(solph.components.Source(
        label='Umgebungsluft_n', 
        outputs={b_umgebungsluft_n: solph.Flow()}))
    
    #------------------------------------------------------------------------------
    # Recovery heat
    #------------------------------------------------------------------------------
    
       
    energysystem.add(solph.components.Source(
        label='AW_n', 
        outputs={b_abwaerme_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=0, 
                                                                      maximum=scalars['System_configurations_2024']['System']['Potential_Abwärme']/4
                                                                      )
                                          )
                  }))
    
    """ Imports """
    
    energysystem.add(solph.components.Converter(
        label="Netzverluste_n",
        inputs={b_el_n_in: solph.Flow()},
        outputs={b_el_n_out: solph.Flow()},
        conversion_factors={b_el_n_out: 0.95}
        ))
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel_n',
        outputs={b_bio_n: solph.Flow(variable_costs = import_price['import_biomass_price'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood_n',
        outputs={b_bioWood_n: solph.Flow(variable_costs =import_price['import_biomass_price'],
                                         #fix=sequences['Base_demand_profile']['base_load'],
                                         #summed_max= scalars['System_configurations_2024']['System']['Holzpotential_nord'],
                                         investment= solph.Investment(ep_costs = 0),
                                             custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
    #if YEAR == 2020:
    energysystem.add(solph.components.Source(
        label='Import_brown_coal_n',
        outputs={b_solidf_n: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                    fix=sequences['Base_demand_profile']['base_load'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=(scalars['System_configurations_2024']['System']['Menge_Braunkohle']/4 )*len(import_price['import_brown_coal_price']),
                                    custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Braunkohle']},
        )}))
        
        #------------------------------------------------------------------------------
        # Import hard coal
        #------------------------------------------------------------------------------
        # energysystem.add(solph.components.Source(
        #     label='Import_hard_coal_n',
        #     outputs={b_solidf_n: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
        #                                 fix=sequences['Base_demand_profile']['base_load'], 
        #                                 #nominal_value = 1,
        #                                 investment = solph.Investment(ep_costs=0),
        #                                 summed_max=(scalars['System_configurations_2024']['System']['Menge_Steinkohle']/4)*len(import_price['import_brown_coal_price']),
        #                                 custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Steinkohle']},
                                        
        #     )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas_n',
        outputs={b_gas_n: solph.Flow(variable_costs = import_price['import_gas_price'],
                                         custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Erdgas'],
                                                            "import_bilanz": -1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil_n',
        outputs={b_oil_fuel_n: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                     custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Oel'],
                                                                        "import_bilanz": -1}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel_n',
        outputs={b_oil_fuel_n: solph.Flow(variable_costs = import_price['import_synt_fuel_price'],
                                          custom_attributes={"import_bilanz": -1}
            )}))
    
    #------------------------------------------------------------------------------
    # Import Hydrogen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Hydrogen_n',
        outputs={b_H2_n: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                  variable_costs = import_price['import_hydrogen_price'],
                                  custom_attributes={"import_bilanz": -1}
            )}))
    
    """
    Transformers
    """
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing_n",
        inputs={b_bio_n: solph.Flow(#custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_upgrading_plant']['existing_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biogas_upgrading_plant']['epc'],
                                                                 maximum=scalars['Parameter_biogas_upgrading_plant']['potential'][model_ID]/4
                                                                 ),
                                   custom_attributes={'emission_factor': scalars['Parameter_biogas_upgrading_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas_n: scalars['Parameter_biogas_upgrading_plant']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_new_n",
        inputs={b_bio_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biomethane_injection_plant']['epc']),
                                   custom_attributes={'emission_factor': scalars['Parameter_biomethane_injection_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas_n: scalars['Parameter_biomethane_injection_plant']['efficiency_'+str(YEAR)][model_ID]/100},
        
                                    
        ))
    
    #------------------------------------------------------------------------------
    # Biogas BHKW
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas- BHKW_n',
        inputs={b_bio_n: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['existing_factor'][model_ID]})},
                                  
        outputs={b_el_n_in: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['biogas_combined_heat_and_power_plant']['epc']), 
                                        custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load']),
                  b_dist_heat_n: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                          fix=sequences['Base_demand_profile']['base_load'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el_n_in: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat_n: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid (Holz)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL_Holz_n",
        inputs={b_bioWood_n: solph.Flow()},
        outputs={b_oil_fuel_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_holz']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                          custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_holz']['EE_factor'][model_ID]}
                                          )},
        conversion_factors={b_oil_fuel_n: scalars['Parameter_biomass_to_liquid_system_holz']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid (Substrat)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL_substrat_n",
        inputs={b_bio_n: solph.Flow()},
        outputs={b_oil_fuel_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_substrat']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                          custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_substrat']['EE_factor'][model_ID]}
                                          )},
        conversion_factors={b_oil_fuel_n: scalars['Parameter_biomass_to_liquid_system_substrat']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell_n",
        inputs={b_H2_n: solph.Flow()},
        outputs={b_el_n_in: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                                ))},
        conversion_factors={b_el_n_in: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation_n",
        inputs={b_H2_n: solph.Flow()},
        outputs={b_gas_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                                 ))},
        conversion_factors={b_gas_n: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]/100}  
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL_n",
        inputs={b_H2_n: solph.Flow(),
                b_el_n_out: solph.Flow()},
        outputs={b_oil_fuel_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                             ))},
        conversion_factors={b_H2_n: (
            (scalars['Parameter_power_to_liquid_system']['efficiency_H2'][model_ID]/100)/
                                   (scalars['Parameter_power_to_liquid_system']['efficiency_ges'][model_ID]/100)),
                            b_el_n_out: (
                                (scalars['Parameter_power_to_liquid_system']['efficiency_el'][model_ID]/100)/
                                   (scalars['Parameter_power_to_liquid_system']['efficiency_ges'][model_ID]/100))
                            }
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD_n',
        inputs={b_gas_n: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el_n_in: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                              maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential_total'][model_ID]/4)),
                 b_dist_heat_n: solph.Flow()},
        conversion_factors={b_el_n_in: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat_n: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_n',
        inputs={b_bioWood_n: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_n_in: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_power_plant']['EE_factor'][model_ID]}),
                 },
                 
        conversion_factors={b_el_n_in: scalars['Parameter_biomass_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            }
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat_n',
        inputs={b_bioWood_n: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                           #nominal_value = 1
                                           #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat_n: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                    investment=solph.Investment(ep_costs=epc_costs['biomass_heating_plant']['epc']),
                                    custom_attributes={'emission_factor': scalars['Parameter_biomass_heating_plant']['EE_factor'][model_ID]})},
        conversion_factors={b_dist_heat_n: scalars['Parameter_biomass_heating_plant']['efficiency_th_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty  and heatproduction)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_heat_n',
        inputs={b_bioWood_n: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_n_in: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_combined_heat_and_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]}),
                 
                  b_dist_heat_n: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                            #fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value= 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )
                  },
        conversion_factors={b_el_n_in: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            b_dist_heat_n: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_th_' +str(YEAR)][model_ID]/100
                            }
        ))  
    
    #------------------------------------------------------------------------------
    # Solid biomass in the same bus as coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BioTransformer_n",
        inputs={b_bioWood_n: solph.Flow()},
        outputs={b_solidf_n: solph.Flow(custom_attributes={'emission_factor': -1})},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler_n",
        inputs={b_el_n_out: solph.Flow()},
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
        conversion_factors={b_dist_heat_n: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]/100}    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Air
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air_n",
        inputs={b_el_n_out: solph.Flow(),
                b_umgebungsluft_n: solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]}
                    )
                },
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Umgebungswärme']['epc'], 
                                                                 #maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]/4)
                                                                 ))},
        conversion_factors={b_el_n_out: 1/COP_n,
                            b_umgebungsluft_n: (COP_n-1)/COP_n},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water_n",
        inputs={b_el_n_out: solph.Flow(),
                b_uw_n:solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]}
                    )},
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential_total'][model_ID]/4
                                                                  ))},
        conversion_factors={b_el_n_out: 1/scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID],
                            b_uw_n: (scalars['Parameter_heat_pump_ground_Flusswärme'][
                                'efficiency_'+str(YEAR)][model_ID]-1)/scalars[
                                    'Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_recovery_heat_n",
        inputs={b_el_n_out: solph.Flow(),
                b_abwaerme_n: solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]})},
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
                                                                  #maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]/4
                                                                  ))},
        conversion_factors={b_el_n_out: 1/scalars['Parameter_heat_pump_air_Abwärme'][
            'efficiency_'+str(YEAR)][model_ID],
                            b_abwaerme_n: (scalars['Parameter_heat_pump_air_Abwärme'][
                                'efficiency_'+str(YEAR)][model_ID]-1)/scalars[
                                    'Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]}   
        ))
    
    #------------------------------------------------------------------------------
    # Elektrolysis
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electrolysis_n",
        inputs={b_el_n_out: solph.Flow()},
        outputs={b_H2_n: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc'], 
                                                                ))},
        conversion_factors={b_H2_n: scalars['Parameter_electrolysis']['efficiency_'+str(YEAR)][model_ID]/100},
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung- WP
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- WP_n",
        inputs={b_el_n_out: solph.Flow(),
                b_preheat_n: solph.Flow()},
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_el_n_out: 1 -(T_seas_storage/T_VL_n),
                            b_preheat_n: (T_seas_storage/T_VL_n)
                            },
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung - Boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- Electric boiler_n",
        inputs={b_el_n_out: solph.Flow(),
                b_preheat_n: solph.Flow()},
        outputs={b_dist_heat_n: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['electrical_heater']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_el_n_out: 1 -(T_seas_storage/T_VL_n),
                            b_preheat_n: (T_seas_storage/T_VL_n)
                            },
        ))
    
           
      
    """
    Energy storage
    """
    
    
    #------------------------------------------------------------------------------
    # Electricity storage (Großbatterie-speicher)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Battery_n',
        inputs={b_el_n_in: solph.Flow()},
        outputs={b_el_n_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                        maximum=scalars['Parameter_storage_electricity']['potential_total'][model_ID]/4,
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Electricity storage (Li-Ion)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Li-Ion_Battery_n',
        inputs={b_el_n_in: solph.Flow()},
        outputs={b_el_n_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Li-Ion']['initial_storage_level'][model_ID],
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
        label='Natrium_Battery_n',
        inputs={b_el_n_in: solph.Flow()},
        outputs={b_el_n_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Natrium']['initial_storage_level'][model_ID],
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
        label='Red-OX_Battery_n',
        inputs={b_el_n_in: solph.Flow()},
        outputs={b_el_n_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Red-OX']['initial_storage_level'][model_ID],
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
        label='Heat storage_dist_heat_n',
        inputs={b_dist_heat_n: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float((scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()    
                                    )},
        outputs={b_dist_heat_n: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float((scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_district_heating']['loss_rate'][model_ID]/24),
        inflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_heat_district_heating']['initial_storage_level'][model_ID],
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
        label='Heat storage_seasonal_n',
        inputs={b_dist_heat_n: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float((scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_preheat_n: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float((scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_seasonal']['loss_rate'][model_ID]),
        fixed_losses_relative=float(scalars['Parameter_storage_heat_seasonal']['fixed_losses_relative'][model_ID]),
        inflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_heat_seasonal']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_heat_seasonal']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat_seasonal']['epc'], 
                                      
                                      )
                                      
        ))
    
    
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas_storage_n",
        inputs={b_gas_n: solph.Flow()},
        outputs={b_gas_n: solph.Flow()},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                      maximum = scalars['Parameter_storage_gas']['potential_total'][model_ID]/4)  
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
        inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                      maximum = scalars['Parameter_storage_hydrogen']['potential_total'][model_ID]/4)  
        ))
    
    #------------------------------------------------------------------------------
    # Pumped hydro storage (Bestand) HochSpannungnetz verbunden
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label="Pumped_hydro_storage_bestand_n",
        inputs={b_el_n_in: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                                          minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4,
                                          maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4)
            )},
        outputs={b_el_n_in: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                              minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4,
                              maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4)
            )},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['initial_storage_level'][model_ID],
        # invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        # invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Becken)']['epc'],
                                      minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID]/4,
                                      maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID]/4)
        ))
    
    """
    Export block
    """
    #------------------------------------------------------------------------------  
    # Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Electricity_n', 
        inputs={b_el_n_out: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_export_power_north_'+str(YEAR)],
                                  variable_costs = [i*(-1) for i in strompreiszeitreihe],
                                  custom_attributes={"export_bilanz": -1}
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen_n', 
        inputs={b_H2_n: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                 variable_costs = import_price['export_hydrogen_price'],
                                 custom_attributes={"export_bilanz": -1}
                                  
        )}))
    
    """
    Defining final energy demand as Sinks
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total_n', 
        inputs={b_el_n_out: solph.Flow(fix=demand['electricity']['north'], 
                                 nominal_value=1,
        )}))
    
    
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_Rechenzentren_n', 
        inputs={b_el_n_out: solph.Flow(fix=demand['rechnenzentrum']['north'],#[80*1e6*0.045/8760] * 8760,
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
    # Oil and fuel demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil & fuel_demand_total_n', 
        inputs={b_oil_fuel_n: solph.Flow(fix=demand['oil']['north']+demand['fuel']['north'], 
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
    # Material demand: Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Biomasse_n', 
        inputs={b_solidf_n: solph.Flow(fix=demand['material_usage_biomasse']['north'], 
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
    Excess energy capture sinks 
    """
    #------------------------------------------------------------------------------
    # Überschuss Senke für Strom
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_el_n', 
        inputs={b_el_n_out: solph.Flow(variable_costs = 200
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_gas_n', 
        inputs={b_gas_n: solph.Flow(variable_costs = 1000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Oel/Kraftstoffe
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_oil_fuel_n', 
        inputs={b_oil_fuel_n: solph.Flow(variable_costs = 1000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_bio_n', 
        inputs={b_bio_n: solph.Flow(variable_costs = 0
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Waerme
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_distheat_n', 
        inputs={b_dist_heat_n: solph.Flow(variable_costs = 0
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Wasserstoff
    #-----------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_H2_n', 
        inputs={b_H2_n: solph.Flow(variable_costs = 1000000
        )}))
    
    ##############################################################       East region         #################################################################
    """ Defining energy system for East region"""
    
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
    #------------------------------------------------------------------------------
    # Umweltwaerme
    #------------------------------------------------------------------------------
    b_uw_e = solph.buses.Bus(label="Environmental heat_e")
    #------------------------------------------------------------------------------
    # Abwaerme
    #------------------------------------------------------------------------------
    b_abwaerme_e = solph.buses.Bus(label="Recovery heat_e")
    #------------------------------------------------------------------------------
    # Preheat
    #------------------------------------------------------------------------------
    b_preheat_e = solph.buses.Bus(label="Preheater_e")
    #------------------------------------------------------------------------------
    
    b_umgebungsluft_e = solph.buses.Bus(label="Umgebungsluftbus_e")
 
    # Hinzufügen der Busse zum Energiesystem-Modell 
    energysystem.add(b_gas_e, b_oil_fuel_e, b_bio_e, b_bioWood_e, b_dist_heat_e, b_H2_e, b_solidf_e,b_uw_e, b_abwaerme_e, b_preheat_e,b_umgebungsluft_e)
    
   
 
 
    """
    Renewable Energy sources
    """
    #------------------------------------------------------------------------------
    # Wind power plants
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Wind_e', 
        outputs={b_el_e_in: solph.Flow(fix=sequences['feed_in_profile']['Wind_east'],
                                        custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                    #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_onshore_wind_power_plant']['potential_east_max_'+str(YEAR)][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_e', 
        outputs={b_el_e_in: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_east'],
                                        custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                    #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_east_max'][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_open_e', 
        outputs={b_el_e_in: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_east'],
                                        custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                    #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_east_max'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant_e', 
        outputs={b_el_e_in: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                        custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                    minimum= scalars['Parameter_run_river_power_plant']['potential_east_min'][model_ID], 
                                                                    maximum = scalars['Parameter_run_river_power_plant']['potential_east_min'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST_e', 
        outputs={b_dist_heat_e: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                      #maximum=scalars['Parameter_solar_thermal_power_plant']['potential_total'][model_ID]/4)
        ))}))
    
    #------------------------------------------------------------------------------
    # Environmental heat
    #------------------------------------------------------------------------------
      
    energysystem.add(solph.components.Source(
        label='UW_e', 
        outputs={b_uw_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=0, 
                                                                      maximum=scalars['System_configurations_2024']['System']['Potential_Umweltwärme']/4
                                                                    )
        )}))
    #------------------------------------------------------------------------------
    # Umgebungsluft
    #------------------------------------------------------------------------------
    
    energysystem.add(solph.components.Source(
        label='Umgebungsluft_e', 
        outputs={b_umgebungsluft_e: solph.Flow()}))
    
    #------------------------------------------------------------------------------
    # Recovery heat
    #------------------------------------------------------------------------------
    
       
    energysystem.add(solph.components.Source(
        label='AW_e', 
        outputs={b_abwaerme_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=0, 
                                                                      maximum=scalars['System_configurations_2024']['System']['Potential_Abwärme']/4
                                                                      )
                                          )
                  }))
    
    """ Imports """
    
    energysystem.add(solph.components.Converter(
        label="Netzverluste_e",
        inputs={b_el_e_in: solph.Flow()},
        outputs={b_el_e_out: solph.Flow()},
        conversion_factors={b_el_e_out: 0.95}
        ))
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel_e',
        outputs={b_bio_e: solph.Flow(variable_costs = import_price['import_biomass_price'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood_e',
        outputs={b_bioWood_e: solph.Flow(variable_costs =import_price['import_biomass_price'],
                                         #fix=sequences['Base_demand_profile']['base_load'],
                                         #summed_max= scalars['System_configurations_2024']['System']['Holzpotential_nord'],
                                         investment= solph.Investment(ep_costs = 0),
                                             custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
    #if YEAR == 2020:
    energysystem.add(solph.components.Source(
        label='Import_brown_coal_e',
        outputs={b_solidf_e: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                    fix=sequences['Base_demand_profile']['base_load'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=(scalars['System_configurations_2024']['System']['Menge_Braunkohle']/4 )*len(import_price['import_brown_coal_price']),
                                    custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Braunkohle']},
        )}))
        
        #------------------------------------------------------------------------------
        # Import hard coal
        #------------------------------------------------------------------------------
        # energysystem.add(solph.components.Source(
        #     label='Import_hard_coal_e',
        #     outputs={b_solidf_e: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
        #                                 fix=sequences['Base_demand_profile']['base_load'], 
        #                                 #nominal_value = 1,
        #                                 investment = solph.Investment(ep_costs=0),
        #                                 summed_max=(scalars['System_configurations_2024']['System']['Menge_Steinkohle']/4)*len(import_price['import_brown_coal_price']),
        #                                 custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Steinkohle']},
                                        
        #     )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas_e',
        outputs={b_gas_e: solph.Flow(variable_costs = import_price['import_gas_price'],
                                         custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Erdgas'],
                                                            "import_bilanz": -1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil_e',
        outputs={b_oil_fuel_e: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                     custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Oel'],
                                                                        "import_bilanz": -1}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel_e',
        outputs={b_oil_fuel_e: solph.Flow(variable_costs = import_price['import_synt_fuel_price'],
                                          custom_attributes={"import_bilanz": -1}
            )}))
    
    #------------------------------------------------------------------------------
    # Import Hydrogen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Hydrogen_e',
        outputs={b_H2_e: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                  variable_costs = import_price['import_hydrogen_price'],
                                  custom_attributes={"import_bilanz": -1}
            )}))
    
    """
    Transformers
    """
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing_e",
        inputs={b_bio_e: solph.Flow(#custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_upgrading_plant']['existing_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biogas_upgrading_plant']['epc'],
                                                                 maximum=scalars['Parameter_biogas_upgrading_plant']['potential'][model_ID]/4
                                                                 ),
                                   custom_attributes={'emission_factor': scalars['Parameter_biogas_upgrading_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas_e: scalars['Parameter_biogas_upgrading_plant']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_new_e",
        inputs={b_bio_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biomethane_injection_plant']['epc']),
                                   custom_attributes={'emission_factor': scalars['Parameter_biomethane_injection_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas_e: scalars['Parameter_biomethane_injection_plant']['efficiency_'+str(YEAR)][model_ID]/100},
        
                                    
        ))
    
    #------------------------------------------------------------------------------
    # Biogas BHKW
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas- BHKW_e',
        inputs={b_bio_e: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['existing_factor'][model_ID]})},
                                  
        outputs={b_el_e_in: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['biogas_combined_heat_and_power_plant']['epc']), 
                                        custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load']),
                  b_dist_heat_e: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                          fix=sequences['Base_demand_profile']['base_load'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el_e_in: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat_e: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid (Holz)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL_Holz_e",
        inputs={b_bioWood_e: solph.Flow()},
        outputs={b_oil_fuel_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_holz']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                          custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_holz']['EE_factor'][model_ID]}
                                          )},
        conversion_factors={b_oil_fuel_e: scalars['Parameter_biomass_to_liquid_system_holz']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid (Substrat)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL_substrat_e",
        inputs={b_bio_e: solph.Flow()},
        outputs={b_oil_fuel_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_substrat']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                          custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_substrat']['EE_factor'][model_ID]}
                                          )},
        conversion_factors={b_oil_fuel_e: scalars['Parameter_biomass_to_liquid_system_substrat']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell_e",
        inputs={b_H2_e: solph.Flow()},
        outputs={b_el_e_in: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                                ))},
        conversion_factors={b_el_e_in: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation_e",
        inputs={b_H2_e: solph.Flow()},
        outputs={b_gas_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                                 ))},
        conversion_factors={b_gas_e: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]/100}  
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL_e",
        inputs={b_H2_e: solph.Flow(),
                b_el_e_out: solph.Flow()},
        outputs={b_oil_fuel_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                             ))},
        conversion_factors={b_H2_e: (
            (scalars['Parameter_power_to_liquid_system']['efficiency_H2'][model_ID]/100)/
                                   (scalars['Parameter_power_to_liquid_system']['efficiency_ges'][model_ID]/100)),
                            b_el_e_out: (
                                (scalars['Parameter_power_to_liquid_system']['efficiency_el'][model_ID]/100)/
                                   (scalars['Parameter_power_to_liquid_system']['efficiency_ges'][model_ID]/100))
                            }
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD_e',
        inputs={b_gas_e: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el_e_in: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                              maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential_total'][model_ID]/4)),
                 b_dist_heat_e: solph.Flow()},
        conversion_factors={b_el_e_in: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat_e: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_e',
        inputs={b_bioWood_e: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_e_in: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_power_plant']['EE_factor'][model_ID]}),
                 },
                 
        conversion_factors={b_el_e_in: scalars['Parameter_biomass_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            }
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat_e',
        inputs={b_bioWood_e: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                           #nominal_value = 1
                                           #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat_e: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                    investment=solph.Investment(ep_costs=epc_costs['biomass_heating_plant']['epc']),
                                    custom_attributes={'emission_factor': scalars['Parameter_biomass_heating_plant']['EE_factor'][model_ID]})},
        conversion_factors={b_dist_heat_e: scalars['Parameter_biomass_heating_plant']['efficiency_th_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty  and heatproduction)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_heat_e',
        inputs={b_bioWood_e: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_e_in: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_combined_heat_and_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]}),
                 
                  b_dist_heat_e: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                            #fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value= 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )
                  },
        conversion_factors={b_el_e_in: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            b_dist_heat_e: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_th_' +str(YEAR)][model_ID]/100
                            }
        ))  
    
    #------------------------------------------------------------------------------
    # Solid biomass in the same bus as coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BioTransformer_e",
        inputs={b_bioWood_e: solph.Flow()},
        outputs={b_solidf_e: solph.Flow(custom_attributes={'emission_factor': -1})},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler_e",
        inputs={b_el_e_out: solph.Flow()},
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
        conversion_factors={b_dist_heat_e: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]/100}    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Air
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air_e",
        inputs={b_el_e_out: solph.Flow(),
                b_umgebungsluft_e: solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]}
                    )
                },
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Umgebungswärme']['epc'], 
                                                                 #maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]/4)
                                                                 ))},
        conversion_factors={b_el_e_out: 1/COP_e,
                            b_umgebungsluft_e: (COP_e-1)/COP_e},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water_e",
        inputs={b_el_e_out: solph.Flow(),
                b_uw_e:solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]}
                    )},
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential_total'][model_ID]/4
                                                                  ))},
        conversion_factors={b_el_e_out: 1/scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID],
                            b_uw_e: (scalars['Parameter_heat_pump_ground_Flusswärme'][
                                'efficiency_'+str(YEAR)][model_ID]-1)/scalars[
                                    'Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_recovery_heat_e",
        inputs={b_el_e_out: solph.Flow(),
                b_abwaerme_e: solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]})},
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
                                                                  #maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]/4
                                                                  ))},
        conversion_factors={b_el_e_out: 1/scalars['Parameter_heat_pump_air_Abwärme'][
            'efficiency_'+str(YEAR)][model_ID],
                            b_abwaerme_e: (scalars['Parameter_heat_pump_air_Abwärme'][
                                'efficiency_'+str(YEAR)][model_ID]-1)/scalars[
                                    'Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]}   
        ))
    
    #------------------------------------------------------------------------------
    # Elektrolysis
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electrolysis_e",
        inputs={b_el_e_out: solph.Flow()},
        outputs={b_H2_e: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc'], 
                                                                ))},
        conversion_factors={b_H2_e: scalars['Parameter_electrolysis']['efficiency_'+str(YEAR)][model_ID]/100},
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung- WP
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- WP_e",
        inputs={b_el_e_out: solph.Flow(),
                b_preheat_e: solph.Flow()},
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_el_e_out: 1 -(T_seas_storage/T_VL_e),
                            b_preheat_e: (T_seas_storage/T_VL_e)
                            },
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung - Boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- Electric boiler_e",
        inputs={b_el_e_out: solph.Flow(),
                b_preheat_e: solph.Flow()},
        outputs={b_dist_heat_e: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['electrical_heater']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_el_e_out: 1 -(T_seas_storage/T_VL_e),
                            b_preheat_e: (T_seas_storage/T_VL_e)
                            },
        ))
    
           
      
    """
    Energy storage
    """
    
    
    #------------------------------------------------------------------------------
    # Electricity storage (Großbatterie-speicher)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Battery_e',
        inputs={b_el_e_in: solph.Flow()},
        outputs={b_el_e_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                        maximum=scalars['Parameter_storage_electricity']['potential_total'][model_ID]/4,
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Electricity storage (Li-Ion)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Li-Ion_Battery_e',
        inputs={b_el_e_in: solph.Flow()},
        outputs={b_el_e_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Li-Ion']['initial_storage_level'][model_ID],
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
        label='Natrium_Battery_e',
        inputs={b_el_e_in: solph.Flow()},
        outputs={b_el_e_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Natrium']['initial_storage_level'][model_ID],
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
        label='Red-OX_Battery_e',
        inputs={b_el_e_in: solph.Flow()},
        outputs={b_el_e_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Red-OX']['initial_storage_level'][model_ID],
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
        label='Heat storage_dist_heat_e',
        inputs={b_dist_heat_e: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float((scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()    
                                    )},
        outputs={b_dist_heat_e: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float((scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_district_heating']['loss_rate'][model_ID]/24),
        inflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_heat_district_heating']['initial_storage_level'][model_ID],
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
        label='Heat storage_seasonal_e',
        inputs={b_dist_heat_e: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float((scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_preheat_e: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float((scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_seasonal']['loss_rate'][model_ID]),
        fixed_losses_relative=float(scalars['Parameter_storage_heat_seasonal']['fixed_losses_relative'][model_ID]),
        inflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_heat_seasonal']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_heat_seasonal']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat_seasonal']['epc'], 
                                      
                                      )
                                      
        ))
    
    
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas_storage_e",
        inputs={b_gas_e: solph.Flow()},
        outputs={b_gas_e: solph.Flow()},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                      maximum = scalars['Parameter_storage_gas']['potential_total'][model_ID]/4)  
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
        inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                      maximum = scalars['Parameter_storage_hydrogen']['potential_total'][model_ID]/4)  
        ))
    
    #------------------------------------------------------------------------------
    # Pumped hydro storage (Bestand) HochSpannungnetz verbunden
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label="Pumped_hydro_storage_bestand_e",
        inputs={b_el_e_in: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                                          minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4,
                                          maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4)
            )},
        outputs={b_el_e_in: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                              minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4,
                              maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4)
            )},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['initial_storage_level'][model_ID],
        # invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        # invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Becken)']['epc'],
                                      minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID]/4,
                                      maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID]/4)
        ))
    
    """
    Export block
    """
    #------------------------------------------------------------------------------  
    # Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Electricity_e', 
        inputs={b_el_e_out: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_export_power_east_'+str(YEAR)],
                                  variable_costs = [i*(-1) for i in strompreiszeitreihe],
                                  custom_attributes={"export_bilanz": -1}
        )}))
 
    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen_e', 
        inputs={b_H2_e: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                 variable_costs = import_price['export_hydrogen_price'],
                                 custom_attributes={"export_bilanz": -1}
                                  
        )}))
    
    """
    Defining final energy demand as Sinks
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total_e', 
        inputs={b_el_e_out: solph.Flow(fix=demand['electricity']['east'], 
                                 nominal_value=1,
        )}))
    
    
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_Rechenzentren_e', 
        inputs={b_el_e_out: solph.Flow(fix=demand['rechnenzentrum']['east'],#[80*1e6*0.045/8760] * 8760,
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
    # Oil and fuel demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil & fuel_demand_total_e', 
        inputs={b_oil_fuel_e: solph.Flow(fix=demand['oil']['east']+demand['fuel']['east'], 
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
    # Material demand: Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Biomasse_e', 
        inputs={b_solidf_e: solph.Flow(fix=demand['material_usage_biomasse']['east'], 
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
    Excess energy capture sinks 
    """
    #------------------------------------------------------------------------------
    # Überschuss Senke für Strom
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_el_e', 
        inputs={b_el_e_out: solph.Flow(variable_costs = 200
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_gas_e', 
        inputs={b_gas_e: solph.Flow(variable_costs = 1000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Oel/Kraftstoffe
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_oil_fuel_e', 
        inputs={b_oil_fuel_e: solph.Flow(variable_costs = 1000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_bio_e', 
        inputs={b_bio_e: solph.Flow(variable_costs = 0
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Waerme
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_distheat_e', 
        inputs={b_dist_heat_e: solph.Flow(variable_costs = 0
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Wasserstoff
    #-----------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_H2_e', 
        inputs={b_H2_e: solph.Flow(variable_costs = 1000000
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
    #------------------------------------------------------------------------------
    # Umweltwaerme
    #------------------------------------------------------------------------------
    b_uw_m = solph.buses.Bus(label="Environmental heat_m")
    #------------------------------------------------------------------------------
    # Abwaerme
    #------------------------------------------------------------------------------
    b_abwaerme_m = solph.buses.Bus(label="Recovery heat_m")
    #------------------------------------------------------------------------------
    # Preheat
    #------------------------------------------------------------------------------
    b_preheat_m = solph.buses.Bus(label="Preheater_m")
    #------------------------------------------------------------------------------
    
    b_umgebungsluft_m = solph.buses.Bus(label="Umgebungsluftbus_m")
 
    # Hinzufügen der Busse zum Energiesystem-Modell 
    energysystem.add(b_gas_m, b_oil_fuel_m, b_bio_m, b_bioWood_m, b_dist_heat_m, b_H2_m, b_solidf_m,b_uw_m, b_abwaerme_m, b_preheat_m,b_umgebungsluft_m)
    
   
 
 
    """
    Renewable Energy sources
    """
    #------------------------------------------------------------------------------
    # Wind power plants
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Wind_m', 
        outputs={b_el_m_in: solph.Flow(fix=sequences['feed_in_profile']['Wind_middle'],
                                        custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                    #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_onshore_wind_power_plant']['potential_middle_max_'+str(YEAR)][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_m', 
        outputs={b_el_m_in: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_middle'],
                                        custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                    #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_middle_max'][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_open_m', 
        outputs={b_el_m_in: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_middle'],
                                        custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                    #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_middle_max'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant_m', 
        outputs={b_el_m_in: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                        custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                    minimum= scalars['Parameter_run_river_power_plant']['potential_middle_min'][model_ID], 
                                                                    maximum = scalars['Parameter_run_river_power_plant']['potential_middle_min'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST_m', 
        outputs={b_dist_heat_m: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                      #maximum=scalars['Parameter_solar_thermal_power_plant']['potential_total'][model_ID]/4)
        ))}))
    
    #------------------------------------------------------------------------------
    # Environmental heat
    #------------------------------------------------------------------------------
      
    energysystem.add(solph.components.Source(
        label='UW_m', 
        outputs={b_uw_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=0, 
                                                                      maximum=scalars['System_configurations_2024']['System']['Potential_Umweltwärme']/4
                                                                    )
        )}))
    #------------------------------------------------------------------------------
    # Umgebungsluft
    #------------------------------------------------------------------------------
    
    energysystem.add(solph.components.Source(
        label='Umgebungsluft_m', 
        outputs={b_umgebungsluft_m: solph.Flow()}))
    
    #------------------------------------------------------------------------------
    # Recovery heat
    #------------------------------------------------------------------------------
    
       
    energysystem.add(solph.components.Source(
        label='AW_m', 
        outputs={b_abwaerme_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=0, 
                                                                      maximum=scalars['System_configurations_2024']['System']['Potential_Abwärme']/4
                                                                      )
                                          )
                  }))
    
    """ Imports """
    
    energysystem.add(solph.components.Converter(
        label="Netzverluste_m",
        inputs={b_el_m_in: solph.Flow()},
        outputs={b_el_m_out: solph.Flow()},
        conversion_factors={b_el_m_out: 0.95}
        ))
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel_m',
        outputs={b_bio_m: solph.Flow(variable_costs = import_price['import_biomass_price'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood_m',
        outputs={b_bioWood_m: solph.Flow(variable_costs =import_price['import_biomass_price'],
                                         #fix=sequences['Base_demand_profile']['base_load'],
                                         #summed_max= scalars['System_configurations_2024']['System']['Holzpotential_nord'],
                                         investment= solph.Investment(ep_costs = 0),
                                             custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
    #if YEAR == 2020:
    energysystem.add(solph.components.Source(
        label='Import_brown_coal_m',
        outputs={b_solidf_m: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                    fix=sequences['Base_demand_profile']['base_load'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=(scalars['System_configurations_2024']['System']['Menge_Braunkohle']/4 )*len(import_price['import_brown_coal_price']),
                                    custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Braunkohle']},
        )}))
        
        #------------------------------------------------------------------------------
        # Import hard coal
        #------------------------------------------------------------------------------
        # energysystem.add(solph.components.Source(
        #     label='Import_hard_coal_m',
        #     outputs={b_solidf_m: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
        #                                 fix=sequences['Base_demand_profile']['base_load'], 
        #                                 #nominal_value = 1,
        #                                 investment = solph.Investment(ep_costs=0),
        #                                 summed_max=(scalars['System_configurations_2024']['System']['Menge_Steinkohle']/4)*len(import_price['import_brown_coal_price']),
        #                                 custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Steinkohle']},
                                        
        #     )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas_m',
        outputs={b_gas_m: solph.Flow(variable_costs = import_price['import_gas_price'],
                                         custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Erdgas'],
                                                            "import_bilanz": -1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil_m',
        outputs={b_oil_fuel_m: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                     custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Oel'],
                                                                        "import_bilanz": -1}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel_m',
        outputs={b_oil_fuel_m: solph.Flow(variable_costs = import_price['import_synt_fuel_price'],
                                          custom_attributes={"import_bilanz": -1}
            )}))
    
    #------------------------------------------------------------------------------
    # Import Hydrogen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Hydrogen_m',
        outputs={b_H2_m: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                  variable_costs = import_price['import_hydrogen_price'],
                                  custom_attributes={"import_bilanz": -1}
            )}))
    
    """
    Transformers
    """
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing_m",
        inputs={b_bio_m: solph.Flow(#custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_upgrading_plant']['existing_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biogas_upgrading_plant']['epc'],
                                                                 maximum=scalars['Parameter_biogas_upgrading_plant']['potential'][model_ID]/4
                                                                 ),
                                   custom_attributes={'emission_factor': scalars['Parameter_biogas_upgrading_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas_m: scalars['Parameter_biogas_upgrading_plant']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_new_m",
        inputs={b_bio_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biomethane_injection_plant']['epc']),
                                   custom_attributes={'emission_factor': scalars['Parameter_biomethane_injection_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas_m: scalars['Parameter_biomethane_injection_plant']['efficiency_'+str(YEAR)][model_ID]/100},
        
                                    
        ))
    
    #------------------------------------------------------------------------------
    # Biogas BHKW
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas- BHKW_m',
        inputs={b_bio_m: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['existing_factor'][model_ID]})},
                                  
        outputs={b_el_m_in: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['biogas_combined_heat_and_power_plant']['epc']), 
                                        custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load']),
                  b_dist_heat_m: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                          fix=sequences['Base_demand_profile']['base_load'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el_m_in: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat_m: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid (Holz)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL_Holz_m",
        inputs={b_bioWood_m: solph.Flow()},
        outputs={b_oil_fuel_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_holz']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                          custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_holz']['EE_factor'][model_ID]}
                                          )},
        conversion_factors={b_oil_fuel_m: scalars['Parameter_biomass_to_liquid_system_holz']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid (Substrat)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL_substrat_m",
        inputs={b_bio_m: solph.Flow()},
        outputs={b_oil_fuel_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_substrat']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                          custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_substrat']['EE_factor'][model_ID]}
                                          )},
        conversion_factors={b_oil_fuel_m: scalars['Parameter_biomass_to_liquid_system_substrat']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell_m",
        inputs={b_H2_m: solph.Flow()},
        outputs={b_el_m_in: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                                ))},
        conversion_factors={b_el_m_in: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation_m",
        inputs={b_H2_m: solph.Flow()},
        outputs={b_gas_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                                 ))},
        conversion_factors={b_gas_m: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]/100}  
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL_m",
        inputs={b_H2_m: solph.Flow(),
                b_el_m_out: solph.Flow()},
        outputs={b_oil_fuel_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                             ))},
        conversion_factors={b_H2_m: (
            (scalars['Parameter_power_to_liquid_system']['efficiency_H2'][model_ID]/100)/
                                   (scalars['Parameter_power_to_liquid_system']['efficiency_ges'][model_ID]/100)),
                            b_el_m_out: (
                                (scalars['Parameter_power_to_liquid_system']['efficiency_el'][model_ID]/100)/
                                   (scalars['Parameter_power_to_liquid_system']['efficiency_ges'][model_ID]/100))
                            }
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD_m',
        inputs={b_gas_m: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el_m_in: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                              maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential_total'][model_ID]/4)),
                 b_dist_heat_m: solph.Flow()},
        conversion_factors={b_el_m_in: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat_m: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_m',
        inputs={b_bioWood_m: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_m_in: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_power_plant']['EE_factor'][model_ID]}),
                 },
                 
        conversion_factors={b_el_m_in: scalars['Parameter_biomass_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            }
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat_m',
        inputs={b_bioWood_m: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                           #nominal_value = 1
                                           #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat_m: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                    investment=solph.Investment(ep_costs=epc_costs['biomass_heating_plant']['epc']),
                                    custom_attributes={'emission_factor': scalars['Parameter_biomass_heating_plant']['EE_factor'][model_ID]})},
        conversion_factors={b_dist_heat_m: scalars['Parameter_biomass_heating_plant']['efficiency_th_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty  and heatproduction)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_heat_m',
        inputs={b_bioWood_m: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_m_in: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_combined_heat_and_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]}),
                 
                  b_dist_heat_m: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                            #fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value= 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )
                  },
        conversion_factors={b_el_m_in: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            b_dist_heat_m: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_th_' +str(YEAR)][model_ID]/100
                            }
        ))  
    
    #------------------------------------------------------------------------------
    # Solid biomass in the same bus as coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BioTransformer_m",
        inputs={b_bioWood_m: solph.Flow()},
        outputs={b_solidf_m: solph.Flow(custom_attributes={'emission_factor': -1})},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler_m",
        inputs={b_el_m_out: solph.Flow()},
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
        conversion_factors={b_dist_heat_m: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]/100}    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Air
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air_m",
        inputs={b_el_m_out: solph.Flow(),
                b_umgebungsluft_m: solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]}
                    )
                },
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Umgebungswärme']['epc'], 
                                                                 #maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]/4)
                                                                 ))},
        conversion_factors={b_el_m_out: 1/COP_m,
                            b_umgebungsluft_m: (COP_m-1)/COP_m},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water_m",
        inputs={b_el_m_out: solph.Flow(),
                b_uw_m:solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]}
                    )},
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential_total'][model_ID]/4
                                                                  ))},
        conversion_factors={b_el_m_out: 1/scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID],
                            b_uw_m: (scalars['Parameter_heat_pump_ground_Flusswärme'][
                                'efficiency_'+str(YEAR)][model_ID]-1)/scalars[
                                    'Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_recovery_heat_m",
        inputs={b_el_m_out: solph.Flow(),
                b_abwaerme_m: solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]})},
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
                                                                  #maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]/4
                                                                  ))},
        conversion_factors={b_el_m_out: 1/scalars['Parameter_heat_pump_air_Abwärme'][
            'efficiency_'+str(YEAR)][model_ID],
                            b_abwaerme_m: (scalars['Parameter_heat_pump_air_Abwärme'][
                                'efficiency_'+str(YEAR)][model_ID]-1)/scalars[
                                    'Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]}   
        ))
    
    #------------------------------------------------------------------------------
    # Elektrolysis
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electrolysis_m",
        inputs={b_el_m_out: solph.Flow()},
        outputs={b_H2_m: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc'], 
                                                                ))},
        conversion_factors={b_H2_m: scalars['Parameter_electrolysis']['efficiency_'+str(YEAR)][model_ID]/100},
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung- WP
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- WP_m",
        inputs={b_el_m_out: solph.Flow(),
                b_preheat_m: solph.Flow()},
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_el_m_out: 1 -(T_seas_storage/T_VL_m),
                            b_preheat_m: (T_seas_storage/T_VL_m)
                            },
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung - Boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- Electric boiler_m",
        inputs={b_el_m_out: solph.Flow(),
                b_preheat_m: solph.Flow()},
        outputs={b_dist_heat_m: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['electrical_heater']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_el_m_out: 1 -(T_seas_storage/T_VL_m),
                            b_preheat_m: (T_seas_storage/T_VL_m)
                            },
        ))
    
           
      
    """
    Energy storage
    """
    
    
    #------------------------------------------------------------------------------
    # Electricity storage (Großbatterie-speicher)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Battery_m',
        inputs={b_el_m_in: solph.Flow()},
        outputs={b_el_m_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                        maximum=scalars['Parameter_storage_electricity']['potential_total'][model_ID]/4,
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Electricity storage (Li-Ion)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Li-Ion_Battery_m',
        inputs={b_el_m_in: solph.Flow()},
        outputs={b_el_m_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Li-Ion']['initial_storage_level'][model_ID],
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
        label='Natrium_Battery_m',
        inputs={b_el_m_in: solph.Flow()},
        outputs={b_el_m_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Natrium']['initial_storage_level'][model_ID],
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
        label='Red-OX_Battery_m',
        inputs={b_el_m_in: solph.Flow()},
        outputs={b_el_m_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Red-OX']['initial_storage_level'][model_ID],
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
        label='Heat storage_dist_heat_m',
        inputs={b_dist_heat_m: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float((scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()    
                                    )},
        outputs={b_dist_heat_m: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float((scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_district_heating']['loss_rate'][model_ID]/24),
        inflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_heat_district_heating']['initial_storage_level'][model_ID],
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
        label='Heat storage_seasonal_m',
        inputs={b_dist_heat_m: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float((scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_preheat_m: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float((scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_seasonal']['loss_rate'][model_ID]),
        fixed_losses_relative=float(scalars['Parameter_storage_heat_seasonal']['fixed_losses_relative'][model_ID]),
        inflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_heat_seasonal']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_heat_seasonal']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat_seasonal']['epc'], 
                                      
                                      )
                                      
        ))
    
    
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas_storage_m",
        inputs={b_gas_m: solph.Flow()},
        outputs={b_gas_m: solph.Flow()},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                      maximum = scalars['Parameter_storage_gas']['potential_total'][model_ID]/4)  
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
        inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                      maximum = scalars['Parameter_storage_hydrogen']['potential_total'][model_ID]/4)  
        ))
    
    #------------------------------------------------------------------------------
    # Pumped hydro storage (Bestand) HochSpannungnetz verbunden
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label="Pumped_hydro_storage_bestand_m",
        inputs={b_el_m_in: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                                          minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4,
                                          maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4)
            )},
        outputs={b_el_m_in: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                              minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4,
                              maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4)
            )},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['initial_storage_level'][model_ID],
        # invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        # invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Becken)']['epc'],
                                      minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID]/4,
                                      maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID]/4)
        ))
    
    """
    Export block
    """
    #------------------------------------------------------------------------------  
    # Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Electricity_m', 
        inputs={b_el_m_out: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_export_power_middle_'+str(YEAR)],
                                  variable_costs = [i*(-1) for i in strompreiszeitreihe],
                                  custom_attributes={"export_bilanz": -1}
        )}))
 
    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen_m', 
        inputs={b_H2_m: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                 variable_costs = import_price['export_hydrogen_price'],
                                 custom_attributes={"export_bilanz": -1}
                                  
        )}))
    
    """
    Defining final energy demand as Sinks
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total_m', 
        inputs={b_el_m_out: solph.Flow(fix=demand['electricity']['middle'], 
                                 nominal_value=1,
        )}))
    
    
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_Rechenzentren_m', 
        inputs={b_el_m_out: solph.Flow(fix=demand['rechnenzentrum']['middle'],#[80*1e6*0.045/8760] * 8760,
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
    # Oil and fuel demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil & fuel_demand_total_m', 
        inputs={b_oil_fuel_m: solph.Flow(fix=demand['oil']['middle']+demand['fuel']['middle'], 
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
    # Material demand: Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Biomasse_m', 
        inputs={b_solidf_m: solph.Flow(fix=demand['material_usage_biomasse']['middle'], 
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
    Excess energy capture sinks 
    """
    #------------------------------------------------------------------------------
    # Überschuss Senke für Strom
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_el_m', 
        inputs={b_el_m_out: solph.Flow(variable_costs = 200
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_gas_m', 
        inputs={b_gas_m: solph.Flow(variable_costs = 1000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Oel/Kraftstoffe
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_oil_fuel_m', 
        inputs={b_oil_fuel_m: solph.Flow(variable_costs = 1000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_bio_m', 
        inputs={b_bio_m: solph.Flow(variable_costs = 0
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Waerme
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_distheat_m', 
        inputs={b_dist_heat_m: solph.Flow(variable_costs = 0
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Wasserstoff
    #-----------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_H2_m', 
        inputs={b_H2_m: solph.Flow(variable_costs = 1000000
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
    #------------------------------------------------------------------------------
    # Umweltwaerme
    #------------------------------------------------------------------------------
    b_uw_s = solph.buses.Bus(label="Environmental heat_s")
    #------------------------------------------------------------------------------
    # Abwaerme
    #------------------------------------------------------------------------------
    b_abwaerme_s = solph.buses.Bus(label="Recovery heat_s")
    #------------------------------------------------------------------------------
    # Preheat
    #------------------------------------------------------------------------------
    b_preheat_s = solph.buses.Bus(label="Preheater_s")
    #------------------------------------------------------------------------------
    
    b_umgebungsluft_s = solph.buses.Bus(label="Umgebungsluftbus_s")
 
    # Hinzufügen der Busse zum Energiesystem-Modell 
    energysystem.add(b_gas_s, b_oil_fuel_s, b_bio_s, b_bioWood_s, b_dist_heat_s, b_H2_s, b_solidf_s,b_uw_s, b_abwaerme_s, b_preheat_s,b_umgebungsluft_s)
    
   
 
 
    """
    Renewable Energy sources
    """
    #------------------------------------------------------------------------------
    # Wind power plants
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Wind_s', 
        outputs={b_el_s_in: solph.Flow(fix=sequences['feed_in_profile']['Wind_swest'],
                                        custom_attributes={'emission_factor': scalars['Parameter_onshore_wind_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['onshore_wind_power_plant']['epc'], 
                                                                    #minimum = scalars['Parameter_onshore_wind_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_onshore_wind_power_plant']['potential_swest_max_'+str(YEAR)][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_s', 
        outputs={b_el_s_in: solph.Flow(fix=sequences['feed_in_profile']['PV_rooftop_swest'],
                                        custom_attributes={'emission_factor': scalars['Parameter_rooftop_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['rooftop_photovoltaic_power_plant']['epc'], 
                                                                    #minimum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_rooftop_photovoltaic_power_plant']['potential_swest_max'][model_ID])
        )}))
    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_open_s', 
        outputs={b_el_s_in: solph.Flow(fix=sequences['feed_in_profile']['PV_openfield_swest'],
                                        custom_attributes={'emission_factor': scalars['Parameter_field_photovoltaic_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['field_photovoltaic_power_plant']['epc'], 
                                                                    #minimum=scalars['Parameter_field_photovoltaic_power_plant']['potential_north_min'][model_ID],
                                                                    maximum=scalars['Parameter_field_photovoltaic_power_plant']['potential_swest_max'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant_s', 
        outputs={b_el_s_in: solph.Flow(fix=sequences['feed_in_profile']['Hydro_power'],
                                        custom_attributes={'emission_factor': scalars['Parameter_run_river_power_plant']['EE_factor'][model_ID]},
                                        investment=solph.Investment(ep_costs=epc_costs['run_river_power_plant']['epc'], 
                                                                    minimum= scalars['Parameter_run_river_power_plant']['potential_swest_min'][model_ID], 
                                                                    maximum = scalars['Parameter_run_river_power_plant']['potential_swest_min'][model_ID])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST_s', 
        outputs={b_dist_heat_s: solph.Flow(fix=sequences['feed_in_profile']['Solarthermal'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=epc_costs['solar_thermal_power_plant']['epc'], 
                                                                      #maximum=scalars['Parameter_solar_thermal_power_plant']['potential_total'][model_ID]/4)
        ))}))
    
    #------------------------------------------------------------------------------
    # Environmental heat
    #------------------------------------------------------------------------------
      
    energysystem.add(solph.components.Source(
        label='UW_s', 
        outputs={b_uw_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=0, 
                                                                      maximum=scalars['System_configurations_2024']['System']['Potential_Umweltwärme']/4
                                                                    )
        )}))
    #------------------------------------------------------------------------------
    # Umgebungsluft
    #------------------------------------------------------------------------------
    
    energysystem.add(solph.components.Source(
        label='Umgebungsluft_s', 
        outputs={b_umgebungsluft_s: solph.Flow()}))
    
    #------------------------------------------------------------------------------
    # Recovery heat
    #------------------------------------------------------------------------------
    
       
    energysystem.add(solph.components.Source(
        label='AW_s', 
        outputs={b_abwaerme_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                          custom_attributes={'emission_factor': scalars['Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]},
                                          investment=solph.Investment(ep_costs=0, 
                                                                      maximum=scalars['System_configurations_2024']['System']['Potential_Abwärme']/4
                                                                      )
                                          )
                  }))
    
    """ Imports """
    
    energysystem.add(solph.components.Converter(
        label="Netzverluste_s",
        inputs={b_el_s_in: solph.Flow()},
        outputs={b_el_s_out: solph.Flow()},
        conversion_factors={b_el_s_out: 0.95}
        ))
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel_s',
        outputs={b_bio_s: solph.Flow(variable_costs = import_price['import_biomass_price'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood_s',
        outputs={b_bioWood_s: solph.Flow(variable_costs =import_price['import_biomass_price'],
                                         #fix=sequences['Base_demand_profile']['base_load'],
                                         #summed_max= scalars['System_configurations_2024']['System']['Holzpotential_nord'],
                                         investment= solph.Investment(ep_costs = 0),
                                             custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
   # if YEAR == 2020:
    energysystem.add(solph.components.Source(
        label='Import_brown_coal_s',
        outputs={b_solidf_s: solph.Flow(variable_costs = import_price['import_brown_coal_price'],
                                    fix=sequences['Base_demand_profile']['base_load'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=(scalars['System_configurations_2024']['System']['Menge_Braunkohle']/4 )*len(import_price['import_brown_coal_price']),
                                    custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Braunkohle']},
        )}))
        
        #------------------------------------------------------------------------------
        # Import hard coal
        #------------------------------------------------------------------------------
        # energysystem.add(solph.components.Source(
        #     label='Import_hard_coal_s',
        #     outputs={b_solidf_s: solph.Flow(variable_costs = import_price['import_hard_coal_price'],
        #                                 fix=sequences['Base_demand_profile']['base_load'], 
        #                                 #nominal_value = 1,
        #                                 investment = solph.Investment(ep_costs=0),
        #                                 summed_max=(scalars['System_configurations_2024']['System']['Menge_Steinkohle']/4)*len(import_price['import_brown_coal_price']),
        #                                 custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Steinkohle']},
                                        
        #     )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas_s',
        outputs={b_gas_s: solph.Flow(variable_costs = import_price['import_gas_price'],
                                         custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Erdgas'],
                                                            "import_bilanz": -1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil_s',
        outputs={b_oil_fuel_s: solph.Flow(variable_costs = import_price['import_oil_price'],
                                                     custom_attributes={'CO2_factor': scalars['System_configurations_2024']['System']['Emission_Oel'],
                                                                        "import_bilanz": -1}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel_s',
        outputs={b_oil_fuel_s: solph.Flow(variable_costs = import_price['import_synt_fuel_price'],
                                          custom_attributes={"import_bilanz": -1}
            )}))
    
    #------------------------------------------------------------------------------
    # Import Hydrogen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Hydrogen_s',
        outputs={b_H2_s: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                  variable_costs = import_price['import_hydrogen_price'],
                                  custom_attributes={"import_bilanz": -1}
            )}))
    
    """
    Transformers
    """
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing_s",
        inputs={b_bio_s: solph.Flow(#custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_upgrading_plant']['existing_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biogas_upgrading_plant']['epc'],
                                                                 maximum=scalars['Parameter_biogas_upgrading_plant']['potential'][model_ID]/4
                                                                 ),
                                   custom_attributes={'emission_factor': scalars['Parameter_biogas_upgrading_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas_s: scalars['Parameter_biogas_upgrading_plant']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_new_s",
        inputs={b_bio_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'],
                                   investment = solph.Investment(ep_costs=epc_costs['biomethane_injection_plant']['epc']),
                                   custom_attributes={'emission_factor': scalars['Parameter_biomethane_injection_plant']['EE_factor'][model_ID]}
                                   )},
        conversion_factors={b_gas_s: scalars['Parameter_biomethane_injection_plant']['efficiency_'+str(YEAR)][model_ID]/100},
        
                                    
        ))
    
    #------------------------------------------------------------------------------
    # Biogas BHKW
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas- BHKW_s',
        inputs={b_bio_s: solph.Flow(fix=sequences['Base_demand_profile']['base_load'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['existing_factor'][model_ID]})},
                                  
        outputs={b_el_s_in: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['biogas_combined_heat_and_power_plant']['epc']), 
                                        custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                        fix=sequences['Base_demand_profile']['base_load']),
                  b_dist_heat_s: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biogas_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                          fix=sequences['Base_demand_profile']['base_load'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el_s_in: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat_s: scalars['Parameter_biogas_combined_heat_and_power_plant']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid (Holz)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL_Holz_s",
        inputs={b_bioWood_s: solph.Flow()},
        outputs={b_oil_fuel_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_holz']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                          custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_holz']['EE_factor'][model_ID]}
                                          )},
        conversion_factors={b_oil_fuel_s: scalars['Parameter_biomass_to_liquid_system_holz']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomass-to-Liquid (Substrat)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BtL_substrat_s",
        inputs={b_bio_s: solph.Flow()},
        outputs={b_oil_fuel_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['biomass_to_liquid_system_substrat']['epc'], 
                                                                              #maximum=scalars['Parameter_biomass_to_liquid_system']['potential'][model_ID]
                                                                              ),
                                          custom_attributes={'emission_factor': scalars['Parameter_biomass_to_liquid_system_substrat']['EE_factor'][model_ID]}
                                          )},
        conversion_factors={b_oil_fuel_s: scalars['Parameter_biomass_to_liquid_system_substrat']['efficiency_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Fuelcell_s",
        inputs={b_H2_s: solph.Flow()},
        outputs={b_el_s_in: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['fuel_cells']['epc'], 
                                                                ))},
        conversion_factors={b_el_s_in: scalars['Parameter_fuel_cells']['efficiency_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation_s",
        inputs={b_H2_s: solph.Flow()},
        outputs={b_gas_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['methanation']['epc'], 
                                                                 ))},
        conversion_factors={b_gas_s: scalars['Parameter_methanation']['efficiency_'+str(YEAR)][model_ID]/100}  
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL_s",
        inputs={b_H2_s: solph.Flow(),
                b_el_s_out: solph.Flow()},
        outputs={b_oil_fuel_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['power_to_liquid_system']['epc'], 
                                                                             ))},
        conversion_factors={b_H2_s: (
            (scalars['Parameter_power_to_liquid_system']['efficiency_H2'][model_ID]/100)/
                                   (scalars['Parameter_power_to_liquid_system']['efficiency_ges'][model_ID]/100)),
                            b_el_s_out: (
                                (scalars['Parameter_power_to_liquid_system']['efficiency_el'][model_ID]/100)/
                                   (scalars['Parameter_power_to_liquid_system']['efficiency_ges'][model_ID]/100))
                            }
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD_s',
        inputs={b_gas_s: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el_s_in: solph.Flow(investment=solph.Investment(ep_costs=epc_costs['combined_heat_and_power_generating_unit']['epc'],
                                                              maximum =scalars['Parameter_combined_heat_and_power_generating_unit']['potential_total'][model_ID]/4)),
                 b_dist_heat_s: solph.Flow()},
        conversion_factors={b_el_s_in: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_el_'+str(YEAR)][model_ID]/100, 
                            b_dist_heat_s: scalars['Parameter_combined_heat_and_power_generating_unit']['efficiency_th_'+str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_s',
        inputs={b_bioWood_s: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_s_in: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_power_plant']['EE_factor'][model_ID]}),
                 },
                 
        conversion_factors={b_el_s_in: scalars['Parameter_biomass_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            }
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat_s',
        inputs={b_bioWood_s: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                           #nominal_value = 1
                                           #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat_s: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                    investment=solph.Investment(ep_costs=epc_costs['biomass_heating_plant']['epc']),
                                    custom_attributes={'emission_factor': scalars['Parameter_biomass_heating_plant']['EE_factor'][model_ID]})},
        conversion_factors={b_dist_heat_s: scalars['Parameter_biomass_heating_plant']['efficiency_th_' +str(YEAR)][model_ID]/100}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty  and heatproduction)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec_heat_s',
        inputs={b_bioWood_s: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value = 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el_s_in: solph.Flow(#fix=sequences['Base_demand_profile']['base_load'],
                                  investment=solph.Investment(ep_costs=epc_costs['biomass_combined_heat_and_power_plant']['epc']),
                                  custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]}),
                 
                  b_dist_heat_s: solph.Flow(custom_attributes={'emission_factor': scalars['Parameter_biomass_combined_heat_and_power_plant']['EE_factor'][model_ID]},
                                            #fix=sequences['Base_demand_profile']['base_load'],
                                            #nominal_value= 1
                                            #investment = solph.Investment(ep_costs=0)
                                            )
                  },
        conversion_factors={b_el_s_in: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_el_' +str(YEAR)][model_ID]/100,
                            b_dist_heat_s: scalars['Parameter_biomass_combined_heat_and_power_plant']['efficiency_th_' +str(YEAR)][model_ID]/100
                            }
        ))  
    
    #------------------------------------------------------------------------------
    # Solid biomass in the same bus as coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BioTransformer_s",
        inputs={b_bioWood_s: solph.Flow()},
        outputs={b_solidf_s: solph.Flow(custom_attributes={'emission_factor': -1})},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler_s",
        inputs={b_el_s_out: solph.Flow()},
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrical_heater']['epc']))},
        conversion_factors={b_dist_heat_s: scalars['Parameter_electrical_heater']['efficiency_' +str(YEAR)][model_ID]/100}    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Air
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air_s",
        inputs={b_el_s_out: solph.Flow(),
                b_umgebungsluft_s: solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]}
                    )
                },
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Umgebungswärme']['epc'], 
                                                                 #maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]/4)
                                                                 ))},
        conversion_factors={b_el_s_out: 1/COP_s,
                            b_umgebungsluft_s: (COP_s-1)/COP_s},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water_s",
        inputs={b_el_s_out: solph.Flow(),
                b_uw_s:solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]}
                    )},
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_heat_pump_ground_Flusswärme']['potential_total'][model_ID]/4
                                                                  ))},
        conversion_factors={b_el_s_out: 1/scalars['Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID],
                            b_uw_s: (scalars['Parameter_heat_pump_ground_Flusswärme'][
                                'efficiency_'+str(YEAR)][model_ID]-1)/scalars[
                                    'Parameter_heat_pump_ground_Flusswärme']['efficiency_'+str(YEAR)][model_ID]},
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_recovery_heat_s",
        inputs={b_el_s_out: solph.Flow(),
                b_abwaerme_s: solph.Flow(custom_attributes={'emission_factor': scalars[
                    'Parameter_solar_thermal_power_plant']['EE_factor'][model_ID]})},
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['heat_pump_air_Abwärme']['epc'], 
                                                                  #maximum = scalars['Parameter_heat_pump_air_Abwärme']['potential_total'][model_ID]/4
                                                                  ))},
        conversion_factors={b_el_s_out: 1/scalars['Parameter_heat_pump_air_Abwärme'][
            'efficiency_'+str(YEAR)][model_ID],
                            b_abwaerme_s: (scalars['Parameter_heat_pump_air_Abwärme'][
                                'efficiency_'+str(YEAR)][model_ID]-1)/scalars[
                                    'Parameter_heat_pump_air_Abwärme']['efficiency_'+str(YEAR)][model_ID]}   
        ))
    
    #------------------------------------------------------------------------------
    # Elektrolysis
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electrolysis_s",
        inputs={b_el_s_out: solph.Flow()},
        outputs={b_H2_s: solph.Flow(investment = solph.Investment(ep_costs=epc_costs['electrolysis']['epc'], 
                                                                ))},
        conversion_factors={b_H2_s: scalars['Parameter_electrolysis']['efficiency_'+str(YEAR)][model_ID]/100},
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung- WP
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- WP_s",
        inputs={b_el_s_out: solph.Flow(),
                b_preheat_s: solph.Flow()},
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['heat_pump_ground_Flusswärme']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_el_s_out: 1 -(T_seas_storage/T_VL_s),
                            b_preheat_s: (T_seas_storage/T_VL_s)
                            },
        ))
    
    #------------------------------------------------------------------------------
    # Nachheizung - Boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Preheater- Electric boiler_s",
        inputs={b_el_s_out: solph.Flow(),
                b_preheat_s: solph.Flow()},
        outputs={b_dist_heat_s: solph.Flow(investment = solph.Investment(ep_costs= epc_costs['electrical_heater']['epc'], 
                                                                  #maximum=scalars['Parameter_electrolysis']['potential'][model_ID]
                                                                  ))},
        conversion_factors={b_el_s_out: 1 -(T_seas_storage/T_VL_s),
                            b_preheat_s: (T_seas_storage/T_VL_s)
                            },
        ))
    
           
      
    """
    Energy storage
    """
    
    
    #------------------------------------------------------------------------------
    # Electricity storage (Großbatterie-speicher)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Battery_s',
        inputs={b_el_s_in: solph.Flow()},
        outputs={b_el_s_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_electricity']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity']['epc'], 
                                        maximum=scalars['Parameter_storage_electricity']['potential_total'][model_ID]/4,
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Electricity storage (Li-Ion)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Li-Ion_Battery_s',
        inputs={b_el_s_in: solph.Flow()},
        outputs={b_el_s_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Li-Ion']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Li-Ion']['initial_storage_level'][model_ID],
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
        label='Natrium_Battery_s',
        inputs={b_el_s_in: solph.Flow()},
        outputs={b_el_s_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Natrium']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Natrium']['initial_storage_level'][model_ID],
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
        label='Red-OX_Battery_s',
        inputs={b_el_s_in: solph.Flow()},
        outputs={b_el_s_in: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_electricity_Red-OX']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_electricity_Red-OX']['initial_storage_level'][model_ID],
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
        label='Heat storage_dist_heat_s',
        inputs={b_dist_heat_s: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float((scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()    
                                    )},
        outputs={b_dist_heat_s: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float((scalars['Parameter_storage_heat_district_heating']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_district_heating']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_district_heating']['loss_rate'][model_ID]/24),
        inflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_district_heating']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_heat_district_heating']['initial_storage_level'][model_ID],
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
        label='Heat storage_seasonal_s',
        inputs={b_dist_heat_s: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float((scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_preheat_s: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float((scalars['Parameter_storage_heat_seasonal']['potential_total'][model_ID]/4)/scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(scalars['Parameter_storage_heat_seasonal']['loss_rate'][model_ID]),
        fixed_losses_relative=float(scalars['Parameter_storage_heat_seasonal']['fixed_losses_relative'][model_ID]),
        inflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor=scalars['Parameter_storage_heat_seasonal']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_heat_seasonal']['initial_storage_level'][model_ID],
        balanced=bool(scalars['Parameter_storage_heat_seasonal']['balanced'][model_ID]),
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_heat_seasonal']['inverse_c_rate'][model_ID]),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_costs['storage_heat_seasonal']['epc'], 
                                      
                                      )
                                      
        ))
    
    
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas_storage_s",
        inputs={b_gas_s: solph.Flow()},
        outputs={b_gas_s: solph.Flow()},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_gas']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_gas']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_gas']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_gas']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_gas']['epc'], 
                                      maximum = scalars['Parameter_storage_gas']['potential_total'][model_ID]/4)  
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
        inflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_hydrogen']['efficiency_out_'+str(YEAR)][model_ID]/100,
        #initial_storage_level=scalars['Parameter_storage_hydrogen']['initial_storage_level'][model_ID],
        invest_relation_input_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        invest_relation_output_capacity = 1/(scalars['Parameter_storage_hydrogen']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_hydrogen']['epc'], 
                                      maximum = scalars['Parameter_storage_hydrogen']['potential_total'][model_ID]/4)  
        ))
    
    #------------------------------------------------------------------------------
    # Pumped hydro storage (Bestand) HochSpannungnetz verbunden
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label="Pumped_hydro_storage_bestand_s",
        inputs={b_el_s_in: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                                          minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4,
                                          maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4)
            )},
        outputs={b_el_s_in: solph.Flow(
            investment = solph.Investment(ep_costs= epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Technology)']['epc'],
                              minimum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4,
                              maximum= scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['potential_bestand'][model_ID]/4)
            )},
        loss_rate=0,
        balanced=bool(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['balanced'][model_ID]),
        inflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_in_'+str(YEAR)][model_ID]/100,
        outflow_conversion_factor = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['efficiency_out_'+str(YEAR)][model_ID]/100,
        # initial_storage_level=scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['initial_storage_level'][model_ID],
        # invest_relation_input_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        # invest_relation_output_capacity = 1/(scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['inverse_c_rate'][model_ID]),
        investment = solph.Investment(ep_costs=epc_costs['storage_electricity_pumped_hydro_storage_power_technology(Becken)']['epc'],
                                      minimum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID]/4,
                                      maximum = scalars['Parameter_storage_electricity_pumped_hydro_storage_power_technology(Becken)']['capacity_bestand'][model_ID]/4)
        ))
    
    """
    Export block
    """
    #------------------------------------------------------------------------------  
    # Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Electricity_s', 
        inputs={b_el_s_out: solph.Flow(nominal_value= scalars['Electricity_grid']['electricity']['max_export_power_swest_'+str(YEAR)],
                                  variable_costs = [i*(-1) for i in strompreiszeitreihe],
                                  custom_attributes={"export_bilanz": -1}
        )}))
 
    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen_s', 
        inputs={b_H2_s: solph.Flow(nominal_value = scalars['Hydrogen_grid']['hydrogen']['max_power'],
                                 variable_costs = import_price['export_hydrogen_price'],
                                 custom_attributes={"export_bilanz": -1}
                                  
        )}))
    
    """
    Defining final energy demand as Sinks
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total_s', 
        inputs={b_el_s_out: solph.Flow(fix=demand['electricity']['swest'], 
                                 nominal_value=1,
        )}))
    
    
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_Rechenzentren_s', 
        inputs={b_el_s_out: solph.Flow(fix=demand['rechnenzentrum']['swest'],#[80*1e6*0.045/8760] * 8760,
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
    # Oil and fuel demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil & fuel_demand_total_s', 
        inputs={b_oil_fuel_s: solph.Flow(fix=demand['oil']['swest']+demand['fuel']['swest'], 
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
    # Material demand: Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Biomasse_s', 
        inputs={b_solidf_s: solph.Flow(fix=demand['material_usage_biomasse']['swest'], 
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
    Excess energy capture sinks 
    """
    #------------------------------------------------------------------------------
    # Überschuss Senke für Strom
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_el_s', 
        inputs={b_el_s_out: solph.Flow(variable_costs = 200
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_gas_s', 
        inputs={b_gas_s: solph.Flow(variable_costs = 1000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Oel/Kraftstoffe
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_oil_fuel_s', 
        inputs={b_oil_fuel_s: solph.Flow(variable_costs = 1000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_bio_s', 
        inputs={b_bio_s: solph.Flow(variable_costs = 0
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Waerme
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_distheat_s', 
        inputs={b_dist_heat_s: solph.Flow(variable_costs = 0
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Wasserstoff
    #-----------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_H2_s', 
        inputs={b_H2_s: solph.Flow(variable_costs = 1000000
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
    
    return energysystem, sim_data