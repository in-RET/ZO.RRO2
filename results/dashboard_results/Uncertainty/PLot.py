# -*- coding: utf-8 -*-
"""
Created on Wed Jul  8 11:52:39 2026

@author: rbala
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings('ignore')

# Load the data from the CSV files
installed_cap_data = pd.read_csv('Installed_cap.csv', sep=';', decimal=',', skiprows=[0,1])
storage_data = pd.read_csv('Storage.csv', sep=';', decimal=',', skiprows=[0,1])

# Clean data - replace string 'None' with NaN and convert to numeric
def clean_dataframe(df):
    """Clean dataframe by converting string 'None' to NaN and ensuring numeric types"""
    df_clean = df.copy()
    
    # Ensure Component and Bus columns are strings
    if 'Component' in df_clean.columns:
        df_clean['Component'] = df_clean['Component'].astype(str)
    if 'Bus' in df_clean.columns:
        df_clean['Bus'] = df_clean['Bus'].astype(str)
    
    for col in df_clean.columns:
        if col not in ['Component', 'Bus', df_clean.columns[0]]:
            # Replace 'None' with NaN
            df_clean[col] = df_clean[col].replace('None', np.nan)
            # Convert to numeric, forcing non-numeric to NaN
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    
    return df_clean

installed_cap_data = clean_dataframe(installed_cap_data)
storage_data = clean_dataframe(storage_data)

# Define the category list
category_list = {
    'Stromspeicher': ['Battery', 'Li-Ion_Battery', 'Natrium_Battery', 'Red-OX_Battery'],
    'Biogas - BHKW': ['Biogas- BHKW'],
    'Biogas - Aufbereitungsanlage': ['Biogas_feedin_existing'],
    'Biogas - Methanisierungsanlage': ['Biogas_feedin_new'],
    'Biomasse-to-fuel': ['BtL_Holz', 'BtL_substrat'],
    'Import - Biowaste': ['Import_solid_fuel'],
    'Biomasse als Festbrennstoff': ['BioTransformer'],
    'Biomasse - KW': ['Biomasse_elec'],
    'Biomasse - HKW': ['Biomasse_elec_heat'],
    'Biomasse - HW': ['Biomasse_heat'],
    'Import - Holz': ['Import_Wood'],
    'Waermespeicher': ['Heat storage_dist_heat', 'Heat storage_seasonal'],
    'Heizstab': ['Electric boiler'],
    'GuD - KW': ['GuD'],
    'Waermepumpen': ['Heatpump', 'Heatpump_air', 'Heatpump_recovery_heat', 'Heatpump_water'],
    'Nachheizung für Speicher': ['Preheater- Electric boiler', 'Preheater- WP'],
    'Import - Strom': ['Import_Electricity'],
    'Pumpspeicherkraftwerk': ['Pumped_hydro_storage', 'Pumped_hydro_storage_bestand', 'Pumped_hydro_technology'],
    'Brennstoffzelle': ['Fuelcell'],
    'Laufwasser - KW': ['Hydro power plant'],
    'PV': ['PV_open_east', 'PV_open_middle', 'PV_open_north', 'PV_open_swest', 'PV_rooftop_east', 'PV_rooftop_middle', 'PV_rooftop_north', 'PV_rooftop_swest'],
    'WIND': ['Wind_east', 'Wind_middle', 'Wind_north', 'Wind_swest'],
    'Elektrolyse': ['Electrolysis'],
    'Power-to-fuel': ['PtL'],
    'Umweltwaerme': ['UW'],
    'Gasspeicher': ['Gas_storage'],
    'Import - Gas': ['Import_Gas'],
    'Wasserstoffspeicher': ['H2_storage'],
    'Methanisierung': ['Methanisation'],
    'Import - Wasserstoff': ['Import_Hydrogen'],
    'Import - Oil': ['Import_Oil'],
    'Import - Kraftstoff': ['Import_Synthetic_fuel'],
    'Import - Braunkohle': ['Import_brown_coal'],
    'Abwärme': ['AW'],
    'Netzverluste': ['Netzverluste']
}

# Process the installed capacity data
def process_installed_capacity(df):
    """Process the installed capacity data from the CSV"""
    # Extract scenario names from the first row
    scenarios = [col for col in df.columns if col not in ['Component', 'Bus']]
    
    # Create a dictionary to store results by scenario
    results = {}
    
    for scenario in scenarios:
        scenario_data = {}
        for idx, row in df.iterrows():
            component = str(row['Component']).strip()  # Ensure string
            bus = str(row['Bus']).strip()  # Ensure string
            value = row[scenario]
            
            # Skip NaN values
            if pd.isna(value) or value == 0:
                continue
            
            # Create a key for the component
            if bus == 'None':
                key = component
            else:
                key = f"{component}_{bus}" if component != bus else component
            
            scenario_data[key] = value
        
        results[scenario] = scenario_data
    
    return results, scenarios

# Process storage data
def process_storage(df):
    """Process storage data from the CSV"""
    scenarios = [col for col in df.columns if col != df.columns[0]]
    
    results = {}
    for scenario in scenarios:
        scenario_data = {}
        for idx, row in df.iterrows():
            component = str(row.iloc[0]).strip()  # Ensure string
            value = row[scenario]
            
            # Skip NaN or zero values
            if pd.isna(value) or value == 0:
                continue
            
            scenario_data[component] = value
        
        results[scenario] = scenario_data
    
    return results, scenarios

# Process the data
installed_results, installed_scenarios = process_installed_capacity(installed_cap_data)
storage_results, storage_scenarios = process_storage(storage_data)

# Create category mapping function
def get_category_for_component(component_name):
    """Map a component to its category based on category_list"""
    component_name = str(component_name).strip()  # Ensure string
    for category, components in category_list.items():
        for comp in components:
            if comp in component_name:
                return category
    return 'Other'

# Create a unified dataset with categories
def create_unified_dataset(installed_data, storage_data, scenarios):
    """Combine installed capacity and storage data into a unified dataset"""
    unified_data = {}
    
    for scenario in scenarios:
        scenario_dict = {}
        
        # Add installed capacity data
        if scenario in installed_data:
            for comp, value in installed_data[scenario].items():
                category = get_category_for_component(comp)
                if category not in scenario_dict:
                    scenario_dict[category] = {}
                scenario_dict[category][comp] = value
        
        # Add storage data
        if scenario in storage_data:
            for comp, value in storage_data[scenario].items():
                category = get_category_for_component(comp)
                if category not in scenario_dict:
                    scenario_dict[category] = {}
                scenario_dict[category][comp] = value
        
        unified_data[scenario] = scenario_dict
    
    return unified_data

# Get all scenarios
all_scenarios = list(set(installed_scenarios + storage_scenarios))

# Create unified dataset
unified_data = create_unified_dataset(installed_results, storage_results, all_scenarios)

# Define main categories for the heatmap
category_map = {
    'Erneuerbare Erzeugung': ['PV', 'WIND', 'Laufwasser - KW'],
    'Bioenergie': [
        'Biogas - BHKW', 'Biogas - Aufbereitungsanlage',
        'Biogas - Methanisierungsanlage', 'Biomasse - HKW',
        'Biomasse - HW', 'Biomasse - KW',
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
        'Umweltwaerme', 'Abwärme'
    ],
    'Konventionelle Erzeugung': ['GuD - KW'],
    'Importe': [
        'Import - Strom', 'Import - Gas', 'Import - Wasserstoff',
        'Import - Oil', 'Import - Kraftstoff', 'Import - Holz',
        'Import - Biowaste', 'Import - Braunkohle'
    ],
    'Netzinfrastruktur': ['Netzverluste']
}

# Function to get components for a category
def get_components_for_category(unified_data, category):
    """Get all components belonging to a category across all scenarios"""
    all_components = set()
    for scenario, data in unified_data.items():
        if category in data:
            all_components.update(data[category].keys())
    return sorted(all_components)

# Create the heatmap data structure
def create_heatmap_data(unified_data, category_map):
    """Create a DataFrame suitable for heatmap plotting"""
    # Get all scenarios
    scenarios = sorted(unified_data.keys())
    
    # Create a list to store rows
    rows = []
    labels = []
    
    for category, component_patterns in category_map.items():
        # Get all actual components for this category
        actual_components = get_components_for_category(unified_data, category)
        
        # Add category header
        rows.append([np.nan] * len(scenarios))
        labels.append(rf"$\bf{{{category}}}$")
        
        # Process each actual component
        for comp in actual_components:
            labels.append(comp)
            
            # Get values for this component across scenarios
            values = []
            for scenario in scenarios:
                value = 0
                if category in unified_data.get(scenario, {}):
                    value = unified_data[scenario][category].get(comp, 0)
                values.append(value)
            
            rows.append(values)
        
        # Add spacer row
        rows.append([np.nan] * len(scenarios))
        labels.append("")
    
    return pd.DataFrame(rows, index=labels, columns=scenarios)

# Create the heatmap data
heatmap_df = create_heatmap_data(unified_data, category_map)

# Replace NaN with 0 for plotting (but keep NaN for spacing)
heatmap_df_clean = heatmap_df.fillna(0)

# Plot the heatmap
plt.figure(figsize=(20, 28))

# Create the heatmap
ax = sns.heatmap(
    heatmap_df_clean,
    cmap="YlOrRd",
    vmin=0,
    vmax=heatmap_df_clean.max().max(),
    linewidths=0.3,
    linecolor="white",
    annot=True,
    fmt=".1f",
    annot_kws={"size": 7},
    cbar_kws={"label": "Installed Capacity (MW) / Storage Capacity (MWh)"},
    square=False
)

# Rotate x-axis labels
plt.xticks(rotation=45, ha='right', fontsize=9)
plt.yticks(fontsize=8)

# Set title and labels
plt.title("Installed Capacity and Storage by Scenario and Category", fontsize=16, fontweight='bold')
plt.xlabel("Scenarios", fontsize=12)
plt.ylabel("Components and Categories", fontsize=12)

# Add colored bars for categories
colors = plt.cm.tab20(np.linspace(0, 1, len(category_map)))
color_idx = 0
for category, component_patterns in category_map.items():
    actual_components = get_components_for_category(unified_data, category)
    if actual_components:
        # Find the row index for this category
        category_indices = heatmap_df.index[heatmap_df.index == rf"$\bf{{{category}}}$"]
        if len(category_indices) > 0:
            pos = heatmap_df.index.get_loc(category_indices[0])
            n_components = len(actual_components)
            # Add a colored rectangle on the left side
            rect = mpatches.Rectangle(
                (-1.5, pos - 0.5), 0.5, n_components + 1,
                facecolor=colors[color_idx % len(colors)],
                alpha=0.4,
                transform=ax.transData
            )
            ax.add_patch(rect)
            color_idx += 1

# Adjust layout
plt.tight_layout()
plt.show()

# Create a second heatmap focusing only on key categories (simplified)
def create_simplified_heatmap(unified_data, category_map):
    """Create a simplified heatmap aggregated by category only"""
    scenarios = sorted(unified_data.keys())
    
    rows = []
    labels = []
    
    for category, component_patterns in category_map.items():
        # Get total for this category across all components
        values = []
        for scenario in scenarios:
            total = 0
            if category in unified_data.get(scenario, {}):
                for key, value in unified_data[scenario][category].items():
                    total += value
            values.append(total)
        
        rows.append(values)
        labels.append(category)
    
    return pd.DataFrame(rows, index=labels, columns=scenarios)

# Create and plot simplified heatmap
simplified_df = create_simplified_heatmap(unified_data, category_map)

plt.figure(figsize=(16, 12))

ax = sns.heatmap(
    simplified_df,
    cmap="viridis",
    vmin=0,
    vmax=simplified_df.max().max(),
    linewidths=0.5,
    linecolor="white",
    annot=True,
    fmt=".1f",
    annot_kws={"size": 11},
    cbar_kws={"label": "Total Installed Capacity (MW) / Storage Capacity (MWh)"}
)

plt.title("Aggregated Capacity by Category and Scenario", fontsize=16, fontweight='bold')
plt.xlabel("Scenarios", fontsize=12)
plt.ylabel("Technology Categories", fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# Create a detailed heatmap for storage technologies specifically
def create_storage_heatmap(unified_data):
    """Create a heatmap focusing on storage technologies"""
    storage_categories = ['Stromspeicher', 'Pumpspeicherkraftwerk', 'Gasspeicher', 
                         'Wasserstoffspeicher', 'Waermespeicher']
    
    scenarios = sorted(unified_data.keys())
    
    rows = []
    labels = []
    
    for category in storage_categories:
        # Add category header
        rows.append([np.nan] * len(scenarios))
        labels.append(rf"$\bf{{{category}}}$")
        
        # Get components in this category
        actual_components = get_components_for_category(unified_data, category)
        
        if actual_components:
            for comp in sorted(actual_components):
                values = []
                for scenario in scenarios:
                    value = 0
                    if category in unified_data.get(scenario, {}):
                        value = unified_data[scenario][category].get(comp, 0)
                    values.append(value)
                
                rows.append(values)
                labels.append(comp)
        
        # Add spacer
        rows.append([np.nan] * len(scenarios))
        labels.append("")
    
    return pd.DataFrame(rows, index=labels, columns=scenarios)

# Create and plot storage heatmap
storage_heatmap_df = create_storage_heatmap(unified_data)
storage_heatmap_clean = storage_heatmap_df.fillna(0)

plt.figure(figsize=(16, 14))

ax = sns.heatmap(
    storage_heatmap_clean,
    cmap="coolwarm",
    vmin=0,
    vmax=storage_heatmap_clean.max().max(),
    linewidths=0.5,
    linecolor="white",
    annot=True,
    fmt=".1f",
    annot_kws={"size": 9},
    cbar_kws={"label": "Storage Capacity (MWh)"}
)

plt.title("Storage Technologies Comparison Across Scenarios", fontsize=16, fontweight='bold')
plt.xlabel("Scenarios", fontsize=12)
plt.ylabel("Storage Components", fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# Create a normalized heatmap to show relative changes
def create_normalized_heatmap(unified_data, category_map):
    """Create a heatmap showing normalized values relative to the maximum for each component"""
    scenarios = sorted(unified_data.keys())
    
    rows = []
    labels = []
    
    for category, component_patterns in category_map.items():
        # Get actual components for this category
        actual_components = get_components_for_category(unified_data, category)
        
        # Add category header
        rows.append([np.nan] * len(scenarios))
        labels.append(rf"$\bf{{{category}}}$")
        
        # Process each actual component
        for comp in actual_components:
            labels.append(comp)
            
            # Get values for this component across scenarios
            values = []
            for scenario in scenarios:
                value = 0
                if category in unified_data.get(scenario, {}):
                    value = unified_data[scenario][category].get(comp, 0)
                values.append(value)
            
            # Normalize values
            max_val = max(values) if max(values) > 0 else 1
            normalized_values = [v / max_val for v in values]
            rows.append(normalized_values)
        
        # Add spacer row
        rows.append([np.nan] * len(scenarios))
        labels.append("")
    
    return pd.DataFrame(rows, index=labels, columns=scenarios)

# Create and plot normalized heatmap
normalized_df = create_normalized_heatmap(unified_data, category_map)
normalized_clean = normalized_df.fillna(0)

plt.figure(figsize=(20, 28))

ax = sns.heatmap(
    normalized_clean,
    cmap="RdBu_r",
    vmin=0,
    vmax=1,
    linewidths=0.3,
    linecolor="white",
    annot=False,
    cbar_kws={"label": "Normalized Capacity (0-1)"},
    square=False
)

plt.title("Normalized Capacity by Scenario (Relative to Maximum per Component)", fontsize=16, fontweight='bold')
plt.xlabel("Scenarios", fontsize=12)
plt.ylabel("Components and Categories", fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# Print summary statistics
print("\n" + "="*50)
print("SUMMARY STATISTICS")
print("="*50 + "\n")

for scenario in sorted(unified_data.keys()):
    total_capacity = 0
    storage_capacity = 0
    generation_capacity = 0
    
    for category, components in unified_data[scenario].items():
        for comp, value in components.items():
            total_capacity += value
            if category in ['Stromspeicher', 'Pumpspeicherkraftwerk', 'Gasspeicher', 
                          'Wasserstoffspeicher', 'Waermespeicher']:
                storage_capacity += value
            else:
                generation_capacity += value
    
    print(f"Scenario: {scenario}")
    print(f"  Total Capacity: {total_capacity:,.2f} MW/MWh")
    print(f"  Generation Capacity: {generation_capacity:,.2f} MW")
    print(f"  Storage Capacity: {storage_capacity:,.2f} MWh")
    if generation_capacity > 0:
        print(f"  Storage/Generation Ratio: {(storage_capacity/generation_capacity):.2f}")
    print()

# Identify scenarios with highest and lowest capacities
total_capacities = {}
for scenario, data in unified_data.items():
    total_capacities[scenario] = sum(sum(comp.values()) for comp in data.values())

if total_capacities:
    max_scenario = max(total_capacities.items(), key=lambda x: x[1])
    min_scenario = min(total_capacities.items(), key=lambda x: x[1])
    
    print(f"\nScenario with highest capacity: {max_scenario[0]}")
    print(f"  Total capacity: {max_scenario[1]:,.2f} MW/MWh")
    print(f"\nScenario with lowest capacity: {min_scenario[0]}")
    print(f"  Total capacity: {min_scenario[1]:,.2f} MW/MWh")

# Print top 5 components with highest capacity
print("\n" + "="*50)
print("TOP 5 COMPONENTS BY TOTAL CAPACITY ACROSS ALL SCENARIOS")
print("="*50 + "\n")

component_totals = {}
for scenario, data in unified_data.items():
    for category, components in data.items():
        for comp, value in components.items():
            if comp not in component_totals:
                component_totals[comp] = 0
            component_totals[comp] += value

# Sort and print top 5
sorted_components = sorted(component_totals.items(), key=lambda x: x[1], reverse=True)[:10]
for comp, total in sorted_components:
    category = get_category_for_component(comp)
    print(f"{comp} ({category}): {total:,.2f} MW/MWh")