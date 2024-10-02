# -*- coding: utf-8 -*-
"""
Created on Thu Sep 19 15:27:10 2024

@author: aoberdorfer
"""

import os
import csv

def is_float(value):
    """Hilfsfunktion, um zu prüfen, ob ein Wert eine Zahl ist."""
    try:
        float(value)
        return True
    except ValueError:
        return False

def multiply_second_row_by_1000():
    # Verzeichnis des laufenden Skripts ermitteln
    directory = os.path.dirname(os.path.abspath(__file__))
    
    # Alle Dateien im aktuellen Verzeichnis durchsuchen
    for filename in os.listdir(directory):
        # Nur Dateien, die mit 'Parameter_' beginnen und auf '.csv' enden, werden verarbeitet
        if filename.startswith("Parameter_") and filename.endswith(".csv"):
            file_path = os.path.join(directory, filename)
            
            # CSV-Datei einlesen
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = list(csv.reader(csvfile))
                
                # Sicherstellen, dass es mindestens drei Zeilen gibt (Überschrift + mindestens 2 Datenzeilen)
                if len(reader) >= 3:
                    # Die dritte Zeile (Excel Zeile 3, Python Index 2) - zweite Datenzeile ohne Überschrift
                    third_row = reader[2]
                    
                    # Überprüfen, ob die zweite und folgende Spalten numerisch sind
                    if all(is_float(value) for value in third_row[1:]):  # Erste Spalte (Index 0) überspringen
                        # Die Werte ab der zweiten Spalte (Index 1) mit 1000 multiplizieren
                        reader[2] = [third_row[0]] + [str(float(value) * 1000) for value in third_row[1:]]
                    else:
                        # Datei überspringen, wenn keine Zahlen in der dritten Zeile vorhanden sind
                        print(f"Überspringe Datei {filename}, da keine Zahlen in der dritten Zeile vorhanden sind.")
                        continue
            
            # Datei mit den neuen Werten überschreiben
            with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(reader)

# Funktion aufrufen
multiply_second_row_by_1000()




