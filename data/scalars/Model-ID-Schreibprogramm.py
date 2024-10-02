# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 15:27:10 2024

@author: aoberdorfer
"""

import os
import csv

def multiply_second_row_by_1000(directory):
    # Alle Dateien im angegebenen Verzeichnis durchsuchen
    for filename in os.listdir(directory):
        # Nur Dateien, die mit 'Parameter_' beginnen und auf '.csv' enden, werden verarbeitet
        if filename.startswith("Parameter_") and filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            
            # CSV-Datei einlesen
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = list(csv.reader(csvfile))
                
                # Sicherstellen, dass es mindestens drei Zeilen gibt (Überschrift + mindestens 2 Datenzeilen)
                if len(reader) >= 3:
                    # Die zweite Zeile (Index 2, da die Überschrift die erste ist) bearbeiten
                    reader[2] = [str(float(value) * 1000) for value in reader[2]]
            
            # Datei mit den neuen Werten überschreiben
            with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(reader)


current_dir = os.getcwd()

# Beispielaufruf: Verzeichnis angeben, in dem die CSV-Dateien liegen
multiply_second_row_by_1000(os.listdir(current_dir))

