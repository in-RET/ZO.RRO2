# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 14:13:49 2024

@author: rbala
CAUTION: 
    
    The script is written in a way to automize the generation of csv files after simulation.
    Please consult the author before altering the script.


!!!!!!!!!!!!!!!!!!!!!!!!!!!
this script consists:
    - the function to export CSV files in a specific format to have a overview of the results.
    
"""

from oemof import solph
import pandas as pd
import os
workdir= os.getcwd()
from src.preprocessing.files import read_input_files
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches

def export_csv_region(results, YEAR, permutation, model_name, scenario_num):
    CSV_PATH = os.path.abspath(os.path.join(os.getcwd(), "results", permutation))
    os.makedirs(CSV_PATH, exist_ok=True)
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
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
        
        Emissionen_Gasimport=(b_gas['sequences'][('Import_Gas_'+ r, 'Gas_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Erdgas']/1000)
        Emissionen_Oelimport=(b_oil['sequences'][('Import_Oil_'+r, 'Oil_fuel_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Oel']/1000)
        Emissionen_Steinkohleimport=(b_solidf['sequences'][('Import_hard_coal_'+r, 'Solidfuel_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Steinkohle']/1000)
        Emissionen_Braunkohleimport=(b_solidf['sequences'][('Import_brown_coal_'+r, 'Solidfuel_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Braunkohle']/1000)
        
#------------------------------------------------------------------------------
# Allgemeine Simulationsergebnisse zum Abgleich
#------------------------------------------------------------------------------
        NaN=str('------------------------------------------------------------------') 
        if r == 'n':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->North', 'Electricity_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->North','Electricity_'+r),'flow'].sum()
        elif r == 'm':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->Middle', 'Electricity_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->Middle','Electricity_'+r),'flow'].sum()
        elif r == 'e':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->East', 'Electricity_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->East','Electricity_'+r),'flow'].sum()
        elif r == 's':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->Swest', 'Electricity_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->Swest','Electricity_'+r),'flow'].sum()
            
        Summe_Emissionen = Emissionen_Gasimport+Emissionen_Oelimport+Emissionen_Stromimport+Emissionen_Steinkohleimport+Emissionen_Braunkohleimport
        Ergebnisse = pd.Series([NaN,
                        b_el['scalars'][('PVooftop_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('PV_open_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Wind_'+ r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Hydro power plant_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Biogas_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Biomasse_elec_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Fuelcell_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('GuD_'+r,'Electricity_'+r),'invest'],
                        b_dist_heat['scalars'][('ST_'+ r,'District heating_'+r),'invest'] ,
                        b_dist_heat['scalars'][('Biomasse_heat_'+r,'District heating_'+r),'invest'],
                        b_dist_heat['scalars'][('Heatpump_water_'+r,'District heating_'+r),'invest'] ,
                        b_dist_heat['scalars'][('Heatpump_air_'+r,'District heating_'+r),'invest'],
                        b_dist_heat['scalars'][('Electric boiler_'+r,'District heating_'+r),'invest'],
                        b_H2['scalars'][('Electrolysis_'+r,'Hydrogen_'+r),'invest'],
                        b_gas['scalars'][('Hydrogen_feedin_'+r,'Gas_'+r),'invest'],
                        b_gas['scalars'][('Biogas_feedin_existing_'+r,'Gas_'+r),'invest'],
                        b_gas['scalars'][('Biogas_feedin_new_'+r,'Gas_'+r),'invest'],
                        b_gas['scalars'][('Methanisation_'+r,'Gas_'+r),'invest'],
                        b_oil['scalars'][('PtL_'+r,'Oil_fuel_'+r),'invest'],
                        NaN,
                        Battery['scalars'][('Battery_'+r,'None'),'invest'] ,
                        Heat_storage['scalars'][('Heat storage_'+r,'None'),'invest'],
                        Pumped_hydro_storage['scalars'][('Pumped_hydro_storage_'+r,'None'),'invest'] ,
                        Gas_storage['scalars'][('Gas_storage_'+r,'None'),'invest'],
                        H2_storage['scalars'][('H2_storage_'+r,'None'),'invest'],
                        NaN,
                        Emissionen_Gasimport,
                        Emissionen_Oelimport,
                        Emissionen_Stromimport,
                        Emissionen_Steinkohleimport,
                        Emissionen_Braunkohleimport,
                        Summe_Emissionen,
                        NaN,
                        import_el,
                        b_el['sequences'][('Electricity_'+r,'Export_Electricity_'+r),'flow'].sum()
                        ],
                index = ['Leistungen',
                       'PV_Dach',
                       'PV_Feld',
                       'Wind',
                       'Wasser',
                       'Biogas_el',
                       'Biomasse_Strom',
                       'Brennstoffzelle',
                       'GuD',
                       'Solarthermie',
                       'Biomasse_Waerme',
                       'WP_Fluss',
                       'WP_Abwaerme',
                       'Heizstab',
                       'Elektrolyse',
                       'Wasserstoffeinspeisung',
                       'B2G_Best.',
                       'B2G_Neu',
                       'Methanisierung',
                       'PtL',
                       'Speicherkapazitäten',
                       'Natriumspeicher',
                       'Waermespeicher',
                       'Pumpspeicher',
                       'Erdgasspeicher',
                       'Wasserstoffspeicher',
                       'Emissionen',
                       'Gasemissionen',
                       'Oelemissionen',
                       'Stromemissionen',
                       'Steinkohleemissionen',
                       'Braunkohleemissionen',
                       'Summe aller Emissionen',
                       'Energiemengen',
                       'Stromimport',
                       'Stromexport'
                       ])
        
        if r == 'n':
            Region_csv['north'] = Ergebnisse
        elif r =='m':
            Region_csv['middle'] = Ergebnisse
        elif r =='e':
            Region_csv['east'] = Ergebnisse
        elif r =='s':
            Region_csv['swest'] = Ergebnisse
            
            
    Region_csv['summe'] = Region_csv['north']+Region_csv['middle'] +Region_csv['east'] +Region_csv['swest']     
    Region_csv.applymap(lambda x: str(x).replace('.', ',')).to_csv(CSV_PATH + '/'+ model_name +"_"+ permutation + "_" + scenario_num + ".csv", sep = ';')
    return Region_csv

def export_csv(results, YEAR, permutation, model_name, scenario_num, sim_data):
    CSV_PATH = os.path.abspath(os.path.join(os.getcwd(), "results", permutation))
    os.makedirs(CSV_PATH, exist_ok=True)
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    csv = pd.DataFrame()

    b_el = solph.views.node(results, 'Electricity')
    b_gas = solph.views.node(results, 'Gas')
    b_oil = solph.views.node(results, 'Oil_fuel')
    b_bio = solph.views.node(results, 'Biomass')
    b_bioWood = solph.views.node(results, 'BioWood')
    b_solidf = solph.views.node(results, 'Solidfuel')
    b_dist_heat = solph.views.node(results, 'District heating')
    b_H2 = solph.views.node(results, 'Hydrogen')
    #Syntbus = solph.views.node(results, 'Synthetische_Kraftstoffe')
    Battery = solph.views.node(results, 'Battery')
    Heat_storage = solph.views.node(results, 'Heat storage')
    Pumped_hydro_storage = solph.views.node(results, 'Pumped_hydro_storage')
    Gas_storage = solph.views.node(results, 'Gas_storage')
    H2_storage = solph.views.node(results, 'H2_storage')
    
    Emissionen_Gasimport=(b_gas['sequences'][('Import_Gas', 'Gas'), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Erdgas']/1000)
    Emissionen_Oelimport=(b_oil['sequences'][('Import_Oil', 'Oil_fuel'), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Oel']/1000)
    Emissionen_Steinkohleimport=(b_solidf['sequences'][('Import_hard_coal', 'Solidfuel'), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Steinkohle']/1000)
    Emissionen_Braunkohleimport=(b_solidf['sequences'][('Import_brown_coal', 'Solidfuel'), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Braunkohle']/1000)
    Emissionen_Stromimport=(b_el['sequences'][('Import_Electricity', 'Electricity'), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
    
    
    Investment_cost = (
                        ((b_el['scalars'][('PV_rooftop_north','Electricity'),'invest']+
                        b_el['scalars'][('PV_rooftop_middle','Electricity'),'invest']+
                        b_el['scalars'][('PV_rooftop_east','Electricity'),'invest']+
                        b_el['scalars'][('PV_rooftop_swest','Electricity'),'invest'])* sim_data['epc_costs']['rooftop_photovoltaic_power_plant']['investk'])+
                        ((b_el['scalars'][('PV_open_north','Electricity'),'invest']+
                         b_el['scalars'][('PV_open_middle','Electricity'),'invest']+
                         b_el['scalars'][('PV_open_east','Electricity'),'invest']+
                         b_el['scalars'][('PV_open_swest','Electricity'),'invest'])*sim_data['epc_costs']['field_photovoltaic_power_plant']['investk'])+
                        ((b_el['scalars'][('Wind_north','Electricity'),'invest']+
                         b_el['scalars'][('Wind_middle','Electricity'),'invest']+
                         b_el['scalars'][('Wind_east','Electricity'),'invest']+
                         b_el['scalars'][('Wind_swest','Electricity'),'invest'])*sim_data['epc_costs']['onshore_wind_power_plant']['investk'])+
                        b_el['scalars'][('Hydro power plant','Electricity'),'invest']*sim_data['epc_costs']['run_river_power_plant']['investk']+
                        b_el['scalars'][('Biogas','Electricity'),'invest']*sim_data['epc_costs']['biogas_combined_heat_and_power_plant']['investk']+
                        b_el['scalars'][('Biomasse_elec','Electricity'),'invest']*sim_data['epc_costs']['biomass_combined_heat_and_power_plant']['investk']+
                        b_el['scalars'][('Fuelcell','Electricity'),'invest']*sim_data['epc_costs']['fuel_cells']['investk']+
                        b_el['scalars'][('GuD','Electricity'),'invest']*sim_data['epc_costs']['combined_heat_and_power_generating_unit']['investk']+
                        b_dist_heat['scalars'][('ST','District heating'),'invest'] *sim_data['epc_costs']['solar_thermal_power_plant']['investk']+
                        b_dist_heat['scalars'][('Biomasse_heat','District heating'),'invest']*sim_data['epc_costs']['biomass_heating_plant']['investk']+
                        b_dist_heat['scalars'][('Heatpump_water','District heating'),'invest'] *sim_data['epc_costs']['heat_pump_ground_Flusswärme']['investk']+
                        b_dist_heat['scalars'][('Heatpump_air','District heating'),'invest']*sim_data['epc_costs']['heat_pump_air_Abwärme']['investk']+
                        b_dist_heat['scalars'][('Electric boiler','District heating'),'invest']*sim_data['epc_costs']['electrical_heater']['investk']+
                        b_H2['scalars'][('Electrolysis','Hydrogen'),'invest']*sim_data['epc_costs']['electrolysis']['investk']+
                        b_gas['scalars'][('Hydrogen_feedin','Gas'),'invest']*sim_data['epc_costs']['hydrogen_feed_in']['investk']+
                        b_gas['scalars'][('Biogas_feedin_existing','Gas'),'invest']*sim_data['epc_costs']['biogas_upgrading_plant']['investk']+
                        b_gas['scalars'][('Biogas_feedin_new','Gas'),'invest']*sim_data['epc_costs']['biomethane_injection_plant']['investk']+
                        b_gas['scalars'][('Methanisation','Gas'),'invest']*sim_data['epc_costs']['methanation']['investk']+
                        b_oil['scalars'][('PtL','Oil_fuel'),'invest']*sim_data['epc_costs']['power_to_liquid_system']['investk']+
                        Battery['scalars'][('Battery','None'),'invest']*sim_data['epc_costs']['storage_electricity']['investk']+
                        Heat_storage['scalars'][('Heat storage','None'),'invest']*sim_data['epc_costs']['storage_heat']['investk']+
                        Pumped_hydro_storage['scalars'][('Pumped_hydro_storage','None'),'invest']*sim_data['epc_costs']['storage_electricity_pumped_hydro_storage_power_technology']['investk']+
                        Gas_storage['scalars'][('Gas_storage','None'),'invest']*sim_data['epc_costs']['storage_gas']['investk']+
                        H2_storage['scalars'][('H2_storage','None'),'invest']*sim_data['epc_costs']['storage_hydrogen']['investk']
                        )
    
    Operating_cost = (
                        ((b_el['scalars'][('PV_rooftop_north','Electricity'),'invest']+
                        b_el['scalars'][('PV_rooftop_middle','Electricity'),'invest']+
                        b_el['scalars'][('PV_rooftop_east','Electricity'),'invest']+
                        b_el['scalars'][('PV_rooftop_swest','Electricity'),'invest'])* sim_data['epc_costs']['rooftop_photovoltaic_power_plant']['betriebsk'])+
                        ((b_el['scalars'][('PV_open_north','Electricity'),'invest']+
                         b_el['scalars'][('PV_open_middle','Electricity'),'invest']+
                         b_el['scalars'][('PV_open_east','Electricity'),'invest']+
                         b_el['scalars'][('PV_open_swest','Electricity'),'invest'])*sim_data['epc_costs']['field_photovoltaic_power_plant']['betriebsk'])+
                        ((b_el['scalars'][('Wind_north','Electricity'),'invest']+
                         b_el['scalars'][('Wind_middle','Electricity'),'invest']+
                         b_el['scalars'][('Wind_east','Electricity'),'invest']+
                         b_el['scalars'][('Wind_swest','Electricity'),'invest'])*sim_data['epc_costs']['onshore_wind_power_plant']['betriebsk'])+
                        b_el['scalars'][('Hydro power plant','Electricity'),'invest']*sim_data['epc_costs']['run_river_power_plant']['betriebsk']+
                        b_el['scalars'][('Biogas','Electricity'),'invest']*sim_data['epc_costs']['biogas_combined_heat_and_power_plant']['betriebsk']+
                        b_el['scalars'][('Biomasse_elec','Electricity'),'invest']*sim_data['epc_costs']['biomass_combined_heat_and_power_plant']['betriebsk']+
                        b_el['scalars'][('Fuelcell','Electricity'),'invest']*sim_data['epc_costs']['fuel_cells']['betriebsk']+
                        b_el['scalars'][('GuD','Electricity'),'invest']*sim_data['epc_costs']['combined_heat_and_power_generating_unit']['betriebsk']+
                        b_dist_heat['scalars'][('ST','District heating'),'invest'] *sim_data['epc_costs']['solar_thermal_power_plant']['betriebsk']+
                        b_dist_heat['scalars'][('Biomasse_heat','District heating'),'invest']*sim_data['epc_costs']['biomass_heating_plant']['betriebsk']+
                        b_dist_heat['scalars'][('Heatpump_water','District heating'),'invest'] *sim_data['epc_costs']['heat_pump_ground_Flusswärme']['betriebsk']+
                        b_dist_heat['scalars'][('Heatpump_air','District heating'),'invest']*sim_data['epc_costs']['heat_pump_air_Abwärme']['betriebsk']+
                        b_dist_heat['scalars'][('Electric boiler','District heating'),'invest']*sim_data['epc_costs']['electrical_heater']['betriebsk']+
                        b_H2['scalars'][('Electrolysis','Hydrogen'),'invest']*sim_data['epc_costs']['electrolysis']['betriebsk']+
                        b_gas['scalars'][('Hydrogen_feedin','Gas'),'invest']*sim_data['epc_costs']['hydrogen_feed_in']['betriebsk']+
                        b_gas['scalars'][('Biogas_feedin_existing','Gas'),'invest']*sim_data['epc_costs']['biogas_upgrading_plant']['betriebsk']+
                        b_gas['scalars'][('Biogas_feedin_new','Gas'),'invest']*sim_data['epc_costs']['biomethane_injection_plant']['betriebsk']+
                        b_gas['scalars'][('Methanisation','Gas'),'invest']*sim_data['epc_costs']['methanation']['betriebsk']+
                        b_oil['scalars'][('PtL','Oil_fuel'),'invest']*sim_data['epc_costs']['power_to_liquid_system']['betriebsk']+
                        Battery['scalars'][('Battery','None'),'invest']*sim_data['epc_costs']['storage_electricity']['betriebsk']+
                        Heat_storage['scalars'][('Heat storage','None'),'invest']*sim_data['epc_costs']['storage_heat']['betriebsk']+
                        Pumped_hydro_storage['scalars'][('Pumped_hydro_storage','None'),'invest']*sim_data['epc_costs']['storage_electricity_pumped_hydro_storage_power_technology']['betriebsk']+
                        Gas_storage['scalars'][('Gas_storage','None'),'invest']*sim_data['epc_costs']['storage_gas']['betriebsk']+
                        H2_storage['scalars'][('H2_storage','None'),'invest']*sim_data['epc_costs']['storage_hydrogen']['betriebsk']
                        )
    
    #import costs
    
    Import_el_cost = 0
    Export_el_cost = 0
    Import_gas_cost = 0 
    Import_oil_cost = 0  
    Export_H2_cost = 0  
    Import_bio_cost = 0 
    Import_biowood_cost=0
    Import_hardcoal_cost=0
    Import_browncoal_cost=0
    Import_Synt_cost =0

    for i in range(0, len(b_el['sequences'][('Import_Electricity','Electricity'),'flow'])-1):
        Import_el_cost += (b_el['sequences'][('Import_Electricity','Electricity'),'flow'][i]) * sim_data['Import_prices']['import_electricity_price'][i]
        Export_el_cost += (b_el['sequences'][('Electricity','Export_Electricity'),'flow'][i]) * (-1) *sim_data['Import_prices']['export_electricity_price'][i]
        
        Import_gas_cost += (b_gas['sequences'][('Import_Gas','Gas'),'flow'][i]) * sim_data['Import_prices']['import_gas_price'][i]
        
        Import_oil_cost += (b_oil['sequences'][('Import_Oil','Oil_fuel'),'flow'][i]) * sim_data['Import_prices']['import_oil_price'][i]
        
        Export_H2_cost += (b_H2['sequences'][('Hydrogen','Export_Hydrogen'),'flow'][i]) * sim_data['Timeseries']['Energy_price']['Hydrogen_' + str(YEAR)][i]
        
        Import_bio_cost += (b_bio['sequences'][('Import_solid_fuel','Biomass'),'flow'][i]) * sim_data['Import_prices']['import_biomass_price'][i]
         
        Import_biowood_cost += (b_bioWood['sequences'][('Import_Wood','BioWood'),'flow'][i]) * sim_data['Import_prices']['import_biomass_price'][i]
            
        Import_hardcoal_cost += (b_solidf['sequences'][('Import_hard_coal','Solidfuel'),'flow'][i]) * sim_data['Import_prices']['import_hard_coal_price'][i]
        Import_browncoal_cost += (b_solidf['sequences'][('Import_brown_coal','Solidfuel'),'flow'][i]) * sim_data['Import_prices']['import_brown_coal_price'][i]

        Import_Synt_cost += (b_oil['sequences'][('Import_Synthetic_fuel','Oil_fuel'),'flow'][i]) * sim_data['Import_prices']['import_synt_fuel_price'][i]
        
    Import_cost_total = Import_el_cost + Import_gas_cost + Import_oil_cost + Import_bio_cost + Import_biowood_cost + Import_hardcoal_cost + Import_browncoal_cost + Import_Synt_cost
    Export_total = Export_el_cost + Export_H2_cost
    profit = Export_total - Import_cost_total
    Grid_fee = max(b_el['sequences'][('Import_Electricity','Electricity'),'flow']) * sim_data['Parameter']['Electricity_grid']['electricity']['grid_annualperformance_fee']
    Costs_total = Investment_cost + Operating_cost - profit +Grid_fee
    #------------------------------------------------------------------------------
    # Allgemeine Simulationsergebnisse zum Abgleich
    #------------------------------------------------------------------------------
    NaN=str('------------------------------------------------------------------') 
            
    Summe_Emissionen = Emissionen_Gasimport+Emissionen_Oelimport+Emissionen_Stromimport+Emissionen_Steinkohleimport+Emissionen_Braunkohleimport
    import_el = b_el['sequences'][('Import_Electricity','Electricity'),'flow'].sum()
    Ergebnisse = pd.Series([NaN,
                    (b_el['scalars'][('PV_rooftop_north','Electricity'),'invest']+
                    b_el['scalars'][('PV_rooftop_middle','Electricity'),'invest']+
                    b_el['scalars'][('PV_rooftop_east','Electricity'),'invest']+
                    b_el['scalars'][('PV_rooftop_swest','Electricity'),'invest']),
                    (b_el['scalars'][('PV_open_north','Electricity'),'invest']+
                     b_el['scalars'][('PV_open_middle','Electricity'),'invest']+
                     b_el['scalars'][('PV_open_east','Electricity'),'invest']+
                     b_el['scalars'][('PV_open_swest','Electricity'),'invest']),
                    (b_el['scalars'][('Wind_north','Electricity'),'invest']+
                     b_el['scalars'][('Wind_middle','Electricity'),'invest']+
                     b_el['scalars'][('Wind_east','Electricity'),'invest']+
                     b_el['scalars'][('Wind_swest','Electricity'),'invest']),
                    b_el['scalars'][('Hydro power plant','Electricity'),'invest'],
                    b_el['scalars'][('Biogas','Electricity'),'invest'],
                    b_el['scalars'][('Biomasse_elec','Electricity'),'invest'],
                    b_el['scalars'][('Fuelcell','Electricity'),'invest'],
                    b_el['scalars'][('GuD','Electricity'),'invest'],
                    b_dist_heat['scalars'][('ST','District heating'),'invest'] ,
                    b_dist_heat['scalars'][('Biomasse_heat','District heating'),'invest'],
                    b_dist_heat['scalars'][('Heatpump_water','District heating'),'invest'] ,
                    b_dist_heat['scalars'][('Heatpump_air','District heating'),'invest'],
                    b_dist_heat['scalars'][('Electric boiler','District heating'),'invest'],
                    b_H2['scalars'][('Electrolysis','Hydrogen'),'invest'],
                    b_gas['scalars'][('Hydrogen_feedin','Gas'),'invest'],
                    b_gas['scalars'][('Biogas_feedin_existing','Gas'),'invest'],
                    b_gas['scalars'][('Biogas_feedin_new','Gas'),'invest'],
                    b_gas['scalars'][('Methanisation','Gas'),'invest'],
                    b_oil['scalars'][('PtL','Oil_fuel'),'invest'],
                    NaN,
                    Battery['scalars'][('Battery','None'),'invest'] ,
                    Heat_storage['scalars'][('Heat storage','None'),'invest'],
                    Pumped_hydro_storage['scalars'][('Pumped_hydro_storage','None'),'invest'] ,
                    Gas_storage['scalars'][('Gas_storage','None'),'invest'],
                    H2_storage['scalars'][('H2_storage','None'),'invest'],
                    NaN,
                    Emissionen_Gasimport,
                    Emissionen_Oelimport,
                    Emissionen_Stromimport,
                    Emissionen_Steinkohleimport,
                    Emissionen_Braunkohleimport,
                    Summe_Emissionen,
                    NaN,
                    Investment_cost/1000000,
                    Operating_cost/1000000,
                    profit*(-1)/1000000,
                    Grid_fee/1000000,
                    Costs_total/1000000,
                    NaN,
                    import_el,
                    b_el['sequences'][('Electricity','Export_Electricity'),'flow'].sum(),
                    ],
            index = ['Leistungen',
                   'PV_Dach',
                   'PV_Feld',
                   'Wind',
                   'Wasser',
                   'Biogas_el',
                   'Biomasse_Strom',
                   'Brennstoffzelle',
                   'GuD',
                   'Solarthermie',
                   'Biomasse_Waerme',
                   'WP_Fluss',
                   'WP_Abwaerme',
                   'Heizstab',
                   'Elektrolyse',
                   'Wasserstoffeinspeisung',
                   'B2G_Best.',
                   'B2G_Neu',
                   'Methanisierung',
                   'PtL',
                   'Speicherkapazitäten',
                   'Natriumspeicher',
                   'Waermespeicher',
                   'Pumpspeicher',
                   'Erdgasspeicher',
                   'Wasserstoffspeicher',
                   'Emissionen',
                   'Gasemissionen',
                   'Oelemissionen',
                   'Stromemissionen',
                   'Steinkohleemissionen',
                   'Braunkohleemissionen',
                   'Summe aller Emissionen',
                   'Kosten [Mio. €]',
                   'Annuität',
                   'OPEX',
                   'Im-Export',
                   'Netz',
                   'Gesamtkosten',
                   'Energiemengen',
                   'Stromimport',
                   'Stromexport'
                   ])
    
    csv['Leistung'] = Ergebnisse
     
    csv.applymap(lambda x: str(x).replace('.', ',')).to_csv(CSV_PATH + '/'+ model_name +"_"+ permutation +"_" + scenario_num + ".csv", sep = ';')
    return csv

def grid_energy_map(results, permutation, model_name, scenario_num):
    
    b_el_n = solph.views.node(results, 'Electricity_n')
    b_el_s = solph.views.node(results, 'Electricity_s')
    b_el_e = solph.views.node(results, 'Electricity_e')
    b_el_m = solph.views.node(results, 'Electricity_m')

    # Energiemengen in GWh
    em_hs_n = b_el_n['sequences'][('HS<->North', 'Electricity_n'), 'flow'].sum()/1000   #in GWh
    em_n_hs = b_el_n['sequences'][('Electricity_n', 'HS<->North'), 'flow'].sum()/1000
    em_hs_m = b_el_m['sequences'][('HS<->Middle', 'Electricity_m'), 'flow'].sum()/1000
    em_m_hs = b_el_m['sequences'][('Electricity_m', 'HS<->Middle'), 'flow'].sum()/1000
    em_hs_e = b_el_e['sequences'][('HS<->East', 'Electricity_e'), 'flow'].sum()/1000
    em_e_hs = b_el_e['sequences'][('Electricity_e', 'HS<->East'), 'flow'].sum()/1000
    em_hs_s = b_el_s['sequences'][('HS<->Swest', 'Electricity_s'), 'flow'].sum()/1000
    em_s_hs = b_el_s['sequences'][('Electricity_s', 'HS<->Swest'), 'flow'].sum()/1000
    em_m_n = b_el_m['sequences'][('Electricity_m', 'North<->Middle'), 'flow'].sum()/1000
    em_n_m = b_el_n['sequences'][('Electricity_n', 'North<->Middle'), 'flow'].sum()/1000
    em_m_e = b_el_m['sequences'][('Electricity_m', 'East<->Middle'), 'flow'].sum()/1000
    em_e_m = b_el_e['sequences'][('Electricity_e', 'East<->Middle'), 'flow'].sum()/1000
    em_m_s = b_el_m['sequences'][('Electricity_m', 'Middle<->Swest'), 'flow'].sum()/1000
    em_s_m = b_el_s['sequences'][('Electricity_s', 'Middle<->Swest'), 'flow'].sum()/1000
    fig, ax = plt.subplots(figsize=(19.1, 10.5))
    img_path = os.path.abspath(os.path.join(os.getcwd(), 
                         'figures','Thuringia_karte_mit_Landkreisen_dull.png'))
    img=mpimg.imread(img_path)
    imgplot=plt.imshow(img)
    imgplot.axes.get_xaxis().set_visible(False)
    imgplot.axes.get_yaxis().set_visible(False)
    
    # Coordinates for red arrows
    x_1 = [120,130,400,410,250,260,690,700]
    y_1 = [440,500,340,400,100,160,440,500]
    z_1 = [60,-60,60,-60,60,-60,60,-60]

    for x,y,z in zip(x_1, y_1,z_1):
        plt.arrow(x ,y,0,z,
                      head_width= 22,
                      width = 8,
                      length_includes_head=True,
                      shape= 'right',
                      color= 'red',
                      ec='red') 
    #Coordinates for green arrows
    x_2 = [280,255,350,385,510,555]
    y_2 = [460,510,230,275,420,465]
    z_2 = [50,-50,50,-50,50,-50]
    w_2 = [-35,35,30,-30,40,-40]

    for x,y,w,z in zip(x_2,y_2,w_2,z_2):
        plt.arrow(x,y,w,z,
                  head_width= 22,
                  width = 8,
                  length_includes_head=True,
                  shape= 'right',
                  color= 'green',
                  ec='green')

    #Netzbezug: North    
    plt.text(200, 140, str(round(em_hs_n)), fontsize = 12)
    plt.text(275,120, str(round(em_n_hs)), fontsize = 12)
    #Netzbezug: Middle
    plt.text(340,385, str(round(em_hs_m)), fontsize = 12)
    plt.text(425,360, str(round(em_m_hs)), fontsize = 12)
    #Netzbezug: East  
    plt.text(630,485, str(round(em_hs_e)), fontsize = 12)
    plt.text(720,465, str(round(em_e_hs)), fontsize = 12)
    #Netzbezug: Swest  
    plt.text(70,485, str(round(em_hs_s)), fontsize = 12)
    plt.text(140,465, str(round(em_s_hs)), fontsize = 12)
    #Netzaustausch: Middle <-> Swest
    plt.text(200,500, str(round(em_m_s)), fontsize = 12)
    plt.text(300,475, str(round(em_s_m)), fontsize = 12)
    #Netzaustausch: Middle <-> North
    plt.text(370,230, str(round(em_m_n)), fontsize = 12)
    plt.text(320,280, str(round(em_n_m)), fontsize = 12)
    #Netzaustausch: Middle <-> East
    plt.text(500,475, str(round(em_m_e)), fontsize = 12)
    plt.text(550,425, str(round(em_e_m)), fontsize = 12)
    plt.text(790,70, '*The values are in GWh', fontsize = 10)
    red_patch = mpatches.Patch(color='red', label='Transformer Hös<->HS')
    green_patch = mpatches.Patch(color='green', label='Connection between regions')
    plt.legend(handles=[red_patch, green_patch])
    #plt.locator_params(nbins=20)
    #plt.grid()
    plt.show()
       
    plt.savefig(os.path.join(os.getcwd(), 'figures',permutation,  model_name + "_" + scenario_num +'_grid.png'), dpi=500)
    