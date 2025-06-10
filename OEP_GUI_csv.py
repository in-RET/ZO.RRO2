# -*- coding: utf-8 -*-
"""
Created on Thu Jun  5 15:27:07 2025

@author: rbala
"""

import os
workdir = os.getcwd()
from src.preprocessing.files import read_input_files
import pandas as pd


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