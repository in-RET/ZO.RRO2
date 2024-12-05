# -*- coding: utf-8 -*-
"""
Created on Tue Dec  3 10:28:08 2024

@author: aoberdorfer
"""


import pandas as pd
# from sqlalchemy.orm import sessionmaker
# import oedialect
# import os
# from sqlalchemy import Column, ForeignKey, Integer, String, FLOAT
# # from sqlalchemy.orm import declarative_base
# from sqlalchemy import MetaData, Table
# from sqlalchemy import create_engine
# import glob
# from pathlib import Path
# from requests.exceptions import HTTPError
# from requests import get, post, put, delete
# from oep_client import OepClient
# from oep_client import cli
# import json
#%% (von AO 3.12.2024)
import json
from random import randint
from getpass import getpass
import os
# from os import environ

import requests as req

topic = "sandbox"
table = f"tutorial_example_table_{randint(0, 100000)}"
token = 'a33d3cf704aba4d9ef29b96561353e71747484c6'
#os.environ.get("OEP_API_TOKEN") or getpass("Enter your OEP API token:") #siehe dein OEP Konto!

# for read/write, we need to add authorization header
auth_headers = {"Authorization": "Token %s" % token}
table_api_url = f"https://openenergyplatform.org/api/v0/schema/{topic}/tables/{table}/"

print(table_api_url)
    
# Ergebnis theoretisch:
# https://openenergyplatform.org/api/v0/schema/sandbox/tables/tutorial_example_table_61248/

#%%
# Base = declarative_base()

my_path = os.path.abspath(os.path.dirname(__file__))


# pfad = os.path.join(my_path, 'parameter_onshore_wind_power_plant_inret.csv')
dateiname = 'parameter_onshore_wind_power_plant_inret'
pfad = os.path.join(my_path, dateiname + '.csv')
parameter_onshore_wind_power_plant_inret = pd.read_csv(pfad, sep=';', decimal='.',  encoding = 'unicode_escape')

pfad = os.path.join(my_path, dateiname + '_meta.csv')
parameter_onshore_wind_power_plant_inret_meta = pd.read_csv(pfad, sep=';', decimal='.',  encoding = 'unicode_escape')

#print(parameter_onshore_wind_power_plant_inret)

#%% von AO

columns = []

for a in parameter_onshore_wind_power_plant_inret.keys():
    prim_key = False
    
    if a == "id":
        data_type = "int"
        prim_key = True
    elif a == "model_id":
        data_type = "varchar(255)"
    elif a == "balanced":
        data_type = "boolean"
    else:
        data_type = "float"
        
    if prim_key:
        columns.append({"name": a, "data_type": data_type, "primary_key": True})
    else:
        columns.append({"name": a, "data_type": data_type})

rawdata = parameter_onshore_wind_power_plant_inret.to_json(orient="table", index=False, indent=4)

data = json.loads(rawdata)["data"]
schema = json.loads(rawdata)["schema"]["fields"]

# print(data)
# print(schema)

# TODO: explain / link to data types
table_schema = {
    "columns": columns
}

# print(table_schema)

#%% AO MetaDataRessources zu Jason machen

metadataressources = []

for a in parameter_onshore_wind_power_plant_inret_meta.keys():
    prim_key = False
    
    if a == "id":
        data_type = "int"
        prim_key = True
    else:
                data_type = "varchar(255)"

    if prim_key:
        metadataressources.append({"name": a, "data_type": data_type, "primary_key": True})
    else:
        metadataressources.append({"name": a, "data_type": data_type})

parameter_onshore_wind_power_plant_inret_meta = parameter_onshore_wind_power_plant_inret_meta.to_json(orient="table", index=False, indent=2)

metadata_ressources_data = json.loads(parameter_onshore_wind_power_plant_inret_meta)["data"]
metadata_ressources_schema = json.loads(parameter_onshore_wind_power_plant_inret_meta)["schema"]["fields"]

# print(data)
# print(schema)

# TODO: explain / link to data types
table_schema_metadata_ressources = {
    "columns": metadataressources
}

print(table_schema_metadata_ressources)


from requests import get

result = get('https://openenergyplatform.org/api/v0/schema/model_draft/tables/parameter_onshore_wind_power_plant_9/rows')
# for row in result.json():
    
#     pass