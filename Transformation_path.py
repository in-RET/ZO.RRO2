# -*- coding: utf-8 -*-
"""
Created on Mon Jun 22 10:40:46 2026

@author: rbala
"""

from pathlib import Path
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import re
from src.postprocessing.plot_report_utils import rename_index_with_category
import os

workdir = os.getcwd()
folder_name = 'Uncertainty'
base_folder = os.path.join(workdir,'results', 'dashboard_results', folder_name)

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

component_results = {}
storage_results = {}

for folder in Path(base_folder).iterdir():

    if not folder.is_dir():
        continue

    name = folder.name

    component_file = folder / "component_capacity_comparison.csv"
    storage_file = folder / "peak_storage_flow_comparison.csv"

    if component_file.exists():

        df = pd.read_csv(component_file, decimal= ',', sep =';', index_col = 0, skiprows = [0])
        component_scalar_df = rename_index_with_category(df, category_list)
        component_results[name] = component_scalar_df

    if storage_file.exists():

        df = pd.read_csv(storage_file, decimal= ',', sep =';', index_col = 0, skiprows = [0])
        storage_scalar_df = rename_index_with_category(df, category_list)
        storage_results[name] = storage_scalar_df
        
    cost = folder / "Costs.csv"
    df_costs = pd.read_csv(cost, decimal= '.', sep =',', index_col = 0)

category_map = {
    'Erneuerbare Erzeugung': ['PV', 'WIND', 'Laufwasser - KW', 'ST'],

    'Bioenergie': [
        'Biogas- BHKW', 'Biogas - Aufbereitungsanlage',
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
        'Umweltwaerme', 'Umgebungsluft', 'Abwärme'
    ],

    'Konventionelle Erzeugung': ['GuD - KW'],

    'Importe': [
        'Import - Strom', 'Import -Gas', 'Import - Wasserstoff',
        'Import - Oil', 'Import - Kraftstoff', 'Import - Holz',
        'Import - Biowaste', 'Import - Braunkohle', 'Import_hard_coal'
    ],

    'Netzinfrastruktur': [
        'Grid_losses', 'East<->Middle', 'HS<->East',
        'HS<->Middle', 'HS<->North', 'HS<->Swest',
        'Middle<->Swest', 'North<->Middle', 'Netzverluste'
    ]
}


# HEATMAP PLOTTING

for category, techs in category_map.items():

    # choose dataset
    if category == "Speichertechnologien":
        source_dict = storage_results
    else:
        source_dict = component_results

    iterations = sorted(source_dict.keys())

    first_df = next(iter(source_dict.values()))
    years = first_df.columns#sorted(first_df.columns, key=lambda x: int(str(x)))
    
    for k in source_dict:
        source_dict[k] = source_dict[k].reindex(columns=years)
 
    
    rows = []
    labels = []
    
    for tech in techs:
    
        # technology header row
        rows.append([np.nan] * len(years))
        labels.append(rf"$\bf{{{tech}}}$")
    
        for it in iterations:
    
            df = source_dict[it]
    
            if tech in df.index:
                values = df.loc[tech].values
            else:
                values = np.zeros(len(years))
    
            rows.append(values)
            labels.append(f"{it}")
    
        # spacer row
        rows.append([np.nan] * len(years))
        labels.append("")
    
    heatmap_df = pd.DataFrame(
        rows,
        index=labels,
        columns=years
    )
    
    new_index = []

    row_counter = 0
    
    for tech in techs:
    
        # bold tech header (mathtext)
        new_index.append("")#rf"$\bf{{{tech}}}$")
    
        row_counter += 1
    
        for it in iterations:
            new_index.append(f"{it}")
            row_counter += 1
    
        # spacer row
        new_index.append("")
        row_counter += 1
    
    heatmap_df.index = new_index
    
    plt.figure(figsize=(12, max(6, len(new_index) * 0.35)))

    ax = sns.heatmap(
        heatmap_df,
        cmap="jet",
        vmin=0,
        vmax=heatmap_df.max().max(),
        linewidths=0.3,
        linecolor="white",
        annot=True,
        fmt=".0f",
        annot_kws={"size": 13},
        cbar_kws={"label": "Leistung in MW / Kapazität in MWh"}
    )
          
    for i, tech in enumerate(techs):

        row = i * (len(iterations) + 2)  # header row position
    
        ax.text(
            len(years) / 2,      # center of heatmap
            row + 0.5,           # center of the header row
            tech,
            ha="center",
            va="center",
            fontweight="bold",
            fontsize=12,
            color="black"
        )
    plt.title(rf"$\bf{{{category}}}$")
    #plt.xlabel("Jahr")

    plt.tight_layout()
    plt.show()
     
#%%  COST Comparison Plot

df = df_costs

base_scenario = df[df['Scenario'] == 'Base Scenario'].iloc[0]
base_total = base_scenario['Total Costs (Mio. €)']
base_investment = base_scenario['Investment Costs (Mio. €)']
base_variable = base_scenario['Variable Costs (Mio. €)']
base_profit = base_scenario['Profits (Mio. €)']

df['Total Costs (%)'] = ((df['Total Costs (Mio. €)'] - base_total) / base_total * 100)
df['Investment Costs (%)'] = ((df['Investment Costs (Mio. €)'] - base_investment) / base_investment * 100)
df['Variable Costs (%)'] = ((df['Variable Costs (Mio. €)'] - base_variable) / base_variable * 100)
df['Profits (%)'] = ((df['Profits (Mio. €)'] - base_profit) / abs(base_profit) * 100)
df_sorted = df.sort_values('Total Costs (%)', ascending=True)
df_sorted_all = df_sorted.copy()

fig = plt.figure(figsize=(20, 16))
colors_positive = '#E74C3C'  # Red for cost increases
colors_negative = '#2ECC71'  # Green for cost decreases


# Total Cost Change Relative to Base Scenario

ax1 = plt.subplot(2, 2, 1)
df_plot1 = df_sorted.copy()

colors = ['#E74C3C' if x > 0 else '#2ECC71' for x in df_plot1['Total Costs (%)']]
bars = ax1.barh(df_plot1['Scenario'], df_plot1['Total Costs (%)'], 
                color=colors, edgecolor='black', linewidth=0.8, alpha=0.8)


for i, (bar, value) in enumerate(zip(bars, df_plot1['Total Costs (%)'])):
    offset = 0.8 if value > 0 else -0.8
    ha = 'left' if value > 0 else 'right'
    ax1.text(value + offset, i, f'{value:+.2f}%', 
             va='center', ha=ha, fontsize=11, fontweight='bold')

ax1.axvline(x=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)

ax1.set_xlabel('Change from BS (%)', fontsize=13, fontweight='bold')
ax1.set_title('Total Cost', fontsize=15, fontweight='bold', pad=15)
ax1.grid(axis='x', alpha=0.2, linestyle='--')
x_max = max(abs(df_plot1['Total Costs (%)'].max()), abs(df_plot1['Total Costs (%)'].min())) * 1.2
ax1.set_xlim(-x_max, x_max)


# Profit Change Relative to Base Scenario (top-right)

ax2 = plt.subplot(2, 2, 2)
df_plot2 = df.sort_values('Profits (%)', ascending=False)
colors_profit = ['#2ECC71' if x > 0 else '#E74C3C' for x in df_plot2['Profits (%)']]
bars = ax2.barh(df_plot2['Scenario'], df_plot2['Profits (%)'], 
                color=colors_profit, edgecolor='black', linewidth=0.8, alpha=0.8)

for i, (bar, value) in enumerate(zip(bars, df_plot2['Profits (%)'])):
    offset = 0.8 if value > 0 else -0.8
    ha = 'left' if value > 0 else 'right'
    ax2.text(value + offset, i, f'{value:+.2f}%', 
             va='center', ha=ha, fontsize=11, fontweight='bold')

ax2.axvline(x=0, color='black', linestyle='-', linewidth=1.5, alpha=0.7)

ax2.set_xlabel('Change from BS (%)', fontsize=13, fontweight='bold')
ax2.set_title('Profit', fontsize=15, fontweight='bold', pad=15)
ax2.grid(axis='x', alpha=0.2, linestyle='--')

x_max_profit = max(abs(df_plot2['Profits (%)'].max()), abs(df_plot2['Profits (%)'].min())) * 1.2
ax2.set_xlim(-x_max_profit, x_max_profit)


# Investment vs Variable Cost Changes (bottom-left)

ax3 = plt.subplot(2, 2, 3)

df_plot3 = df.copy()
scatter = ax3.scatter(df_plot3['Investment Costs (%)'], 
                     df_plot3['Variable Costs (%)'],
                     s=abs(df_plot3['Total Costs (%)']) * 80 + 100,  # Bubble size
                     c=df_plot3['Total Costs (%)'],  # Color by total change
                     cmap='RdYlGn_r',
                     alpha=0.7,
                     edgecolors='black',
                     linewidth=1.5,
                     vmin=-10, vmax=10)

# Add labels for each point
for i, row in df_plot3.iterrows():
    if row['Scenario'] != 'Base Scenario':
        # Shorten scenario names for better readability
        label = row['Scenario'].replace('No ', '').replace(' (B, H2_sto, Sea_Sto)', '')
        label = label.replace('Base Scenario', 'Base')
        ax3.annotate(label,
                    (row['Investment Costs (%)'], row['Variable Costs (%)']),
                    fontsize=9, ha='center', va='bottom', fontweight='bold')

# Mark base scenario
base_point = df_plot3[df_plot3['Scenario'] == 'Base Scenario']
ax3.scatter(base_point['Investment Costs (%)'], base_point['Variable Costs (%)'],
           s=300, c='gold', marker='*', edgecolors='black', linewidth=2, 
           label='BS', zorder=5)

# Add quadrant lines
ax3.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.4)
ax3.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.4)

# Add quadrant labels
props = dict(boxstyle='round', facecolor='wheat', alpha=0.6)
ax3.text(0.85, 0.85, 'High Investment\nHigh Variable', transform=ax3.transAxes, 
         fontsize=9, ha='center', va='center', bbox=props)
ax3.text(0.15, 0.85, 'Low Investment\nHigh Variable', transform=ax3.transAxes, 
         fontsize=9, ha='center', va='center', bbox=props)
ax3.text(0.85, 0.15, 'High Investment\nLow Variable', transform=ax3.transAxes, 
         fontsize=9, ha='center', va='center', bbox=props)
ax3.text(0.15, 0.15, 'Low Investment\nLow Variable', transform=ax3.transAxes, 
         fontsize=9, ha='center', va='center', bbox=props)

# Customize
ax3.set_xlabel('Investment Cost Change from BS (%)', fontsize=13, fontweight='bold')
ax3.set_ylabel('Variable Cost Change from BS (%)', fontsize=13, fontweight='bold')
ax3.set_title('Investment vs Variable Cost', fontsize=15, fontweight='bold', pad=15)
ax3.grid(alpha=0.15)
ax3.legend(loc='upper left', fontsize=10)

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax3)
cbar.set_label('Total Cost Change from BS (%)', fontsize=11, fontweight='bold')

# Set consistent axis limits
max_val = max(abs(df_plot3['Investment Costs (%)'].max()), 
              abs(df_plot3['Investment Costs (%)'].min()),
              abs(df_plot3['Variable Costs (%)'].max()),
              abs(df_plot3['Variable Costs (%)'].min())) * 1.2
ax3.set_xlim(-max_val, max_val)
ax3.set_ylim(-max_val, max_val)

# Heatmap of Relative Changes from Base (bottom-right)

ax4 = plt.subplot(2, 2, 4)
heatmap_data = df.set_index('Scenario')[['Total Costs (%)', 'Investment Costs (%)', 
                                         'Variable Costs (%)', 'Profits (%)']]
heatmap_data = heatmap_data.sort_values('Total Costs (%)', ascending=False)
heatmap_data.columns = ['Total Cost', 'Investment', 'Variable', 'Profit']

sns.heatmap(heatmap_data, 
            annot=True, 
            fmt='+.2f', 
            cmap='RdBu_r',
            center=0,
            ax=ax4,
            cbar_kws={'label': 'Change from BS (%)', 'shrink': 0.8},
            linewidths=0.5,
            linecolor='white',
            annot_kws={'fontsize': 10, 'fontweight': 'bold'},
            square=False)

ax4.set_title('Heatmap of Relative Changes from BS (%)', fontsize=15, fontweight='bold', pad=15)
ax4.set_xlabel('Cost Category', fontsize=13, fontweight='bold')
ax4.set_ylabel('Scenario', fontsize=13, fontweight='bold')

ax4.set_xticklabels(ax4.get_xticklabels(), fontsize=11, fontweight='bold')
ax4.set_yticklabels(ax4.get_yticklabels(), fontsize=10)

cbar = ax4.collections[0].colorbar
cbar.ax.tick_params(labelsize=10)

plt.tight_layout()
plt.subplots_adjust(top=0.95)
plt.show()
