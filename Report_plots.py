# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 10:26:09 2026

@author: rbala

Abbildungen für Sogeht's II
"""
import pandas as pd
import joblib
import matplotlib.pyplot as plt
from datetime import datetime
from src.postprocessing.utils_dump import get_dump_file_path,load_results_from_dump
from src.postprocessing.plot_report_utils import interpret_results, create_combined_bus_component_dfs, plot_bus_flows, categorize_for_sequence, rename_index_with_category
from src.postprocessing.plot_report_utils import create_barplot_dict, scalars_bar_plot, create_bus_dataframes, create_component_dataframes, extract_sankey_flow_data
from src.postprocessing.plot_report_utils import create_sankey_excel_new
from src.preprocessing.conversion import CO2_price_addition
from src.preprocessing.files import read_input_files
from matplotlib.patches import ConnectionPatch
import os 
import textwrap
import numpy as np
from pathlib import Path
from sklearn.inspection import partial_dependence
from sklearn.ensemble import RandomForestRegressor
workdir = os.getcwd()
import re
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
from src.models.automatic_cost_calc import cost_calculation_from_energysystem

CM = 1 / 2.54

# Book page
PAGE_WIDTH = 17.5 * CM
PAGE_HEIGHT = 25.0 * CM

# Approximate usable area
TEXT_WIDTH = 14.5 * CM
TEXT_HEIGHT = 22.0 * CM

FIG_FULL = (TEXT_WIDTH, 21.5 * CM)
FIG_WIDE = (TEXT_WIDTH, 6.5 * CM)
FIG_SMALL = (7.0 * CM, 6.5 * CM
)

fontsizenr = 14
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": [
        "Times New Roman",
        "Times",
        "DejaVu Serif"
    ],

    "font.size": fontsizenr,

    "axes.titlesize": fontsizenr,
    "axes.labelsize": fontsizenr,

    "xtick.labelsize": fontsizenr,
    "ytick.labelsize": fontsizenr,
    "text.usetex" : False,
    "axes.titlepad": 10,

    "savefig.dpi": 600,
    "savefig.bbox": "tight",
})
figure_bg_color='#159A3433'


#%%
scenarios =["REF-04", "Innovative_scenario", "MVB"]
year = 2045
variation = "BS0006"
model_name = "Basic_example_zorro_1"#"_regionalization"   
model_name_BE = "Basic_example_zorro_1_BE"
model_data={}
results_dict = {}
all_data = {
    'electricity': [],
    'hydrogen': [],
    'gas': [],
    'heat': [],
    'biomass': [],
    'oil': []
}

# Store component scalars and costs for all scenarios
all_component_scalars = []
all_costs = []

for scenario_num in scenarios:
    OUTPUT_DIR = Path(workdir) / 'figures' / 'Abschlussbericht'/"Chapter_5_results" / (
        f"{scenario_num}_{year}_{variation}"
    )

    OUTPUT_DIR.mkdir(parents=True,
        exist_ok=True)
    print("Loading results...")
    if scenario_num == "MVB":
        model_name = model_name_BE
    else:
        model_name = model_name
    dump_path = get_dump_file_path(year, variation, model_name, scenario_num)
    es, model = load_results_from_dump(dump_path)

    print("Extracting results...")   
  
        
    bus_sequences, bus_scalars, component_sequences, component_scalars, component_bus_mapping = interpret_results(model)
    bus_dfs = create_bus_dataframes(bus_sequences, es)
    component_dfs = create_component_dataframes(component_sequences, es)
    combined_df = create_combined_bus_component_dfs(bus_sequences, component_sequences, es)
    
    # Store component scalars and costs
    all_component_scalars.append(component_scalars)
    all_costs.append(cost_calculation_from_energysystem(es))
    
    Color_mapping=  {
        # Generation sources
        'PV': '#FFD700',           # Gold for solar
        'WIND': '#4169E1',         # Royal Blue for wind
        'HYDRO': '#1E90FF',        # Dodger Blue for hydro
        'LAUFWASSER - KW': '#1E90FF',
        'GRID LOSS' : '#800000',
        'NACHFRAGE': '#723E04',
        'NACHFRAGE inkl. stoffl. Nutzung': '#723E04',
        
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
        'Biomasse - HKW': ['Biomasse_elec_heat'],
        'Biomasse als Festbrennstoff': ['BioTransformer'],
        'Biomasse - KW': ['Biomasse_elec'],
        'Biomasse - HW': ['Biomasse_heat'],
        'Import - Holz': ['Import_Wood'],
        'Waermespeicher': ['storage_dist_heat', 'storage_seasonal'],
        'Nachheizung für Speicher': ['Preheater- Electric boiler', 'Preheater- WP'],
        'Heizstab': ['Electric boiler'],
        'GuD - KW': ['GuD'],
        'Waermepumpen': ['Heatpump'],
         #'Solarthermie': ['ST'],
        'Import - Strom': ['Import_Electricity'],
        'Pumpspeicherkraftwerk' : ['Pumped_hydro'],
        'Brennstoffzelle': ['Fuelcell'],
        'Laufwasser - KW' : ['Hydro power plant'],
        'PV': ['PV', 'SOLAR'],
        'WIND': ['WIND'],
        'Nachfrage': ['LOAD', 'DEMAND'],
        'Elektrolyse': ['Electrolysis'],
        'Export': ['Export'],
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
        
    
    }   
    RENEWABLE_CATEGORIES = {
        "WIND":            ("ElectricityIn", "WIND", "IN"),
        "PV":              ("ElectricityIn", "PV", "IN"),
        "Laufwasser - KW": ("ElectricityIn", "Laufwasser - KW", "IN"),
    }
     
    BIOMASS_ELECTRICITY_CATEGORIES = [
        ("ElectricityIn", "Biomasse - KW", "IN"),
        ("ElectricityIn", "Biomasse - HKW", "IN"),
        ("ElectricityIn", "Biogas- BHKW", "IN"),
    ]
    categorized_dict = categorize_for_sequence(category_list, combined_df)
    
    summer_weak = plot_bus_flows(categorized_dict,
                   OUTPUT_DIR,
                   bus_name = 'Electricity',
                   inflow_plot_title = 'Strombereitstellung',
                   outflow_plot_title = 'Stromverwendung',
                   COLOR_MAPPING = Color_mapping,
                   start_date=str(year)+'-04-12',
                   end_date = str(year)+'-04-19',
                   figsize = (14, 10),
                   title_fontsize=14,
                   label_fontsize=14,
                   figure_bg_color='#159A3433',
                   axes_bg_color='#FFFFFF',#'#159A3400',#'#FFFFFF',
                   labels_with_info = False)
    
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
 
    CATEGORY_COLOR_OVERRIDES = {
        'Biomasse - Biogas': 'BIOGAS- BHKW',
        'Import - Biowaste': 'IMPORT',
        'Import - Holz': 'IMPORT',
        'Import - Strom': 'IMPORT',
        'Import -Gas': 'IMPORT',
        'Import - Wasserstoff': 'IMPORT',
        'Import - Oil': 'IMPORT',
        'Import - Kraftstoff': 'IMPORT',
        'Import - Braunkohle': 'IMPORT',
        'Netzverluste': 'GRID LOSS',
        'Rechenzentren': 'DEFAULT',
        'Abregelung': 'ABWAERME'
         }

# help funtion
    def _normalize(label):
        return re.sub(r"\s+", " ", str(label).upper().strip())
     
     
    def tech_color(category_name):
        """Colour for a category_list name, taken from Color_mapping (the
        exact palette used in Bilder_Abschlussbericht.py)."""
     
        if category_name in CATEGORY_COLOR_OVERRIDES:
            key = CATEGORY_COLOR_OVERRIDES[category_name]
        else:
            key = _normalize(category_name)
     
        if key in Color_mapping:
            return Color_mapping[key]
     
        normalized = _normalize(key)
        for color_key, color in Color_mapping.items():
            if _normalize(color_key) == normalized:
                return color
     
        return Color_mapping['DEFAULT']
     
     
    def tech_colors(labels):
        return [tech_color(label) for label in labels]
     
     
    def fmt_de(value, decimals=0):
        """
        Format a number in German convention (comma as decimal separator,
        period as thousands separator),
        """
     
        text = f"{value:,.{decimals}f}"
        text = (
            text
            .replace(",", "§")
            .replace(".", ",")
            .replace("§", ".")
        )
        return text
     
     
    def node_label(node):
        """
        Safely obtain the label/name of an oemof component.
        """
     
        if node is None:
            return ""
     
        if hasattr(node, "label"):
            return str(node.label)
     
        if hasattr(node, "name"):
            return str(node.name)
     
        return str(node)
     
     
    def save_figure(fig, filename):
        """
        Save both vector PDF and high-resolution PNG.
        """
     
        pgf_path = OUTPUT_DIR / f"{filename}.pgf"
        png_path = OUTPUT_DIR / f"{filename}.png"
     
        fig.savefig(
            pgf_path,
            format="pgf"
        )
     
        fig.savefig(
            png_path,
            format="png",
            dpi=400
        )
     
        print(
            f"Saved: {pgf_path.name}"
        )
         
    def _reference_index():
        """Hourly index taken from the first available bus dataframe."""
     
        for df in categorized_dict.values():
            if isinstance(df, pd.DataFrame) and len(df.index) > 0:
                return df.index
     
        raise RuntimeError("Could not determine model time index.")
     
     
    def zero_series():
        return pd.Series(0.0, index=_reference_index())
     
    def calculate_renewable_generation():
     
        result = {}
     
        for name, flow in RENEWABLE_CATEGORIES.items():
            result[name] = annual_gwh(*flow)
     
        result["Biomasse - Biogas"] = sum(
            annual_gwh(*flow)
            for flow in BIOMASS_ELECTRICITY_CATEGORIES
        )
     
        return pd.Series(result) 
    def category_series(bus_name, category_name, direction="IN"):
        """
        Hourly series for one flow category on one bus, e.g.
        category_series("Electricity_Hös", "Import - Strom", "IN").
     
        Missing buses/columns are replaced with zeros (with a warning), same
        behaviour as Report_plots.py's original `safe_series`.
        """
     
        column = f"{direction}: {category_name}"
     
        df = categorized_dict.get(bus_name)
     
        if df is None:
            print(f"WARNING: bus '{bus_name}' not found in categorized_dict.")
            return zero_series()
     
        if column not in df.columns:
            print(f"WARNING: column '{column}' not found on bus '{bus_name}'.")
            return zero_series()
     
        return df[column].fillna(0.0).astype(float)
     
     
    def annual_gwh(bus_name, category_name, direction="IN"):
        """
        Convert hourly MW flow (as stored in categorized_dict) to annual GWh.
        """
     
        series = category_series(bus_name, category_name, direction)
     
        return series.sum() / 1000.0

     
    def calculate_electricity_balance():
     
        data = {}
     
        # Supply
        for name, flow in RENEWABLE_CATEGORIES.items():
            data[name] = annual_gwh(*flow)
     
        data["Biomasse - Biogas"] = sum(
            annual_gwh(*flow)
            for flow in BIOMASS_ELECTRICITY_CATEGORIES
        )
     
        data["Import - Strom"] = annual_gwh(
            "Electricity_Hös", "Import - Strom", "IN"
        )
        
        data["Ausspeicherung des Pumpspeicherkraftwerks"] = annual_gwh(
            "ElectricityIn", "Pumpspeicherkraftwerk", "IN"
        )
        
        data["Brennstoffzelle"] = annual_gwh(
            "ElectricityIn", "Brennstoffzelle", "IN"
        )
        
        data["GuD"] = annual_gwh(
            "ElectricityIn", "GuD - KW", "IN"
        )
        data["Stromspeicher_aus"] = annual_gwh(
            "ElectricityIn", "Stromspeicher", "IN"
        )
        
        data["Stromspeicher_ein"] = annual_gwh(
            "ElectricityIn", "Stromspeicher", "OUT"
        )
        
        # Demand
        data["Nachfrage"] = annual_gwh(
            "ElectricityOut", "Nachfrage", "OUT"
        )
     
        data["Elektrolyse"] = annual_gwh(
            "ElectricityOut", "Elektrolyse", "OUT"
        )
             
        data["Power-to-fuel"] = annual_gwh(
            "ElectricityOut", "Power-to-fuel", "OUT"
        )
     
        data["Waermepumpen"] = annual_gwh(
            "ElectricityOut", "Waermepumpen", "OUT"
        )
     
        data["Heizstab"] = annual_gwh(
            "ElectricityOut", "Heizstab", "OUT"
        )
        data["Nachheizung für Speicher"] = annual_gwh(
            "ElectricityOut", "Nachheizung für Speicher", "OUT"
        )
        data["Export"] = annual_gwh(
            "ElectricityOut", "Export", "OUT"
        )
        data["Einspeicherung des Pumpspeicherkraftwerks"] = annual_gwh(
            "ElectricityIn", "Pumpspeicherkraftwerk", "OUT"
        )
        
        data["Netzverluste"] = annual_gwh("ElectricityIn", "Netzverluste", "OUT")  - annual_gwh("ElectricityOut", "Netzverluste", "IN")
        data['Speicherverlust'] =  (data["Einspeicherung des Pumpspeicherkraftwerks"]+data["Stromspeicher_ein"])-(data["Ausspeicherung des Pumpspeicherkraftwerks"] +data["Stromspeicher_aus"])
        return pd.Series(data)

       
    def calculate_hydrogen_balance():
     
        return pd.Series({
            "Import - Wasserstoff": annual_gwh("Hydrogen", "Import - Wasserstoff", "IN"),
            "Elektrolyse": annual_gwh("Hydrogen", "Elektrolyse", "IN"),
            "Einspeicherung": annual_gwh("Hydrogen", "Wasserstoffspeicher", "OUT"),
            "Nachfrage": annual_gwh("Hydrogen", "Nachfrage", "OUT"),
            "Brennstoffzelle": annual_gwh("Hydrogen", "Brennstoffzelle", "OUT"),
            "Power-to-fuel": annual_gwh("Hydrogen", "Power-to-fuel", "OUT"),
            "Methanisierung": annual_gwh("Hydrogen", "Methanisierung", "OUT"),
            "Export": annual_gwh("Hydrogen", "Export", "OUT"),
            "Ausspeicherung": annual_gwh("Hydrogen", "Wasserstoffspeicher", "IN"),
            "Speicherverlust": annual_gwh("Hydrogen", "Wasserstoffspeicher", "OUT")-annual_gwh("Hydrogen", "Wasserstoffspeicher", "IN")
        })
     
    def calculate_heat_balance():
     
        return pd.Series({
            "Biomasse - Biogas": (annual_gwh("District heating", "Biogas- BHKW", "IN")+
                                     annual_gwh("District heating", "Biomasse - HW", "IN")+
                                     annual_gwh("District heating", "Biomasse - HKW", "IN")),
            "GuD": annual_gwh("District heating", "GuD - KW", "IN"),
            "Solarthermie": annual_gwh("District heating", "ST", "IN"),
            "Nachfrage": annual_gwh("District heating", "Nachfrage", "OUT"),
            "Heizstab": annual_gwh("District heating", "Heizstab", "IN"),
            "Waermepumpen": annual_gwh("District heating", "Waermepumpen", "IN"),
            "Einspeicherung": annual_gwh("District heating", "Waermespeicher", "OUT"),
            "Ausspeicherung": annual_gwh("District heating", "Waermespeicher", "IN")+annual_gwh("District heating", "Nachheizung für Speicher", "IN"),
            "Speicherverlust": annual_gwh("District heating", "Waermespeicher", "OUT")-(annual_gwh("District heating", "Waermespeicher", "IN")+annual_gwh("District heating", "Nachheizung für Speicher", "IN")),
            "Abregelung": annual_gwh("District heating", "Excess", "OUT"),
        })
    
    def calculate_biomass_balance():
     
        return pd.Series({
            "Import - Biowaste": annual_gwh("Biomass", "Import - Biowaste", "IN"),
            "Import - Holz": annual_gwh("BioWood", "Import - Holz", "IN"),
            "Biomasse-to-fuel": annual_gwh("Biomass", "Biomasse-to-fuel", "OUT")+annual_gwh("BioWood", "Biomasse-to-fuel", "OUT") ,
            "Biogas - Methanisierungsanlage": annual_gwh("Biomass", "Biogas - Methanisierungsanlage", "OUT"),
            "Biogas - BHKW": annual_gwh("Biomass", "Biogas- BHKW", "OUT"),
            "Biogas - Aufbereitungsanlage": annual_gwh("Biomass", "Biogas - Aufbereitungsanlage", "OUT"),
            "Biomasse als Festbrennstoff": annual_gwh("BioWood", "Biomasse als Festbrennstoff", "OUT"),
            "Biomasse - KW": annual_gwh("BioWood", "Biomasse - KW", "OUT"),
            "Biomasse - HW": annual_gwh("BioWood", "Biomasse - HW", "OUT"),
            "Biomasse - HKW": annual_gwh("BioWood", "Biomasse - HKW", "OUT"),
            "Nachfrage inkl. stoffl. Nutzung": annual_gwh("Solidfuel", "Nachfrage", "OUT"),
             
        })
    
    def calculate_gas_balance():
     
        return pd.Series({
            "Einspeicherung": annual_gwh("Gas", "Gasspeicher", "OUT"),
            "Ausspeicherung": annual_gwh("Gas", "Gasspeicher", "IN"),
            "Speicherverlust":  annual_gwh("Gas", "Gasspeicher", "OUT")-annual_gwh("Gas", "Gasspeicher", "IN"),
            "GuD": annual_gwh("Gas", "GuD - KW", "OUT"),
            "Biogas - Methanisierungsanlage": annual_gwh("Gas", "Biogas - Methanisierungsanlage", "IN"),
            "Biogas - Aufbereitungsanlage": annual_gwh("Gas", "Biogas - Aufbereitungsanlage", "IN"),
            "Import - Gas": annual_gwh("Gas", "Import -Gas", "IN"),
            "Methanisierung": annual_gwh("Gas", "Methanisierung", "IN"),
            "Nachfrage inkl. stoffl. Nutzung": annual_gwh("Gas", "Nachfrage", "OUT"),
             
        })
    
    def calculate_oil_balance(scenario_num):
        if scenario_num == "MVB":
            return pd.Series({
                "Import - Oil": annual_gwh("Oil_fuel", "Import - Oil", "IN"),
                "Import - Kraftstoff": annual_gwh("Oil_fuel", "Import - Kraftstoff", "IN"),
                "Power-to-fuel": annual_gwh("Oil_fuel", "Power-to-fuel", "IN"),
                "Biomasse-to-fuel": annual_gwh("Oil_fuel", "Biomasse-to-fuel", "IN"),
                "Nachfrage inkl. stoffl. Nutzung": annual_gwh("Oil_fuel", "Nachfrage", "OUT"),
                "Export": annual_gwh("Oil_fuel", "Export", "OUT"),
            })
        else:
            return pd.Series({
                "Import - Oil": annual_gwh("Oil_fuel", "Import - Oil", "IN"),
                "Import - Kraftstoff": annual_gwh("Oil_fuel", "Import - Kraftstoff", "IN"),
                "Power-to-fuel": annual_gwh("Oil_fuel", "Power-to-fuel", "IN"),
                "Biomasse-to-fuel": annual_gwh("Oil_fuel", "Biomasse-to-fuel", "IN"),
                "Nachfrage inkl. stoffl. Nutzung": annual_gwh("Oil_fuel", "Nachfrage", "OUT"),
                "Export": 0

                })
     
    
    CAPACITY_CATEGORY_MAP = {
    'Stromerzeugung\nohne Biomasse': ['PV', 'WIND', 'Laufwasser - KW', 'ST'],

    'Bioenergie': [
        'Biogas- BHKW', 'Biogas - Aufbereitungsanlage', 'Biogas - Methanisierungsanlage',
        'Biomasse - HKW', 'Biomasse - HW', 'Biomasse - KW',
        'Biomasse als Festbrennstoff', 'Biomasse-to-fuel', 'GuD - KW'
    ],

    'Wasserstofftechnologien': [
        'Elektrolyse', 'Power-to-fuel', 'Methanisierung', 'Brennstoffzelle'
    ],

    'Waermeerzeugung\nohne Biomasse': [
        'Heizstab', 'Waermepumpen', 'Nachheizung für Speicher',
        'Umweltwaerme', 'Umgebungsluft', 'Abwärme'
    ],
}

    
    COMPONENT_TO_DISPLAY = {
    'PV_open_east': 'PV', 'PV_open_middle': 'PV', 'PV_open_north': 'PV', 'PV_open_swest': 'PV',
    'PV_rooftop_east': 'PV', 'PV_rooftop_middle': 'PV', 'PV_rooftop_north': 'PV', 'PV_rooftop_swest': 'PV',
    'Wind_east': 'WIND', 'Wind_middle': 'WIND', 'Wind_north': 'WIND', 'Wind_swest': 'WIND',
    'Hydro power plant': 'Laufwasser - KW',
    'ST': 'ST',
    'Biogas- BHKW': 'Biogas- BHKW',
    'Biogas_feedin_existing': 'Biogas - Aufbereitungsanlage',
    'Biogas_feedin_new': 'Biogas - Methanisierungsanlage',
    'Biomasse_elec_heat': 'Biomasse - HKW',
    'Biomasse_heat': 'Biomasse - HW',
    'Biomasse_elec': 'Biomasse - KW',
    'BioTransformer': 'Biomasse als Festbrennstoff',
    'BtL_Holz': 'Biomasse-to-fuel', 'BtL_substrat': 'Biomasse-to-fuel',
    'Electrolysis': 'Elektrolyse',
    'PtL': 'Power-to-fuel',
    'Methanisation': 'Methanisierung',
    'Fuelcell': 'Brennstoffzelle',
    'Battery': 'Stromspeicher', 'Li-Ion_Battery': 'Stromspeicher',
    'Natrium_Battery': 'Stromspeicher', 'Red-OX_Battery': 'Stromspeicher',
    'Pumped_hydro_storage': 'Pumpspeicherkraftwerk',
    'Pumped_hydro_storage_bestand': 'Pumpspeicherkraftwerk',
    'Pumped_hydro_technology': 'Pumpspeicherkraftwerk',
    'Gas_storage': 'Gasspeicher',
    'H2_storage': 'Wasserstoffspeicher',
    'Heat storage_dist_heat': 'Waermespeicher', 'Heat storage_seasonal': 'Waermespeicher',
    'Electric boiler': 'Heizstab', 'Preheater- Electric boiler': 'Nachheizung für Speicher',
    'Heatpump_air': 'Waermepumpen', 'Heatpump_water': 'Waermepumpen', 'Heatpump_recovery_heat': 'Waermepumpen',
    'Preheater- WP': 'Nachheizung für Speicher',
    'UW': 'Umweltwaerme',
    'Umgebungsluft': 'Umgebungsluft',
    'AW': 'Abwärme',
    'GuD': 'GuD - KW',
    'Import_Electricity': 'Import - Strom',
    'Import_Gas': 'Import -Gas',
    'Import_Hydrogen': 'Import - Wasserstoff',
    'Import_Oil': 'Import - Oil',
    'Import_Synthetic_fuel': 'Import - Kraftstoff',
    'Import_Wood': 'Import - Holz',
    'Import_solid_fuel': 'Import - Biowaste',
    'Import_brown_coal': 'Import - Braunkohle',
    'Netzverluste': 'Netzverluste',
}
    _CAPACITY_DISPLAY_TO_GROUP = {
        name: group for group, names in CAPACITY_CATEGORY_MAP.items() for name in names
    }
    
    # Define plot functions
    def aggregate_capacities(component_scalars):
        """
        Aggregate component_scalars into:
          - power_by_group:   {group: {display_name: capacity_MW}}
          - storage_by_display: {display_name: capacity_MWh}
        """
        power_by_group = {}
        storage_by_display = {}

        for component, flows in component_scalars.items():
            display_name = COMPONENT_TO_DISPLAY.get(component)

            if display_name is None:
                print(f"WARNING: component '{component}' not in COMPONENT_TO_DISPLAY, "
                      f"assigning to 'Sonstige'.")
                display_name = component
                group = 'Sonstige'
            else:
                group = _CAPACITY_DISPLAY_TO_GROUP.get(display_name, 'Sonstige')

            storage_capacity = flows.get('None', 0.0) or 0.0
            power_capacity = sum(v for k, v in flows.items() if k != 'None')

           
            power_gw = power_capacity/1000
            storage_gwh = storage_capacity/1000

            if abs(power_gw) > 1e-9:
                power_by_group.setdefault(group, {})
                power_by_group[group][display_name] = (
                    power_by_group[group].get(display_name, 0.0) + power_gw  
                )

            if abs(storage_gwh) > 1e-9 or (display_name.lower().endswith("speicher") and not display_name.lower().startswith("nachheizung")):
                storage_by_display[display_name] = (
                    storage_by_display.get(display_name, 0.0) + storage_gwh
                )

        return power_by_group, storage_by_display
    
    def _draw_capacity_bars(ax, groups, power_by_group, x_positions, bar_width,
                             legend_handles, stack_order, all_techs):
        for xi, group in zip(x_positions, groups):
            bottom = 0.0
            techs_sorted = [
                (tech, value) for tech, value in
                sorted(power_by_group[group].items(), key=lambda kv: -kv[1])
                if value > 0
            ]
            stack_order[group] = techs_sorted
    
            for tech, value in techs_sorted:
                bars = ax.bar(
                    xi, value, bottom=bottom, width=bar_width,
                    color=tech_colors([tech])[0], edgecolor="white", linewidth=0.6,
                    label=tech,
                )
                legend_handles.setdefault(tech, bars[0])
                if tech not in all_techs:
                    all_techs.append(tech)
                bottom += value
    
    
    def _draw_storage_bars(ax, labels, values, x_positions, bar_width=0.6):
        ax.bar(
            x_positions, values, width=bar_width,
            color=tech_colors(labels), edgecolor="white", linewidth=0.6,
        )
    
    def plot_system_cost_balance(
        cost,
        filename="system_cost_balance",
        y_max=None , # Added parameter for fixed y-axis
        y_min = None
    ):

        investment_cost = cost["investment costs"].fillna(0).sum()
        variable_cost = cost["variable costs"].fillna(0).sum()
        profit = cost["profits"].fillna(0).sum()
        gross_cost = investment_cost + variable_cost
        total_cost = gross_cost + profit
    
        investment_pct = investment_cost / gross_cost * 100 if gross_cost > 0 else 0
        variable_pct = variable_cost / gross_cost * 100 if gross_cost > 0 else 0
        profit_pct = profit / gross_cost * 100 if gross_cost > 0 else 0
    
        print("\nSystem cost balance")
        print("-" * 55)
    
        print(
            f"Kapitalgebundene Kosten : "
            f"{investment_cost / 1e6:,.2f} Mio. € "
            f"({investment_pct:.1f} %)"
        )
    
        print(
            f"Betriebsgebundene Kosten: "
            f"{variable_cost / 1e6:,.2f} Mio. € "
            f"({variable_pct:.1f} %)"
        )
    
        print(
            f"Gesamtkosten brutto     : "
            f"{gross_cost / 1e6:,.2f} Mio. €"
        )
    
        print(
            f"Gewinn / Erlöse         : "
            f"{profit / 1e6:,.2f} Mio. € "
            f"({profit_pct:.1f} %)"
        )
    
        print(
            f"Gesamtkosten netto      : "
            f"{total_cost / 1e6:,.2f} Mio. €"
        )
        labels = [
            "Kapitalgebundene\nKosten",
            "Betriebsgebundene\nKosten",
            "Gewinn/Erlöse",
            "Gesamtkosten"
        ]
    
        values = [
            investment_cost / 1e6,
            variable_cost / 1e6,
            profit / 1e6,
            total_cost / 1e6
        ]
    
        colors = [
            "#4472C4",
            "#ED7D31",
            "#70AD47",
            "#A5A5A5"
        ]
    
        fig, ax = plt.subplots(figsize=(12 / 2.54, 12 / 2.54))
        fig.patch.set_facecolor(figure_bg_color)
        ax.set_facecolor("white")
        bars = ax.bar(
            labels,
            values,
            color=colors,
            width=0.65
        )
        plt.axhline(y=0,linewidth=1, color='k')
    
        if y_max is not None:
            max_value = y_max
            ax.set_ylim(y_min * 1.4, max_value * 1.4)
        else:
            max_value = max(values)
            ax.set_ylim(max_value * -0.4, max_value * 1.4)
    
        for bar, value in zip(bars, values):
    
            value = bar.get_height()
            if value >= 0:
                y_pos = value + max_value * 0.025
                va = 'bottom'
            else:
                y_pos = value - max_value * 0.025
                va = 'top'
            
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                y_pos,
                f"{value:.1f}",
                ha="center",
                va=va,
                fontweight="bold",
                fontsize=fontsizenr
            )
    
    
        ax.set_ylabel("Kosten in Mio. €",fontsize = fontsizenr)
        ax.set_title("Zusammensetzung der Systemkosten", fontweight="bold", fontsize = fontsizenr )
        ax.tick_params(axis="both", labelsize=fontsizenr)
        ax.tick_params(axis="x", rotation = 45)
        ax.grid(axis="y", alpha=0.3, linestyle="-")
        ax.set_axisbelow(True)
        # Remove unnecessary borders
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout()
    
        save_figure(fig, filename)
        plt.show()
    
        return fig, ax
    
    def plot_capacity_overview(component_scalars, filename="capacity_overview",
                               y_max_power=None, y_max_storage=None):
    
        power_by_group, storage_by_display = aggregate_capacities(component_scalars)
    
        groups_present = [g for g in CAPACITY_CATEGORY_MAP if g in power_by_group]
        n_groups = len(groups_present)
    
        fig = plt.figure(figsize=(10, 6))
        fig.patch.set_facecolor(figure_bg_color)
    
        outer_gs = fig.add_gridspec(
            2, 2, height_ratios=[4, 1.5], width_ratios=[2, 1])
        ax_main = fig.add_subplot(outer_gs[0, 0])
        ax_storage = fig.add_subplot(outer_gs[0, 1])
    
        ax_legends = fig.add_subplot(outer_gs[1, :])
        ax_legends.axis("off")
    
        # -------------------- main: power capacity --------------------
        x = np.arange(n_groups)
        bar_width = 0.6
        legend_handles = {}
        stack_order = {}
        all_techs = []
    
        _draw_capacity_bars(ax_main, groups_present, power_by_group, x, bar_width,
                             legend_handles, stack_order, all_techs)
    
        ax_main.set_xticks(x)
        ax_main.set_xticklabels(groups_present, rotation=30, ha="right", fontsize=fontsizenr)
        ax_main.set_ylabel("Installierte Leistung in GW")
        ax_main.set_title("Installierte Kapazitäten", loc="center", fontweight="bold")
        ax_main.grid(axis="y", linestyle="--", linewidth=0.4, alpha=0.5)
        ax_main.set_axisbelow(True)
        
        # Set fixed y-limit if provided
        if y_max_power is not None:
            ax_main.set_ylim(0, y_max_power)
    
        # -------------------- inset zoom for small power categories --------------------
        small_groups = [g for g in ["Bioenergie", "Wasserstofftechnologien"] if g in groups_present]
        if small_groups:
            idx_small = [groups_present.index(g) for g in small_groups]
            x_small = x[idx_small]
    
            y_max_small = max(
                sum(v for _, v in
                    sorted(power_by_group[g].items(), key=lambda kv: -kv[1]) if v > 0)
                for g in small_groups
            ) * 1.25
            
            # If global y_max is provided and smaller than local, use global
            if y_max_power is not None:
                y_max_small = min(y_max_small, y_max_power)
    
            axins_main = ax_main.inset_axes([0.30, 0.42, 0.4, 0.40]) 
            _draw_capacity_bars(axins_main, small_groups, power_by_group, x_small, bar_width,
                                 legend_handles, stack_order, all_techs)
    
            axins_main.set_xlim(x_small.min() - 0.6, x_small.max() + 0.6)
            axins_main.set_ylim(0, y_max_small)
            axins_main.set_xticks(x_small)
            axins_main.set_xticklabels([textwrap.fill(g, 25) for g in small_groups],
                                        fontsize=fontsizenr - 5)
            axins_main.tick_params(axis="y", labelsize=fontsizenr - 5)
            axins_main.set_facecolor("white")
            axins_main.grid(axis="y", linestyle="--", linewidth=0.4, alpha=0.5)
            axins_main.set_axisbelow(True)
    
            #ax_main.indicate_inset_zoom(axins_main, edgecolor="gray", alpha=0.45, linewidth=0.6)
            _, connectors = ax_main.indicate_inset_zoom(
                axins_main, edgecolor="gray", alpha=0.45, linewidth=0.6
            )
            for c in connectors:
                c.set_visible(False)

            # Top edge of the zoomed region (in ax_main data coords)
            x_lo, x_hi = x_small.min() - 0.6, x_small.max() + 0.6
            y_top = y_max_small

            # Top-left corner of zoom box -> bottom-left corner of inset
            cp_left = ConnectionPatch(
                xyA=(x_lo, y_top), coordsA="data", axesA=ax_main,
                xyB=(0.0, 0.0), coordsB="axes fraction", axesB=axins_main,
                lw=0.6, color="gray", linestyle=":",
            )
            # Top-right corner of zoom box -> bottom-right corner of inset
            cp_right = ConnectionPatch(
                xyA=(x_hi, y_top), coordsA="data", axesA=ax_main,
                xyB=(1.0, 0.0), coordsB="axes fraction", axesB=axins_main,
                lw=0.6, color="gray", linestyle=":",
            )

            ax_main.add_patch(cp_left)
            ax_main.add_patch(cp_right)
        # -------------------- side: storage energy capacity --------------------
        storage_items = sorted(storage_by_display.items(), key=lambda kv: -kv[1])
        s_labels = [name for name, _ in storage_items]
        s_values = [value for _, value in storage_items]
        x_s = np.arange(len(s_labels))
    
        _draw_storage_bars(ax_storage, s_labels, s_values, x_s)
    
        ax_storage.set_xticks(x_s)
        ax_storage.set_xticklabels(s_labels, rotation=45, ha="right", fontsize=fontsizenr)
        ax_storage.set_ylabel("Speicherkapazität in GWh")
        ax_storage.set_title("Speicherkapazitäten", loc="center", fontweight="bold")
        ax_storage.grid(axis="y", linestyle="--", linewidth=0.4, alpha=0.5)
        ax_storage.set_axisbelow(True)
        
        # Set fixed storage y-limit if provided
        if y_max_storage is not None:
            ax_storage.set_ylim(0, y_max_storage)
    
        # -------------------- inset zoom for small storage categories --------------------
        small_storage = [name for name in ["Pumpspeicherkraftwerk", "Stromspeicher"] if name in s_labels]
        if small_storage:
            idx_small_s = [s_labels.index(name) for name in small_storage]
            x_small_s = x_s[idx_small_s]
            values_small_s = [s_values[i] for i in idx_small_s]
    
            y_max_small_s = max(values_small_s) * 1.4 if max(values_small_s) > 0 else 1.0
            
            # If global y_max is provided and smaller than local, use global
            if y_max_storage is not None:
                y_max_small_s = min(y_max_small_s, y_max_storage)
    
            axins_storage = ax_storage.inset_axes([0.6, 0.40, 0.35, 0.35])
            _draw_storage_bars(axins_storage, small_storage, values_small_s, x_small_s)
    
            axins_storage.set_xlim(x_small_s.min() - 0.6, x_small_s.max() + 0.6)
            axins_storage.set_ylim(0, y_max_small_s)
            axins_storage.set_xticks(x_small_s)
            axins_storage.set_xticklabels([textwrap.fill(name, 13) for name in small_storage],
                                           fontsize=fontsizenr - 5, rotation = 30, ha="right")
            axins_storage.tick_params(axis="y", labelsize=fontsizenr - 5)
            axins_storage.set_facecolor("white")
            axins_storage.grid(axis="y", linestyle="--", linewidth=0.3, alpha=0.5)
            axins_storage.set_axisbelow(True)

            _, c_s = ax_storage.indicate_inset_zoom(
                axins_storage, edgecolor="gray", alpha=0.45, linewidth=0.6
            )
        
            c_s[0].set_visible(True)
            c_s[1].set_visible(False)
            c_s[2].set_visible(True)
            c_s[3].set_visible(False)
            plt.setp([c_s[:]], linestyle=":", lw=0.7)
          
        # -------------------- legends --------------------
        all_legend_items = []
    
        for group in groups_present:
            techs_top_to_bottom = list(reversed(stack_order[group]))
            if techs_top_to_bottom:
                handles = [legend_handles[tech] for tech, _ in techs_top_to_bottom]
                labels = [textwrap.fill(tech, width=15) for tech, _ in techs_top_to_bottom]
                all_legend_items.append((group, handles, labels))
    
        n_legend_groups = len(all_legend_items)
        max_items_per_group = max([len(items[1]) for items in all_legend_items]) if all_legend_items else 0
    
        from matplotlib.patches import Rectangle
    
        combined_handles = []
        combined_labels = []
        combined_group_indices = []
    
        for group, handles, labels in all_legend_items:
            header_handle = Rectangle((0, 0), 0, 0, alpha=0)
            combined_handles.append(header_handle)
            combined_labels.append(f"{group}")
            combined_group_indices.append(len(combined_labels) - 1)
    
            # Add the actual items
            for h, l in zip(handles, labels):
                combined_handles.append(h)
                combined_labels.append(l)
            n_pad = max_items_per_group - len(handles)
            for _ in range(n_pad):
                combined_handles.append(Rectangle((0, 0), 0, 0, alpha=0))
                combined_labels.append("")
    
        ncol = n_legend_groups 
    
        legend = ax_legends.legend(
            combined_handles,
            combined_labels,
            frameon=True,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.1),
            fontsize=fontsizenr - 3,
            handlelength=1.2,
            handletextpad=0.4,
            labelspacing=0.5,
            columnspacing=4.5,
            ncol=ncol,
            borderaxespad=0.2,
        )
    
        for text in legend.get_texts():
            if text.get_text() in ["Stromerzeugung\nohne Biomasse", "Bioenergie", "Wasserstofftechnologien", "Waermeerzeugung\nohne Biomasse"]:
                text.set_weight('bold')
                text.set_fontsize(fontsizenr - 2)
    
        # fig.suptitle(
        #     f"Installierte Kapazitäten – {scenario_num}, {year}",
        #     fontsize=fontsizenr, fontweight="bold",
        # )
        fig.subplots_adjust(left=0.08, right=0.97, top=0.90, bottom=0.12)
    
        save_figure(fig, filename)
        plt.show()
        return power_by_group, storage_by_display
    
    def plot_bus_balance(
        ax,
        data,
        supply_names,
        demand_names,
        title,
        ylabel,
        y_max=None,  # Parameter for fixed y-axis
    ):
        supply = data[supply_names].copy()
        demand = data[demand_names].copy()

        x_supply = 0
        x_demand = 0.2
        bar_width = 0.15

        supply_bottom = 0.0

        for tech in supply.index:

            value = float(supply.loc[tech])

            if value == 0:
                continue

            ax.bar(
                x_supply,
                value,
                bottom=supply_bottom,
                width=bar_width,
                color=tech_colors([tech])[0],
                edgecolor="white",
                linewidth=0.6,
                label=tech,
            )

            supply_bottom += value

        demand_bottom = 0.0

        for tech in demand.index:

            value = float(demand.loc[tech])

            if value == 0:
                continue

            ax.bar(
                x_demand,
                value,
                bottom=demand_bottom,
                width=bar_width,
                color=tech_colors([tech])[0],
                edgecolor="white",
                linewidth=0.6,
                hatch="////",
                alpha=0.85,
                label=tech,
            )

            demand_bottom += value

        ax.set_xticks([x_supply, x_demand])
        ax.set_xticklabels([
            "Erzeugung",
            "Bedarf/\nUmwandlung"
        ], fontweight = "bold", fontsize = fontsizenr)

        ax.set_ylabel(ylabel, fontsize = fontsizenr)
        ax.set_title(
            title,
            loc="center",
            fontweight="bold",
            fontsize = fontsizenr
        )

        ax.grid(
            axis="y",
            linestyle="--",
            linewidth=0.4,
            alpha=0.5,
        )

        ax.set_axisbelow(True)

        if y_max is not None:
            ax.set_ylim(0, y_max * 1.1)  # Add 10% margin

        handles, labels = ax.get_legend_handles_labels()
        handle_dict = dict(zip(labels, handles))

        # Reverse order so legend follows visual top → bottom
        supply_order = list(reversed(supply.index))
        demand_order = list(reversed(demand.index))
        
        supply_handles = [handle_dict[name] for name in supply_order if name in handle_dict]
        supply_labels = [name for name in supply_order if name in handle_dict]
        demand_handles = [handle_dict[name] for name in demand_order if name in handle_dict]
        demand_labels = [name for name in demand_order if name in handle_dict]
        total_items = len(supply_handles) + len(demand_handles)

        # Create invisible handle for headers
        from matplotlib.patches import Patch
        header_handle = Patch(facecolor='none', edgecolor='none', alpha=0)
        
        if total_items > 7:
            # Supply legend on the right side
            all_handles = []
            all_labels = []
            
            # Supply section
            all_handles.append(header_handle)
            all_labels.append("Erzeugung")
            
            for h, l in zip(supply_handles, supply_labels):
                all_handles.append(h)
                all_labels.append(l)
            
            legend_supply = ax.legend(
                all_handles,
                all_labels,
                frameon=True,
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                fontsize=fontsizenr-3,
                handlelength=1.5,
                handletextpad=0.5,
                labelspacing=0.8,
            )
            
            # Format supply header as bold
            for text in legend_supply.get_texts():
                if text.get_text() in ["Erzeugung"]:
                    text.set_weight('bold')
                    text.set_fontsize(fontsizenr-2)
            
            ax.add_artist(legend_supply)
            
            # Demand legend at the bottom
            all_handles_demand = []
            all_labels_demand = []
            
            for h, l in zip(demand_handles, demand_labels):
                all_handles_demand.append(h)
                all_labels_demand.append(l)
            
            legend_demand = ax.legend(
                all_handles_demand,
                all_labels_demand,
                frameon=True,
                loc="upper center",
                bbox_to_anchor=(0.8, -0.2),
                fontsize=fontsizenr-3,
                handlelength=1.5,
                handletextpad=0.5,
                labelspacing=0.5,
                ncol=3,
                title="Bedarf/Umwandlung",
                title_fontproperties=FontProperties(weight='bold', size=fontsizenr-2)
            )
                    
            plt.subplots_adjust(bottom=0.25)
        
        else:
            all_handles = []
            all_labels = []
            
            # Supply section
            all_handles.append(header_handle)
            all_labels.append("Erzeugung")
            
            for h, l in zip(supply_handles, supply_labels):
                all_handles.append(h)
                all_labels.append(l)
            
            # Demand section
            all_handles.append(header_handle)
            all_labels.append("Bedarf/Umwandlung")
            
            for h, l in zip(demand_handles, demand_labels):
                all_handles.append(h)
                all_labels.append(l)
            
            legend = ax.legend(
                all_handles,
                all_labels,
                frameon=True,
                loc="upper left",
                bbox_to_anchor=(1.02, 1),
                fontsize=fontsizenr-3,
                handlelength=1.5,
                handletextpad=0.5,
                labelspacing=0.8,
            )
            
            # Format section headers as bold
            for text in legend.get_texts():
                if text.get_text() in ["Erzeugung", "Bedarf/Umwandlung"]:
                    text.set_weight('bold')
                    text.set_fontsize(fontsizenr-2)
                       

        return supply, demand

    # Store data from both scenarios
    all_balances = {
        'electricity': {},
        'hydrogen': {},
        'gas': {},
        'heat': {},
        'biomass': {},
        'oil': {}
    }

############################# Main  ######################################    
    fig1, axes1 = plt.subplots(3, 1, figsize=(6, 20), constrained_layout = True)
    fig1.patch.set_facecolor(figure_bg_color)
    
    # Calculate data for this scenario
    electricity_data = calculate_electricity_balance()
    hydrogen_data = calculate_hydrogen_balance()
    gas_data = calculate_gas_balance()
    heat_data = calculate_heat_balance()
    biomass_data = calculate_biomass_balance()
    oil_data = calculate_oil_balance(scenario_num)
    oil_data[oil_data<0] =0
    
    # Store for finding max values later
    all_data['electricity'].append(electricity_data)
    all_data['hydrogen'].append(hydrogen_data)
    all_data['gas'].append(gas_data)
    all_data['heat'].append(heat_data)
    all_data['biomass'].append(biomass_data)
    all_data['oil'].append(oil_data)
    
    # Plot for this scenario
    plot_bus_balance(
        axes1[0],
        electricity_data,
        supply_names=[
            *list(RENEWABLE_CATEGORIES.keys()),
            "Biomasse - Biogas",
            "Import - Strom",
            "Brennstoffzelle",
            "GuD",
        ],
        demand_names=[
            "Nachfrage",
            "Elektrolyse",
            "Power-to-fuel",
            "Waermepumpen",
            "Heizstab",
            "Export",
            "Nachheizung für Speicher",
            "Netzverluste",
            "Speicherverlust"
        ],
        title="Strombilanz",
        ylabel="Energiemenge in GWh",
        y_max=None,  
    )
    
    plot_bus_balance(
        axes1[1],
        hydrogen_data,
        supply_names=[
            "Import - Wasserstoff",
            "Elektrolyse",
        ],
        demand_names=[
            "Nachfrage",
            "Methanisierung",
            "Power-to-fuel",
            "Export",
            "Brennstoffzelle",
            "Speicherverlust"
        ],
        title="Wasserstoffbilanz",
        ylabel="Energiemenge in GWh",
        y_max=None,  
    )
    
    plot_bus_balance(
        axes1[2],
        gas_data,
        supply_names=[
            "Import - Gas",
            "Biogas - Methanisierungsanlage",
            "Biogas - Aufbereitungsanlage",
            "Methanisierung",
        ],
        demand_names=[
            "Nachfrage inkl. stoffl. Nutzung",
            "GuD",
            "Speicherverlust"
        ],
        title="Gasbilanz",
        ylabel="Energiemenge in GWh",
        y_max=None,  
    )
    
    # fig1.suptitle(
    #     f"Energiebilanzen nach Energieträger im Referenzszenario – {scenario_num}, {year} (links)",
    #     fontsize=fontsizenr,
    #     fontweight="bold",
    # )
    

    fig2, axes2 = plt.subplots(3, 1, figsize=(6, 20), constrained_layout = True)
    fig2.patch.set_facecolor(figure_bg_color)
    
    plot_bus_balance(
        axes2[0],
        heat_data,
        supply_names=[
            "Biomasse - Biogas",
            "GuD",
            "Solarthermie",
            "Heizstab",
            "Waermepumpen",
        ],
        demand_names=[
            "Nachfrage",
            "Speicherverlust",
            "Abregelung"
        ],
        title="Waermebilanz",
        ylabel="Energiemenge in GWh",
        y_max=None,
    )
    
    plot_bus_balance(
        axes2[1],
        biomass_data,
        supply_names=[
            "Import - Biowaste",
            "Import - Holz",
        ],
        demand_names=[
            "Nachfrage inkl. stoffl. Nutzung",
            "Biomasse-to-fuel",
            "Biogas - Methanisierungsanlage",
            "Biogas - BHKW",
            "Biogas - Aufbereitungsanlage",
            "Biomasse - KW",
            "Biomasse - HW",
            "Biomasse - HKW",
        ],
        title="Bioenergiebilanz",
        ylabel="Energiemenge in GWh",
        y_max=None,
    )
    
    plot_bus_balance(
        axes2[2],
        oil_data,
        supply_names=[
            "Import - Oil",
            "Import - Kraftstoff",
            "Power-to-fuel",
            "Biomasse-to-fuel",
        ],
        demand_names=[
            "Nachfrage inkl. stoffl. Nutzung",
            "Export"
            ],
        title="Oel- bzw. Kraftstoffbilanz",
        ylabel="Energiemenge in GWh",
        y_max=None,
    )
    
    # fig2.suptitle(
    #     f"Energiebilanzen nach Energieträger im Referenzszenario – {scenario_num}, {year} (rechts)",
    #     fontsize=fontsizenr,
    #     fontweight="bold",
    # )
    

print("\n" + "="*50)
print("Re-plotting with fixed y-axes for comparison...")
print("="*50)

max_values = {
    'electricity': 0,
    'hydrogen': 0,
    'gas': 0,
    'heat': 0,
    'biomass': 0,
    'oil': 0
}

for i, scenario_num in enumerate(scenarios):
    elec_data = all_data['electricity'][i]
    hydro_data = all_data['hydrogen'][i]
    gas_data = all_data['gas'][i]
    heat_data = all_data['heat'][i]
    bio_data = all_data['biomass'][i]
    oil_data = all_data['oil'][i]
    
    # Electricity
    elec_supply_max = elec_data[[
        *list(RENEWABLE_CATEGORIES.keys()),
        "Biomasse - Biogas",
        "Import - Strom",
        "Brennstoffzelle",
        "GuD",
    ]].sum()
    elec_demand_max = abs(elec_data[[
        "Nachfrage",
        "Elektrolyse",
        "Power-to-fuel",
        "Waermepumpen",
        "Heizstab",
        "Export",
        "Nachheizung für Speicher",
        "Netzverluste",
        "Speicherverlust"
    ]].sum())
    max_values['electricity'] = max(max_values['electricity'], elec_supply_max, elec_demand_max)
    
    # Hydrogen
    hydro_supply_max = hydro_data[[
        "Import - Wasserstoff",
        "Elektrolyse",
    ]].sum()
    hydro_demand_max = abs(hydro_data[[
        "Nachfrage",
        "Methanisierung",
        "Power-to-fuel",
        "Export",
        "Brennstoffzelle",
        "Speicherverlust"
    ]].sum())
    max_values['hydrogen'] = max(max_values['hydrogen'], hydro_supply_max, hydro_demand_max)
    
    # Gas
    gas_supply_max = gas_data[[
        "Import - Gas",
        "Biogas - Methanisierungsanlage",
        "Biogas - Aufbereitungsanlage",
        "Methanisierung",
    ]].sum()
    gas_demand_max = abs(gas_data[[
        "Nachfrage inkl. stoffl. Nutzung",
        "GuD",
        "Speicherverlust"
    ]].sum())
    max_values['gas'] = max(max_values['gas'], gas_supply_max, gas_demand_max)
    
    # Heat
    heat_supply_max = heat_data[[
        "Biomasse - Biogas",
        "GuD",
        "Solarthermie",
        "Heizstab",
        "Waermepumpen",
    ]].sum()
    heat_demand_max = abs(heat_data[[
        "Nachfrage",
        "Speicherverlust",
        "Abregelung"
    ]].sum())
    max_values['heat'] = max(max_values['heat'], heat_supply_max, heat_demand_max)
    
    # Biomass
    bio_supply_max = bio_data[[
        "Import - Biowaste",
        "Import - Holz",
    ]].sum()
    bio_demand_max = abs(bio_data[[
        "Nachfrage inkl. stoffl. Nutzung",
        "Biomasse-to-fuel",
        "Biogas - Methanisierungsanlage",
        "Biogas - BHKW",
        "Biogas - Aufbereitungsanlage",
        "Biomasse - KW",
        "Biomasse - HW",
        "Biomasse - HKW",
    ]].sum())
    max_values['biomass'] = max(max_values['biomass'], bio_supply_max, bio_demand_max)
    
    # Oil
    oil_supply_max = oil_data[[
        "Import - Oil",
        "Import - Kraftstoff",
        "Power-to-fuel",
        "Biomasse-to-fuel",
    ]].sum()
    
    oil_demand_columns = [
        "Nachfrage inkl. stoffl. Nutzung",
        "Export"
    ]
    
    oil_demand_max = abs(oil_data[oil_demand_columns].sum())
    max_values['oil'] = max(max_values['oil'], oil_supply_max, oil_demand_max)

max_power_cap = 0
max_storage_cap = 0

for component_scalars in all_component_scalars:
    power_by_group, storage_by_display = aggregate_capacities(component_scalars)
    
    for group, techs in power_by_group.items():
        total_power = sum(techs.values())
        max_power_cap = max(max_power_cap, total_power)
    
    for storage_name, value in storage_by_display.items():
        max_storage_cap = max(max_storage_cap, value)

max_power_cap = max_power_cap * 1.15  # Add 15% margin
max_storage_cap = max_storage_cap * 1.15
max_cost = 0
for cost in all_costs:
    investment_cost = cost["investment costs"].fillna(0).sum() / 1e6
    variable_cost = cost["variable costs"].fillna(0).sum() / 1e6
    profit = cost["profits"].fillna(0).sum() / 1e6
    total_cost = investment_cost + variable_cost + profit
    max_cost = max(max_cost, total_cost)
    min_cost = profit
# Re-plot energy balances with fixed axes
for i, scenario_num in enumerate(scenarios):
    print(f"\nRe-plotting {scenario_num} with fixed axes...")
    OUTPUT_DIR = Path(workdir) / 'figures' / 'Abschlussbericht'/"Chapter_5_results" / (
        f"{scenario_num}_{year}_{variation}"
    )
    
    # Left side - Electricity, Hydrogen, Gas
    fig1, axes1 = plt.subplots(3, 1, figsize=(6, 20), constrained_layout=True)
    fig1.patch.set_facecolor(figure_bg_color)
    
    plot_bus_balance(
        axes1[0],
        all_data['electricity'][i],
        supply_names=[
            *list(RENEWABLE_CATEGORIES.keys()),
            "Biomasse - Biogas",
            "Import - Strom",
            "Brennstoffzelle",
            "GuD",
        ],
        demand_names=[
            "Nachfrage",
            "Elektrolyse",
            "Power-to-fuel",
            "Waermepumpen",
            "Heizstab",
            "Export",
            "Nachheizung für Speicher",
            "Netzverluste",
            "Speicherverlust"
        ],
        title="Strombilanz",
        ylabel="Energiemenge in GWh",
        y_max=max_values['electricity'],
    )
    
    plot_bus_balance(
        axes1[1],
        all_data['hydrogen'][i],
        supply_names=[
            "Import - Wasserstoff",
            "Elektrolyse",
        ],
        demand_names=[
            "Nachfrage",
            "Methanisierung",
            "Power-to-fuel",
            "Export",
            "Brennstoffzelle",
            "Speicherverlust"
        ],
        title="Wasserstoffbilanz",
        ylabel="Energiemenge in GWh",
        y_max=max_values['hydrogen'],
    )
    
    plot_bus_balance(
        axes1[2],
        all_data['gas'][i],
        supply_names=[
            "Import - Gas",
            "Biogas - Methanisierungsanlage",
            "Biogas - Aufbereitungsanlage",
            "Methanisierung",
        ],
        demand_names=[
            "Nachfrage inkl. stoffl. Nutzung",
            "GuD",
            "Speicherverlust"
        ],
        title="Gasbilanz",
        ylabel="Energiemenge in GWh",
        y_max=max_values['gas'],
    )
    
    # fig1.suptitle(
    #     f"Energiebilanzen nach Energieträger – {scenario_num}, {year} (links)",
    #     fontsize=fontsizenr,
    #     fontweight="bold",
    # )
    
    save_figure(fig1, f"energy_balances_links_{scenario_num}_fixed")
    plt.show()
    
    # Right side - Heat, Biomass, Oil
    fig2, axes2 = plt.subplots(3, 1, figsize=(6, 20), constrained_layout=True)
    fig2.patch.set_facecolor(figure_bg_color)
    
    plot_bus_balance(
        axes2[0],
        all_data['heat'][i],
        supply_names=[
            "Biomasse - Biogas",
            "GuD",
            "Solarthermie",
            "Heizstab",
            "Waermepumpen",
        ],
        demand_names=[
            "Nachfrage",
            "Speicherverlust",
            "Abregelung"
        ],
        title="Waermebilanz",
        ylabel="Energiemenge in GWh",
        y_max=max_values['heat'],
    )
    
    plot_bus_balance(
        axes2[1],
        all_data['biomass'][i],
        supply_names=[
            "Import - Biowaste",
            "Import - Holz",
        ],
        demand_names=[
            "Nachfrage inkl. stoffl. Nutzung",
            "Biomasse-to-fuel",
            "Biogas - Methanisierungsanlage",
            "Biogas - BHKW",
            "Biogas - Aufbereitungsanlage",
            "Biomasse - KW",
            "Biomasse - HW",
            "Biomasse - HKW",
        ],
        title="Bioenergiebilanz",
        ylabel="Energiemenge in GWh",
        y_max=max_values['biomass'],
    )
    
    plot_bus_balance(
        axes2[2],
        all_data['oil'][i],
        supply_names=[
            "Import - Oil",
            "Import - Kraftstoff",
            "Power-to-fuel",
            "Biomasse-to-fuel",
        ],
        demand_names=[
            "Nachfrage inkl. stoffl. Nutzung",
            "Export",
            ],
        title="Oel- bzw. Kraftstoffbilanz",
        ylabel="Energiemenge in GWh",
        y_max=max_values['oil'],
    )
    
    # fig2.suptitle(
    #     f"Energiebilanzen nach Energieträger – {scenario_num}, {year} (rechts)",
    #     fontsize=fontsizenr,
    #     fontweight="bold",
    # )
    
    save_figure(fig2, f"energy_balances_rechts_{scenario_num}_fixed")
    plt.show()
    
    plot_capacity_overview(
        all_component_scalars[i], 
        f"capacity_overview_{scenario_num}_fixed",
        y_max_power=max_power_cap,
        y_max_storage=max_storage_cap
    )

    plot_system_cost_balance(
        all_costs[i], 
        f"system_cost_balance_{scenario_num}_fixed",
        y_max=max_cost,
        y_min = min_cost
    )

# Create Sankey excel
create_sankey_excel_new(model_data, os.path.join(workdir, 'results', 'sankey', model_name+'_'+variation +'_report.xlsx')) 


#%% Timeseries plots:
    
feed_in_path = Path(workdir) /"data" / "sequences" /"feed_in_profile_2009.csv"
feed_in_df = pd.read_csv(feed_in_path, sep=';', decimal = ',',encoding = 'unicode_escape', index_col=0)

pv_feed_in = feed_in_df["PV_openfield_north_scaled"]

def feed_in_plot(data): 
    winter_week = data.iloc[24 * 14 : 24 * 28].reset_index(drop=True)
    summer_week = data.iloc[24 * 196 : 24 * 210].reset_index(drop=True)
    hours = range(336)
    data_sorted = data.sort_values(ascending=False).reset_index(drop=True)

    duration = (data_sorted.index + 1) / len(data_sorted) * 100
    fig = plt.figure(figsize=(12,6))
    fig.patch.set_facecolor(figure_bg_color)
    gs = fig.add_gridspec(
        1, 2,
        width_ratios=[2,1],
    )

    ax1 = fig.add_subplot(gs[0, 0])

    ax1.plot(
        hours,
        winter_week,
        label="Winterwoche",
        linewidth=1.8
    )
    
    ax1.plot(
        hours,
        summer_week,
        label="Sommerwoche",
        linewidth=1.8
    )

    ax1.set_xlabel("Tag der Woche", fontsize = fontsizenr)
    ax1.text(0, 1.02, '[MW/MW$_{\mathrm{N}}$]', transform=ax1.transAxes, 
             fontsize=fontsizenr, ha='right', va='bottom')
    ax1.set_title("Repräsentative Wochenprofile", fontweight="bold", fontsize = fontsizenr)

    ax1.set_xlim(0, 336)
    ax1.set_xticks([
    0, 24, 48, 72, 96, 120, 144,
    168, 192, 216, 240, 264, 288, 312
])
    ax1.set_xticklabels([
    "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So",
    "Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"
], fontsize = fontsizenr)
    
    ax1.grid(True, alpha=0.3)
    ax1.legend()

    ax2 = fig.add_subplot(gs[0, 1])
    
    ax2.plot(
        duration,
        data_sorted,
        linewidth=1.8
    )
    
    ax2.set_xlabel("Dauer %", fontsize = fontsizenr)
    ax2.text(0, 1.02, '[MW/MW$_{\mathrm{N}}$]', transform=ax2.transAxes, 
             fontsize=fontsizenr, ha='right', va='bottom')
    ax2.set_title("Dauerlinie", fontweight="bold", fontsize = fontsizenr)
    
    ax2.set_xlim(0, 100)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
feed_in_plot(feed_in_df["PV_openfield_north_scaled"])
feed_in_plot(feed_in_df["Wind_middle_scaled"])
feed_in_plot(feed_in_df["Hydro_power"])
feed_in_plot(feed_in_df["Solarthermal"])

#%% Sensitivity Anlaysis plot

save_dir_morris = os.path.join(workdir,'dumps', 'SALIB', f'results_morris_1400.joblib')
output_morris, analyse_morris, result_morris, output_names, problem = joblib.load(save_dir_morris)
#Read MC results
save_dir_mc = os.path.join(workdir,'dumps', 'SALIB', f'results_mc_1400.joblib')
output_mc, result_mc, problem_mc = joblib.load(save_dir_mc)

models = {}
for i, out in enumerate(output_names):
    # Correlation
    corr = result_mc[problem["names"] + [out]].corr()[out].drop(out)

    # Train model
    model = RandomForestRegressor()
    model.fit(result_mc[problem["names"]], result_mc[out])
    models[out] = model
    
def translate_param(param_name):
    """Übersetzt englische Parameternamen ins Deutsche"""
    translations = {
        # Renewables
        "wind_flh": "Volllaststunden Wind",
        "pv_flh": "Volllaststunden PV", 
        "potential_wind": "Windpotenzial (Flächenkulisse)",
        "potential_pv": "PV-Potenzial (Flächenkulisse)",
        "potential_biomasse": "Biomassepotenzial",
        
        # Storage
        "capex_batterie": "Investitionskosten Batteriespeicher",
        "capex_heat_storage": "Investitionskosten Wärmespeicher",
        
        # Imports
        "import_biomasse": "Importpreis Biomasse",
        "import_H2/fuel": "Importpreis H2 / synth. Kraftstoff",
        "import_electricity_price": "Strom-Importpreis",
        
        # Demand
        "demand_HH_waerme": "Wärmebedarf Haushalt",
        "person_mob": "Personenmobilität (Verkehrsnachfrage)",
        
        # Other
        "capex_PtL/BtL": "Investitionskosten PtL/BtL",
    }
    return translations.get(param_name, param_name)
#%%
def create_evidence_chain_abschluss_bericht(
        analyse_morris,
        problem,
        output_names,
        result_mc,
        models,
        plot_para
    ):

    output_mapping = {
        'Optimierte Wind-Leistung': 'wind',
        'Optimierte PV-Leistung': 'pv',
        'Optimierte Stromspeicher-Kapazität': 'stromspeicher',
        'Optimierte Wärmespeicher-Kapazität': 'waermespeicher',
        'Gesamtsystemkosten': 'cost'
    }

    target_output = output_mapping.get(plot_para, output_names[0])

    if target_output in output_names:
        index = output_names.index(target_output)
    else:
        print(
            f"Warnung: {target_output} nicht gefunden. "
            f"Verwende ersten Output."
        )
        index = 0

    fig, axes = plt.subplots(2, 2, figsize=(16, 11))
    fig.patch.set_facecolor(figure_bg_color)

    ax1 = axes[0, 0]
    ax2 = axes[0, 1]
    ax3 = axes[1, 0]
    ax4 = axes[1, 1]

    parameter_de = [translate_param(p) for p in problem["names"]]

    df_temp = pd.DataFrame({
        'Parameter_de': parameter_de,
        'Parameter_orig': problem["names"],
        'mu_star': analyse_morris[index]['mu_star'],
        'mu_star_conf': analyse_morris[index]['mu_star_conf']
    })

    max_mu_star = df_temp['mu_star'].max()

    if max_mu_star > 0:

        df_temp['mu_star_norm'] = (
            df_temp['mu_star'] / max_mu_star
        )*100

        df_temp['mu_star_conf_norm'] = (
            df_temp['mu_star_conf'] / max_mu_star
        )*100

    else:
        df_temp['mu_star_norm'] = 0
        df_temp['mu_star_conf_norm'] = 0

    df_temp = df_temp.sort_values('mu_star_norm', ascending=True)

    # ---------------------------------------------------------
    # TOP 3 ROT
    # ---------------------------------------------------------

    colors = [
        '#d62728'
        if i >= len(df_temp) - 3
        else '#ff7f0e'
        for i in range(len(df_temp))
    ]


    ax1.barh(
        df_temp['Parameter_de'],
        df_temp['mu_star_norm'],
        xerr=df_temp['mu_star_conf_norm'],
        color=colors,
        capsize=3,
        error_kw={
            'elinewidth': 1.2,
            'ecolor': 'gray'
        }
    )

    ax1.set_xlabel('Normierte Einflussstärke (μ*) in %', fontsize= fontsizenr)
    ax1.set_title(f'1. Kritische Parameter\nfür {plot_para}', fontsize=fontsizenr, fontweight='bold')
    ax1.set_xlim(0, max(1.05,(df_temp['mu_star_norm'] + df_temp['mu_star_conf_norm']).max() * 1.05))
    ax1.tick_params(axis='y', labelsize=fontsizenr)
    ax1.grid(axis='x', alpha=0.3)

    top3_params = (
        df_temp
        .nlargest(3, 'mu_star_norm')
        ['Parameter_orig']
        .values
    )

    top2_params = top3_params[:2]

    pdp_colors = ['#d62728', '#1f77b4', '#8b5a2b']

    if output_names[index] in models:

        model = models[output_names[index]]

        for i, param in enumerate(top3_params):

            try:

                pd_result = partial_dependence(
                    model,
                    result_mc[problem["names"]],
                    [param]
                )

                x = pd_result['grid_values'][0]
                y = pd_result['average'][0]

                if 'cost' in target_output.lower():
                    y = y / 1_000_000
                else:
                    y = y/ 1000  #in GW/Gwh

                param_de = translate_param(param)

                ax2.plot(
                    x,
                    y,
                    color=pdp_colors[i],
                    linewidth=3,
                    label=param_de
                )

            except Exception as e:

                print(
                    f"PDP konnte für {param} "
                    f"nicht berechnet werden: {e}"
                )

    ax2.axvline(
        x=1,
        color='black',
        linestyle='--',
        linewidth=2,
        alpha=0.8,
        label='Referenzszenario'
    )

    median_wert = result_mc[output_names[index]].median()
    mean_wert = result_mc[output_names[index]].mean()

    if 'cost' in target_output.lower():

        median_wert /= 1_000_000
        mean_wert /= 1_000_000
        einheit = "Mio. €/a"

    elif "leistung" in plot_para.lower():
        median_wert /= 1_000
        mean_wert /= 1_000
        einheit = "GW"

    elif "kapazität" in plot_para.lower():
        median_wert /= 1_000
        mean_wert /= 1_000
        einheit = "GWh"

    else:

        einheit = ""

    ax2.axhline(
        median_wert,
        color='gray',
        linestyle='--',
        linewidth=1.5,
        alpha=0.7,
        label=f'Median: {median_wert:.1f} {einheit}'
    )

    ax2.axhline(
        mean_wert,
        color='green',
        linestyle='--',
        linewidth=1.5,
        alpha=0.7,
        label=f'Mittelwert: {mean_wert:.1f} {einheit}'
    )

    ax2.set_xlabel(
        'Skalierungsfaktor (1 = Referenzwert)',
        fontsize=fontsizenr
    )

    ax2.set_ylabel(
        f'{plot_para} in {einheit}',
        fontsize=fontsizenr
    )

    ax2.set_title(
        '2. Wie Parameter Wirken\n'
        'Partielle Abhängigkeit (PDP)',
        fontsize=fontsizenr,
        fontweight='bold'
    )

    ax2.legend(
        loc='best',
        fontsize=fontsizenr
    )

    ax2.grid(
        alpha=0.3
    )

    # 3. MONTE-CARLO-VERTEILUNG

    mc_results = (
        result_mc[output_names[index]]
        .dropna()
        .values
    )

    n_sims = len(mc_results)

    if 'cost' in target_output.lower():

        mc_results = mc_results / 1_000_000
        einheit_y = "Mio. €/a"
        x_label = f'{plot_para} in Mio. €/a'

    elif "leistung" in plot_para.lower():
        mc_results = mc_results / 1_000
        einheit_y = "GW"
        x_label = f'{plot_para} in GW'

    elif "kapazität" in plot_para.lower():
        mc_results = mc_results / 1_000
        einheit_y = "GWh"
        x_label = f'{plot_para} in GWh'

    else:

        einheit_y = ""
        x_label = plot_para

    ax3.hist(
        mc_results,
        bins=20,
        color='#2ca02c',
        alpha=0.7,
        edgecolor='black'
    )

    mean_val = np.mean(mc_results)
    median_val = np.median(mc_results)

    p5, p95 = np.percentile(
        mc_results,
        [5, 95]
    )

    ax3.axvline(
        mean_val,
        color='red',
        linestyle='--',
        linewidth=2,
        label=f'Mittelwert: {mean_val:.1f}'
    )

    ax3.axvline(
        median_val,
        color='blue',
        linestyle=':',
        linewidth=2,
        label=f'Median: {median_val:.1f}'
    )

    ax3.axvline(
        p5,
        color='orange',
        linestyle=':',
        linewidth=1.5
    )

    ax3.axvline(
        p95,
        color='orange',
        linestyle=':',
        linewidth=1.5,
        label=f'90%-Intervall: {p5:.1f} – {p95:.1f}'
    )

    ymin, ymax = ax3.get_ylim()

    ax3.fill_betweenx(
        [0, ymax],
        p5,
        p95,
        alpha=0.2,
        color='orange'
    )

    ax3.set_xlabel(
        x_label,
        fontsize=fontsizenr
    )

    ax3.set_ylabel(
        'Anzahl der Simulationen',
        fontsize=fontsizenr
    )

    ax3.set_title(
        f'3. Unsicherheit\n'
        f'{plot_para}\n'
        f'aus {n_sims:,} Simulationen',
        fontsize=fontsizenr,
        fontweight='bold'
    )

    ax3.legend(
        loc='best',
        fontsize = fontsizenr,
    )

    ax3.grid(
        alpha=0.3
    )

    # 4. PARAMETERINTERAKTION
    if len(top2_params) >= 2:

        # INTERACTION SCATTER:
        param_x = top2_params[0]
        param_color = top2_params[1]
        
        # Daten vorbereiten
        scatter_df = result_mc[[param_x, param_color, output_names[index]]].dropna()
        
        x_data = scatter_df[param_x].values
        color_data = scatter_df[param_color].values
        y_data = scatter_df[output_names[index]].values
        
        # Output skalieren
        if 'cost' in target_output.lower():
            y_data = y_data / 1_000_000
            y_unit = "Mio. €/a"
        elif "leistung" in plot_para.lower():
            y_data = y_data / 1_000
            y_unit = "GW"
        elif "kapazität" in plot_para.lower():
            y_data = y_data / 1_000
            y_unit = "GWh"
        else:
            y_unit = ""
        
        # Scatter plot
        scatter = ax4.scatter(
            x_data,
            y_data,
            c=color_data,
            cmap='viridis',
            alpha=0.65,
            s=25,
            edgecolors='none'
        )
        
        cbar = fig.colorbar(scatter, ax=ax4, pad=0.02)
        cbar.set_label(translate_param(param_color)+"\n(Skalierungsfaktor)", fontsize = fontsizenr,)
        ax4.set_xlabel(translate_param(param_x)+"\n(Skalierungsfaktor)", fontsize = fontsizenr,)
        
        ax4.set_ylabel(f'{plot_para} in {y_unit}' if y_unit else plot_para,
            fontsize = fontsizenr,
        )
        
        ax4.set_title(
            '4. Parameterinteraktion\n'
            f'{translate_param(param_x)} vs. {translate_param(param_color)}',
            fontsize = fontsizenr,
            fontweight='bold'
        )
        
        ax4.grid(alpha=0.3)
        
    # GESAMTTITEL

    fig.suptitle(f'Beweiskette: Analyse für {plot_para}', fontsize = fontsizenr, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.show()
    OUTPUT_DIR = Path(workdir) / 'figures' / 'Abschlussbericht' / 'Chapter_5_results' / 'Sensitivitätsanalyse' / f"Beweiskette_{plot_para}.pdf"
    OUTPUT_DIR.parent.mkdir(parents=True, exist_ok=True)
    
    fig.savefig(OUTPUT_DIR)
    return df_temp, mc_results

for parameter in [
    'Optimierte Wind-Leistung',
    'Optimierte PV-Leistung',
    'Optimierte Stromspeicher-Kapazität',
    'Optimierte Wärmespeicher-Kapazität',
    'Gesamtsystemkosten'
]:

    df_top, mc_dist = create_evidence_chain_abschluss_bericht(
        analyse_morris=analyse_morris,
        problem=problem,
        output_names=output_names,
        result_mc=result_mc,
        models=models,
        plot_para=parameter
    )