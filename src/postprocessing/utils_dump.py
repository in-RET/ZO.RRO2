# -*- coding: utf-8 -*-
"""
Created on Tue Feb 18 09:59:03 2025

@author: rbala
"""
import os
from oemof.tools import economics
from oemof import network, solph
from oemof.solph import processing
import pandas as pd
import os
import pickle
from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from src.preprocessing.files import read_input_files
from src.preprocessing.conversion import investment_parameter, CO2_price_addition
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches

workdir = os.getcwd()
my_path = os.path.abspath(os.path.dirname(__file__))
def get_dump_file_path(year, variation, model_name, scenario_num):
    return os.path.join(workdir, 'dumps',
                         f"{year}_{variation}",
                         f"{model_name}_{year}_{variation}_{scenario_num}.dump")
    

def load_results_from_dump(dump_path):
    energysystem = solph.EnergySystem()
    energysystem.restore(my_path, dump_path)
    return energysystem, energysystem.results["main"]

def interpret_results(results):          
    bus_sequences = {}
    bus_scalars = {}
    component_sequences = {}
    component_scalars = {}
    
    # Iterate through results to classify flows for Bus, Source, Converter, etc.
    for key, value in results.items():
        component_name = str(key[1].label) if key[1] else "None"  # Extract component name (e.g., Source, Converter, etc.)
        
        if isinstance(key[0], solph.Bus):
            bus_name = str(key[0].label)  # Extract bus name
            
            # Extract sequences for Bus
            if isinstance(value, dict) and "sequences" in value:
                if bus_name not in bus_sequences:
                    bus_sequences[bus_name] = {}
                bus_sequences[bus_name][component_name] = value["sequences"]
    
            # Extract scalar values for Bus
            elif isinstance(value, (int, float)):
                if bus_name not in bus_scalars:
                    bus_scalars[bus_name] = {}
                bus_scalars[bus_name][component_name] = value["scalars"]["total"]
    
        
        elif isinstance(key[0], (solph.components.Source, solph.components.Link, solph.components.Converter, solph.components.Sink, solph.components.GenericStorage)):
            component_name = str(key[0].label)  # Extract component name
            # Extract sequences for Component
            if isinstance(value, dict):
                if "scalars" in value:
                    # Accessing the total scalar value from the 'scalars' pandas Series
                    total_value = value["scalars"].get("total", 0)
            
                    if component_name not in component_scalars:
                        component_scalars[component_name] = {}
            
                    component_scalars[component_name][str(key[1].label) if key[1] else "None"] = total_value
            
                # Handling 'sequences' part (if needed)
                if "sequences" in value:
                    sequence_data = value["sequences"]
            
                    # You can choose to store sequences in a separate dictionary or process as needed
                    if component_name not in component_sequences:
                        component_sequences[component_name] = {}
            
                    component_sequences[component_name][str(key[1].label) if key[1] else "None"] = sequence_data

    return bus_sequences, bus_scalars, component_sequences, component_scalars

def extract_value(component_name, value):
    if isinstance(value, dict):
        if component_name == 'Battery' or 'storage' in component_name:
            return value.get('None', list(value.values())[0])
        elif component_name == 'Biogas- BHKW' or 'GuD':
            return value.get('Electricity', list(value.values())[0])
        else:
            return list(value.values())[0]
    elif isinstance(value, (int, float)):
        return float(value)
    else:
        return None

def calculate_investment_costs(epc_costs, all_component_scalars, region= True):
    """
    This calculates the investment and the operating costs for each components
    Parameters
    ----------
    epc_costs : dict
        Read from the scalars file, see in preprocess for the code
    all_component_scalars : dict
        Scalars extrated from the dumpfile

    Returns
    -------
    investment_costs : TYPE
        DESCRIPTION.

    """
    investment_costs = {}
    
    component_mapping_info ={
        "Battery":                  ("storage_electricity", "None"),
        "Biogas- BHKW":             ("biogas_combined_heat_and_power_plant", "Electricity"),
        "Biogas_feedin_existing":   ("biomethane_injection_plant", "Gas"),
        "Biogas_feedin_new":        ("biogas_upgrading_plant","Gas"),
        "Biomasse_elec_heat":       ("biomass_combined_heat_and_power_plant", "Electricity"),
        "Biomasse_elec":            ("biomass_power_plant", "Electricity"),
        "Biomasse_heat":            ("biomass_heating_plant","District heating"),
        "BioTransformer":           ("biotransformer","Solidfuel"),
        "Pre-heater":               ("heat_pump_ground_Flusswärme","District heating"),
        "BtL":                      ("biomass_to_liquid_system", "Oil_fuel"),
        "Electric boiler":          ("electrical_heater","District heating"),
        "Electrolysis":             ("electrolysis","Hydrogen"),
        "Fuelcell":                 ("fuel_cells", "Electricity"),
        "Gas_storage":              ("storage_gas", "None"),
        "GuD":                      ("combined_heat_and_power_generating_unit","Electricity"),
        "H2_storage":               ("storage_hydrogen","None"),
        "Heat storage":             ("storage_heat_district_heating","None"),
        "Heat storage_dist_heat":   ("storage_heat_district_heating", "None"),
        "Heat storage_seasonal":    ("storage_heat_seasonal","None"),
        "Heatpump_air":             ("heat_pump_air_Abwärme","District heating"),
        "Heatpump_water":           ("heat_pump_ground_Flusswärme","District heating"),
        "Heatpump_recovery_heat":   ("heat_pump_air_Abwärme","District heating"),
        "Hydro power plant":        ("run_river_power_plant","Electricity"),
        "Hydrogen_feedin":          ("hydrogen_feed_in","Gas"),
        "Methanisation":            ("methanation","Gas"),
        "PtL":                      ("power_to_liquid_system", "Oil_fuel"),
        "Pumped_hydro_storage":     ("storage_electricity_pumped_hydro_storage_power_technology","None"),
        "Pumped_hydro_storage_Goldistal": ("storage_electricity_pumped_hydro_storage_power_technology","None"),
        "PV_open_east":             ("field_photovoltaic_power_plant", "Electricity"),
        "PV_open_middle":           ("field_photovoltaic_power_plant","Electricity"),
        "PV_open_north":            ("field_photovoltaic_power_plant","Electricity"),
        "PV_open_swest":            ("field_photovoltaic_power_plant","Electricity"),
        "PV_rooftop_east":          ("rooftop_photovoltaic_power_plant","Electricity"),
        "PV_rooftop_middle":        ("rooftop_photovoltaic_power_plant","Electricity"),
        "PV_rooftop_north":         ("rooftop_photovoltaic_power_plant","Electricity"),
        "PV_rooftop_swest":         ("rooftop_photovoltaic_power_plant","Electricity"),
        "ST":                       ("solar_thermal_power_plant","District heating"),
        "Wind_east":                ("onshore_wind_power_plant","Electricity"),
        "Wind_middle":              ("onshore_wind_power_plant","Electricity"),
        "Wind_north":               ("onshore_wind_power_plant","Electricity"),
        "Wind_swest":               ("onshore_wind_power_plant","Electricity"),
        "Preheater- WP":            ("heat_pump_ground_Flusswärme","District heating"),
        "Preheater- Electric boiler":("electrical_heater","District heating"),
        
    }
    
    def match_base_component(component_with_region):
        """Extracts base component name by removing region suffix."""
        for base_name in component_mapping_info:
            if component_with_region.startswith(base_name):
                return base_name
        return None

    for scenario, components in all_component_scalars.items():
        investment_costs[scenario] = {}
        total_scenario_capital_cost = 0
        total_scenario_operating_cost = 0
        total_scenario_cost=0
        
        if region:
            for full_component_name in components:
                base_name = match_base_component(full_component_name)
                if not base_name:
                    continue
                
                epc_category, value_type = component_mapping_info[base_name]
                value= components[full_component_name].get(value_type, 0)
                investk = epc_costs.get(epc_category, {}).get("investk", 0)
                operatk = epc_costs.get(epc_category, {}).get("betriebsk", 0)
                
                component_capital_cost = value * investk
                component_operating_cost = value * operatk
    
                if base_name == "Pumped_hydro_storage_Goldistal":
                    component_capital_cost = 0  # No capital cost
                    total_component_cost = component_operating_cost
                else:
                    total_component_cost = component_capital_cost + component_operating_cost
    
                investment_costs[scenario][full_component_name] = {
                    "capital costs": component_capital_cost,
                    "operating costs": component_operating_cost
                }
                total_scenario_cost += total_component_cost
                total_scenario_capital_cost += component_capital_cost
                total_scenario_operating_cost += component_operating_cost
        else:
            for component, (epc_category, value_type) in component_mapping_info.items():
                investment_costs[scenario][component] = {}
                investk = epc_costs.get(epc_category, {}).get("investk", 0)
                operatk = epc_costs.get(epc_category, {}).get("betriebsk", 0)
    
                # Check if component exists in all_components, otherwise set value to 0
                if component in components:
                    value = components[component].get(value_type, 0)  # Get electricity or dist_heating value
                else:
                    value = 0  # Fail-safe: Missing component defaults to zero
                if component == "Pumped_hydro_storage_Goldistal":
                    total_component_investment = (value * operatk)# Compute cost
                    component_capital_cost = 0
                    component_operating_cost = (value * operatk)
                    #investment_costs[scenario][component] = total_component_investment
                    investment_costs[scenario][component]['capital costs'] = component_capital_cost
                    investment_costs[scenario][component]['operating costs'] = component_operating_cost
                    
                else:
                    total_component_investment = (value * investk)  + (value * operatk)# Compute cost
                    #investment_costs[scenario][component] = total_component_investment
                    component_capital_cost = (value * investk)
                    component_operating_cost = (value * operatk)
                    investment_costs[scenario][component]['capital costs'] = component_capital_cost
                    investment_costs[scenario][component]['operating costs'] = component_operating_cost
            
                total_scenario_cost += total_component_investment
                total_scenario_capital_cost += component_capital_cost
                total_scenario_operating_cost += component_operating_cost
        investment_costs[scenario]['total_cost'] = total_scenario_cost
        investment_costs[scenario]['total_capital_cost'] = total_scenario_capital_cost
        investment_costs[scenario]['total_operating_cost'] = total_scenario_operating_cost

    return investment_costs

def clean_sequence_data(all_sequences, data_source):
    """
    Replaces Nan(last timestep result from the energy system with previous value)
    Parameters
    ----------
    all_sequences : dict either (componet or bus dict)
        extracted from dumpfile
    
    data_source: str
        need to specify whether the flow is from the component or to the component
        either 'component' or 'bus'
    
    Returns
    -------
    cleaned_data : dict
        
    """
    cleaned_data = {}  
    if data_source == 'component':    
        for scenario, components in all_sequences.items():
            # Create a sub-dictionary for each scenario
            cleaned_data[scenario] = {}
            
            # Iterate through each component inside the scenario
            for component, buses in components.items():
                cleaned_data[scenario][component] = {}
                # Iterate through each bus inside the component
                for bus, df in buses.items():
                    if isinstance(df, pd.DataFrame) and 'flow' in df.columns:
                        # Forward-fill the NaN values in the 'flow' column
                        flow_series = df['flow'].ffill()
                        cleaned_data[scenario][component][bus] = flow_series
                    elif isinstance(df, pd.DataFrame) and 'storage_content' in df.columns:
                        flow_series = df['storage_content'].ffill()
                        cleaned_data[scenario][component][bus] = flow_series
    elif data_source == 'bus':
        for scenario, buses in all_sequences.items():
            # Create a sub-dictionary for each scenario
            cleaned_data[scenario] = {}
            
            # Iterate through each component inside the scenario
            for bus, components in buses.items():
                cleaned_data[scenario][bus] = {}
                # Iterate through each bus inside the component
                for component, df in components.items():
                    if isinstance(df, pd.DataFrame) and 'flow' in df.columns:
                        # Forward-fill the NaN values in the 'flow' column
                        flow_series = df['flow'].ffill()
                        cleaned_data[scenario][bus][component] = flow_series
                    elif isinstance(df, pd.DataFrame) and 'storage_content' in df.columns:
                        flow_series = df['storage_content'].ffill()
                        cleaned_data[scenario][bus][component] = flow_series
        
    return cleaned_data

def calc_energyimport_cost (year,import_price,cleaned_sequences):
    """
    This function calculates the costs for importing the energy based on price timeseries and flow values.

    Parameters
    ----------
    import_price : dict
        look preprocessing for more details
    cleaned_sequences_component : dict
        flow values from component to a bus 

    Returns
    -------
    import_costs : dict
        import cost for every energy carrier

    """
    
    import_costs = {}
    total_import_cost = 0
    sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    # Define mapping for price lookup
    price_mapping = {
        'Import_Electricity': 'import_electricity_price',
        'Import_Gas': 'import_gas_price',
        'Import_Oil': 'import_oil_price',
        'Import_Hydrogen': 'import_hydrogen_price',
        'Import_Synthetic_fuel': 'import_synt_fuel_price',
        'Import_Wood': 'import_biomass_price',
        'Import_brown_coal': 'import_brown_coal_price',
        'Import_hard_coal': 'import_hard_coal_price',
        'Import_solid_fuel': 'import_biomass_price'
    }
    for scenario, components_data in cleaned_sequences.items():
        # Initialize the import costs for this scenario
        scenario_import_costs = {}
        if scenario == '001':
            import_price = CO2_price_addition(scalars, sequences, year, 'Energy_price')
        elif scenario =='002':
            import_price = CO2_price_addition(scalars, sequences, year, 'Energy_price')
            price_mapping = {
                'Import_Electricity': 'import_electricity_price_2019',
                'Import_Gas': 'import_gas_price',
                'Import_Oil': 'import_oil_price',
                'Import_Hydrogen': 'import_hydrogen_price',
                'Import_Synthetic_fuel': 'import_synt_fuel_price',
                'Import_Wood': 'import_biomass_price',
                'Import_brown_coal': 'import_brown_coal_price',
                'Import_hard_coal': 'import_hard_coal_price',
                'Import_solid_fuel': 'import_biomass_price'
            }
        else:
            import_price = import_price
        # Iterate through the components and energy types within the scenario
        for component, bus_data in components_data.items():  # `bus_data` is a dict with bus names as keys
            # Check if the component has a price mapping
            if component in price_mapping:
                # Get the corresponding price series for the component
                price_series = import_price[price_mapping[component]]
    
                if isinstance(bus_data,dict):
                    for bus_name, df in bus_data.items():
                        if isinstance(df,pd.DataFrame) and 'flow' in df.columns:
                            flow_series = df['flow'].to_numpy()
                        elif isinstance(df, pd.Series):
                            flow_series = df.to_numpy()
                            bus_name = bus_name
                        else:
                            continue
                        
                        # Ensure both the flow series and price series align properly (length check)
                        if len(flow_series) == len(price_series):
                            # Calculate the import cost for this component and bus in this scenario
                            cost = (flow_series * price_series).sum()  # Sum the cost for the entire period
    
                            # Store the import cost for the component and bus in this scenario
                            scenario_import_costs[component] = cost
    
                            # Add the component's cost to the total import cost
                            total_import_cost += cost
        scenario_import_costs["total_import_cost"] = sum(scenario_import_costs.values())
        # Store the import costs for this scenario in the main dictionary
        import_costs[scenario] = scenario_import_costs
    
    return import_costs

def calc_energyexport_cost(year,import_price,cleaned_sequences_bus):
    
    """
    This function calculates the costs for exporting the energy based on price timeseries and flow values.

    Parameters
    ----------
    import_price : dict
        look preprocessing for more details
    cleaned_sequences_bus : dict
        flow values from teh bus to the component

    Returns
    -------
    import_costs : dict
        import cost for every energy carrier

    """
    export_costs = {}
    total_export_cost = 0
    sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name=None)
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    # Define mapping for price lookup
    price_mapping = {
        'Export_Electricity': 'export_electricity_price',
        'Export_Hydrogen': 'export_hydrogen_price',
    }
    for scenario, bus_data in cleaned_sequences_bus.items():
        # Initialize the import costs for this scenario
        scenario_export_costs = {}
        if scenario == '001':
            import_price = CO2_price_addition(scalars, sequences, year, 'Energy_price')
        elif scenario =='002':
            import_price = CO2_price_addition(scalars, sequences, year, 'Energy_price')
            price_mapping = {
                'Export_Electricity': 'export_electricity_price_2019',
                'Export_Hydrogen': 'export_hydrogen_price',
            }
        else:
            import_price = import_price
        # Iterate through the components and energy types within the scenario
        for bus, component_data in bus_data.items():  # `bus_data` is a dict with bus names as keys
            # Check if the component has a price mapping
            
            for component,df in component_data.items():
                if component in price_mapping:
                    # Get the corresponding price series for the component
                    price_series = import_price[price_mapping[component]]
        
                    if isinstance(df,pd.DataFrame) and 'flow' in df.columns:
                        flow_series = df['flow'].to_numpy()
                    elif isinstance(df, pd.Series):
                        flow_series = df.to_numpy()
                        component_name = component
                    else:
                        continue
                    
                        # Ensure both the flow series and price series align properly (length check)
                    if len(flow_series) == len(price_series):
                        # Calculate the import cost for this component and bus in this scenario
                        cost = (flow_series * (-1)*price_series).sum()  # Sum the cost for the entire period
    
                        # Store the import cost for the component and bus in this scenario
                        scenario_export_costs[(bus,component_name)] = cost
    
                        # Add the component's cost to the total import cost
                        total_export_cost += cost
        scenario_export_costs["total_export_cost"] = sum(scenario_export_costs.values())
        # Store the import costs for this scenario in the main dictionary
        export_costs[scenario] = scenario_export_costs
    return export_costs

def grid_operating_fee(data,grid_fees):
    selected_components = {"Import_Electricity", "Hös<->HS"}
    result = {}
    
    for scenario, components in data.items():
        scenario_results = {}
        total_grid_fee = 0
        if scenario != 'ref':
            scenario_num = int(scenario)
        for component in selected_components:
            
            bus_data = components[component]
            scenario_results[component] = {}
    
            for bus,df in bus_data.items():  # Auto-detect buses for each component
                sequence = df['flow']
    
                total_sum = sequence.sum()
                max_value = sequence.max()
                total_usage_time = total_sum / max_value if max_value > 0 else 0
                
                if scenario_num >= 14:
                    if component == 'Import_Electricity':
                        variable_cost = (
                            grid_fees["grid_operating_fee_HöS<2500h"]
                            if total_usage_time <= 2500
                            else grid_fees["grid_operating_fee_HöS>2500h"]
                        )
                    elif component== 'Hös<->HS':
                        variable_cost = (
                            grid_fees["grid_operating_fee_HS<2500h"]
                            if total_usage_time <= 2500
                            else grid_fees["grid_operating_fee_HS>2500h"]
                        )
                else:
                    variable_cost = grid_fees["grid_operating_fee_old"]
                
                if scenario_num < 14 and component == 'Import_Electricity' or scenario_num>= 14:
                    if len(variable_cost)== len(sequence):
                        grid_cost = (sequence * variable_cost).sum()
                    elif len(variable_cost) == 1:
                        grid_cost = total_sum * grid_fees
                elif scenario_num < 14 and component == 'Hös<->HS':
                    grid_cost = 0
                
                    
                total_grid_fee += grid_cost
    
                scenario_results[component][bus] = {
                    "Total Sum": total_sum,
                    "Max Value": max_value,
                    "Total Usage Time": total_usage_time,
                    "Variable Cost": variable_cost,
                    "Grid_usage_Cost": grid_cost,
                    }
        scenario_results["total_grid_usage_fee"]= total_grid_fee
        scenario_results["peak_load"]= max_value
    
        result[scenario] = scenario_results  # Store results for the scenario
    return result

def sankey_excel_output(all_bus_sequences, all_component_sequences, model_name, permutation, scenarios, output_path, region = False):
    """
    Save the sum of flows classified by bus name and component name to an Excel file. 
    Created for easy linking with Sankey diagram.
    
    Parameters:
        all_bus_sequences (dict): Dictionary with scenario numbers as keys and bus sequences as values.
                                  This dict contains flow values from bus to a component.
        all_component_sequences (dict): Dictionary with scenario numbers as keys and component sequences as values.
                                        This dict contains flow values from component to bus.
        model_name (str): The model ID to write at the top of each sheet.
        scenarios (list): List of scenario numbers to process.
        output_path (str): Path to save the Excel file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    year, variation = permutation.split('_') 
    
    bus_name_mapping = {
        'BioWood': 'Bioholz',
        'Biomass': 'Biomass',
        'District heating': 'Fernwaerme',
        'Electricity': 'Strom',
        'Environmental heat': 'Umweltwaerme',
        'Gas': 'Gas',
        'Hydrogen': 'Wassterstoff',
        'Oil_fuel': 'Oel&Kraftstoff',
        'Pre-heating': 'Nachheizung',
        'Recovery heat': 'Abwaerme',
        'Solidfuel': 'Festbrennstoff'
    }

    component_name_mapping = {
        'BioTransformer' : 'Biomasse als Festbrennstoff',
        'Biomasse_elec_heat': 'Biomasse - Heizkraftwerk',
        'Biomasse_elec': 'Biomasse - Kraftwerk',
        'Biomasse_heat': 'Biomasse - Heizwerk',
        'Import_Wood': 'Biomasse - Holz',
        'Import_solid_fuel': 'Biomasse - Substrat',
        'Biogas- BHKW': 'Biogas-BHKW',
        'Electric boiler': 'Elektodenheizstab',
        'GuD': 'GuD in KWK',
        'Heat storage_dist_heat': 'Fernwaermespeicher',
        'Heatpump_air' : 'Luft-Waermepumpe',
        'Heatpump_recovery_heat': 'Abwaerme-Waermepumpe',
        'Heatpump_water': 'Erd-Waermepumpe',
        'Preheater': 'Nachheizung',
        'ST': 'Solarthermie',
        'Battery': 'Batteriespeicher',
        'Fuelcell': 'Brennstoffzelle',
        'Hydro power plant': 'Wasserkraft',
        'Pumped_hydro_storage': 'Pumpspeicherkraftwerk',
        'Import_Electricity' : 'Import - Stromboerse',
        'Pumped_hydro_storage_Goldistal': 'Pumpspeicherkraftwerk - Goldistal',
        'UW' : 'Umweltwaerme',
        'Biogas_feedin_existing': 'Biogasaufbereitunganlage',
        'Biogas_feedin_new': 'Biomethaneinspeisungsanlage',
        'Gas_storage' : 'Erdgasspeicher',
        'Hydrogen_feedin': 'Wasserstoff-Einspeisung',
        'Import_Gas': 'Import - Gasnetz',
        'Methanisation': 'Methanisierung',
        'Electrolysis': 'Elektrolyse',
        'H2_storage': 'Wasserstoffspeicher',
        'Import_Hydrogen': 'Import - Wasserstoff',
        'BtL': 'Biomass to Liquid',
        'Import_Oil': 'Import - Heizoel & Kraftstoffe',
        'Import_Synthetic_fuel': 'Import - Synth. Kraftstoffe',
        'PtL' : 'Power to Liquid',
        'Heat storage_seasonal': 'Saisonaler Waermespeicher',
        'Import_brown_coal' : 'Import - Braunkohle',
        'Import_hard_coal': 'Import - Steinkohle',
        "PV_open_east":"PV_open_east",
        "PV_open_middle":"PV_open_middle",
        "PV_open_north":"PV_open_north",
        "PV_open_swest":"PV_open_swest",
        "PV_rooftop_east":"PV_rooftop_east",
        "PV_rooftop_middle":"PV_rooftop_middle",
        "PV_rooftop_north":"PV_rooftop_north",
        "PV_rooftop_swest":"PV_rooftop_swest",
        "Wind_east":"Wind_east",
        "Wind_middle":"Wind_middle",
        "Wind_north":"Wind_north",
        "Wind_swest":"Wind_swest",
        "Preheater- WP": "Nachheizung - WP",
        "Preheater- Electric boiler": "Nachheizung - Heizstab"

    }

    def adjust_column_width_for_all_sheets(wb):
        for sheet in wb.sheetnames: 
            current_sheet = wb[sheet]
            for col in current_sheet.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                current_sheet.column_dimensions[column].width = adjusted_width
    def map_name(original_name, name_mapping):   
        if '_' in original_name and region:
            base, suffix = original_name.split('_', 1)
            mapped_base = name_mapping.get(base, base)
            return f"{mapped_base}_{suffix}"
        else:
            return name_mapping.get(original_name, original_name)


    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # create a dummy sheet to prevent index error
        pd.DataFrame({"Message": ["Dummy sheet, will be deleted"]}).to_excel(writer, sheet_name="Dummy_Sheet", index=False)
        pd.DataFrame({"Info: Use the drop down box to select the scenario": [""]}).to_excel(writer, sheet_name="Main_Sheet", index=False)
        sheets_created = False

        # extract reference structure from the ref scenario
        if region:
            ref_scenario ='ref'
        else:
            ref_scenario = 'ref'
        
        reference_bus_structure = all_bus_sequences[ref_scenario]
        reference_component_structure = all_component_sequences[ref_scenario]
        
        for scenario_num in scenarios:
            total_pv = 0
            total_wind = 0
            total_pumpspeicher_ein = 0
            total_pumpspeicher_aus = 0
            import_strom = 0
            bus_sequences = all_bus_sequences.get(scenario_num, {})
            component_sequences = all_component_sequences.get(scenario_num, {})

            if not bus_sequences and not component_sequences:
                print(f"Warning: No sequences found for scenario {scenario_num}")
                continue

            data_frames = []

            # process buses using reference structure
            for bus_name, reference_components in reference_bus_structure.items():
                mapped_bus_name = map_name(bus_name, bus_name_mapping)
                bus_data = []
                for component_name in reference_components:
                    mapped_component_name = map_name(component_name, component_name_mapping)
                    if bus_name in bus_sequences and component_name in bus_sequences[bus_name]:
                        flow_sum = bus_sequences[bus_name][component_name]['flow'].sum()
                    else:
                        flow_sum = 0
                    if mapped_component_name.startswith("PV_"):
                        total_pv += flow_sum
                    elif mapped_component_name.startswith("Wind_"):
                        total_wind += flow_sum
                    elif mapped_component_name.startswith("Pumpspeicherkraftwerk"):
                        total_pumpspeicher_ein += flow_sum
                    elif mapped_component_name.startswith("Luft-Waermepumpe"):
                        elec_WP_flow = flow_sum
                    
                    bus_data.append({
                        'Bus': mapped_bus_name,
                        'From': mapped_bus_name + " Bus",
                        'To': mapped_component_name,
                        'Flow': flow_sum,
                        'Unit': 'MWh',
                        'Type': 'Bus sequence'
                    })
                if bus_data:
                    bus_df = pd.DataFrame(bus_data)
                    data_frames.append(bus_df)

            # process components using reference structure
            for component_name, reference_buses in reference_component_structure.items():
                mapped_component_name = map_name(component_name, component_name_mapping)
                component_data = []
                for bus_name in reference_buses:
                    mapped_bus_name = map_name(bus_name, bus_name_mapping)
                    if component_name in component_sequences and bus_name in component_sequences[component_name] and bus_name != 'None' :
                        flow_sum = component_sequences[component_name][bus_name]['flow'].sum()
                    else:
                        flow_sum = 0
                    if mapped_component_name.startswith("PV_"):
                        total_pv += flow_sum
                    elif mapped_component_name.startswith("Wind_"):
                        total_wind += flow_sum
                    elif mapped_component_name.startswith("Pumpspeicherkraftwerk"):
                        total_pumpspeicher_aus += flow_sum
                    elif mapped_component_name.startswith("Import - Stromboerse"):
                        import_strom += flow_sum
                    elif mapped_component_name.startswith("Luft-Waermepumpe"):
                        WP_heat_flow = flow_sum
                    
                    component_data.append({
                        'Bus': mapped_bus_name,
                        'From': mapped_component_name,
                        'To': mapped_bus_name + " Bus",
                        'Flow': flow_sum,
                        'Unit': 'MWh',
                        'Type': 'Component sequence'
                    })
                    
                if component_data:
                    component_df = pd.DataFrame(component_data)
                    data_frames.append(component_df)

            # combine all data frames for the scenario
            if data_frames:
                combined_df = pd.concat(data_frames)

                # sort teh excel according to bus name 
                separated_df = pd.DataFrame()
                for bus_name in combined_df['Bus'].unique():
                    bus_df = combined_df[combined_df['Bus'] == bus_name]
                    separated_df = pd.concat([separated_df, bus_df, pd.DataFrame([[]]*6)])

                # create sheet for the scenario
                sheet_name = f"{permutation}_{scenario_num}"
                df_model_info = pd.DataFrame({
                    'Model ID': [model_name],
                    'Scenario Number': [permutation + '_' + str(scenario_num)]
                })

                # write the data to the sheet
                df_model_info.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=0)
                separated_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=20)
                
                if not region:
                    workbook = writer.book
                    scenario_sheet = workbook[sheet_name]
                    scenario_sheet['A7'] = "Import Strom flow"
                    scenario_sheet['B7'] = import_strom
                    scenario_sheet['A8'] = "Total PV Flow"
                    scenario_sheet['B8'] = total_pv
                    scenario_sheet['A9'] = "Total Wind Flow"
                    scenario_sheet['B9'] = total_wind
                    scenario_sheet['A10'] = "Total Pumpspeicher Eingangsflow"
                    scenario_sheet['B10'] = total_pumpspeicher_ein
                    scenario_sheet['A11'] = "Total Pumpspeicher Ausgangsflow"
                    scenario_sheet['B11'] = total_pumpspeicher_aus
                    scenario_sheet['A12'] = "Umweltwaermemenge_Luft_waermepumpe"
                    scenario_sheet['B12'] =  WP_heat_flow - elec_WP_flow 
                    sheets_created = True
            
    # remove dummy sheet
    workbook = load_workbook(output_path)
    if 'Dummy_Sheet' in workbook.sheetnames and sheets_created:
        del workbook['Dummy_Sheet']
    

    # add dropdowns and hyperlinks in the Main_Sheet
    main_sheet = workbook["Main_Sheet"]
    main_sheet['A2'] = "Year"
    main_sheet['B2'] = str(year)
    main_sheet['A3'] = "Select scenario:"
    main_sheet['B3']= sheet_name


    dv = DataValidation(
            type="list",
            formula1=f'"{",".join([f"{permutation}_{s}" for s in scenarios])}"',  # Reference scenario names
            showDropDown=False
        )

    main_sheet.add_data_validation(dv)
    dv.add(main_sheet["B3"])
        
    # use Indirect to set live links
    for row in range(7, 1500):  
            for col in range(1, 20):  
                cell = main_sheet.cell(row=row, column=col)
                cell.value = f'=IF(INDIRECT(B3 & "!{get_column_letter(col)}{row}")="", "", INDIRECT(B3 & "!{get_column_letter(col)}{row}"))'

    # Adjust column widths and save
    adjust_column_width_for_all_sheets(workbook)
    workbook.save(output_path)

    print(f"Sankey excel saved to {output_path}")
    

    
def calc_CO2_emission (year,cleaned_sequences):
    """
    This function calculates the costs for importing the energy based on price timeseries and flow values.
    
    Parameters
    ----------
    year : int
       The year for which the calculation is performed.
    cleaned_sequences : dict
        Dictionary with flow values from components to buses.
    
    Returns
    -------
    co2_emissions : dict
        Dictionary containing total CO₂ emissions for each scenario.
    """
    
    co2_emissions = {}
    scalars = read_input_files(folder_name='data/scalars', sub_folder_name=None)
    
    # Mapping for CO₂ factors lookup
    co2_factors = {
        'Import_Electricity': scalars['System_configurations_2024']['System'][f'Emission_Strom_{year}'],
        'Import_Gas': scalars['System_configurations_2024']['System']['Emission_Erdgas'],
        'Import_Oil': scalars['System_configurations_2024']['System']['Emission_Oel'],
        'Import_brown_coal': scalars['System_configurations_2024']['System']['Emission_Braunkohle'],
        'Import_hard_coal': scalars['System_configurations_2024']['System']['Emission_Steinkohle'],
    }
    region_suffixes = ['_n', '_s', '_e', '_m']
    for scenario, components_data in cleaned_sequences.items():
        total_CO2_emission = 0
        scenario_co2_emissions = {}
    
        # Iterate through components
        for component, bus_data in components_data.items():
            
            if component.startswith("Import_"):
                base_component = next((component[:-len(suffix)] for suffix in region_suffixes if component.endswith(suffix)), component)
                # Split only if the last part is a known suffix
            else:
                base_component = component
                
            if base_component in co2_factors:
                co2_factor = co2_factors[base_component]  
    
                if isinstance(bus_data, dict):
                    for bus_name, df in bus_data.items():
                        if isinstance(df, pd.DataFrame) and 'flow' in df.columns:
                            flow_series = df['flow'].to_numpy()
                        elif isinstance(df, pd.Series):
                            flow_series = df.to_numpy()
                        else:
                            continue
    
                        # Calculate CO₂ emissions
                        co2_emission = (flow_series.sum()* co2_factor)/1000     #'conversion in tonnes'
    
                        # Store results
                        scenario_co2_emissions[component] = co2_emission
                        total_CO2_emission += co2_emission
    
        scenario_co2_emissions["total_CO2_emission"] = total_CO2_emission  # Store total CO₂ emissions
        co2_emissions[scenario] = scenario_co2_emissions
    
    return co2_emissions

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
    