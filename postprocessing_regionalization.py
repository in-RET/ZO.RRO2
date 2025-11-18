# -*- coding: utf-8 -*-
"""
Created on Tue Oct 14 14:47:38 2025

@author: rbala

Regionalisation dumpfile processsing
"""

from src.postprocessing.utils_dump import get_dump_file_path,load_results_from_dump,interpret_results, extract_value, calc_CO2_emission, sankey_excel_output, calculate_investment_costs,clean_sequence_data
from src.postprocessing.plots import grid_energy_map, plot_bus_energy_flows
from src.postprocessing.utils_dump import summarize_sequences_by_name, prepare_two_day_data
from src.preprocessing.conversion import investment_parameter
from src.preprocessing.files import read_input_files
from src.models.automatic_cost_calc import cost_calculation_from_es_and_results
from oemof import solph
import pandas as pd
import os
workdir = os.getcwd()

scenarios = ["test_sim", "ref"]
year = 2030
variation = "BS0006"
model_name = "BS_regionalization"    

scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)    
permutation = str(year)+'_'+variation
CSV_DIR = os.path.abspath(os.path.join(workdir,"results", permutation))
CSV_PATH = os.path.join(CSV_DIR, "Scenario_comparison_region.xlsx")
COSTS_PATH = os.path.join(CSV_DIR, "Costs_and_emission_region.csv")
Sankey_excel_path = os.path.join(CSV_DIR, "Sankey_sequences_all_scenarios_region.xlsx")
epc_costs = investment_parameter(scalars, year, variation)
all_bus_sequences = {}
all_bus_scalars = {}
all_component_sequences = {}
all_component_scalars = {}
all_component_bus_mapping= {}
costs = {}           
for scenario_num in scenarios:
    dump_path = get_dump_file_path(year, variation, model_name, scenario_num)
    es, results = load_results_from_dump(dump_path)
    costs[scenario_num] = cost_calculation_from_es_and_results(es, results)
    print('Total scenario costs: '+ scenario_num +
          '\n' + str(costs[scenario_num].sum()))
    print('Sum:\t\t\t\t' + str(round(costs[scenario_num].sum().sum()/1000000))+ ' Mio. €\n')
    
    if not os.path.exists(dump_path):
        print(f"Warning: Dump file not found for scenario {scenario_num}")
        continue
    
    # Extract sequences and scalars for this scenario
    bus_sequences, bus_scalars, component_sequences, component_scalars, component_bus_mapping = interpret_results(results)
      
    # Store the extracted data by scenario number
    all_bus_sequences[scenario_num] = bus_sequences
    all_bus_scalars[scenario_num] = bus_scalars
    all_component_sequences[scenario_num] = component_sequences
    all_component_scalars[scenario_num] = component_scalars
    all_component_bus_mapping[scenario_num] = component_bus_mapping
    
region_suffix_map = {'_n': 'North', '_m': 'Middle', '_s': 'Southwest', '_e': 'East'}
scenario_dfs={}    
for scenario_num in scenarios:
    scenario_data = all_component_scalars.get(scenario_num, {})
    data_by_tech = {}
    
    for component_name, bus_data in scenario_data.items():
        is_storage = component_name.lower().endswith("storage")
        
    # Identify suffix and technology
        matched = False
        for suffix, region in region_suffix_map.items():
            if component_name.endswith(suffix):
                base_tech = component_name[:-len(suffix)]
                matched = True
                break
        if not matched:
            base_tech = component_name
            region = 'Unknown'
        if base_tech not in data_by_tech:
            data_by_tech[base_tech] = {r: 0 for r in region_suffix_map.values()}
        
        for bus_name, value in bus_data.items():
        # Extract value (inlined from your code)
            try:
                value = extract_value(component_name, value)
            except:
                value = value  # fallback if extract_value is not essential
                
            data_by_tech[base_tech][region] = value
    df = pd.DataFrame.from_dict(data_by_tech, orient='index')
    df.index.name = 'Technology'
    df['Total'] = df.sum(axis = 1)
    scenario_dfs[scenario_num] = df

with pd.ExcelWriter(CSV_PATH) as writer:
    for scenario, df in scenario_dfs.items():
        df.to_excel(writer, sheet_name=f"Scenario {scenario}")
        

sankey_excel_output(all_bus_sequences, all_component_sequences, model_name, permutation, scenarios, Sankey_excel_path, region=True)
cleaned_sequences_component = clean_sequence_data(all_component_sequences, data_source='component')
cleaned_sequences_bus = clean_sequence_data(all_bus_sequences, data_source= 'bus')
CO2_emission = calc_CO2_emission(year, cleaned_sequences_component)
grid_energy_map(results, permutation, model_name, scenario_num)

summarized_sequences_bus, summarized_sequences_component = summarize_sequences_by_name(cleaned_sequences_bus, cleaned_sequences_component)
plot_bus_energy_flows(summarized_sequences_bus, summarized_sequences_component, scenarios = ['test_sim'],days=round(8760/24/2))

#%%

#%%
# def remove_regional_suffix(component_name):
   
#     regional_suffixes = ['_n', '_e', '_m', '_s', '_north', '_east', '_middle', '_south']
    
#     for suffix in regional_suffixes:
#         if component_name.endswith(suffix):
#             return component_name[:-len(suffix)]
    
#     parts = component_name.split('_')
#     if len(parts) > 1:
#         last_part = parts[-1]
#         if last_part in ['n', 'e', 'm', 's', 'north', 'east', 'middle', 'south']:
#             return '_'.join(parts[:-1])
    
#     return component_name

# summarized_mapping = {}
    
# for component_name, bus_name in component_bus_mapping.items():
#     # Remove regional suffixes
#     base_component = remove_regional_suffix(component_name)
#     base_bus = remove_regional_suffix(bus_name)
    
#     if base_component in summarized_mapping:
#         existing_bus = summarized_mapping[base_component]
        
#         if existing_bus != bus_name:
#             pass
#     else:
#         summarized_mapping[base_component] = base_bus

#%%

