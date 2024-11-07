# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 10:40:00 2022

@author: treinhardt01
"""

import pandas as pd
from sqlalchemy.orm import sessionmaker
import oedialect
import os
from sqlalchemy import Column, ForeignKey, Integer, String, FLOAT
# from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData, Table
from sqlalchemy import create_engine
import glob
from pathlib import Path
from requests.exceptions import HTTPError
from requests import get, post, put, delete
from oep_client import OepClient
from oep_client import cli
import json

    
#%%

# Base = declarative_base()

my_path = os.path.abspath(os.path.dirname(__file__))


# Mobility

pfad = os.path.join(my_path, '../03_Eingangsdaten_OEP/Emobility/Lastprofil_Bahn.csv')
profile_train = pd.read_csv(pfad, 
                            encoding = 'unicode_escape', sep=',', decimal=',', index_col=0)

pfad = os.path.join(my_path, '../03_Eingangsdaten_OEP/Emobility/Lastprofil_Bus.csv')
profile_bus = pd.read_csv(pfad, index_col=0, sep=',', decimal=',',  encoding = 'unicode_escape')

pfad = os.path.join(my_path, '../03_Eingangsdaten_OEP/Emobility/Lastprofil_PKW.csv')
profile_car = pd.read_csv(pfad,
                          encoding = 'unicode_escape', sep=',', decimal=',')

#%%
# Heat 

pfad = os.path.join(my_path, '../03_Eingangsdaten_OEP/Wärmelast/Heizlastprofil.csv')
profile_heat = pd.read_csv(pfad,
                          encoding = 'unicode_escape', sep=';', decimal=',')

#%%

user = 'in.RET Hochschule Nordhausen'
token = 'b6c3ba972cc005c0ba41c371ee8125b76dfd12b8'

OEP_URL = 'oep.iks.cs.ovgu.de'
OED_STRING = f'postgresql+oedialect://{user}:{token}@{OEP_URL}'

engine = create_engine(OED_STRING)
metadata = MetaData(bind=engine)

schema_name = 'model_draft'

engine.connect()

 
#%%

# oep_cl = OepClient(token=token)

# # data = cli.read_json('metadata_template.json', encoding="utf-8")
# with open(my_path+'/Metadaten/hsn_inret_heat_load_profiles_metadata.json') as json_file:
#     data = json.load(json_file)
    
# #%%
    
# oep_cl.set_metadata(metadata=data, table="hsn_inret_heat_load_profiles")

# #%%

# with open(my_path+'/Metadaten/hsn_inret_mobility_load_profile_bus.metadata.json') as json_file:
#     data = json.load(json_file)
    
# oep_cl.set_metadata(metadata=data, table="hsn_inret_mobility_load_profile_bus")

#%% ("Put" tut die leere Tabelle in die OEP)

# Create table
schema = 'model_draft'
table = 'hsn_inret_mobility_load_profile_bus' #small letters with underscore
oep_url = 'https://openenergy-platform.org'

data = { 
    "query": { 
        "columns": [
            { "name":"id", "data_type": "bigserial", "is_nullable": "NO", "primary_key": True },
            { "name":"time", "data_type": "varchar(128)" },
            { "name":"charging_profile", "data_type": "numeric" }
        ]
    }
}

res = put(
    oep_url + '/api/v0/schema/' + schema + '/tables/' + table + '/',
    json=data,
    headers={'Authorization': f'Token {token}'}
)
print(res)#Response [201] succesfully created table! 


#BIS HIERHIN laufen lassen
#%% Löscht die ganze Tabelle wieder weg!
# table = "Mobility_Load_Profile_Bus"
# oep_url = 'https://openenergy-platform.org'
# schema = 'model_draft'

# # Delete table
# delete(oep_url + '/api/v0/schema/' + schema + '/tables/' + table, 
#        headers={'Authorization': f'Token {token}'} )#Response [200] succesfully deleted table!

#%% Hier wird die Variable "data" mit Inhalt gefüllt: WEGLASSEN

#Insert data

mylist = []

for i in range(0, 8760):
    mylist.append({"time": profile_bus.index[i], 
                   "charging_profile": profile_bus['Ladelast'][i]})
    
data = {
    "query": mylist
}



#%% Hier werden die Daten (im definierten Format) auf die OEP hochgeladen: WEGLASSEN

post(
    oep_url + '/api/v0/schema/' + schema + '/tables/' + table + '/rows/new', 
    json=data,
    headers={'Authorization': f'Token {token}'}
)

#%% WDH

# Create table
schema = 'model_draft'
table = 'hsn_inret_mobility_load_profile_train' #small letters with underscore
oep_url = 'https://openenergy-platform.org'

data = { 
    "query": { 
        "columns": [
            { "name":"id", "data_type": "bigserial", "is_nullable": "NO", "primary_key": True },
            { "name":"time", "data_type": "varchar(128)" },
            { "name":"charging_profile", "data_type": "numeric" }
        ]
    }
}

res = put(
    oep_url + '/api/v0/schema/' + schema + '/tables/' + table + '/',
    json=data,
    headers={'Authorization': f'Token {token}'}
)
print(res)#Response [201] succesfully created table! 

#%%WDH

# Delete table
delete(oep_url + '/api/v0/schema/' + schema + '/tables/' + table, 
       headers={'Authorization': f'Token {token}'} )#Response [200] succesfully deleted table!

#%%WDH

#Insert data

mylist = []

for i in range(0, 8760):
    mylist.append({"time": profile_train.index[i], 
                   "charging_profile": profile_train['Ladelast'][i]})
    
data = {
    "query": mylist
}



#%%WDH

post(
    oep_url + '/api/v0/schema/' + schema + '/tables/' + table + '/rows/new', 
    json=data,
    headers={'Authorization': f'Token {token}'}
)

#%%WDH

# Create table
schema = 'model_draft'
table = 'hsn_inret_mobility_load_profile_car' #small letters with underscore
oep_url = 'https://openenergy-platform.org'

data = { 
    "query": { 
        "columns": [
            { "name":"id", "data_type": "bigserial", "is_nullable": "NO", "primary_key": True },
            { "name":"time", "data_type": "varchar(128)" },
            { "name":"charging_profile", "data_type": "numeric" }
        ]
    }
}

res = put(
    oep_url + '/api/v0/schema/' + schema + '/tables/' + table + '/',
    json=data,
    headers={'Authorization': f'Token {token}'}
)
print(res)#Response [201] succesfully created table! 

#%%WDH

#Insert data

mylist = []

for i in range(0, 8760):
    mylist.append({"time": profile_car['Unnamed: 0'][i], 
                   "charging_profile": profile_car['Ladelast'][i]})
    
data = {
    "query": mylist
}

#%%WDH

post(
    oep_url + '/api/v0/schema/' + schema + '/tables/' + table + '/rows/new', 
    json=data,
    headers={'Authorization': f'Token {token}'}
)

#%%WDH

# Create table
schema = 'model_draft'
table = 'hsn_inret_heat_load_profiles' #small letters with underscore
oep_url = 'https://openenergy-platform.org'

data = { 
    "query": { 
        "columns": [
            { "name":"id", "data_type": "bigserial", "is_nullable": "NO", "primary_key": True },
            { "name":"time", "data_type": "varchar(128)" },
            { "name":"middle_thuringia", "data_type": "numeric" },
            { "name":"east_thuringia", "data_type": "numeric" },
            { "name":"southwest_thuringia", "data_type": "numeric" },
            { "name":"north_thuringia", "data_type": "numeric" }
        ]
    }
}

res = put(
    oep_url + '/api/v0/schema/' + schema + '/tables/' + table + '/',
    json=data,
    headers={'Authorization': f'Token {token}'}
)
print(res)#Response [201] succesfully created table! 

#%%WDH

#Insert data

mylist = []

for i in range(0, 8760):
    mylist.append({"time": profile_heat['Unnamed: 0'][i], 
                   "middle_thuringia": profile_heat['Middle Thuringia'][i],
                   "east_thuringia": profile_heat['East Thuringia'][i],
                   "southwest_thuringia": profile_heat['Southwest Thuringia'][i],
                   "north_thuringia": profile_heat['North Thuringia'][i]})
    
data = {
    "query": mylist
}

#%%WDH

post(
    oep_url + '/api/v0/schema/' + schema + '/tables/' + table + '/rows/new', 
    json=data,
    headers={'Authorization': f'Token {token}'}
)

#%%WDH
table="hs_nordhausen_inret_heat_load_profiles"
# Delete table
delete(oep_url + '/api/v0/schema/' + schema + '/tables/' + table, 
       headers={'Authorization': f'Token {token}'} )#Response [200] succesfully deleted table!