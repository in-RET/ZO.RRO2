# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 10:35:21 2025

@author: rbala
"""

import pandas as pd
import os
from src.preprocessing.files import read_input_files
from src.preprocessing.conversion import investment_parameter, CO2_price_addition
from src.postprocessing.utils_dump import get_dump_file_path, load_results_from_dump, interpret_results, calculate_investment_costs,clean_sequence_data, calc_energyimport_cost
from src.postprocessing.utils_dump import calc_energyexport_cost, sankey_excel_output, extract_value
from src.models.automatic_cost_calc import cost_calculation_from_es_and_results
workdir = os.getcwd()
my_path = os.path.abspath(os.path.dirname(__file__))


# Define the scenarios you want to compare
scenarios = ["001","002","003", "004", "005", "006","007","008","009","010","ref"]#, ,,"011", "012", "013", "ref"]  
year = 2030
variation = "BS0001"
model_name = "Basic_example_zorro_1"
permutation = str(year)+'_'+variation

sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
import_price = CO2_price_addition(scalars,sequences, year)
epc_costs = investment_parameter(scalars, year, variation)

CSV_DIR = os.path.abspath(os.path.join(workdir,"results", permutation))
CSV_PATH = os.path.join(CSV_DIR, "Scenario_comparison.csv")
INVESTMENT_COSTS_PATH = os.path.join(CSV_DIR, "Investment_Costs.csv")
Sankey_excel_path = os.path.join(CSV_DIR, "Sankey_sequences_all_scenarios.xlsx")
os.makedirs(CSV_DIR, exist_ok=True)

all_bus_sequences = {}
all_bus_scalars = {}
all_component_sequences = {}
all_component_scalars = {}
costs = {}           
for scenario_num in scenarios:
    dump_path = get_dump_file_path(year, variation, model_name, scenario_num)
    
    if not os.path.exists(dump_path):
        print(f"Warning: Dump file not found for scenario {scenario_num}")
        continue
    
    # Load results from the current dump file
    es, results = load_results_from_dump(dump_path)
    costs[scenario_num] = cost_calculation_from_es_and_results(es, results)
    
    # Extract sequences and scalars for this scenario
    bus_sequences, bus_scalars, component_sequences, component_scalars = interpret_results(results)
      
    # Store the extracted data by scenario number
    all_bus_sequences[scenario_num] = bus_sequences
    all_bus_scalars[scenario_num] = bus_scalars
    all_component_sequences[scenario_num] = component_sequences
    all_component_scalars[scenario_num] = component_scalars

# # Compare component scalars for different scenarios
# print("Comparing Component Scalars:")
# for component_name in all_component_scalars[scenarios[-1]]:  # Loop over components from the first scenario
#     print(f"Component: {component_name}")
#     for scenario_num in scenarios:
#         if component_name in all_component_scalars[scenario_num]:
#             print(f"  Scenario {scenario_num} Scalar: {all_component_scalars[scenario_num][component_name]}")
#     print()
    
component_scalars_list = []

# to compare all scenarios and export as csv
for component_name in all_component_scalars["ref"]:  # Use first scenario as a reference
    row = {"Component": component_name}
    for scenario_num in scenarios:
        row[f"Scenario {scenario_num}"] = all_component_scalars.get(scenario_num, {}).get(component_name, 0)  # Default to 0 if missing
    component_scalars_list.append(row)

df_component_scalars_formatted = pd.DataFrame(component_scalars_list)

for column in df_component_scalars_formatted.columns:
    if column.startswith('Scenario'):  
        df_component_scalars_formatted[column] = df_component_scalars_formatted.apply(lambda row: extract_value(row['Component'], row[column]), axis=1)

df_component_scalars_formatted.applymap(lambda x: str(x).replace('.', ',')).to_csv(CSV_PATH, sep = ';', index=False)

# Calculate investment costs
investment_costs = calculate_investment_costs(epc_costs, all_component_scalars)

cleaned_sequences_component = clean_sequence_data(all_component_sequences, data_source='component')
cleaned_sequences_bus = clean_sequence_data(all_bus_sequences, data_source= 'bus')
import_cost = calc_energyimport_cost(import_price, cleaned_sequences_component)
export_cost = calc_energyexport_cost(import_price, cleaned_sequences_bus)
sankey_excel_output(all_bus_sequences, all_component_sequences, model_name, permutation, scenarios, Sankey_excel_path)

print("Ende")



