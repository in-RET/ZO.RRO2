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


categories = {
    "Sources": {
        "files": ["solar_data.csv", "wind_data.csv"],
        "description": "Datasets related to renewable energy sources (solar, wind).",
        "keywords": ["renewables", "solar", "wind"],
        "license": {"id": "CC-BY-4.0", "name": "Creative Commons Attribution 4.0"}
    },
    "Storages": {
        "files": ["battery_storage.csv", "hydrogen_storage.csv"],
        "description": "Datasets about energy storage technologies.",
        "keywords": ["battery", "hydrogen", "storage"],
        "license": {"id": "ODbL-1.0", "name": "Open Database License"}
    },
    "PTX": {
        "files": ["power_to_x.csv", "electrolysis_data.csv"],
        "description": "Power-to-X (PTX) conversion process datasets.",
        "keywords": ["ptx", "electrolysis", "synthetic_fuels"],
        "license": {"id": "MIT", "name": "MIT License"}
    }
}


def generate_oep_metadata(df, filename, category_info):
    """Generate OEP metadata for a DataFrame."""
    # Infer column types
    def get_field_type(dtype):
        if "float" in str(dtype) or "int" in str(dtype):
            return "number"
        elif "datetime" in str(dtype):
            return "datetime"
        else:
            return "string"

    # Current date for publicationDate
    current_date = datetime.now().strftime("%Y-%m-%d")

    metadata = {
        "name": filename.replace(".csv", ""),
        "title": f"{category_info.get('title_prefix', '')}{filename}",
        "description": category_info["description"],
        "language": ["en"],
        "keywords": category_info["keywords"],
        "publicationDate": datetime.now().strftime("%Y-%m-%d"),
        "license": category_info["license"],
        "resources": [{
            "profile": "tabular-data-resource",
            "name": filename,
            "path": f"https://example.com/data/{filename}",  # Update path
            "format": "csv",
            "encoding": "UTF-8",
            "schema": {
                "fields": [
                    {
                        "name": col,
                        "description": f"Description of {col}",  # Edit manually
                        "type": get_field_type(df[col].dtype)
                    }
                    for col in df.columns
                ]
            }
        }],
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
    return metadata

metadata_dict = {}
for filename, df in filtered_data_dict.items():
    cols_to_drop = df.columns[df.columns.str.contains('potential')]
    df.drop(cols_to_drop, axis=1, inplace=True)
    print(filename +"        " +str(df.isnull().values.any()))
    
    metadata_dict[filename] = generate_oep_metadata(df, filename)  
    

for filename, metadata in metadata_dict.items():
    json_filename = f"metadata_{filename.replace('.csv', '.json')}"
    with open(os.path.join('OEP', 'MEtadata',json_filename), "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Generated: {json_filename}")
    
for category, info in categories.items():
    for filename in info["files"]:
        if filename in filtered_data_dict:
            metadata = generate_oep_metadata(filtered_data_dict[filename], filename, info)
            json_filename = f"metadata_{filename.replace('.csv', '.json')}"
            with open(os.path.join('OEP', 'MEtadata',json_filename), "w") as f:
                json.dump(metadata, f, indent=2)
            print(f"Generated: metadata_{filename.replace('.csv', '.json')}")
