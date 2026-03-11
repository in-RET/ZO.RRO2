# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 15:30:57 2025

@author: rbala
"""
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from src.postprocessing.utils_dump import get_dump_file_path,load_results_from_dump
from src.postprocessing.plot_report_utils import interpret_results, create_combined_bus_component_dfs, plot_bus_flows, categorize_for_sequence, rename_index_with_category
from src.postprocessing.plot_report_utils import create_barplot_dict, scalars_bar_plot, create_bus_dataframes, create_component_dataframes, extract_sankey_flow_data
from src.postprocessing.plot_report_utils import create_sankey_excel
import os 

workdir = os.getcwd()

#%%
scalars_comp_plot = True
component_filename = 'component_peak_flow_comparison_20260119_1655.csv'
storage_filename = 'peak_storage_flow_comparison_20260119_1656.csv'





#%%
scenarios =["final_26_02_26"]
year = 2045
variation = "BS0006"
model_name = "Basic_example_zorro_1"#"_regionalization"   

# plt.style.use('seaborn-v0_8-paper')
# plt.rcParams['figure.figsize'] = (14, 8)
# plt.rcParams['font.size'] = 12
model_data={}
# ref_csv_path = os.path.join(workdir, 'results',
#                      "sankey", 'Ref.csv')
# ref_df = pd.read_csv(ref_csv_path, decimal= ',', sep =';', index_col= 0)
# model_data['ref'] = ref_df
for scenario_num in scenarios:
    print("Loading results...")
    dump_path = get_dump_file_path(year, variation, model_name, scenario_num)
    es, model = load_results_from_dump(dump_path)

    print("Extracting results...")   
    flows = {}
    capacities={}
    flow_descriptions = {}
    
        
    bus_sequences, bus_scalars, component_sequences, component_scalars, component_bus_mapping = interpret_results(model)
    bus_dfs = create_bus_dataframes(bus_sequences, es)
    component_dfs = create_component_dataframes(component_sequences, es)
    combined_df = create_combined_bus_component_dfs(bus_sequences, component_sequences, es)
    Color_mapping=  {
        # Generation sources
        'PV': '#FFD700',           # Gold for solar
        'WIND': '#4169E1',         # Royal Blue for wind
        'HYDRO': '#1E90FF',        # Dodger Blue for hydro
        'LAUFWASSER - KW': '#1E90FF',
        'GRID LOSS' : '#C6C3C3',
        'NACHFRAGE': '#723E04', 
        
        # Bioenergy
        'BIOGAS- BHKW': '#32CD32',                   # Lime Green
        'BIOGAS - AUFBEREITUNGSANLAGE': '#228B22',    # Forest Green
        'BIOGAS - METHANISIERUNGSANLAGE': '#00FF7F',  # Spring Green
        'BIOMASSE': '#163c32',                        # Dark Green/Black
        'BIOMASSE-TO-FUEL': '#8B4513',                # Saddle Brown
        'BIOMASSE ALS FESTBRENNSTOFF': '#654321',     # Dark Brown
        'BIOMASSE - KW': '#228B22',                   # Forest Green
        'BIOMASSE - HKW': '#2E8B57',                  # Sea Green
        'BIOMASSE - HW': '#3CB371',                   # Medium Sea Green
        
        # Fossil fuels
        'GUD': '#FF4500',          # Gas und Dampf
        'GUD - KW': '#FF4500',
        # Storage
        'WAERMESPEICHER': '#FF8C00',                  # Dark Orange
        'ST': '#D10000',                    # Light Orange
        'PUMPSPEICHERKRAFTWERK': '#8A2BE2',         # Blue Violet for pumped storage
        'STROMSPEICHER': '#4B0082',      # Indigo for battery
        'GASSPEICHER': '#DAF0AD',
        'WASSERSTOFFSPEICHER': '#91EDF7',
        #PtX
        'HEIZSTAB': '#FFA500',   
        'WAERMEPUMPEN': '#FF69B4',                     # Orange        
        'NACHHEIZUNG FÜR SPEICHER': '#FF7F50', 
        'POWER-TO-FUEL': '#420075',
        
        # Hydrogen
        'H2': '#00CED1',           # Dark Turquoise
        'HYDROGEN': '#00CED1',
        'BRENNSTOFFZELLE': '#00CED1',     # Fuel cells use hydrogen
        'H2-KW': '#00CED1',
        'ELEKTROLYSE': '#20B2AA',
        'METHANISIERUNG': '#F2AC57',
        # Imports/Exports
        'IMPORT': '#B07800',       
        'EXPORT': '#9370DB',       # Medium Purple
        'EXCESS': '#3B3A3A',
        
        #SONSTIGE
        'UMWELTWAERME': '#C6EF6B',
        'STOFFLICHE NUTZUNG': '#FF5CC6',
        'ABWAERME': '#F59184',
        'UMGEBUNGSLUFT': '#D6F5B5',
                
        # Default
        'DEFAULT': '#A9A9A9'       # Dark Gray
    }

    category_list = {
        'Stromspeicher': ['Battery'],
        'Biogas - BHKW': ['Biogas-BHKW'],
        'Biogas - Aufbereitungsanlage': ['Biogas_feedin_existing'],
        'Biogas - Methanisierungsanlage': ['Biogas_feedin_new'],
        'Biomasse-to-fuel': ['BtL_Holz', 'BtL_substrat'],
        'Import - Biowaste': ['Import_solid_fuel'],
        'Biomasse als Festbrennstoff': ['BioTransformer'],
        'Biomasse - KW': ['Biomasse_elec'],
        'Biomasse - HKW': ['Biomasse_elec_heat'],
        'Biomasse - HW': ['Biomasse_heat'],
        'Import - Holz': ['Import_Wood'],
        'Waermespeicher': ['storage_dist_heat', 'storage_seasonal'],
        'Heizstab': ['Electric boiler'],
        'GuD - KW': ['GuD'],
        'Waermepumpen': ['Heatpump'],
        'Nachheizung für Speicher': ['Preheater'],
        #'Solarthermie': ['ST'],
        'Import - Strom': ['Hös'],
        'Pumpspeicherkraftwerk' : ['Pumped_hydro'],
        'Brennstoffzelle': ['Fuelcell'],
        'Laufwasser - KW' : ['Hydro power plant'],
        'PV': ['PV', 'SOLAR'],
        'WIND': ['WIND'],
        'Nachfrage': ['LOAD', 'DEMAND'],
        'Elektrolyse': ['Electrolysis'],
        'Power-to-fuel': ['PtL'],
        'Umweltwaerme': ['UW'],
        'Gasspeicher' :['Gas_storage'],
        'Stoffliche Nutzung': ['Material_demand'],
        'Import -Gas': ['Import_Gas'],
        'Wasserstoffspeicher': ['H2_storage'],
        'Methanisierung': ['Methanisation'],
        'Import - Wasserstoff' : ['Import_Hydrogen'],
        'Import - Oil': ['Import_Oil'],
        'Import - Kraftstoff' : ['Import_Synthetic_fuel'],
        'Import - Braunkohle': ['Import_brown_coal'],
        'Abwärme' : ['AW'],
        'Excess' : ['excess'],
        'Export': ['Export']
    
    }   
    categorized_dict = categorize_for_sequence(category_list, combined_df)
    
    summer_weak = plot_bus_flows(categorized_dict,
                   bus_name = 'Electricity',
                   inflow_plot_title = 'Strombereitstellung',
                   outflow_plot_title = 'Stromverwendung',
                   COLOR_MAPPING = Color_mapping,
                   start_date=str(year)+'-02-12',
                   end_date = str(year)+'-02-19',
                   figsize = (14, 10),
                   title_fontsize=14,
                   label_fontsize=14,
                   figure_bg_color='#159A3433',
                   axes_bg_color='#159A3400',#'#FFFFFF',
                   labels_with_info = True)

#%%
if scalars_comp_plot:
    # Import component peak flow output csv file from Dashboard 
    component_csv_path = os.path.join(workdir, 'results',
                         "dashboard_results",component_filename)
    raw_component_scalar_df = pd.read_csv(component_csv_path, decimal= '.', sep =',', index_col = 0, skiprows = [0])
    component_scalar_df = rename_index_with_category(raw_component_scalar_df, category_list)
    
    # Import storage peak flow output csv file from Dashboard 
    storage_csv_path = os.path.join(workdir, 'results',
                         "dashboard_results",storage_filename)
    raw_storage_scalar_df = pd.read_csv(storage_csv_path, decimal= '.', sep =',', index_col = 0, skiprows = [0])
    storage_scalar_df = rename_index_with_category(raw_storage_scalar_df, category_list)
    
    category_map = {
        'Erneuerbare Erzeugung': ['PV', 'WIND', 'Laufwasser - KW', 'ST'],
        
        'Bioenergie': ['Biogas- BHKW', 'Biogas - Aufbereitungsanlage', 'Biogas - Methanisierungsanlage',
            'Biomasse - HKW', 'Biomasse - HW', 'Biomasse - KW', 
            'Biomasse als Festbrennstoff', 'Biomasse-to-fuel'
        ],
        
        'Power-to-X (PtX) & Wasserstoff': [
            'Elektrolyse', 'Power-to-fuel', 'Methanisierung', 'Brennstoffzelle'
        ],
        
        'Speichertechnologien': [
            'Stromspeicher', 'Pumpspeicherkraftwerk', 'Gasspeicher', 
            'Wasserstoffspeicher', 'Waermespeicher'
        ],
        
        'Waermesysteme': [
            'Heizstab', 'Waermepumpen', 'Nachheizung für Speicher',
            'Umweltwaerme', 'Umgebungsluft', 'Abwärme'
        ],
        
        'Konventionelle Erzeugung': [
            'GuD - KW',
        ],
        
        'Importe': [
            'Import_Electricity', 'Import -Gas', 'Import - Wasserstoff',
            'Import - Oil', 'Import - Kraftstoff', 'Import - Holz',
            'Import - Biowaste', 'Import_brown_coal', 'Import_hard_coal'
        ],
        
        'Netzinfrastruktur': [
            'Grid_losses', 'East<->Middle', 'HS<->East', 'HS<->Middle',
            'HS<->North', 'HS<->Swest', 'Middle<->Swest', 'North<->Middle'
        ],
        
        'Sonstige': []  # Für nicht kategorisierte Komponenten
    }
    
    category_color = {
            'Erneuerbare Erzeugung': '#A0E24B',      
            'Bioenergie': '#397302',                
            'Power-to-X (PtX) & Wasserstoff': '#4DE0E0', 
            'Waermesysteme': '#D14900',              
            #'Importe': '#795548',                   # Braun
            'Konventionelle Erzeugung': '#969696'   # Grau
        }
    
    bar_plot_scalars = create_barplot_dict(component_scalar_df, category_map)
    del_list = ['Importe', 'Netzinfrastruktur', 'Speichertechnologien']
    for l in del_list:
        bar_plot_scalars.pop(l)
    

    scalars_bar_plot(bar_plot_dict = bar_plot_scalars,
                     Category_color_mapping = category_color,
                     Technology_color_mapping = Color_mapping,
                     fig_title = 'Transformationspfade',
                     figsize = (14, 10),
                     fontsize=14,
                     figure_bg_color='#159A3433',
                     axes_bg_color='#159A3400'#'#FFFFFF',
                     )
    san_df = extract_sankey_flow_data(bus_dfs, component_dfs, component_bus_mapping, group_similar=True)
    PV_mask = san_df['source'].str.startswith('PV')
    Wind_mask = san_df['source'].str.startswith('Wind')
    value_PV = san_df.loc[PV_mask, 'value'].sum()
    value_Wind = san_df.loc[Wind_mask, 'value'].sum()

    PV_row = pd.DataFrame({
        'source': ['PV_total'],
        'target': ['ElectricityIN'],
        'flow_type': ['incoming'],
        'value': [value_PV]
    })
    Wind_row = pd.DataFrame({
        'source': ['Wind_total'],
        'target': ['ElectricityIN'],
        'flow_type': ['incoming'],
        'value': [value_Wind]
    })

    san_df = pd.concat([san_df, PV_row], ignore_index=True)
    san_df = pd.concat([san_df, Wind_row], ignore_index=True)    
   
    model_data[str(year) +'_'+variation+'_'+ scenario_num] = san_df
    
    
#%%

duration_curve_df = pd.DataFrame()
duration_curve_df['Strom'] = categorized_dict['ElectricityIn']["IN: Import - Strom"]
duration_curve_df['Gas'] = categorized_dict['Gas']["IN: Import -Gas"]
duration_curve_df['Wasserstoff'] = categorized_dict['Hydrogen']["IN: Import - Wasserstoff"]
duration_curve_df['Oel'] = categorized_dict['Oil_fuel']["IN: Import - Oil"]
duration_curve_df['Syn. Kraftstoff'] = categorized_dict['Oil_fuel']["IN: Import - Kraftstoff"]
duration_curve_df['Holz'] = categorized_dict['BioWood']["IN: Import - Holz"]
duration_curve_df['Biomasse'] = categorized_dict['Biomass']["IN: Import - Biowaste"]
if year < 2030:
    duration_curve_df['Kohle'] = categorized_dict['Solidfuel']["IN: Import - Braunkohle"]
plt.figure(figsize = (8,5))
for col in duration_curve_df:
    series = duration_curve_df[col].ffill().bfill() 
    sorted_series= duration_curve_df[col].sort_values(ascending=False).reset_index(drop=True)
    sorted_series.index = sorted_series.index/24# len(sorted_series)* 100
    plt.plot(sorted_series,linewidth=2, label = col)

plt.xlabel("Tage des Jahres")
plt.ylabel("Leistung in MW")
plt.title("Jahresdauerlinie")
plt.grid(True)
plt.xlim(0,365)
plt.legend(fontsize = 16)
plt.tight_layout()
plt.show()

#%%
create_sankey_excel(model_data, os.path.join(workdir, 'results', 'sankey', model_name+'_'+variation +'.xlsx'))
