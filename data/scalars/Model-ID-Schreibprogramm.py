# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 15:27:10 2024

@author: aoberdorfer
"""

import os
import pandas as pd

# Funktion zum Anpassen und Verarbeiten der CSV-Dateien
def process_csv_files():
    # Durchlaufe alle Dateien im aktuellen Verzeichnis
    for filename in os.listdir('.'):
        if filename.startswith("Parameter_") and filename.endswith(".csv"):
            # Datei einlesen
            df = pd.read_csv(filename, sep=';', decimal=',', header=0)
            
            # Sicherstellen, dass mindestens 3 Zeilen vorhanden sind
            if len(df) >= 3:
                try:
                    # Spalten 2 bis 8 in der 3. Zeile (index 2) mit 1000 multiplizieren, falls numerisch
                    df.iloc[1, 1:8] = pd.to_numeric(df.iloc[1, 1:8], errors='coerce') * 1000
                    
                    # Datei nach Anpassung speichern
                    df.to_csv(filename, sep=';', decimal=',', index=False)
                    print(f"Datei '{filename}' erfolgreich angepasst.")
                except Exception as e:
                    print(f"Fehler beim Verarbeiten der Datei '{filename}': {e}")
            else:
                print(f"Datei '{filename}' übersprungen (nicht genug Zeilen).")

# Funktion ausführen
process_csv_files()



