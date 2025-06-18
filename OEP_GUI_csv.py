# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:27:07 2025

@author: rbala
"""

import os
import json
workdir = os.getcwd()
from src.preprocessing.files import read_input_files
import pandas as pd
from datetime import datetime


sequences = read_input_files(folder_name='data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name='data/scalars', sub_folder_name=None)

# sorting out the files starting with Parameter
T_list = []             
for i in scalars:
    if i.startswith('Parameter'):
        i = i[10:]
        T_list.append(i)

filtered_data_dict = {}
for filename, df in scalars.items():
    if filename.startswith('Parameter'):
        # Filter the dataframe to model ID 'BS0002'
        row = df.loc['BS0002']
        
        year_suffixes = ['_2025', '_2030', '_2035', '_2040', '_2045']
        year_columns = [col for col in row.index if any(col.endswith(suffix) for suffix in year_suffixes)]


        data = {}
        for col in year_columns:
            param, year = col.rsplit('_', 1)
            data.setdefault(year, {})[param] = row[col]

        # Convert to DataFrame and sort by year
        structured_df = pd.DataFrame.from_dict(data, orient='index')
        structured_df.index.name = 'year'
        structured_df = structured_df.sort_index()
        

        # Store in result dict
        filtered_data_dict[filename] = structured_df

filtered_timeseries_dict = {}
for filename,df in sequences.items():
    avg_df = pd.DataFrame()
    for y in year_suffixes:
        
        if filename.startswith('Electricity'):
            avg_df[f'electricity_demand{y}'] = (df[f'north{y}'] + df[f'east{y}'] +df[f'swest{y}'] + df[f'middle{y}']) / 4
        elif filename.startswith('Cooling') or filename.startswith('Domestic'):
            avg_df['demand'] = (df['north'] + df['east'] +df['swest'] + df['middle']) / 4
        elif filename.startswith('Base_demand'):
            avg_df['demand'] = df['base_load']
        elif filename.startswith('feed_in_profile'):
            avg_df['PV_rooftop'] = (df['PV_rooftop_north'] + df['PV_rooftop_east'] +df['PV_rooftop_swest'] + df['PV_rooftop_middle']) / 4
            avg_df['PV_openfield'] = (df['PV_openfield_north'] + df['PV_openfield_east'] +df['PV_openfield_swest'] + df['PV_openfield_middle']) / 4
            avg_df['Wind'] = (df['Wind_north'] + df['Wind_east'] +df['Wind_swest'] + df['Wind_middle']) / 4
            avg_df['Solarthermal'] = df['Solarthermal']
            avg_df['Hydro_power'] = df['Hydro_power']
        elif filename.startswith('Heat'):
            avg_df['Household_space_heating_demand'] = (df['Household_north'] + df['Household_east'] +df['Household_swest'] + df['Household_middle']) / 4
            avg_df['HA4_thuringia'] = (df['HA4_north'] + df['HA4_east'] +df['HA4_swest'] + df['HA4_middle']) / 4
            avg_df['Household_heat_plus_DHW_demand'] = (df['Heat+TWW_north'] + df['Heat+TWW_east'] +df['Heat+TWW_swest'] + df['Heat+TWW_middle']) / 4
        elif filename.startswith('Mobility'):
            avg_df = df
        elif filename.startswith('other'):
            avg_df = df
            filename = 'Standard_load_profile'
        
        filtered_timeseries_dict[filename] = avg_df

filtered_timeseries_dict.pop("Energy_price")
filtered_timeseries_dict.pop("Energy_price_brainpool_2024")
#%% Categorize the files

category_keywords = {
    "Sources": ["photovoltaic", "solar", "wind", "river"],
    "Storages": ["storage"],
    #"PTX": ["ptx", "biomass", "biogas", "biomethane", "combined_heat", "methanation", "hydrogen", "fuel", ]
}

def categorize_file(filename):
    filename_lower = filename.lower()
    for category, keywords in category_keywords.items():
        if any(keyword in filename_lower for keyword in keywords):
            return category
    return "Sector-coupling"

categories = {
    "Sources": {
        "description": "Techno-economic parameters for renewable sources; data based on literature data."+
                        "The data was collected in the ZO.RRO II project by Nordhausen University of Applied Sciences.",
        "keywords": ["renewables", "solar", "wind", "Thuringia", "oemof", "ZO.RRO II", "climate neutrality", "HSN in.RET"],
        "license": {"id": "CC-BY-4.0", "name": "Creative Commons Attribution 4.0"}
    },
    "Storages": {
        "description": "Techno-economic parameters for storages; data based on literature data."+
                        "The data was collected in the ZO.RRO II project by Nordhausen University of Applied Sciences.",
        "keywords": ["battery", "hydrogen", "storage", "Thuringia", "oemof", "ZO.RRO II", "climate neutrality", "HSN in.RET"],
        "license": {"id": "CC-BY-4.0", "name": "Creative Commons Attribution 4.0"}
    },
    "Sector-coupling": {
        "description": "Techno-economic parameters for sector coupling technologies; data based on literature data."+
                        "The data was collected in the ZO.RRO II project by Nordhausen University of Applied Sciences.",
        "keywords": ["ptx", "electrolysis", "synthetic_fuels", "sector-coupling", "Thuringia", "oemof", "ZO.RRO II", "climate neutrality", "HSN in.RET"],
        "license": {"id": "CC-BY-4.0", "name": "Creative Commons Attribution 4.0"}
    }
}


metadata_dict = {}
for filename, df in filtered_data_dict.items():
    cols_to_drop = df.columns[df.columns.str.contains('potential')]
    df.drop(cols_to_drop, axis=1, inplace=True)
    df.to_csv((os.path.join('OEP','CSV', filename + ".csv")), sep= ";", decimal = ',')
    print(filename +"        " +str(df.isnull().values.any()))

for filename, df in filtered_timeseries_dict.items():
    df.to_csv((os.path.join('OEP','CSV', filename + ".csv")), sep= ";", decimal = ',')
    
    
dummy = {}
for filename, df in filtered_data_dict.items():
    category = categorize_file(filename)
    dummy[filename]= categorize_file(filename)
    metadata = {
        "name": filename.replace(".csv", ""),
        "title": f"{category}_{filename}",
        "description": categories[category]["description"],
        "resources": [{
            "name": filename,
            "schema": {
                "fields": [
                    {
                        "name": col,
                        "description": f"Description of {col}",
                        "type": "number" if "float" in str(df[col].dtype) or "int" in str(df[col].dtype) else "string"
                    }
                    for col in df.columns
                ]
            }
        }],
        "keywords": categories[category]["keywords"],
        "publicationDate": datetime.now().strftime("%Y-%m-%d"),
        "license": categories[category]["license"],
        "context": {  
            "contact": "Hochschule Nordhausen - Institut für Regenerative Energietechnik",  
            "grantNo": "",  
            "homepage": "https://hs-nordhausen.de/",  
            "sourceCode": "https://github.com/in-RET",  
            "documentation": "https://hs-nordhausen.de"  
            },  
        "contributors": [  
        {  
          "title": "Amèlie Oberdorfer",  
          "organization": "Hochschule Nordhausen - Institut für regenerative Energietechnik",  
          "roles": [  
            "Data curation"  
          ],  
          "date": "2024-12-31",  
          "object": "",  
          "comment": ""  
        },  
        {  
          "title": "Andreas Lubojanski",  
          "organization": "Hochschule Nordhausen - Institut für regenerative Energietechnik",  
          "roles": [  
            "Software"  
          ],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": ""  
        },  
        {  
          "title": "Christoph Schmidt",  
          "organization": "Hochschule Nordhausen - Institut für regenerative Energietechnik",  
          "roles": [  
            "Data curation"  
          ],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": "0000-0002-4269-3779"  
        },  
        {  
          "title": "Rohith Krishnan Bala Krishnan",  
          "organization": "Hochschule Nordhausen - Institut für regenerative Energietechnik",  
          "roles": [  
            "Software"  
          ],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": ""  
        },  
        {  
          "title": "Theresa Reinhardt",  
          "organization": "Hochschule Nordhausen - Institut für regenerative Energietechnik",  
          "roles": [  
            "Software"  
          ],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": "0009-0004-8449-3443"  
        },  
        {  
          "title": "Viktor Wesselak",  
          "organization": "Hochschule Nordhausen - Institut für regenerative Energietechnik",  
          "roles": [],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": ""  
        },  
        {  
          "title": "Stefan Kirsch",  
          "organization": "Thüringer Kompetenzzentrum Forschungsdatenmanagement, Ernst-Abbe-Hochschule Jena",  
          "roles": [  
            "Data curation"  
          ],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": ""  
        },  
        {  
          "title": "Kevin Lindt",  
          "organization": "Thüringer Kompetenzzentrum Forschungsdatenmanagement, Technische Universität Ilmenau",  
          "roles": [  
            "Data curation"  
          ],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": ""  
        },  
        {  
          "title": "Ann-Kathrin Weidlich",  
          "organization": "",  
          "roles": [],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": ""  
        },  
        {  
          "title": "Anne Schierenbeck",  
          "organization": "",  
          "roles": [],  
          "date": "2025-09-01",  
          "object": "",  
          "comment": ""  
        }  
      ],  
        
        "version": "1.0.0",
        "metaMetadata": {
            "metadataVersion": "OEP-1.5.0",
            "metadataLicense": {
                "id": "CC0-1.0",
                "name": "CC0 1.0",
                "url": "https://creativecommons.org/publicdomain/zero/1.0/"
            }
        }
    }
    

    json_filename = f"metadata_{filename}.json"
    with open(os.path.join('OEP', 'Metadata',json_filename), "w") as f:
        json.dump(metadata, f, indent=2)
        print(f"Generated: metadata_{filename.replace('.csv', '.json')}")
