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
from src.preprocessing.files import read_input_files

def export_csv_region(results, YEAR):
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    region = ['n','s', 'e', 'm']
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
        Gas_storage = solph.views.node(results, 'Gas storage_'+ r)
        H2_storage = solph.views.node(results, 'H2_storage_'+ r)
        
        Emissionen_Gasimport=(b_gas['sequences'][('Import_Gas_'+ r, 'Gas_'+r), 'flow'].sum()*scalars['System']['System_configurations']['Emission_Erdgas']/1000)
        Emissionen_Oelimport=(b_oil['sequences'][('Import_Oil_'+r, 'Oil_fuel_'+r), 'flow'].sum()*scalars['System']['System_configurations']['Emission_Oel']/1000)
        Emissionen_Steinkohleimport=(b_solidf['sequences'][('Import_hard_coal_'+r, 'Solidfuel_'+r), 'flow'].sum()*scalars['System']['System_configurations']['Emission_Steinkohle']/1000)
        Emissionen_Braunkohleimport=(b_solidf['sequences'][('Import_brown_coal_'+r, 'Solidfuel_'+r), 'flow'].sum()*scalars['System']['System_configurations']['Emission_Braunkohle']/1000)
        
#------------------------------------------------------------------------------
# Allgemeine Simulationsergebnisse zum Abgleich
#------------------------------------------------------------------------------
        NaN=str('------------------------------------------------------------------') 
        if r == 'n':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->North', 'Electricity_'+r), 'flow'].sum()*scalars['System']['System_configurations']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->North','Electricity_'+r),'flow'].sum()
        elif r == 'm':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->Middle', 'Electricity_'+r), 'flow'].sum()*scalars['System']['System_configurations']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->Middle','Electricity_'+r),'flow'].sum()
        elif r == 'e':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->East', 'Electricity_'+r), 'flow'].sum()*scalars['System']['System_configurations']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->East','Electricity_'+r),'flow'].sum()
        elif r == 's':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->Swest', 'Electricity_'+r), 'flow'].sum()*scalars['System']['System_configurations']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->Swest','Electricity_'+r),'flow'].sum()
            
        Summe_Emissionen = Emissionen_Gasimport+Emissionen_Oelimport+Emissionen_Stromimport+Emissionen_Steinkohleimport+Emissionen_Braunkohleimport
        Ergebnisse = pd.Series([NaN,
                        b_el['scalars'][('PV_rooftop_'+r,'Electricity_'+r),'invest'],
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
                        Heat_storage['scalars'][('Heat_storage_'+r,'None'),'invest'],
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
