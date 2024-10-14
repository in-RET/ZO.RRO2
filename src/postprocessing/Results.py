#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 01:27:40 2024

@author: Melie
"""
from oemof.tools import economics
from oemof import network, solph
import pandas as pd
import os
workdir = os.getcwd()

# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
# %%

my_path = os.path.abspath(os.path.dirname(__file__))

energysystem = solph.EnergySystem()
energysystem.restore(my_path, os.path.join(workdir, '..', '..',
                     'dumps', '2030_BS0001', 'BS_regionalization_2030_BS0001.dump'))

# model_name '_' years '_' variations '.dump'

results = energysystem.results["main"]

print("Ende")


#%%
# define an alias for shorter calls below (optional)
Electricity_swest = solph.views.node(results, 'Electricity_swest')

#%%
# import os
# import pandas as pd
# from oemof.solph import views

# # Ordner für CSV-Dateien erstellen, falls noch nicht vorhanden
# output_dir = 'results_csv_output'
# if not os.path.exists(output_dir):
#     os.makedirs(output_dir)

# # Dictionary zur Verfolgung von bereits verarbeiteten Bussen
# processed_buses = {}

# # Funktion, um Ergebnisse in Spyder zu speichern
# def save_to_spyder(name, data):
#     globals()[name] = data  # Speichere Variable dynamisch in Spyder

# # Hauptschleife durch die Results-Keys
# for key, value in results.items():
#     for element in key:
#         if element is None:
#             continue  # Ignoriere None-Elemente
#         if "solph.buses._bus.Bus" in str(element):
#             # Extrahiere den Busnamen

#         # Überprüfen, ob es sich um einen Bus handelt
#             bus_name = element.split(": '")[1][:-2]
            
#             if bus_name not in processed_buses:
#                 # Bus mit solph auslesen
#                 bus_data = views.node(results, bus_name) 
                
#                 # Speichern in Spyder-Variable
#                 save_to_spyder(bus_name, bus_data)
                
#                 # Als CSV speichern
#                 csv_path = os.path.join(output_dir, f"{bus_name}.csv")
#                 bus_data.to_csv(csv_path)
                
#                 # Markiere den Bus als verarbeitet
#                 processed_buses[bus_name] = True

#         # Überprüfen, ob es sich um einen GenericStorage handelt
#         elif "solph.components._generic_storage.GenericStorage" in str(element):
#             # Extrahiere den Speicher-Namen
#             storage_name = element.split(": '")[1][:-2]
            
#             # Verarbeite den GenericStorage (nicht iterierbar)
#             if storage_name not in processed_buses:
#                 # Speicher mit solph auslesen
#                 storage_data = views.node(results, storage_name)
                
#                 # Speichern in Spyder-Variable
#                 save_to_spyder(storage_name, storage_data)
                
#                 # Als CSV speichern
#                 csv_path = os.path.join(output_dir, f"{storage_name}.csv")
#                 storage_data.to_csv(csv_path)
                
#                 # Markiere den Speicher als verarbeitet
#                 processed_buses[storage_name] = True


#%%


import os
import re
import pandas as pd
from oemof.solph import views

# Ordner für CSV-Dateien erstellen, falls noch nicht vorhanden
output_dir = 'results_csv_output'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Dictionary zur Verfolgung von bereits verarbeiteten Namen
processed_names = {}

# Funktion, um Ergebnisse in Spyder zu speichern
def save_to_spyder(name, data):
    globals()[name] = data  # Speichere Variable dynamisch in Spyder

# Logging-Funktion
def log_message(message):
    print(message)

# Regulärer Ausdruck zum Extrahieren von Namen in Hochkommas
name_pattern = re.compile(r"(?:Bus:|GenericStorage:)\s*'([^']*)'")

# Anzahl der Einträge in results ausgeben
log_message(f"Anzahl der Einträge in results: {len(results)}")

# Hauptschleife durch die Results-Keys
for key, value in results.items():
    log_message(f"Verarbeite Key: {key}")  # Loggen des aktuellen Keys

    # Variable für den extrahierten Namen (Bus oder GenericStorage)
    extracted_name = None

    # Schleife durch die Elemente des Tuples
    for element in key:
        if element is None:
            log_message("Element ist None, wird übersprungen.")
            continue  # Ignoriere None-Elemente

        # Überprüfen, ob es sich um einen Bus handelt
        if "solph.buses._bus.Bus" in str(key):
            log_message(f"Bus gefunden im Key: {key}")
            # Extrahiere den Busnamen mit regulärem Ausdruck
            match = name_pattern.search(str(key))
            if match:
                extracted_name = match.group(1)
                log_message(f"Bus-Name extrahiert: {extracted_name}")
                break  # Sobald ein Bus gefunden wurde, Schleife abbrechen

        # Überprüfen, ob es sich um einen GenericStorage handelt
        elif "solph.components._generic_storage.GenericStorage" in str(key):
            log_message(f"GenericStorage gefunden im Key: {key}")
            # Extrahiere den GenericStorage-Namen mit regulärem Ausdruck
            match = name_pattern.search(str(key))
            if match:
                extracted_name = match.group(1)
                log_message(f"GenericStorage-Name extrahiert: {extracted_name}")
                break  # Sobald ein GenericStorage gefunden wurde, Schleife abbrechen

    # Wenn kein Name gefunden wurde, überspringen
    if not extracted_name:
        log_message("Kein gültiger Name gefunden, Eintrag wird übersprungen.")
        continue

    # Verarbeite den Namen, wenn er noch nicht verarbeitet wurde
    if extracted_name not in processed_names:
        # Versuche, die Daten mit solph auszulesen
        try:
            node_data = solph.views.node(results, extracted_name)
            if node_data is None:
                log_message(f"Keine Daten für: {extracted_name}")
                continue

            # Speichern in Spyder-Variable
            save_to_spyder(extracted_name, node_data)

            # Als CSV speichern
            csv_path_bus = os.path.join(output_dir, f"{extracted_name}_bus.csv")
            node_data['sequences'].applymap(lambda x: str(x).replace('.', ',')).to_csv(csv_path_bus, sep=';', index=True)
            log_message(f"CSV für {extracted_name} gespeichert unter: {csv_path_bus}")

            csv_path_bussum = os.path.join(output_dir, f"{extracted_name}_bussum.csv")
            # (pd.concat
            (node_data['sequences'].sum()).applymap(lambda x: str(x).replace('.', ',')).to_csv(csv_path_bussum, sep=';', index=True)
             # )
            log_message(f"CSV für {extracted_name} gespeichert unter: {csv_path_bussum}")


            
            # Markiere den Namen als verarbeitet
            processed_names[extracted_name] = True

        except Exception as e:
            log_message(f"Fehler beim Auslesen oder Speichern für {extracted_name}: {e}")

# Busses+name+= pd.concat([
#                 Strombus['sequences'].sum(),
#                 Gasbus['sequences'].sum(),
#                 Oelbus['sequences'].sum(),
#                 Biobus['sequences'].sum(),
#                 BioHolzbus['sequences'].sum(),
#                 Fernwbus['sequences'].sum(),
#                 Wasserstoffbus['sequences'].sum()
#                 ])
# Busse.to_csv('../04_Ergebnisse/'+name+'_Busse.csv', decimal=',', sep=';')

#%%
# Gasbus = solph.views.node(results, 'Gas')
# Oelbus = solph.views.node(results, 'Oel_Kraftstoffe')
# Biobus = solph.views.node(results, 'Bio')
# BioHolzbus = solph.views.node(results, 'BioHolz')
# Fernwbus = solph.views.node(results, 'Fernwaerme')
# Wasserstoffbus = solph.views.node(results, 'Wasserstoff')
# Syntbus = solph.views.node(results, 'Synthetische_Kraftstoffe')
# Natriumspeicher = solph.views.node(results, 'Batterie')
# Waermespeicher_results = solph.views.node(results, 'Waermespeicher')
# Pumpspeicherkraftwerk_results = solph.views.node(results, 'Pumpspeicherkraftwerk')
# Erdgasspeicher_results = solph.views.node(results, 'Erdgasspeicher')
# H2speicher_results = solph.views.node(results, 'H2speicher')


# Ergebnisse= pd.Series([ NaN,
#                         Strombus['scalars'][7]+Strombus['scalars'][4]+Strombus['scalars'][5]+Strombus['scalars'][6],
#                         Strombus['scalars'][11]+Strombus['scalars'][8]+Strombus['scalars'][9]+Strombus['scalars'][10],
#                         Strombus['scalars'][19]+Strombus['scalars'][16]+Strombus['scalars'][17]+Strombus['scalars'][18],
#                         Fernwbus['scalars'][3],
#                         Strombus['scalars'][15],
#                         Strombus['scalars'][1],
#                         Strombus['scalars'][2],
#                         Fernwbus['scalars'][0],
#                         Fernwbus['scalars'][1],
#                         Wasserstoffbus['scalars'][0],
#                         Strombus['scalars'][20],
#                         Gasbus['scalars'][5],
#                         Gasbus['scalars'][0],
#                         Gasbus['scalars'][1],
#                         Strombus['scalars'][3],
#                         Gasbus['scalars'][4],
#                         Fernwbus['scalars'][5],
#                         Fernwbus['scalars'][4],
#                         Oelbus['scalars'][0],
#                         NaN,
#                         Natriumspeicher['scalars'][1],
#                         Waermespeicher_results['scalars'][3],
#                         Pumpspeicherkraftwerk_results['scalars'][1],
#                         Erdgasspeicher_results['scalars'][2],
#                         H2speicher_results['scalars'][1],
#                         NaN,
#                         Emissionen_Gasimport,
#                         Emissionen_Oelimport,
#                         0,
#                         NaN,
#                         Annuitaet_Capex_ges/1000000,
#                         Opex_ges/1000000, 
#                         gewinn*(-1)/1000000, 
#                         Jahresleistungspreis/1000000, 
#                         (Kosten_total+Jahresleistungspreis)/1000000,
           
#                         ],
#                 index=['Leistungen',
#                        'PV_Dach',
#                        'PV_Feld',
#                        'Wind',
#                        'Solarthermie',
#                        'Wasser',
#                        'Biogas_el',
#                        'Biomasse_Strom',
#                        'Biomasse_Waerme',
#                        'Heizstab',
#                        'E-lyse',
#                        'Brennstoffzelle',
#                        'Wasserstoffeinspeisung',
#                        'B2G_Best.',
#                        'B2G_Neu',
#                        'GuD',
#                        'Methanisierung',
#                        'WP_Fluss',
#                        'WP_Abwaerme',
#                        'PtL',
#                        'Speicherkapazitäten',
#                        'Natriumspeicher',
#                        'Wärmespeicher',
#                        'Pumpspeicher',
#                        'Erdgasspeicher',
#                        'Wasserstoffspeicher',
#                        'Emissionen',
#                        'Gasemissionen',
#                        'Oelemissionen',
#                        'Stromemissionen',
#                        'Kosten',
#                        'Annuität', 
#                        'OPEX', 
#                        'Im-/Export',
#                        'Netz', 
#                        'Gesamtkosten',
                                    
#                                  ])


# Ergebnisse.to_csv('../04_Ergebnisse/'+name+'_Ergebnisse.csv', decimal=',', )#sep=';')
    
# #------------------------------------------------------------------------------
# # Ergebnisse der Busse
# #------------------------------------------------------------------------------    
# Busse= pd.concat([
#                 Strombus['sequences'].sum(),
#                 Gasbus['sequences'].sum(),
#                 Oelbus['sequences'].sum(),
#                 Biobus['sequences'].sum(),
#                 BioHolzbus['sequences'].sum(),
#                 Fernwbus['sequences'].sum(),
#                 Wasserstoffbus['sequences'].sum()
#                 ])
# Busse.to_csv('../04_Ergebnisse/'+name+'_Busse.csv', decimal=',', sep=';')

# Strombus['sequences'].to_csv('../04_Ergebnisse/'+name+'Strombus_sequences.csv', decimal=',')
# Gasbus['sequences'].to_csv('../04_Ergebnisse/'+name+'Gasbus_sequences.csv', decimal=',')
# Oelbus['sequences'].to_csv('../04_Ergebnisse/'+name+'Oelbus_sequences.csv', decimal=',')
# Biobus['sequences'].to_csv('../04_Ergebnisse/'+name+'Biobus_sequences.csv', decimal=',')
# BioHolzbus['sequences'].to_csv('../04_Ergebnisse/'+name+'BioHolzbus_sequences.csv', decimal=',')
# Fernwbus['sequences'].to_csv('../04_Ergebnisse/'+name+'Fernwbus_sequences.csv', decimal=',')
# Wasserstoffbus['sequences'].to_csv('../04_Ergebnisse/'+name+'Wasserstoffbus_sequences.csv', decimal=',')
