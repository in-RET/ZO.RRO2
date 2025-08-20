# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 10:35:21 2025

@author: rbala
"""

import pandas as pd
from oemof import solph
import os
from src.preprocessing.files import read_input_files
from src.preprocessing.conversion import investment_parameter, CO2_price_addition, load_profile_scaling
from src.postprocessing.utils_dump import get_dump_file_path, load_results_from_dump, interpret_results, calculate_investment_costs,clean_sequence_data, calc_energyimport_cost
from src.postprocessing.utils_dump import calc_energyexport_cost, sankey_excel_output, extract_value, grid_operating_fee, calc_CO2_emission, grid_energy_map
from src.models.automatic_cost_calc import cost_calculation_from_es_and_results
workdir = os.getcwd()
my_path = os.path.abspath(os.path.dirname(__file__))
import matplotlib.pyplot as plt
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
from matplotlib import gridspec



# Define the scenarios you want to compare
scenarios = ["R16","ref"]#["001","002","003", "004", "005", "006","007","008","009","010","011","012", "013","ref"]#
year = 2030
variation = "BS0005"
model_name = "BS_regionalization"
#model_name = "Basic_example_zorro_1"
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
    grid_energy_map(results, permutation, model_name, scenario_num)
#%%
    b_el_n = solph.views.node(results, 'Electricity_n')
    b_el_s = solph.views.node(results, 'Electricity_s')
    b_el_e = solph.views.node(results, 'Electricity_e')
    b_el_m = solph.views.node(results, 'Electricity_m')
    hs_north_flow = b_el_n['sequences'][('HS<->North', 'Electricity_n'), 'flow']/1000 #in GWh 
    north_hs_flow = b_el_n['sequences'][('Electricity_n', 'HS<->North'), 'flow']/1000 
    hs_middle_flow = b_el_m['sequences'][('HS<->Middle', 'Electricity_m'), 'flow']/1000 
    middle_hs_flow = b_el_m['sequences'][('Electricity_m', 'HS<->Middle'), 'flow']/1000 
    hs_east_flow = b_el_e['sequences'][('HS<->East', 'Electricity_e'), 'flow']/1000 
    east_hs_flow = b_el_e['sequences'][('Electricity_e', 'HS<->East'), 'flow']/1000 
    hs_swest_flow = b_el_s['sequences'][('HS<->Swest', 'Electricity_s'), 'flow']/1000 
    swest_hs_flow = b_el_s['sequences'][('Electricity_s', 'HS<->Swest'), 'flow']/1000 
    middle_north_flow = b_el_m['sequences'][('Electricity_m', 'North<->Middle'), 'flow']/1000 
    north_middle_flow = b_el_n['sequences'][('Electricity_n', 'North<->Middle'), 'flow']/1000 
    middle_east_flow = b_el_m['sequences'][('Electricity_m', 'East<->Middle'), 'flow']/1000 
    east_middle_flow = b_el_e['sequences'][('Electricity_e', 'East<->Middle'), 'flow']/1000 
    middle_swest_flow = b_el_m['sequences'][('Electricity_m', 'Middle<->Swest'), 'flow']/1000 
    swest_middle_flow = b_el_s['sequences'][('Electricity_s', 'Middle<->Swest'), 'flow']/1000 
    
    fig = plt.figure(figsize=(22, 12)) 
    gs = gridspec.GridSpec(3, 3, width_ratios=[2, 1, 1]) 
    
    ##### Grid map with arrows ######## 
    
    ax0 = fig.add_subplot(gs[:2, 0]) 
    img_path = os.path.abspath(os.path.join(os.getcwd(), 'figures', 'Thuringia_karte_mit_Landkreisen_dull.png')) 
    img = mpimg.imread(img_path) 
    ax0.imshow(img) 
    ax0.axis('off') 
    x_1 = [120,130,400,410,250,260,690,700] 
    y_1 = [440,500,340,400,100,160,440,500] 
    z_1 = [60,-60,60,-60,60,-60,60,-60] 
    #Coordinates for green arrows 
    x_2 = [280,255,350,385,510,555] 
    y_2 = [460,510,230,275,420,465] 
    z_2 = [50,-50,50,-50,50,-50] 
    w_2 = [-35,35,30,-30,40,-40] 
    for x, y, z in zip(x_1, y_1, z_1): 
        ax0.arrow(x, y, 0, z, head_width=22, width=8, length_includes_head=True, shape='right', color='red') 
    
    for x, y, w, z in zip(x_2, y_2, w_2, z_2): 
        ax0.arrow(x, y, w, z, head_width=22, width=8, length_includes_head=True, shape='right', color='green') 
    
    ax0.text(200, 140, str(round(hs_north_flow.sum())), fontsize = 12) 
    ax0.text(275,120, str(round(north_hs_flow.sum())), fontsize = 12) 
    #Netzbezug: Middle 
    ax0.text(340,385, str(round(hs_middle_flow.sum())), fontsize = 12) 
    ax0.text(425,360, str(round(middle_hs_flow.sum())), fontsize = 12) 
    #Netzbezug: East 
    ax0.text(630,485, str(round(hs_east_flow.sum())), fontsize = 12) 
    ax0.text(720,465, str(round(east_hs_flow.sum())), fontsize = 12) 
    #Netzbezug: Swest 
    ax0.text(70,485, str(round(hs_swest_flow.sum())), fontsize = 12) 
    ax0.text(140,465, str(round(swest_hs_flow.sum())), fontsize = 12) 
    #Netzaustausch: Middle <-> Swest 
    ax0.text(200,500, str(round(middle_swest_flow.sum())), fontsize = 12) 
    ax0.text(300,475, str(round(swest_middle_flow.sum())), fontsize = 12) 
    #Netzaustausch: Middle <-> North 
    ax0.text(370,230, str(round(middle_north_flow.sum())), fontsize = 12) 
    ax0.text(320,280, str(round(north_middle_flow.sum())), fontsize = 12) 
    #Netzaustausch: Middle <-> East 
    ax0.text(500,475, str(round(middle_east_flow.sum())), fontsize = 12) 
    ax0.text(550,425, str(round(east_middle_flow.sum())), fontsize = 12) 
    ax0.text(790, 70, '*The values are in GWh', fontsize=10) 
    red_patch = mpatches.Patch(color='red', label='Transformer Hös<->HS') 
    green_patch = mpatches.Patch(color='green', label='Connection between regions') 
    ax0.legend(handles=[red_patch, green_patch], loc='lower right') 
    
    # North region flow plot 
    ax1 = fig.add_subplot(gs[0, 1]) 
    ax1.plot(north_hs_flow.index, north_hs_flow.values*(-1), label='North → HS', color='blue') 
    ax1.plot(hs_north_flow.index, hs_north_flow.values, label='HS → North', color='orange') 
    ax1.set_title('North Flows (GWh)') 
    ax1.legend() 
    ax1.tick_params(axis='x', labelrotation=45) 
    ax1.grid(True) 
    
    # Middle region flow plot 
    ax2 = fig.add_subplot(gs[0, 2]) 
    ax2.plot(middle_hs_flow.index, middle_hs_flow.values*(-1), label='Middle → HS', color='blue') 
    ax2.plot(hs_middle_flow.index, hs_middle_flow.values, label='HS → Middle', color='orange') 
    ax2.set_title('Middle Flows (GWh)') 
    ax2.legend() 
    ax2.tick_params(axis='x', labelrotation=45) 
    ax2.grid(True) 
    
    #Swest 
    ax3 = fig.add_subplot(gs[1, 1]) 
    ax3.plot(swest_hs_flow.index, swest_hs_flow.values*(-1), label='Swest → HS', color='blue') 
    ax3.plot(hs_swest_flow.index, hs_swest_flow.values, label='HS → Swest', color='orange') 
    ax3.set_title('Swest Flows (GWh)') 
    ax3.legend() 
    ax3.tick_params(axis='x', labelrotation=45) 
    ax3.grid(True) 
    
    #East 
    ax4 = fig.add_subplot(gs[1, 2]) 
    ax4.plot(east_hs_flow.index, east_hs_flow.values*(-1), label='East → HS', color='blue') 
    ax4.plot(hs_east_flow.index, hs_east_flow.values, label='HS → East', color='orange') 
    ax4.set_title('East Flows (GWh)') 
    ax4.legend() 
    ax4.tick_params(axis='x', labelrotation=45) 
    ax4.grid(True) 
    
    #Leitung north- middle 
    ax5 = fig.add_subplot(gs[2, 1]) 
    ax5.plot(north_middle_flow.index, north_middle_flow.values*(-1), label='North → Middle', color='blue') 
    ax5.plot(middle_north_flow.index, middle_north_flow.values, label='Middle → North', color='orange') 
    ax5.set_title('North <-> Middle (GWh)') 
    ax5.legend() 
    ax5.tick_params(axis='x', labelrotation=45) 
    ax5.grid(True) 
    
    ax6 = fig.add_subplot(gs[2, 2]) 
    ax6.plot(east_middle_flow.index, east_middle_flow.values*(-1), label='East → Middle', color='blue') 
    ax6.plot(middle_east_flow.index, middle_east_flow.values, label='Middle → East', color='orange') 
    ax6.set_title('East <-> Middle (GWh)') 
    ax6.legend() 
    ax6.tick_params(axis='x', labelrotation=45) 
    ax6.grid(True) 
    
    ax7 = fig.add_subplot(gs[2,0]) 
    ax7.plot(middle_swest_flow.index, middle_swest_flow.values*(-1), label='Middle → Swest', color='blue') 
    ax7.plot(swest_middle_flow.index, swest_middle_flow.values, label='Swest → Middle', color='orange') 
    ax7.set_title('Middle <-> Swest (GWh)') 
    ax7.legend() 
    ax7.tick_params(axis='x', labelrotation=45) 
    ax7.grid(True) 
    
    # Table for Overview of maximum value and predefined value 
    flows_sum = { 
        'North <-> HS' :(north_hs_flow + hs_north_flow)*1000, 
        'Middle <-> HS': (middle_hs_flow + hs_middle_flow)*1000, 
        'East <-> HS': (east_hs_flow + hs_east_flow)*1000, 
        'Swest <-> HS':(swest_hs_flow + hs_swest_flow)*1000, 
        'North <-> Middle':(north_middle_flow + middle_north_flow)*1000, 
        'East <-> Middle':(east_middle_flow + middle_east_flow)*1000, 
        'Swest <-> Middle':(swest_middle_flow + middle_swest_flow)*1000 } 
    
    flow_max = { region: flows_sum[region].max() for region in flows_sum} 
    max_def = { 
        'North <-> HS' :scalars['Electricity_grid']['electricity']['max_power_north'], 
        'Middle <-> HS': scalars['Electricity_grid']['electricity']['max_power_middle'], 
        'East <-> HS': scalars['Electricity_grid']['electricity']['max_power_east'], 
        'Swest <-> HS':scalars['Electricity_grid']['electricity']['max_power_swest'], 
        'North <-> Middle':scalars['Electricity_grid']['electricity']['connection_north_middle'], 
        'East <-> Middle':scalars['Electricity_grid']['electricity']['connection_east_middle'], 
        'Swest <-> Middle':scalars['Electricity_grid']['electricity']['connection_middle_swest'] 
        } 
    names =['North <-> HS','Middle <-> HS','East <-> HS','Swest <-> HS','North <-> Middle','East <-> Middle','Swest <-> Middle'] 
    table_data = [[f"{max_def[reg]:.1f}", f"{flow_max[reg]:.1f}"] for reg in names] 
    column_labels = ['Limit (MW)', 'Max (MW)'] 
    
    ax8 = fig.add_subplot(gs[1, 2]) 
    table = ax8.table( 
        cellText=table_data,
        rowLabels=names, 
        colLabels=column_labels, 
        loc='upper left', 
        colLoc='center', 
        rowLoc='center', 
        cellLoc='center', 
        bbox=[-0.5, 0.4, 0.48, 0.5] # Adjust as needed 
        ) 
    
    table.auto_set_font_size(False) 
    table.set_fontsize(9) 
    table.scale(1, 1.3) 
    plt.tight_layout() 
    #plt.savefig(os.path.join(os.getcwd(), 'figures', permutation, model_name + "_" + scenario_num + '_grid_and_subplots.png'), dpi=500) 
    plt.show()
    