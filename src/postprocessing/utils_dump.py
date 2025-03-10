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
workdir = os.getcwd()
my_path = os.path.abspath(os.path.dirname(__file__))
def get_dump_file_path(year, variation, model_name, scenario_num):
    return os.path.join(workdir, 'dumps',
                         f"{year}_{variation}",
                         f"{model_name}_{year}_{variation}_{scenario_num}.dump")
    

def load_results_from_dump(dump_path):
    energysystem = solph.EnergySystem()
    energysystem.restore(my_path, dump_path)
    return energysystem.results["main"]

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
    
        
        elif isinstance(key[0], (solph.components.Source, solph.components.Converter, solph.components.Sink, solph.components.GenericStorage)):
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

def calculate_investment_costs(epc_costs, all_component_scalars):
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
        "Biogas":                   ("biogas_combined_heat_and_power_plant", "Electricity"),
        "Biogas_feedin_existing":   ("biomethane_injection_plant", "Gas"),
        "Biogas_feedin_new":        ("biogas_upgrading_plant","Gas"),
        "Biomasse_elec":            ("biomass_combined_heat_and_power_plant", "Electricity"),
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
    }


    for scenario, components in all_component_scalars.items():
        investment_costs[scenario] = {}
        total_scenario_cost = 0

        for component, (epc_category, value_type) in component_mapping_info.items():
            investk = epc_costs.get(epc_category, {}).get("investk", 0)
            operatk = epc_costs.get(epc_category, {}).get("betriebsk", 0)

            # Check if component exists in all_components, otherwise set value to 0
            if component in components:
                value = components[component].get(value_type, 0)  # Get electricity or dist_heating value
            else:
                value = 0  # Fail-safe: Missing component defaults to zero

            total_component_investment = (value * investk)  + (value * operatk)# Compute cost
            investment_costs[scenario][component] = total_component_investment
            total_scenario_cost += total_component_investment
        investment_costs[scenario]['total'] = sum

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

def calc_energyimport_cost (import_price,cleaned_sequences):
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
        scenario_import_costs["Total_Import_Cost"] = sum(scenario_import_costs.values())
        # Store the import costs for this scenario in the main dictionary
        import_costs[scenario] = scenario_import_costs
    
    return import_costs

def calc_energyexport_cost(import_price,cleaned_sequences_bus):
    
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
    
    # Define mapping for price lookup
    price_mapping = {
        'Export_Electricity': 'export_electricity_price',
        'Export_Hydrogen': 'export_hydrogen_price',
    }
    for scenario, bus_data in cleaned_sequences_bus.items():
        # Initialize the import costs for this scenario
        scenario_export_costs = {}
        
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
        scenario_export_costs["Total_Export_Cost"] = sum(scenario_export_costs.values())
        # Store the import costs for this scenario in the main dictionary
        export_costs[scenario] = scenario_export_costs
    return export_costs