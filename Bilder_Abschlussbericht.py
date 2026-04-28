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
from src .preprocessing.conversion import CO2_price_addition
from src.preprocessing.files import read_input_files
import os 
import textwrap
import numpy as np

workdir = os.getcwd()

#%%
scalars_comp_plot = True
folder_name = 'comp_BP_weather'
plot_variable = 'peak' #/total
component_filename = 'component_'+ plot_variable +'_flow_comparison.csv'
storage_filename = 'peak_storage_flow_comparison.csv'





#%%
scenarios =["REF-04", "REF-04(Test)"]
year = 2045
variation = "BS0006"
model_name = "Basic_example_zorro_1"#"_regionalization"   

# plt.style.use('seaborn-v0_8-paper')
# plt.rcParams['figure.figsize'] = (14, 8)
# plt.rcParams['font.size'] = 12
model_data={}
results_dict ={}
# ref_csv_path = os.path.join(workdir, 'results',
#                      "sankey", 'Ref.csv')
# ref_df = pd.read_csv(ref_csv_path, decimal= ',', sep =';', index_col= 0)
# model_data['ref'] = ref_df
for scenario_num in scenarios:
    print("Loading results...")
    dump_path = get_dump_file_path(year, variation, model_name, scenario_num)
    es, model = load_results_from_dump(dump_path)

    print("Extracting results...")   
  
        
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
        'METHANISIERUNG': '#DDA0DD',
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
        'Import - Strom': ['Import_Electricity'],
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
    
    # summer_weak = plot_bus_flows(categorized_dict,
    #                bus_name = 'Electricity',
    #                inflow_plot_title = 'Strombereitstellung',
    #                outflow_plot_title = 'Stromverwendung',
    #                COLOR_MAPPING = Color_mapping,
    #                start_date=str(year)+'-02-12',
    #                end_date = str(year)+'-02-19',
    #                figsize = (14, 10),
    #                title_fontsize=14,
    #                label_fontsize=14,
    #                figure_bg_color='#159A3433',
    #                axes_bg_color='#159A3400',#'#FFFFFF',
    #                labels_with_info = True)
    
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
    results_dict[scenario_num] = combined_df  
  
create_sankey_excel(model_data, os.path.join(workdir, 'results', 'sankey', model_name+'_'+variation +'.xlsx')) 

#%% Scalar Bar Plot
if scalars_comp_plot:
    # Import component peak flow output csv file from Dashboard 
    component_csv_path = os.path.join(workdir, 'results',
                         "dashboard_results", folder_name, component_filename)
    raw_component_scalar_df = pd.read_csv(component_csv_path, decimal= '.', sep =',', index_col = 0, skiprows = [0])
    component_scalar_df = rename_index_with_category(raw_component_scalar_df, category_list)
    
    # Import storage peak flow output csv file from Dashboard 
    storage_csv_path = os.path.join(workdir, 'results',
                         "dashboard_results",folder_name, storage_filename)
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
            'Import - Strom', 'Import -Gas', 'Import - Wasserstoff',
            'Import - Oil', 'Import - Kraftstoff', 'Import - Holz',
            'Import - Biowaste', 'Import - Braunkohle', 'Import_hard_coal',
        ],
        
        'Netzinfrastruktur': [
            'Grid_losses', 'East<->Middle', 'HS<->East', 'HS<->Middle',
            'HS<->North', 'HS<->Swest', 'Middle<->Swest', 'North<->Middle', 'Netzverluste'
        ],
        
        'Sonstige': []  # Für nicht kategorisierte Komponenten
    }
    
    category_color = {
            'Erneuerbare Erzeugung': '#A0E24B',      
            'Bioenergie': '#397302',                
            'Power-to-X (PtX) & Wasserstoff': '#4DE0E0', 
            'Waermesysteme': '#D14900',              
            'Importe': '#795548',                   # Braun
            'Konventionelle Erzeugung': '#969696'   # Grau
        }
    
    bar_plot_scalars = create_barplot_dict(component_scalar_df, category_map)
    bar_storage = create_barplot_dict(storage_scalar_df, category_map)
    del_list = ['Importe','Netzinfrastruktur', 'Speichertechnologien', 'Sonstige']
    for l in del_list:
        bar_plot_scalars.pop(l)
    
    bar_plot_scalars_sort = {
        k: df.loc[(df != 0).any(axis=1)]
        for k, df in bar_plot_scalars.items()
        }

    scalars_bar_plot(bar_plot_dict = bar_plot_scalars_sort,
                     Category_color_mapping = category_color,
                     Technology_color_mapping = Color_mapping,
                     #fig_title = 'Transformationspfade',
                     x_title = 'Szenarien',
                     figsize = (14, 10),
                     fontsize=14,
                     figure_bg_color='#159A3433',
                     axes_bg_color='#159A3400'#'#FFFFFF',
                     )
    
    #%% Storage Comparison plot
   
    df_raw = bar_storage["Speichertechnologien"].T
    #df_raw = bar_plot_scalars["Bioenergie"].T
    
    # normalize for radar
    df = df_raw / df_raw.max()
    fontsize = 14
    
    categories = df.columns.tolist()
    N = len(categories)
    
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    
    fig, (ax, ax_leg) = plt.subplots(
        ncols=2,
        figsize=(14, 7),
        subplot_kw={ 'polar': True },
        gridspec_kw={'width_ratios': [2, 1]}
    )
    
    ax_leg.remove()
    ax_leg = fig.add_subplot(1, 2, 2)
    
    # RADAR PLOT
    for storage in df.index:
        values = df.loc[storage].values.tolist()
        values += values[:1]
    
        ax.plot(angles, values, linewidth=2, label = storage)
        ax.fill(angles, values, alpha=0.1)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=fontsize)
    ax.tick_params(axis='y', labelsize=fontsize-2)
    ax.legend(
            loc="upper left",
            bbox_to_anchor=(0.0, 1.1),
            fontsize=fontsize-2,
            frameon=True
        )
    ax.set_title("Speichertechnologien",
                 fontsize=fontsize+2, fontweight="bold")
    
    # LEGEND TABLE 
    ax_leg.axis("off")
    
    # build table text
    table_data = []
    for storage in df_raw.index:
        row = [storage] + [f"{df_raw.loc[storage, col]:.0f}" for col in categories]
        table_data.append(row)
    
    col_labels = [""] + categories
    

    wrapped_labels = ["\n".join(textwrap.wrap(col, 10)) for col in col_labels]
    
    table = ax_leg.table(
        cellText=table_data,
        colLabels=wrapped_labels,
        loc="center", 
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(fontsize-2)
    table.scale(1.5,2)
                
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight='bold')
    
    plt.tight_layout()
    plt.show()

       
#%% Duration curve

duration_curve_df = pd.DataFrame()
duration_curve_df['Strom'] = categorized_dict['Electricity_Hös']["IN: Import - Strom"]
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

#%% Vergleich für Brainpool
sequences = read_input_files(
    folder_name='data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name='data/scalars', sub_folder_name=None)
#year = 2030
import_price_2021 = CO2_price_addition(scalars,sequences, year, 'Energy_price_brainpool_2021')
import_price_2021['import_electricity_price'][import_price_2021['import_electricity_price']<0]= 0
import_price_2023 = CO2_price_addition(scalars,sequences, year, 'Energy_price_brainpool_2023')
import_price_2026 = CO2_price_addition(scalars,sequences, year, 'Energy_price_brainpool_2026')

# Jahresdauerlinie Strompreis
carrier = 'electricity'
plt.figure(figsize=(8,5))
plt.plot(import_price_2021['import_'+carrier+'_price'])
plt.plot(import_price_2023['import_'+carrier+'_price'])
plt.plot(import_price_2026['import_'+carrier+'_price'])
plt.legend(['Brainpool_2021 Mean:' + str(round(import_price_2021['import_'+carrier+'_price'].mean())), 
            'Brainpool_2023 Mean:' + str(round(import_price_2023['import_'+carrier+'_price'].mean())),
            'Brainpool_2026 Mean:' + str(round(import_price_2026['import_'+carrier+'_price'].mean()))],loc='upper right', fontsize = 14)
plt.title(carrier+'preis für das Jahr 2045', fontsize = 14)
plt.ylabel(carrier+"preis in € pro MWh",fontsize = 14)
plt.xlabel("Stunden des Jahres",fontsize = 14)
plt.tight_layout()
plt.grid(True)
plt.show()

duration_curve_df = pd.DataFrame()
duration_curve_df['Brainpool_2021'] = import_price_2021['import_'+carrier+'_price']
duration_curve_df['Brainpool_2023'] = import_price_2023['import_'+carrier+'_price']
duration_curve_df['Brainpool_2026'] = import_price_2026['import_'+carrier+'_price']

plt.figure(figsize = (8,5))
for col in duration_curve_df:
    series = duration_curve_df[col].ffill().bfill() 
    sorted_series= duration_curve_df[col].sort_values(ascending=False).reset_index(drop=True)
    sorted_series.index = sorted_series.index/24# len(sorted_series)* 100
    plt.plot(sorted_series,linewidth=2, label = col)

plt.xlabel("Tage des Jahres",fontsize = 14)
plt.ylabel(carrier+"preis in € pro MWh",fontsize = 14)
plt.title("Jahresdauerlinie der "+ carrier +"preise", fontsize = 14)
plt.grid(True)
plt.xlim(0,365)
plt.legend(fontsize = 16)
plt.tight_layout()
plt.show()

results_dict['BRAIN-SIM-SEN']['price'] = import_price_2021
results_dict['REF-01-SEN']['price'] = import_price_2023
results_dict['REF-02-SEN']['price'] = import_price_2026 
summary_data = []
threshold_analysis =[]
fig, axes = plt.subplots(3, 2, figsize=(14, 12))
for idx,sim in enumerate(results_dict):
    price_data = results_dict[sim]['price']
    result_data = results_dict[sim]
    import_mwh = result_data.get('Electricity_Hös')['IN: Import_Electricity'].sum()
    export_mwh = result_data.get('ElectricityOut')['OUT: Export_Electricity'].sum()
    net_import = import_mwh - export_mwh
    avg_price = price_data['import_electricity_price'].mean()
    max_price = price_data['import_electricity_price'].max()
    min_price = price_data['import_electricity_price'].min()
    simultaneous_hours = ((result_data.get('Electricity_Hös')['IN: Import_Electricity'] > 1e-6) & (result_data.get('ElectricityOut')['OUT: Export_Electricity'] > 1e-6)).sum()
    
    summary_data.append({
            'Scenario': sim,
            'Avg Import Price (EUR/MWh)': avg_price,
            'Max Price (EUR/MWh)': max_price,
            'Min Price (EUR/MWh)': min_price,
            'Total Imports (MWh)': import_mwh,
            'Total Exports (MWh)': export_mwh,
            'Net Imports (MWh)': net_import,
            'Simultaneous Hours': simultaneous_hours
        })
    
    net_position= result_data.get('Electricity_Hös')['IN: Import_Electricity']-result_data.get('ElectricityOut')['OUT: Export_Electricity']
    df_price_anal = pd.DataFrame({
            'price': price_data['import_electricity_price'].values,
            'net_position': net_position,
            'imports': result_data.get('Electricity_Hös')['IN: Import_Electricity'],
            'exports': result_data.get('ElectricityOut')['OUT: Export_Electricity']
            })
    
    df_price_anal['action'] = 'neutral'
    df_price_anal.loc[df_price_anal['net_position'] > 0, 'action'] = 'import'
    df_price_anal.loc[df_price_anal['net_position'] < 0, 'action'] = 'export'
    
    import_prices = df_price_anal[df_price_anal['net_position'] > 0]['price']
    export_prices = df_price_anal[df_price_anal['net_position'] < 0]['price']
    threshold_analysis.append({
        'Scenario': sim,
        'Import hours': (df_price_anal.get('action') == 'import').sum(),
        'Export hours': (df_price_anal.get('action') == 'export').sum(),
        'Neutral hours': (df_price_anal.get('action') == 'neutral').sum(),
        'Avg Import Price': import_prices.mean() if len(import_prices) > 0 else np.nan,
        'Avg Export Price': export_prices.mean() if len(export_prices) > 0 else np.nan,
        'Price Spread': export_prices.mean() - import_prices.mean() if len(import_prices) > 0 and len(export_prices) > 0 else np.nan
        
    })
    
    # Visualization
    ax1 = axes[idx, 0]
    colors = {'import': 'red', 'export': 'green', 'neutral': 'gray'}
    for action, color in colors.items():
        prices_action = df_price_anal[df_price_anal['action'] == action]['price']
        if len(prices_action) > 0:
            ax1.hist(prices_action, bins=50, alpha=0.5, color=color, label=action, density=False)
    ax1.set_xlabel('Electricity Price (EUR/MWh)', fontsize=14)
    ax1.set_ylabel('Frequency in Hours',fontsize=14)
    ax1.set_title(f'{sim}: Price Distribution by Action', fontsize=14)
    ax1.legend(fontsize=14)
    ax1.grid(True, alpha=0.3)
    
    ax2 = axes[idx, 1]
    sample = df_price_anal.head(336)  # 2 weeks
    ax2.fill_between(sample.index, 0, sample['net_position'], 
                      where=sample['net_position'] > 0, color='red', alpha=0.5, label='Import')
    ax2.fill_between(sample.index, sample['net_position'], 0, 
                      where=sample['net_position'] < 0, color='green', alpha=0.5, label='Export')
    ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    ax2.set_ylabel('Net Position (MWh)', fontsize=14)
    ax2.set_title(f'{sim}: Net Position (2-week)', fontsize=14)
    ax2.legend(fontsize=14)
    ax2.grid(True, alpha=0.3)
    
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)


plt.tight_layout()
plt.show()
threshold_analysis_df = pd.DataFrame(threshold_analysis)
summary_df = pd.DataFrame(summary_data)
print("\n", summary_df.to_string(index=False))