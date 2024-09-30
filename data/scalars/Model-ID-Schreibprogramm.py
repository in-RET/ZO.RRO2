# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 15:27:10 2024

@author: aoberdorfer
"""

import os
import pandas as pd

# Ordnerpfad, in dem das Skript liegt
folder_path = os.path.dirname(os.path.abspath(__file__))

# Alle CSV-Dateien, die mit "Parameter_" beginnen
csv_files = [f for f in os.listdir(folder_path) if f.startswith("Parameter_") and f.endswith(".csv")]

# Durchlaufe alle gefundenen Dateien
for file in csv_files:
    file_path = os.path.join(folder_path, file)
    
    try:
        # CSV-Datei mit Fehlerbehebung einlesen (inkonsistente Spaltenanzahl ignorieren)
        df = pd.read_csv(file_path, error_bad_lines=False, warn_bad_lines=True)
        
        # In die erste Spalte der zweiten Zeile "BS0001" einfügen (Index 1 für die zweite Zeile)
        df.iloc[1, 0] = "BS0001"
        
        # Datei wieder speichern
        df.to_csv(file_path, index=False)
        
        print(f"Datei {file} erfolgreich angepasst.")
    
    except Exception as e:
        print(f"Fehler beim Verarbeiten der Datei {file}: {e}")

print(f"{len(csv_files)} Dateien wurden bearbeitet.")
