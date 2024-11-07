# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 11:17:58 2024

@author: hhauer
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import glob

name = os.path.basename(__file__)
name = name.replace(".py", "")
my_path = os.path.abspath(os.path.dirname(__file__))

# Definition der Schriftgröße
plt.rcParams.update({'font.size': 10})
# Definition der Linienstärke
plt.rcParams['lines.linewidth'] = 1

#%% Einlesen der Parameterdateien 

## Verzeichnis festlegen (gleiche Ebene wie das Skript)
input_path = './Parameter'

# Alle Parameter-Dateien mit dem Muster "Parameter_*.csv" auslesen
parameter_csv_files = glob.glob(os.path.join(input_path, 'Parameter_*.csv'))

# Dictionary zum Speichern der DataFrames und Liste für die Labels
parameter_dataframes = {}
labels = []

for filepath in parameter_csv_files:
    # Dateiname ohne Pfad und Dateiendung
    filename = os.path.basename(filepath)
    parameter_name = filename.split('Parameter_')[-1].split('.')[0]
    
    # Einlesen der Datei und Extrahieren der ersten 7 Zeilen für die Spaltennamen
    df = pd.read_csv(filepath, nrows=7, encoding='unicode_escape', sep=';', decimal=',')
    
    # Spaltennamen setzen, indem die erste Zeile des DataFrames als Spaltenüberschrift genommen wird (außer erste Spalte)
    new_column_names = df.iloc[0, 1:].tolist()
    df = pd.read_csv(filepath, skiprows=7, usecols=range(1, 8), encoding='unicode_escape', sep=';', decimal=',', index_col=0)
    df.columns = new_column_names
    
    # DataFrame und Label in Dictionary und Liste speichern
    parameter_dataframes[parameter_name] = df
    labels.append(parameter_name)

# Beispiel: Zugriff auf spezifische DataFrames
# Wind = parameter_dataframes.get('onshore_wind_power_plant')
# PV_Dach = parameter_dataframes.get('rooftop_photovoltaic_power_plant')
# PV_FF = parameter_dataframes.get('field_photovoltaic_power_plant')

# Alle DataFrames in einer Liste speichern, falls sie zusammengefasst werden sollen
data_frames = list(parameter_dataframes.values())

# Labels entsprechend der Dateinamenliste
print("DataFrames:", parameter_dataframes)
print("Labels:", labels)

# Farben der Technologien
Color_Wind = '#3e9bfe'
Color_PV_Dach = '#46f783'
Color_PV_FF = '#e1dc37'
Color_Wasser = '#ef5a11'

#%% Plot

# # ganzer Plot Hintergrundfarbe (Tabellengrün in LaTex Datei), schwarzer Rand
# fig, ax = plt.subplots(figsize=(6.3,6.5), facecolor=(0.4,0.74,0,0.2), linewidth=0.3, edgecolor='black')

# #Platzierung des Plots, anpassbar bei Ausgabe des Plots in der Menüleiste, Symbol mit drei Schiebeschalter 
# # (zwischen Lupe und Graph, 'configure subplots'), mit 'export values' einfach hier reinkopierbar
# plt.subplots_adjust(top=0.945,
# bottom=0.165,
# left=0.155,
# right=0.92,
# hspace=0.3,
# wspace=0.2)

# # Zur Automatisierung des Erstellens des Plots hier die Dataframes der Technologien die geplottet werden 
# # sollen einfügen (plus dazugehörige Farben und Labels) 
# data_frames = [Wind, PV_Dach, PV_FF]
# colors = [Color_Wind, Color_PV_Dach, Color_PV_FF]
# labels = ['Wind', 'PV Dach', 'PV Freifeld']

# # Linien BS0002
# for df, color, label in zip(data_frames, colors, labels):
#     plt.plot(df.loc['BS0002']/1000, color=color, label=f'{label} BS0002')

# # Spanne zwischen Unter- und Obergrenze
# for df, color, label in zip(data_frames, colors, labels):
#     plt.fill_between(df.columns, df.loc['Untergrenze']/1000, df.loc['Obergrenze']/1000, 
#                      color=color, alpha=0.1, label=f'Abweichung {label} ')

# # Punkte BS0001 (als Linienplot ohne Linie, nur Marker)
# for df, color, label in zip(data_frames, colors, labels):
#     plt.plot(df.loc['BS0001']/1000, color=color, label=f'{label} BS0001', linestyle='None', marker='o')

# # Vertikale Linien an der Stelle der Datenpunkte (Jahren)
# for i, x in enumerate(Wind.columns):
#     for df, color, label in zip(data_frames, colors, labels):
#         plt.vlines(x, df.loc['Untergrenze', x]/1000, df.loc['Obergrenze', x]/1000, 
#                color='black', linestyle='-', linewidth=1)

# # Legende, Titel und Beschriftung Y-Achse 
# plt.legend(loc='upper center', bbox_to_anchor=(0.45, -0.05), ncols=3)
# ax.set_ylabel('Preis in €/kW')
# ax.set_title('Parameterstudie', weight='bold')

# plt.show()
# ordner = my_path + '/Bilder'
# name = 'Parameterstudie.png'
# fig.savefig(f"{ordner}/{name}", dpi=600, format='png', edgecolor=fig.get_edgecolor())