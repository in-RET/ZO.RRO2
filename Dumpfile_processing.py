# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 10:35:21 2025

@author: rbala
"""

import pandas as pd
import os
from src.preprocessing.files import read_input_files
from src.preprocessing.conversion import investment_parameter, CO2_price_addition, load_profile_scaling
from src.postprocessing.utils_dump import get_dump_file_path, load_results_from_dump, interpret_results, calculate_investment_costs,clean_sequence_data, calc_energyimport_cost
from src.postprocessing.utils_dump import calc_energyexport_cost, sankey_excel_output, extract_value, grid_operating_fee, calc_CO2_emission
from src.models.automatic_cost_calc import cost_calculation_from_es_and_results
workdir = os.getcwd()
my_path = os.path.abspath(os.path.dirname(__file__))
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter


# Define the scenarios you want to compare
scenarios = ["014","015","ref"]#["001","002","003", "004", "005", "006","007","008","009","010","011","012", "013","ref"]#
year = 2030
variation = "BS0002"
#model_name = "BS_regionalization"
model_name = "Basic_example_zorro_1"
permutation = str(year)+'_'+variation

sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
import_price = CO2_price_addition(scalars,sequences, year, 'Energy_price_brainpool_2024')
epc_costs = investment_parameter(scalars, year, variation)
demand = load_profile_scaling(scalars,sequences,year, region = True)
CSV_DIR = os.path.abspath(os.path.join(workdir,"results", permutation))

if model_name== 'BS_regionalization':
    CSV_PATH = os.path.join(CSV_DIR, "Scenario_comparison_region.xlsx")
    COSTS_PATH = os.path.join(CSV_DIR, "Costs_and_emission_region.csv")
    Sankey_excel_path = os.path.join(CSV_DIR, "Sankey_sequences_all_scenarios_region.xlsx")
else:
    CSV_PATH = os.path.join(CSV_DIR, "Scenario_comparison.csv")
    COSTS_PATH = os.path.join(CSV_DIR, "Costs_and_emission.csv")
    FIG_PATH = os.path.abspath(os.path.join(workdir, "figures", permutation))
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

if model_name != 'BS_regionalization':   
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
    del df_component_scalars_formatted['Scenario ref'] #delete the refernce scenario
    df_component_scalars_formatted.applymap(lambda x: str(x).replace('.', ',')).to_csv(CSV_PATH, sep = ';', index=False)
    
    
    #%%
    # Calculate investment costs
    investment_costs = calculate_investment_costs(epc_costs, all_component_scalars, region =False)
    
    cleaned_sequences_component = clean_sequence_data(all_component_sequences, data_source='component')
    cleaned_sequences_bus = clean_sequence_data(all_bus_sequences, data_source= 'bus')
    import_costs = calc_energyimport_cost(year,import_price, cleaned_sequences_component)
    export_costs = calc_energyexport_cost(year,import_price, cleaned_sequences_bus)
    grid_import_usage_fee = grid_operating_fee(all_component_sequences, import_price)
    sankey_excel_output(all_bus_sequences, all_component_sequences, model_name, permutation, scenarios, Sankey_excel_path, region = False)
    CO2_emission = calc_CO2_emission(year, cleaned_sequences_component)
    #%% Export cost csv
    
    categories = ["Capital costs", "Operating costs", "Import cost", "Export cost", "Grid usage cost", "Grid yearly cost", "Total cost", " ", "Emission", 
                  "Electricity", "Gas", "Oil","Hard coal", "Brown coal", "Total Emission"]
    data = {category: [] for category in categories}
    #dicts = [investment_costs,import_cost,export_cost,grid_import_usage_fee]
    total_scenarios = len(scenarios)
    for scenario in scenarios:
        capital_cost = investment_costs.get(scenario, {}).get("total_capital_cost", 0)/1000000
        operating_cost = investment_costs.get(scenario, {}).get("total_operating_cost", 0)/1000000
        import_cost = import_costs.get(scenario, {}).get("total_import_cost", 0)/1000000
        export_cost = export_costs.get(scenario, {}).get("total_export_cost", 0)/1000000
        grid_cost = grid_import_usage_fee.get(scenario, {}).get("total_grid_usage_fee", 0)/1000000
        grid_yearly_cost = grid_import_usage_fee.get(scenario, {}).get("peak_load", 0)* scalars['Electricity_grid']['electricity']['grid_annualperformance_fee']/1000000
       
        import_elec = CO2_emission.get(scenario, {}).get("Import_Electricity",0)
        import_gas = CO2_emission.get(scenario, {}).get("Import_Gas",0)
        import_oil = CO2_emission.get(scenario, {}).get("Import_Oil",0)
        import_hard_coal = CO2_emission.get(scenario, {}).get("Import_hard_coal",0)
        import_brown_coal = CO2_emission.get(scenario, {}).get("Import_brown_coal",0)
        total_emission = CO2_emission.get(scenario, {}).get("total_CO2_emission",0)
        
        # Append the costs to the corresponding lists
        data["Capital costs"].append(capital_cost)
        data["Operating costs"].append(operating_cost)
        data["Import cost"].append(import_cost)
        data["Export cost"].append(export_cost)
        data["Grid usage cost"].append(grid_cost)
        data["Grid yearly cost"].append(grid_yearly_cost)
    
        total_cost = (capital_cost + operating_cost + import_cost + grid_cost +grid_yearly_cost - export_cost)
        data["Total cost"].append(total_cost)
        data[" "].append(' ')
        data["Emission"].append(' ')
        data["Electricity"].append(import_elec)
        data["Gas"].append(import_gas)
        data["Oil"].append(import_oil)
        data["Hard coal"].append(import_hard_coal)
        data["Brown coal"].append(import_brown_coal)
        data["Total Emission"].append(total_emission)
        
        
    df = (pd.DataFrame(data, index=[f"Scenario {scenario}" for scenario in scenarios]).T)
    df.round().applymap(lambda x: str(x).replace('.', ',')).to_csv(COSTS_PATH, sep = ';', index=True)
    
    print("Ende")
    
    
    #%% Plot
    
    storage_plot = ['Heat storage_dist_heat', 'Heat storage_seasonal']
    date_time_index = pd.date_range('1/1/'+ str(year), periods=8760,freq='H')
    for scenario, component_data in all_component_sequences.items(): 
        for component, dict_data in component_data.items():
            if component in storage_plot:                     
                fig = plt.figure(figsize=(19.1, 10.5))
                fig.canvas.set_window_title('Speicherverläufe-' +scenario)
                plt.plot(date_time_index,(((dict_data['None']['storage_content'])/all_component_scalars[scenario][component]['None'])*100),label=component, linewidth=0.5)
                # plt.plot(date_time_index,(((Erdgasspeicher_results['sequences'][('Erdgasspeicher','None'),'storage_content']).dropna()/Erdgasspeicher_results['scalars'][('Erdgasspeicher','None'),'invest'])*100),label='Erdgasspeicher')
                # plt.plot(date_time_index,(((Natriumspeicher['sequences'][('Batterie','None'),'storage_content']).dropna()/Natriumspeicher['scalars'][('Batterie','None'),'invest'])*100),label='Natriumspeicher', color = 'lightgreen')   
                # plt.plot(date_time_index,(((Waermespeicher_results['sequences'][('Waermespeicher','None'),'storage_content']).dropna()/Waermespeicher_results['scalars'][('Waermespeicher','None'),'invest'])*100), label='Waermespeicher')
                plt.grid()
                plt.legend()
                plt.ylabel('Speicherfüllstand in \%')
                plt.xlabel('Zeit')
                plt.title('Speicherverläufe_'+component +'_'+ scenario)
                plt.savefig(os.path.join(FIG_PATH, scenario, 'Speicherverläufe_'+component+'.png'))

else:
    
    # Scalars comparision for regionilization
    region_suffix_map = {'_n': 'North', '_m': 'Middle', '_s': 'Southwest', '_e': 'East'}
    scenario_dfs={}
    component_info ={
        "Battery":                  "None",
        "Biogas- BHKW":              "Electricity",
        "Biogas_feedin_existing":    "Gas",
        "Biogas_feedin_new":        "Gas",
        "Biomasse_elec_heat":       "Electricity",
        "Biomasse_elec":            "Electricity",
        "Biomasse_heat":            "District heating",
        "BioTransformer":          "Solidfuel",
        "Pre-heater":              "District heating",
        "BtL":                      "Oil_fuel",
        "Electric boiler":          "District heating",
        "Electrolysis":             "Hydrogen",
        "Fuelcell":                 "Electricity",
        "Gas_storage":               "None",
        "GuD":                      "Electricity",
        "H2_storage":               "None",
        "Heat storage":             "None",
        "Heat storage_dist_heat":    "None",
        "Heat storage_seasonal":   "None",
        "Heatpump_air":             "District heating",
        "Heatpump_water":           "District heating",
        "Heatpump_recovery_heat":   "District heating",
        "Hydro power plant":        "Electricity",
        "Hydrogen_feedin":          "Gas",
        "Methanisation":            "Gas",
        "PtL":                      "Oil_fuel",
        "Pumped_hydro_storage":     "None",
        "Pumped_hydro_storage_Goldistal": "None",
        "PV_open_east":             "Electricity",
        "PV_open_middle":           "Electricity",
        "PV_open_north":            "Electricity",
        "PV_open_swest":            "Electricity",
        "PV_rooftop_east":          "Electricity",
        "PV_rooftop_middle":        "Electricity",
        "PV_rooftop_north":         "Electricity",
        "PV_rooftop_swest":         "Electricity",
        "ST":                       "District heating",
        "Wind_east":                "Electricity",
        "Wind_middle":              "Electricity",
        "Wind_north":               "Electricity",
        "Wind_swest":               "Electricity",
        "Preheater- WP":            "District heating",
        "Preheater- Electric boiler":"District heating",
        
    }
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
        scenario_dfs[scenario_num] = df
    
    with pd.ExcelWriter(CSV_PATH) as writer:
        for scenario, df in scenario_dfs.items():
            df.to_excel(writer, sheet_name=f"Scenario {scenario}")
    
    sankey_excel_output(all_bus_sequences, all_component_sequences, model_name, permutation, scenarios, Sankey_excel_path, region=True)
    investment_costs = calculate_investment_costs(epc_costs, all_component_scalars, region =True)
    cleaned_sequences_component = clean_sequence_data(all_component_sequences, data_source='component')
    cleaned_sequences_bus = clean_sequence_data(all_bus_sequences, data_source= 'bus')
    CO2_emission = calc_CO2_emission(year, cleaned_sequences_component)
    
#%%
    