import os
import json
import pandas as pd

from random import randint
from src.oep_handler import OepHandler, create_tabledata, create_tableschema, create_metadata

WITH_UPLOAD = False

topic =  "sandbox" #"model_draft"
token = os.environ.get("OEP_API_TOKEN") #% TODO: .env-File anlegen nicht vergessen!
print("Gewählter Token:", token)

data_path = os.path.abspath(os.path.join("data"))
print("Datenpfad:", data_path)

general_meta = pd.read_csv(
    filepath_or_buffer=os.path.join(data_path, "meta_data_general.csv"),
    index_col=0,
    sep=";",
    decimal=".",
)

for root, dirs, files in os.walk(data_path, topdown=True):
    pass # TODO for later

raw_file_name = "parameter_onshore_wind_power_plant_inret.csv"
table = f"%s_{randint(0, 100000)}" % raw_file_name.replace(".csv", "")
raw_csv = pd.read_csv(
    filepath_or_buffer=os.path.join(data_path, "scalars", "parameter", raw_file_name),
    index_col=0,
    sep=';',
    decimal='.',
    encoding = 'unicode_escape'
)

# Create API-Handler-Object
OepApi = OepHandler(f"https://openenergyplatform.org/api/v0/schema/{topic}/tables/{table}/", token)

raw_data = raw_csv.loc["data", :] # Pandas ist geil
raw_meta = raw_csv.loc[["data_type", "type", "unit", "description", "primary_key"], :]

########################################################################################################################
#   Create Table Schema
########################################################################################################################
table_schema = create_tableschema(raw_data, raw_meta)

########################################################################################################################
#   Upload Table Schema
########################################################################################################################
if WITH_UPLOAD:
    response = OepApi.create_table(table_schema)
    print(response)

########################################################################################################################
#   Create Table Data
########################################################################################################################
table_data = create_tabledata(raw_data)

########################################################################################################################
#   Upload Table Data
########################################################################################################################
if WITH_UPLOAD:
    response = OepApi.upload_data(table_data)
    print(response)

########################################################################################################################
#   Create Meta Data
########################################################################################################################
meta_fields = create_metadata(raw_meta)

meta_data = general_meta.to_dict()["value"]
meta_data["name"] = table
meta_data["title"] = table.replace("_", " ")
meta_data["id"] = f"https://openenergyplatform.org/dataedit/view/{topic}/{table}"
meta_data["description"] = ["This table contains techno-economic parameters (investment costs, operating costs, service life and efficiency) for every 5 years between 2020 and 2050, as well as installation potential for the 4 planning regions of Thuringia, and in some cases technology-specific additional parameters. They were determined by a literature analysis, which can be found in the german final project report under “sources”. The sources and methodology are therein described in detail. The parameters were used for the energy system modeling of the federal state of Thuringia (Germany). First line: Values from the first project ZO.RRO I, only aviable for the years 2030, 40, 50. Second line: Determined median from literature analysis, standard value for this project ZO.RRO II. Third line: Upper quartile, obtained from literature analysis. Fourth line: Lower quartile, obtained from literature analysis. Further lines: Sensitivity analyses, described in more detail see documentation. Upper and lower quartiles are useful parameters for Monte Carlo simulations, for example, to represent the variance of the literature assumptions."],
meta_data["languages"] = ["EN", "DE"]
meta_data["subject"] = ["economic value, optimisation model, parameterisation", "investment cost", "fixed cost", "life time", "Efficiency value", "potential"], #Suchwörter aus der Ontology!
meta_data["keywords"] = ["Optimization model", "linear optimization", "Target scenarios", "Political target achievement", "1,5°C", "Transformation pathway", "Energy system modeling", "Thuringia", "Germany", "ZO.RRO", "ZORRO", "Energy demand", "Heat transition", "Energie transition", "in.RET", "inRET", "University of Applied Science Nordhausen", "HSN", "Hochschule Nordhausen" ]
meta_data["publicationdate"] = ["31.12.2024"] #bitte rechtzeitig ändern, wenn die Daten dann wirklich hochgeladen werden.s
meta_data["context"] = OepApi.context
meta_data["sources"] = OepApi.sources #ich hoffe, es gibt auch diese Funktion analog zu context. Aber warum gibt es licenses nicht?? Hm. Sorry, falls es nicht klappt *entschuldigend grins*

meta_data["licenses"] = [
    {
        "name": "CC-BY-4.0",
        "path": "https://spdx.github.io/license-list-data/CC-BY-4.0.html",
        "title": "Creative Commons Attribution 4.0 International"
        "instruction": "" #Platzhalter für Ergänzungen
        "attribution": "" #Platzhalter für Ergänzungen
        "copyrightStatement": "" #Platzhalter für Ergänzungen
    }
]

# meta_data["contributors"] = [
#     {
#         "title": "", Ann-Kathrin Weidlich?
#         "path": "",
#         "organization": ""
#         "roles": "" #Platzhalter für Ergänzungen
#         "date": "" #Platzhalter für Ergänzungen
#         "object": "" #Platzhalter für Ergänzungen
#         "comment": "" #Platzhalter für Ergänzungen
#     }
# ]

meta_data["resources"] = [{
    "name": table,
    "schema": {
        "fields": meta_fields
    },
    "dialect":"delimiter":";"
    "dialect:":"decimalSeparator":"."
    "Encoding":"unicode_escape"
}]

with open('meta_debug.json', 'w', encoding='utf-8') as f:
    json.dump(meta_data, f, ensure_ascii=False, indent=2)

########################################################################################################################
#   Upload Meta Data
########################################################################################################################
if WITH_UPLOAD:
    response = OepApi.upload_metadata(meta_data)
    print(response)

print(f"https://openenergyplatform.org/dataedit/view/{topic}/{table}")









