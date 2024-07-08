# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 18:07:31 2024

@author: rbala

!!!!!!!!!!!!!!!!!!!!!!!!!!!

CAUTION: 
    
    The script is written to define a function to read all CSV files from a folder and store it a dictionary.
    Please consult the author before altering the script.


!!!!!!!!!!!!!!!!!!!!!!!!!!!
this script consists:
    - the function read all the csv files from a folder
    - necessary inputs are only folder name and subfolder name if needed
    
"""

import os
workdir= os.getcwd()
import pandas as pd

def read_input_files(folder_name, sub_folder_name= None):
    if sub_folder_name != None:
        path = os.path.abspath(os.path.join(workdir, '../..',folder_name,sub_folder_name))
    else:
        path = os.path.abspath(os.path.join(workdir, '../..',folder_name))
    
    files = dict()
      
    for filename in os.listdir(path):
        if filename.endswith('.csv'):
            file_path = os.path.join(path,filename)
            filename = filename[:-4]                            # to remove the file format from the file name (eg. removing .csv)
            files[filename] = pd.read_csv(file_path, sep=';', decimal = ',',encoding = 'unicode_escape', index_col=0)
    
    return(files)

