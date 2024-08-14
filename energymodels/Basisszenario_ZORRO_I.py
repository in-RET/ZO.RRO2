# -*- coding: utf-8 -*-
"""
Created on Tue May 28 13:49:27 2024

@author: rbala

Infos zum Modell:
    Projekt: ZO.RRO
    Modell: Basisszenario 2030
    version:
        oemof: v0.5.2
        
Ändereungen von alte Basisszenario sind in Kommentaren beschrieben    
"""

__copyright__ = "oemof developer group"
__license__ = "GPLv3"

from oemof.tools import logger
from oemof import solph
import logging

import os
import pandas as pd
import matplotlib
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None
from oemof.tools import economics
matplotlib.pyplot.margins
from oemof.solph._plumbing import sequence            # _plumbing statt plumbing, war in neue version umbennant
from oemof.solph import constraints
import pyomo.environ as po


name = os.path.basename(__file__)
name = 'BS030002'#name.replace(".py", "")
my_path = os.path.abspath(os.path.dirname(__file__))
results_path = os.path.abspath(os.path.join(my_path, '..', 'results', name))
if not os.path.isdir(results_path):
    os.makedirs(results_path)
    
Zeitreihen = os.path.abspath(os.path.join(my_path,'..', 'data/sequences','00_ZORRO_I_old_sequences'))                # pfad für Zeitreihen und Eingangsdaten als variable --> besser nachzufolgen im script.
Eingangsdaten = os.path.abspath(os.path.join(my_path,'..', 'data/scalars','00_ZORRO_I_old_scalars'))

#%% Einlesen von Eingangsdaten und Zeitreihen
'Zeitreihen'
###############################################################################
pfad = os.path.join(Zeitreihen,'Einspeiseprofile_Stundenwerte.csv')
Einspeiseprofile_Stundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',')
###############################################################################
pfad = os.path.join(Zeitreihen,'Einspeiseprofile_Viertelstundenwerte.csv')
Einspeiseprofile_Viertelstundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',')
###############################################################################
pfad = os.path.join(Zeitreihen,'Einspeiseprofile_neu_2024_nicht skaliert.csv')
Einspeiseprofile_stundenwerte_neu = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',')
###############################################################################
pfad = os.path.join(Zeitreihen,'Lastprofile_Stundenwerte.csv')
Lastprofile_Stundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',')
###############################################################################
pfad = os.path.join(Zeitreihen,'Lastprofile_Viertelstundenwerte.csv')
Lastprofile_Viertelstundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',')
###############################################################################
# pfad = os.path.join(Zeitreihen,'Preise_2030_Stundenwerte_Variation10047.csv')
# Preise_2030_Stundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',') 
###############################################################################

pfad = os.path.join(Zeitreihen,'Preise_2030_Stundenwerte.csv')
Preise_2030_Stundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',') #alte Brainpool preiszeitreihen

'Eingangsdaten'
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_Industrie_2030.csv')
data_Industrie = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_Industrie_Prozesswaerme_2030.csv')
data_Industrie_Prozesswaerme = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_GHD_2030.csv')
data_GHD = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_Haushalte_2030.csv')
data_Haushalte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_Verkehr_2030.csv')
data_Verkehr = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_GuD_2030.csv')
Parameter_GuD_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Biomasse_Biogas_2030.csv')
Parameter_Biomasse_Biogas_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Biogaseinspeisung_2030.csv')
Parameter_Biogaseinspeisung_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Brennstoffzelle_Methanisierung_PtL_2030.csv')
Parameter_Brennstoffzelle_Methanisierung_PtL_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Elektrolyse_Elektrodenheizkessel_2030.csv')
Parameter_Elektrolyse_Elektrodenheizkessel_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Waermepumpen_2030.csv')
Parameter_Waermepumpen_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_PV_Wind_2030.csv')
Parameter_PV_Wind_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030.csv')
Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Waermespeicher_2030.csv')
Parameter_Waermespeicher_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Pumpspeicher_2030.csv')
Parameter_Pumpspeicher_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_ST_2030.csv')
Parameter_ST_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Wasserkraft_2030.csv')
Parameter_Wasserkraft_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Wasserstoffeinspeisung_2030.csv')
Parameter_Wasserstoffeinspeisung_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Stromnetz_2030.csv')
Parameter_Stromnetz_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Parameter_Wasserstoffnetz_2030.csv')
Parameter_Wasserstoffnetz_2030 = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Systemeigenschaften.csv')
data_Systemeigenschaften = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################

#%%
# Definition der Anzahl der Zeitschritte pro Simulationsdurchlauf
number_of_time_steps = int(data_Systemeigenschaften['System']['Anzahl_Zeitschritte'])

#%% CO2-Preis für 2030 wird zu den fossilen Rohstoffpreisen aufgeschlagen
Import_Erdgaspreis_2030 = [None] * number_of_time_steps
Import_Oelpreis_2030 = [None] * number_of_time_steps
Import_Steinkohlepreis_2030 = [None] * number_of_time_steps
Import_Braunkohlepreis_2030 = [None] * number_of_time_steps
for a in range(0, number_of_time_steps):
    Import_Erdgaspreis_2030[a]= Preise_2030_Stundenwerte['Erdgaspreis_2030'][a]+(data_Systemeigenschaften['System']['Emission_Erdgas']*data_Systemeigenschaften['System']['CO2_Preis_2030'])
    Import_Oelpreis_2030[a] = Preise_2030_Stundenwerte['Oelpreis_2030'][a]+(data_Systemeigenschaften['System']['Emission_Oel']*data_Systemeigenschaften['System']['CO2_Preis_2030'])
    Import_Steinkohlepreis_2030[a]=Preise_2030_Stundenwerte['Steinkohlepreis_2030'][a]+(data_Systemeigenschaften['System']['Emission_Steinkohle']*data_Systemeigenschaften['System']['CO2_Preis_2030'])
    Import_Braunkohlepreis_2030[a]=Preise_2030_Stundenwerte['Braunkohlepreis_2030'][a]+(data_Systemeigenschaften['System']['Emission_Braunkohle']*data_Systemeigenschaften['System']['CO2_Preis_2030'])
    
#%% Umrechnung von Viertelstunden- auf Stundenwerte

# data_Wind_Erfurt = [None]*number_of_time_steps
# data_Wind_Nordhausen = [None]*number_of_time_steps
# data_Wind_Gera = [None]*number_of_time_steps
# data_Wind_Hildburghausen = [None]*number_of_time_steps
# data_PV_Aufdach_Erfurt = [None]*number_of_time_steps
# data_PV_Aufdach_Nordhausen = [None]*number_of_time_steps
# data_PV_Aufdach_Gera = [None]*number_of_time_steps
# data_PV_Aufdach_Hildburghausen = [None]*number_of_time_steps
# data_PV_Freifeld_Erfurt = [None]*number_of_time_steps
# data_PV_Freifeld_Nordhausen = [None]*number_of_time_steps
# data_PV_Freifeld_Gera = [None]*number_of_time_steps
# data_PV_Freifeld_Hildburghausen = [None]*number_of_time_steps
data_Wasserkraft = [None]*number_of_time_steps
data_G3 = [None]*number_of_time_steps
data_G0 = [None]*number_of_time_steps
data_H0 = [None]*number_of_time_steps

i = 0
for a in range(0, number_of_time_steps):
    # Summe_Wind_Erfurt = 0
    # Summe_Wind_Nordhausen = 0
    # Summe_Wind_Gera = 0
    # Summe_Wind_Hildburghausen = 0
    # Summe_PV_Aufdach_Erfurt = 0
    # Summe_PV_Aufdach_Nordhausen = 0
    # Summe_PV_Aufdach_Gera = 0
    # Summe_PV_Aufdach_Hildburghausen = 0
    # Summe_PV_Freifeld_Erfurt = 0
    # Summe_PV_Freifeld_Nordhausen = 0
    # Summe_PV_Freifeld_Gera = 0
    # Summe_PV_Freifeld_Hildburghausen = 0
    Summe_Wasserkraft = 0
    Summe_data_G3 = 0
    Summe_data_G0 = 0
    Summe_data_H0 = 0
    #Bilde die Summe von 4 Werten hintereinander (den Werten von 4 Viertelstunden, sprich einer Stunde)
    for k in range(0, 4):
        # Summe_Wind_Erfurt += Einspeiseprofile_Viertelstundenwerte['Wind_Erfurt'][i]
        # Summe_Wind_Nordhausen += Einspeiseprofile_Viertelstundenwerte['Wind_Nordhausen'][i]
        # Summe_Wind_Gera += Einspeiseprofile_Viertelstundenwerte['Wind_Gera'][i]
        # Summe_Wind_Hildburghausen += Einspeiseprofile_Viertelstundenwerte['Wind_Hildburghausen'][i]
        # Summe_PV_Aufdach_Erfurt += Einspeiseprofile_Viertelstundenwerte['PV_Aufdach_Erfurt'][i]
        # Summe_PV_Aufdach_Nordhausen += Einspeiseprofile_Viertelstundenwerte['PV_Aufdach_Nordhausen'][i]
        # Summe_PV_Aufdach_Gera += Einspeiseprofile_Viertelstundenwerte['PV_Aufdach_Gera'][i]
        # Summe_PV_Aufdach_Hildburghausen += Einspeiseprofile_Viertelstundenwerte['PV_Aufdach_Hildburghausen'][i]
        # Summe_PV_Freifeld_Erfurt += Einspeiseprofile_Viertelstundenwerte['PV_Freifeld_Erfurt'][i]
        # Summe_PV_Freifeld_Nordhausen += Einspeiseprofile_Viertelstundenwerte['PV_Freifeld_Nordhausen'][i]
        # Summe_PV_Freifeld_Gera += Einspeiseprofile_Viertelstundenwerte['PV_Freifeld_Gera'][i]
        # Summe_PV_Freifeld_Hildburghausen += Einspeiseprofile_Viertelstundenwerte['PV_Freifeld_Hildburghausen'][i]
        Summe_Wasserkraft += Einspeiseprofile_Viertelstundenwerte['Wasserkraft'][i]
        Summe_data_G3 += (Lastprofile_Viertelstundenwerte['G3'][i])*4
        Summe_data_G0 += (Lastprofile_Viertelstundenwerte['G0'][i])*4
        Summe_data_H0 += (Lastprofile_Viertelstundenwerte['H0'][i])*4
        i += 1
    #Bilde ein Viertel vom stündlichen Mittelwert
    # data_Wind_Erfurt[a]=Summe_Wind_Erfurt/4
    # data_Wind_Nordhausen[a]=Summe_Wind_Nordhausen/4
    # data_Wind_Gera[a]=Summe_Wind_Gera/4
    # data_Wind_Hildburghausen[a]=Summe_Wind_Hildburghausen/4
    # data_PV_Aufdach_Erfurt[a] = Summe_PV_Aufdach_Erfurt/4
    # data_PV_Aufdach_Nordhausen[a] = Summe_PV_Aufdach_Nordhausen/4
    # data_PV_Aufdach_Gera[a] = Summe_PV_Aufdach_Gera/4
    # data_PV_Aufdach_Hildburghausen[a] = Summe_PV_Aufdach_Hildburghausen/4
    # data_PV_Freifeld_Erfurt[a] = Summe_PV_Freifeld_Erfurt/4
    # data_PV_Freifeld_Nordhausen[a] = Summe_PV_Freifeld_Nordhausen/4
    # data_PV_Freifeld_Gera[a] = Summe_PV_Freifeld_Gera/4
    # data_PV_Freifeld_Hildburghausen[a] = Summe_PV_Freifeld_Hildburghausen/4
    data_Wasserkraft[a] = Summe_Wasserkraft/4
    data_G3[a] = Summe_data_G3/4
    data_G0[a] = Summe_data_G0/4
    data_H0[a] = Summe_data_H0/4
    
data_Wind_Erfurt=Einspeiseprofile_stundenwerte_neu['Wind_Erfurt']
data_Wind_Nordhausen=Einspeiseprofile_stundenwerte_neu['Wind_Nordhausen']
data_Wind_Gera=Einspeiseprofile_stundenwerte_neu['Wind_Gera']
data_Wind_Hildburghausen=Einspeiseprofile_stundenwerte_neu['Wind_Hildburghausen']
data_PV_Aufdach_Erfurt = Einspeiseprofile_stundenwerte_neu['PV_rooftop_Erfurt']
data_PV_Aufdach_Nordhausen = Einspeiseprofile_stundenwerte_neu['PV_rooftop_Nordhausen']
data_PV_Aufdach_Gera = Einspeiseprofile_stundenwerte_neu['PV_rooftop_Gera']
data_PV_Aufdach_Hildburghausen = Einspeiseprofile_stundenwerte_neu['PV_rooftop_Hildburghausen']
data_PV_Freifeld_Erfurt = Einspeiseprofile_stundenwerte_neu['PV_open_Erfurt']
data_PV_Freifeld_Nordhausen = Einspeiseprofile_stundenwerte_neu['PV_open_Nordhausen']
data_PV_Freifeld_Gera = Einspeiseprofile_stundenwerte_neu['PV_open_Gera']
data_PV_Freifeld_Hildburghausen = Einspeiseprofile_stundenwerte_neu['PV_open_Hildburghausen']
#%%
def Nutz_zu_Endenergieumrechnung (NE_ges, NE_proz, h_voll, EER):
    # absoluter Nutzenergieanteil
    E_ges = (
                                (NE_ges *                                       # Nutzenergie gesamt
                                 NE_proz                                        # proz. Anteil an Nutzenergie im Bereich Strom durch Endgeräte
                                 )/(100)                                        # Umrechnung zwecks proz. Anteils
                            )*(10**(9)) / 3600                                  # Umrechnung von PJ zu MWh
    # norminelle Leisung für Nutzenergielastgang
    P_nom_NE = E_ges / h_voll                                                   # Division durch die Volllaststunden des Lastprofils
    # nominielle Leistung für Endenergielastgang
    P_nom_EE = P_nom_NE / EER                                                   # Division durch den Energy Efficency Ratio (Wirkungsgrad)
    
    return P_nom_EE

#%%
if 1==1:
    """
    Ab hier Industrie
    """
    #-------------------------------------------------------------------------
    # Industrie - Stromanwendungen --------------------------------------------
    P_nom_Industrie_Strom = Nutz_zu_Endenergieumrechnung(data_Industrie['Strom']['Summe'], data_Industrie['Strom']['Elektrogeraete'], sum(Lastprofile_Viertelstundenwerte['G3']), data_Industrie['EER']['Elektrogeraete'])
    
    # Industrie - Raumwärme | Warmwasser
    P_nom_Industrie_Raumwaerme_Heizstab = Nutz_zu_Endenergieumrechnung(data_Industrie['Raumwaerme']['Summe'], data_Industrie['Raumwaerme']['PtH Heizstab'], sum(Lastprofile_Stundenwerte['HA4']), data_Industrie['EER']['PtH Heizstab'])
    P_nom_Industrie_Raumwaerme_Luftwaermepumpe = Nutz_zu_Endenergieumrechnung(data_Industrie['Raumwaerme']['Summe'], data_Industrie['Raumwaerme']['PtH Luftwaermepumpe'], sum(Lastprofile_Stundenwerte['HA4']), data_Industrie['EER']['PtH Luftwaermepumpe'])
    P_nom_Industrie_Raumwaerme_Erdwaermepumpe = Nutz_zu_Endenergieumrechnung(data_Industrie['Raumwaerme']['Summe'], data_Industrie['Raumwaerme']['PtH Erdwaermepumpe'],  sum(Lastprofile_Stundenwerte['HA4']), data_Industrie['EER']['PtH Erdwaermepumpe'])
    P_nom_Industrie_Raumwaerme_Festbrennstoffkessel = Nutz_zu_Endenergieumrechnung(data_Industrie['Raumwaerme']['Summe'], data_Industrie['Raumwaerme']['Festbrennstoffkessel'], sum(Lastprofile_Stundenwerte['HA4']), data_Industrie['EER']['Festbrennstoffkessel'])
    P_nom_Industrie_Raumwaerme_Heizkessel_Gas = Nutz_zu_Endenergieumrechnung(data_Industrie['Raumwaerme']['Summe'], data_Industrie['Raumwaerme']['Heizkessel Gas'], sum(Lastprofile_Stundenwerte['HA4']), data_Industrie['EER']['Heizkessel Gas'])
    P_nom_Industrie_Raumwaerme_Heizkessel_Oel = Nutz_zu_Endenergieumrechnung(data_Industrie['Raumwaerme']['Summe'], data_Industrie['Raumwaerme']['Heizkessel Oel'], sum(Lastprofile_Stundenwerte['HA4']), data_Industrie['EER']['Heizkessel Oel'])
    P_nom_Industrie_Raumwaerme_Fernwaerme = Nutz_zu_Endenergieumrechnung(data_Industrie['Raumwaerme']['Summe'], data_Industrie['Raumwaerme']['Waermeuebergabestation'], sum(Lastprofile_Stundenwerte['HA4']), data_Industrie['EER']['Waermeuebergabestation'])
    
    # Industrie Prozesswärme---------------------------------------------------
    P_nom_Industrie_Prozesswaerme_Heizstab = Nutz_zu_Endenergieumrechnung(data_Industrie_Prozesswaerme['Prozesswaerme']['Summe'], data_Industrie_Prozesswaerme['Prozesswaerme']['PtH Heizstab'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_Industrie_Prozesswaerme['EER']['PtH Heizstab'])
    P_nom_Industrie_Prozesswaerme_Luftwaermepumpe = Nutz_zu_Endenergieumrechnung(data_Industrie_Prozesswaerme['Prozesswaerme']['Summe'], data_Industrie_Prozesswaerme['Prozesswaerme']['PtH Luftwaermepumpe'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_Industrie_Prozesswaerme['EER']['PtH Luftwaermepumpe'])
    P_nom_Industrie_Prozesswaerme_Erdwaermepumpe = Nutz_zu_Endenergieumrechnung(data_Industrie_Prozesswaerme['Prozesswaerme']['Summe'], data_Industrie_Prozesswaerme['Prozesswaerme']['PtH Erdwaermepumpe'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_Industrie_Prozesswaerme['EER']['PtH Erdwaermepumpe'])
    P_nom_Industrie_Prozesswaerme_Festbrennstoffkessel = Nutz_zu_Endenergieumrechnung(data_Industrie_Prozesswaerme['Prozesswaerme']['Summe'], data_Industrie_Prozesswaerme['Prozesswaerme']['Festbrennstoffkessel'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_Industrie_Prozesswaerme['EER']['Festbrennstoffkessel'])
    P_nom_Industrie_Prozesswaerme_Heizkessel_Gas = Nutz_zu_Endenergieumrechnung(data_Industrie_Prozesswaerme['Prozesswaerme']['Summe'], data_Industrie_Prozesswaerme['Prozesswaerme']['Heizkessel Gas'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_Industrie_Prozesswaerme['EER']['Heizkessel Gas'])
    P_nom_Industrie_Prozesswaerme_Heizkessel_Oel = Nutz_zu_Endenergieumrechnung(data_Industrie_Prozesswaerme['Prozesswaerme']['Summe'], data_Industrie_Prozesswaerme['Prozesswaerme']['Heizkessel Oel'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_Industrie_Prozesswaerme['EER']['Heizkessel Oel'])
    P_nom_Industrie_Prozesswaerme_Fernwaerme = Nutz_zu_Endenergieumrechnung(data_Industrie_Prozesswaerme['Prozesswaerme']['Summe'], data_Industrie_Prozesswaerme['Prozesswaerme']['Waermeuebergabestation'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_Industrie_Prozesswaerme['EER']['Waermeuebergabestation'])
    
    # Industrie Klima- und Prozesskälte----------------------------------------
    P_nom_Industrie_Prozesskaelte_Kompressionskaelte = Nutz_zu_Endenergieumrechnung(data_Industrie['Klima- und Prozesskaelte']['Summe'], data_Industrie['Klima- und Prozesskaelte']['Kompressionskaelte'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Industrie['EER']['Kompressionskaelte'])
    P_nom_Industrie_Prozesskaelte_Sorptionskaelte = Nutz_zu_Endenergieumrechnung(data_Industrie['Klima- und Prozesskaelte']['Summe'], data_Industrie['Klima- und Prozesskaelte']['Sorptionskaelte'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Industrie['EER']['Sorptionskaelte'])
    
    # Industrie stoffliche Nutzung-------------------------------------------------
    P_nom_Industrie_Materialnutzung_Gas = Nutz_zu_Endenergieumrechnung(data_Industrie['Stoffl_Nutzung_Gas']['Summe'], data_Industrie['Stoffl_Nutzung_Gas']['Materialnutzung'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Industrie['EER']['Materialnutzung'])
    P_nom_Industrie_Materialnutzung_Oel = Nutz_zu_Endenergieumrechnung(data_Industrie['Stoffl_Nutzung_Oel']['Summe'], data_Industrie['Stoffl_Nutzung_Oel']['Materialnutzung'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Industrie['EER']['Materialnutzung'])
  
    """
    Ab hier GHD
    """
    
    # GHD - Stromanwendungen --------------------------------------------------
    P_nom_GHD_Strom = Nutz_zu_Endenergieumrechnung(data_GHD['Strom']['Summe'], data_GHD['Strom']['Elektrogeraete'], sum(Lastprofile_Viertelstundenwerte['G0']), data_GHD['EER']['Elektrogeraete'])
    
    # GHD Raumwaerme | Warmwasser ---------------------------------------------
    P_nom_GHD_Raumwaerme_Heizstab = Nutz_zu_Endenergieumrechnung(data_GHD['Raumwaerme']['Summe'], data_GHD['Raumwaerme']['PtH Heizstab'], sum(Lastprofile_Stundenwerte['HA4']), data_GHD['EER']['PtH Heizstab'])
    P_nom_GHD_Raumwaerme_Luftwaermepumpe = Nutz_zu_Endenergieumrechnung(data_GHD['Raumwaerme']['Summe'], data_GHD['Raumwaerme']['PtH Luftwaermepumpe'], sum(Lastprofile_Stundenwerte['HA4']), data_GHD['EER']['PtH Luftwaermepumpe'])
    P_nom_GHD_Raumwaerme_Erdwaermepumpe = Nutz_zu_Endenergieumrechnung(data_GHD['Raumwaerme']['Summe'], data_GHD['Raumwaerme']['PtH Erdwaermepumpe'], sum(Lastprofile_Stundenwerte['HA4']), data_GHD['EER']['PtH Erdwaermepumpe'])
    P_nom_GHD_Raumwaerme_Festbrennstoffkessel = Nutz_zu_Endenergieumrechnung(data_GHD['Raumwaerme']['Summe'], data_GHD['Raumwaerme']['Festbrennstoffkessel'], sum(Lastprofile_Stundenwerte['HA4']), data_GHD['EER']['Festbrennstoffkessel'])
    P_nom_GHD_Raumwaerme_Heizkessel_Gas = Nutz_zu_Endenergieumrechnung(data_GHD['Raumwaerme']['Summe'], data_GHD['Raumwaerme']['Heizkessel Gas'], sum(Lastprofile_Stundenwerte['HA4']), data_GHD['EER']['Heizkessel Gas'])
    P_nom_GHD_Raumwaerme_Heizkessel_Oel = Nutz_zu_Endenergieumrechnung(data_GHD['Raumwaerme']['Summe'], data_GHD['Raumwaerme']['Heizkessel Oel'], sum(Lastprofile_Stundenwerte['HA4']), data_GHD['EER']['Heizkessel Oel'])
    P_nom_GHD_Raumwaerme_Fernwaerme = Nutz_zu_Endenergieumrechnung(data_GHD['Raumwaerme']['Summe'], data_GHD['Raumwaerme']['Waermeuebergabestation'], sum(Lastprofile_Stundenwerte['HA4']), data_GHD['EER']['Waermeuebergabestation'])
    
    # GHD Prozesswärme---------------------------------------------------------
    P_nom_GHD_Prozesswaerme_Heizstab = Nutz_zu_Endenergieumrechnung(data_GHD['Prozesswaerme']['Summe'], data_GHD['Prozesswaerme']['PtH Heizstab'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_GHD['EER']['PtH Heizstab'])
    P_nom_GHD_Prozesswaerme_Luftwaermepumpe = Nutz_zu_Endenergieumrechnung(data_GHD['Prozesswaerme']['Summe'], data_GHD['Prozesswaerme']['PtH Luftwaermepumpe'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_GHD['EER']['PtH Luftwaermepumpe'])
    P_nom_GHD_Prozesswaerme_Erdwaermepumpe = Nutz_zu_Endenergieumrechnung(data_GHD['Prozesswaerme']['Summe'], data_GHD['Prozesswaerme']['PtH Erdwaermepumpe'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_GHD['EER']['PtH Erdwaermepumpe'])
    P_nom_GHD_Prozesswaerme_Festbrennstoffkessel = Nutz_zu_Endenergieumrechnung(data_GHD['Prozesswaerme']['Summe'], data_GHD['Prozesswaerme']['Festbrennstoffkessel'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_GHD['EER']['Festbrennstoffkessel'])
    P_nom_GHD_Prozesswaerme_Heizkessel_Gas = Nutz_zu_Endenergieumrechnung(data_GHD['Prozesswaerme']['Summe'], data_GHD['Prozesswaerme']['Heizkessel Gas'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_GHD['EER']['Heizkessel Gas'])
    P_nom_GHD_Prozesswaerme_Heizkessel_Oel = Nutz_zu_Endenergieumrechnung(data_GHD['Prozesswaerme']['Summe'], data_GHD['Prozesswaerme']['Heizkessel Oel'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_GHD['EER']['Heizkessel Oel'])
    P_nom_GHD_Prozesswaerme_Fernwaerme = Nutz_zu_Endenergieumrechnung(data_GHD['Prozesswaerme']['Summe'], data_GHD['Prozesswaerme']['Waermeuebergabestation'], sum(Lastprofile_Stundenwerte['Prozessgas']), data_GHD['EER']['Waermeuebergabestation'])
    
    
    # GHD Klima- und Prozesskälte----------------------------------------------
    P_nom_GHD_Prozesskaelte_Kompressionskaelte = Nutz_zu_Endenergieumrechnung(data_GHD['Klima- und Prozesskaelte']['Summe'], data_GHD['Klima- und Prozesskaelte']['Kompressionskaelte'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_GHD['EER']['Kompressionskaelte'])
    P_nom_GHD_Prozesskaelte_Sorptionskaelte = Nutz_zu_Endenergieumrechnung(data_GHD['Klima- und Prozesskaelte']['Summe'], data_GHD['Klima- und Prozesskaelte']['Sorptionskaelte'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_GHD['EER']['Sorptionskaelte'])

    """
    Ab hier Haushalte
    """
    
    # Haushalte - Stromanwendungen --------------------------------------------
    P_nom_Haushalte_Strom = Nutz_zu_Endenergieumrechnung(data_Haushalte['Strom']['Summe'], data_Haushalte['Strom']['Elektrogeraete'], sum(Lastprofile_Viertelstundenwerte['H0']), data_Haushalte['EER']['Elektrogeraete'])
    
    # Haushalte Raumwärme | Warmwasser ----------------------------------------
    P_nom_Haushalte_Raumwaerme_Heizstab = Nutz_zu_Endenergieumrechnung(data_Haushalte['Raumwaerme']['Summe'], data_Haushalte['Raumwaerme']['PtH Heizstab'], sum(Lastprofile_Stundenwerte['T24']), data_Haushalte['EER']['PtH Heizstab'])
    P_nom_Haushalte_Raumwaerme_Luftwaermepumpe = Nutz_zu_Endenergieumrechnung(data_Haushalte['Raumwaerme']['Summe'], data_Haushalte['Raumwaerme']['PtH Luftwaermepumpe'], sum(Lastprofile_Stundenwerte['T24']), data_Haushalte['EER']['PtH Luftwaermepumpe'])
    P_nom_Haushalte_Raumwaerme_Erdwaermepumpe = Nutz_zu_Endenergieumrechnung(data_Haushalte['Raumwaerme']['Summe'], data_Haushalte['Raumwaerme']['PtH Erdwaermepumpe'], sum(Lastprofile_Stundenwerte['T24']), data_Haushalte['EER']['PtH Erdwaermepumpe'])
    P_nom_Haushalte_Raumwaerme_Festbrennstoffkessel = Nutz_zu_Endenergieumrechnung(data_Haushalte['Raumwaerme']['Summe'], data_Haushalte['Raumwaerme']['Festbrennstoffkessel'], sum(Lastprofile_Stundenwerte['T24']), data_Haushalte['EER']['Festbrennstoffkessel'])
    P_nom_Haushalte_Raumwaerme_Heizkessel_Gas = Nutz_zu_Endenergieumrechnung(data_Haushalte['Raumwaerme']['Summe'], data_Haushalte['Raumwaerme']['Heizkessel Gas'], sum(Lastprofile_Stundenwerte['T24']), data_Haushalte['EER']['Heizkessel Gas'])
    P_nom_Haushalte_Raumwaerme_Heizkessel_Oel = Nutz_zu_Endenergieumrechnung(data_Haushalte['Raumwaerme']['Summe'], data_Haushalte['Raumwaerme']['Heizkessel Oel'], sum(Lastprofile_Stundenwerte['T24']), data_Haushalte['EER']['Heizkessel Oel'])
    P_nom_Haushalte_Raumwaerme_Fernwaerme = Nutz_zu_Endenergieumrechnung(data_Haushalte['Raumwaerme']['Summe'], data_Haushalte['Raumwaerme']['Waermeuebergabestation'], sum(Lastprofile_Stundenwerte['T24']), data_Haushalte['EER']['Waermeuebergabestation'])
    
    # Haushalte Klimakälte-----------------------------------------------------
    P_nom_Haushalte_Klimakaelte_Kompressionskaelte = Nutz_zu_Endenergieumrechnung(data_Haushalte['Klima- und Prozesskaelte']['Summe'], data_Haushalte['Klima- und Prozesskaelte']['Kompressionskaelte'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Haushalte['EER']['Kompressionskaelte'])
    P_nom_Haushalte_Klimakaelte_Sorptionskaelte = Nutz_zu_Endenergieumrechnung(data_Haushalte['Klima- und Prozesskaelte']['Summe'], data_Haushalte['Klima- und Prozesskaelte']['Sorptionskaelte'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Haushalte['EER']['Sorptionskaelte'])
    
    '''
    Ab hier Verkehr
    '''
    
    # Personenverkehr ---------------------------------------------------------
    P_nom_Verkehr_Personenv_PKW_Batterie = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['PKW - batterieelektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['PKW - batterieelektrisch'])
    P_nom_Verkehr_Personenv_PKW_Wasserstoff = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['PKW - wasserstoffelektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['PKW - wasserstoffelektrisch'])
    P_nom_Verkehr_Personenv_PKW_Verbrenner_CNG =Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['PKW - Verbrenner CNG'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['PKW - Verbrenner CNG'])
    P_nom_Verkehr_Personenv_PKW_Verbrenner_sonst = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['PKW - Verbrenner sonst.'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['PKW - Verbrenner sonst.'])
    P_nom_Verkehr_Personenv_LKW_Elektrisch = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['LKW - elektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['LKW - elektrisch'])
    P_nom_Verkehr_Personenv_LKW_Wasserstoff = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['LKW - wasserstoffelektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['LKW - wasserstoffelektrisch'])
    P_nom_Verkehr_Personenv_LKW_Verbrenner_CNG = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['LKW - Verbrenner CNG'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['LKW - Verbrenner CNG'])
    P_nom_Verkehr_Personenv_LKW_Verbrenner_sonst = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['LKW - Verbrenner sonst.'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['LKW - Verbrenner sonst.'])
    P_nom_Verkehr_Personenv_Schiene_Elektrisch = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['Schiene - elektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['Schiene - elektrisch'])
    P_nom_Verkehr_Personenv_Schiene_Wasserstoff = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['Schiene - wasserstoffelektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['Schiene - wasserstoffelektrisch'])
    P_nom_Verkehr_Personenv_Schiene_Verbrenner = Nutz_zu_Endenergieumrechnung(data_Verkehr['Personenverkehr']['Summe'], data_Verkehr['Personenverkehr']['Schiene - Verbrenner'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['Schiene - Verbrenner'])
     
    # Güterverkehr ------------------------------------------------------------
    P_nom_Verkehr_Gueterv_PKW_Batterie = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['PKW - batterieelektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['PKW - batterieelektrisch'])
    P_nom_Verkehr_Gueterv_PKW_Wasserstoff = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['PKW - wasserstoffelektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['PKW - wasserstoffelektrisch'])
    P_nom_Verkehr_Gueterv_PKW_Verbrenner_CNG = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['PKW - Verbrenner CNG'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['PKW - Verbrenner CNG'])
    P_nom_Verkehr_Gueterv_PKW_Verbrenner_sonst = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['PKW - Verbrenner sonst.'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['PKW - Verbrenner sonst.'])
    P_nom_Verkehr_Gueterv_LKW_Elektrisch = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['LKW - elektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['LKW - elektrisch'])
    P_nom_Verkehr_Gueterv_LKW_Wasserstoff = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['LKW - wasserstoffelektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['LKW - wasserstoffelektrisch'])
    P_nom_Verkehr_Gueterv_LKW_Verbrenner_CNG = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['LKW - Verbrenner CNG'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['LKW - Verbrenner CNG'])
    P_nom_Verkehr_Gueterv_LKW_Verbrenner_sonst = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['LKW - Verbrenner sonst.'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['LKW - Verbrenner sonst.'])
    P_nom_Verkehr_Gueterv_Schiene_Elektrisch = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['Schiene - elektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['Schiene - elektrisch'])
    P_nom_Verkehr_Gueterv_Schiene_Wasserstoff = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['Schiene - wasserstoffelektrisch'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['Schiene - wasserstoffelektrisch'])
    P_nom_Verkehr_Gueterv_Schiene_Verbrenner = Nutz_zu_Endenergieumrechnung(data_Verkehr['Gueterverkehr']['Summe'], data_Verkehr['Gueterverkehr']['Schiene - Verbrenner'], sum(Einspeiseprofile_Stundenwerte['Grundlast']), data_Verkehr['EER']['Schiene - Verbrenner'])

    """
    Ab hier Zusammenfassung der Lasten
    """
    #------------------------------------------------------------------------------
    # Deklarieren von Variablen für die Zusammenführung
    #------------------------------------------------------------------------------
    Last_Strom_Zusammen = [None] * number_of_time_steps
    Last_Gas_Zusammen = [None] * number_of_time_steps
    Last_Bio_Zusammen = [None] * number_of_time_steps
    Last_Oel_Zusammen = [None] * number_of_time_steps
    Last_Fernw_Zusammen = [None] * number_of_time_steps
    Last_H2_Zusammen = [None] * number_of_time_steps
    Last_Verbrenner_Zusammen = [None] * number_of_time_steps
    #------------------------------------------------------------------------------
    # Zusammenfassen aller Leistungen, die den gleichen Lastgang haben, je Bus
    #------------------------------------------------------------------------------
    # Verkehr
    P_nom_Verkehr_Verbrenner_sonst_gesamt = (P_nom_Verkehr_Gueterv_PKW_Verbrenner_sonst 
                                           + P_nom_Verkehr_Gueterv_LKW_Verbrenner_sonst 
                                           + P_nom_Verkehr_Gueterv_Schiene_Verbrenner 
                                           + P_nom_Verkehr_Personenv_PKW_Verbrenner_sonst 
                                           + P_nom_Verkehr_Personenv_LKW_Verbrenner_sonst 
                                           + P_nom_Verkehr_Personenv_Schiene_Verbrenner)
    
    P_nom_Verkehr_Wasserstoff_gesamt = (P_nom_Verkehr_Personenv_PKW_Wasserstoff
                                      + P_nom_Verkehr_Personenv_LKW_Wasserstoff 
                                      + P_nom_Verkehr_Personenv_Schiene_Wasserstoff 
                                      + P_nom_Verkehr_Gueterv_PKW_Wasserstoff 
                                      + P_nom_Verkehr_Gueterv_LKW_Wasserstoff 
                                      + P_nom_Verkehr_Gueterv_Schiene_Wasserstoff)
    
    # Fernwärme
    P_nom_Fernw_T24_gesamt = P_nom_Haushalte_Raumwaerme_Fernwaerme
    
    P_nom_Fernw_Prozessgas_gesamt = (P_nom_Industrie_Prozesswaerme_Fernwaerme 
                                   + P_nom_GHD_Prozesswaerme_Fernwaerme)
    
    P_nom_Fernw_HA4_gesamt = (P_nom_Industrie_Raumwaerme_Fernwaerme 
                            + P_nom_GHD_Raumwaerme_Fernwaerme)
    
    # Öl
    P_nom_Oel_T24_gesamt = P_nom_Haushalte_Raumwaerme_Heizkessel_Oel
    
    P_nom_Oel_Prozessgas_gesamt = (P_nom_Industrie_Prozesswaerme_Heizkessel_Oel 
                                 + P_nom_GHD_Prozesswaerme_Heizkessel_Oel)
    
    P_nom_Oel_HA4_gesamt = (P_nom_Industrie_Raumwaerme_Heizkessel_Oel 
                          + P_nom_GHD_Raumwaerme_Heizkessel_Oel)
    
    P_nom_Oel_Grundlast_Materialnutzung = P_nom_Industrie_Materialnutzung_Oel

    # Biomasse
    P_nom_Bio_HA4_gesamt = (P_nom_Industrie_Raumwaerme_Festbrennstoffkessel 
                          + P_nom_GHD_Raumwaerme_Festbrennstoffkessel)
    
    P_nom_Bio_T24_gesamt = P_nom_Haushalte_Raumwaerme_Festbrennstoffkessel
    
    P_nom_Bio_Prozessgas_gesamt = (P_nom_Industrie_Prozesswaerme_Festbrennstoffkessel 
                                 + P_nom_GHD_Prozesswaerme_Festbrennstoffkessel)

    # Erdgas
    P_nom_Gas_Prozessgas_gesamt = (P_nom_Industrie_Prozesswaerme_Heizkessel_Gas 
                                 + P_nom_GHD_Prozesswaerme_Heizkessel_Gas)
    
    P_nom_Gas_HA4_gesamt = (P_nom_Industrie_Raumwaerme_Heizkessel_Gas 
                          + P_nom_GHD_Raumwaerme_Heizkessel_Gas)
    
    P_nom_Gas_Grundlast_gesamt = (P_nom_Verkehr_Personenv_PKW_Verbrenner_CNG 
                                + P_nom_Verkehr_Personenv_LKW_Verbrenner_CNG 
                                + P_nom_Verkehr_Gueterv_PKW_Verbrenner_CNG 
                                + P_nom_Verkehr_Gueterv_LKW_Verbrenner_CNG)
    
    P_nom_Gas_T24_gesamt = P_nom_Haushalte_Raumwaerme_Heizkessel_Gas
    
    P_nom_Gas_Grundlast_Materialnutzung= P_nom_Industrie_Materialnutzung_Gas

    # Strom
    P_nom_Strom_G3_gesamt = P_nom_Industrie_Strom
    
    P_nom_Strom_HA4_gesamt = (P_nom_Industrie_Raumwaerme_Heizstab 
                            + P_nom_Industrie_Raumwaerme_Luftwaermepumpe 
                            + P_nom_Industrie_Raumwaerme_Erdwaermepumpe 
                            + P_nom_GHD_Raumwaerme_Heizstab
                            + P_nom_GHD_Raumwaerme_Luftwaermepumpe 
                            + P_nom_GHD_Raumwaerme_Erdwaermepumpe)
    
    P_nom_Strom_Prozessgas_gesamt = (P_nom_Industrie_Prozesswaerme_Heizstab 
                                   + P_nom_Industrie_Prozesswaerme_Luftwaermepumpe 
                                   + P_nom_Industrie_Prozesswaerme_Erdwaermepumpe 
                                   + P_nom_GHD_Prozesswaerme_Heizstab 
                                   + P_nom_GHD_Prozesswaerme_Luftwaermepumpe 
                                   + P_nom_GHD_Prozesswaerme_Erdwaermepumpe)
    
    P_nom_Strom_G0_gesamt = P_nom_GHD_Strom
    
    P_nom_Strom_H0_gesamt = P_nom_Haushalte_Strom
    
    P_nom_Strom_T24_gesamt = (P_nom_Haushalte_Raumwaerme_Heizstab 
                            + P_nom_Haushalte_Raumwaerme_Luftwaermepumpe 
                            + P_nom_Haushalte_Raumwaerme_Erdwaermepumpe)
    
    P_nom_Strom_Grundlast_gesamt = (P_nom_Industrie_Prozesskaelte_Kompressionskaelte 
                                  + P_nom_Industrie_Prozesskaelte_Sorptionskaelte 
                                  + P_nom_GHD_Prozesskaelte_Kompressionskaelte 
                                  + P_nom_GHD_Prozesskaelte_Sorptionskaelte 
                                  + P_nom_Haushalte_Klimakaelte_Kompressionskaelte 
                                  + P_nom_Haushalte_Klimakaelte_Sorptionskaelte 
                                  + P_nom_Verkehr_Personenv_PKW_Batterie 
                                  + P_nom_Verkehr_Personenv_LKW_Elektrisch 
                                  + P_nom_Verkehr_Personenv_Schiene_Elektrisch 
                                  + P_nom_Verkehr_Gueterv_PKW_Batterie 
                                  + P_nom_Verkehr_Gueterv_LKW_Elektrisch 
                                  + P_nom_Verkehr_Gueterv_Schiene_Elektrisch)
    #------------------------------------------------------------------------------
    # Zuordnung der zusammengefassten Leistungen zu den Viertelstundenwerten und Bildung der Gesamtlastprofile
    #------------------------------------------------------------------------------  
    for a in range(0, number_of_time_steps):
    #    Zusammenfassung der Lasten auf die Busse
        Last_Strom_Zusammen[a] =(((P_nom_Strom_G3_gesamt * data_G3[a])) 
                               + ((P_nom_Strom_HA4_gesamt * Lastprofile_Stundenwerte['HA4'][a])) 
                               + ((P_nom_Strom_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'][a])) 
                               + ((P_nom_Strom_G0_gesamt * data_G0[a])) 
                               + ((P_nom_Strom_H0_gesamt * data_H0[a])) 
                               + ((P_nom_Strom_T24_gesamt * Lastprofile_Stundenwerte['T24'][a])) 
                               + ((P_nom_Strom_Grundlast_gesamt * Einspeiseprofile_Stundenwerte['Grundlast'][a]))
                                                   )
       
        Last_Gas_Zusammen[a] =(((P_nom_Gas_HA4_gesamt * Lastprofile_Stundenwerte['HA4'][a])) 
                             + ((P_nom_Gas_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'][a])) 
                             + ((P_nom_Gas_Grundlast_gesamt * Einspeiseprofile_Stundenwerte['Grundlast'][a])) 
                             + ((P_nom_Gas_T24_gesamt * Lastprofile_Stundenwerte['T24'][a])))
        
        Last_Bio_Zusammen[a] =(((P_nom_Bio_HA4_gesamt * Lastprofile_Stundenwerte['HA4'][a])) 
                             + ((P_nom_Bio_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'][a]))  
                             + ((P_nom_Bio_T24_gesamt * Lastprofile_Stundenwerte['T24'][a])))
        
        Last_Oel_Zusammen[a] =(((P_nom_Oel_HA4_gesamt * Lastprofile_Stundenwerte['HA4'][a]))
                             + ((P_nom_Oel_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'][a])) 
                             + ((P_nom_Oel_T24_gesamt * Lastprofile_Stundenwerte['T24'][a])))
        
        Last_Fernw_Zusammen[a] =(((P_nom_Fernw_HA4_gesamt * Lastprofile_Stundenwerte['HA4'][a]))
                               + ((P_nom_Fernw_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'][a])) 
                               + ((P_nom_Fernw_T24_gesamt * Lastprofile_Stundenwerte['T24'][a])))
        
        Last_H2_Zusammen[a] = ((P_nom_Verkehr_Wasserstoff_gesamt * Einspeiseprofile_Stundenwerte['Grundlast'][a]))
        
        Last_Verbrenner_Zusammen[a] = ((P_nom_Verkehr_Verbrenner_sonst_gesamt * Einspeiseprofile_Stundenwerte['Grundlast'][a]))
        
#%%
##########################################################################
######   Berechnungen zu Kosten   #################################
##########################################################################

Zinssatz=data_Systemeigenschaften['System']['Zinssatz']

def epc_calc(capex, opex, Amortisierungszeit):
    investk = economics.annuity(capex=capex, n=Amortisierungszeit, wacc=Zinssatz/100)
    betriebsk = capex * (opex/100)
    epc = investk + betriebsk
    
    return epc, investk, betriebsk

# Photovoltaik Aufdach
epc_PV_Aufdach, investk_PV_Aufdach, betriebsk_PV_Aufdach = epc_calc(Parameter_PV_Wind_2030['PV_Aufdach']['CAPEX'], 
                                                                    Parameter_PV_Wind_2030['PV_Aufdach']['OPEX'], 
                                                                    Parameter_PV_Wind_2030['PV_Aufdach']['Amortisierungszeit'])
# Photovoltaik Freifeld
epc_PV_Freifeld, investk_PV_Freifeld, betriebsk_PV_Freifeld = epc_calc(Parameter_PV_Wind_2030['PV_Freifeld']['CAPEX'], 
                                                                       Parameter_PV_Wind_2030['PV_Freifeld']['OPEX'], 
                                                                       Parameter_PV_Wind_2030['PV_Freifeld']['Amortisierungszeit'])
# Wind
epc_Wind, investk_Wind, betriebsk_Wind = epc_calc(Parameter_PV_Wind_2030['Wind']['CAPEX'], 
                                                  Parameter_PV_Wind_2030['Wind']['OPEX'], 
                                                  Parameter_PV_Wind_2030['Wind']['Amortisierungszeit'])
# Biomasse
epc_Biomasse, investk_Biomasse, betriebsk_Biomasse = epc_calc(Parameter_Biomasse_Biogas_2030['Biomasse']['CAPEX'], 
                                                              Parameter_Biomasse_Biogas_2030['Biomasse']['OPEX'], 
                                                              Parameter_Biomasse_Biogas_2030['Biomasse']['Amortisierungszeit'])
# Biogas
epc_Biogas, investk_Biogas, betriebsk_Biogas = epc_calc(Parameter_Biomasse_Biogas_2030['Biogas']['CAPEX'], 
                                                        Parameter_Biomasse_Biogas_2030['Biogas']['OPEX'], 
                                                        Parameter_Biomasse_Biogas_2030['Biogas']['Amortisierungszeit'])
# Solarthermie
epc_ST, investk_ST, betriebsk_ST = epc_calc(Parameter_ST_2030['Solarthermie']['CAPEX'], 
                                            Parameter_ST_2030['Solarthermie']['OPEX'], 
                                            Parameter_ST_2030['Solarthermie']['Amortisierungszeit'])
# Wasserkraft
epc_Wasserkraft, investk_Wasserkraft, betriebsk_Wasserkraft = epc_calc(Parameter_Wasserkraft_2030['Wasserkraft']['CAPEX'], 
                                                                       Parameter_Wasserkraft_2030['Wasserkraft']['OPEX'], 
                                                                       Parameter_Wasserkraft_2030['Wasserkraft']['Amortisierungszeit'])
# Natriumspeicher
epc_Natriumspeicher, investk_Natriumspeicher, betriebsk_Natriumspeicher = epc_calc(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['CAPEX'], 
                                                                                   Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['OPEX'], 
                                                                                   Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Amortisierungszeit'])    
# Wärmespeicher
epc_Waermespeicher, investk_Waermespeicher, betriebsk_Waermespeicher = epc_calc(Parameter_Waermespeicher_2030['Waermespeicher']['CAPEX'], 
                                                                                Parameter_Waermespeicher_2030['Waermespeicher']['OPEX'], 
                                                                                Parameter_Waermespeicher_2030['Waermespeicher']['Amortisierungszeit']) 
# Pumpspeicherkraftwerk
epc_Pumpspeicherkraftwerk, investk_Pumpspeicherkraftwerk, betriebsk_Pumpspeicherkraftwerk = epc_calc(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['CAPEX'], 
                                                                                                     Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['OPEX'], 
                                                                                                     Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Amortisierungszeit']) 
# Erdgasspeicher 
epc_Erdgasspeicher, investk_Erdgasspeicher, betriebsk_Erdgasspeicher = epc_calc(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['CAPEX'], 
                                                                                Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['OPEX'], 
                                                                                Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Amortisierungszeit']) 
# Wasserstoffspeicher
epc_Wasserstoffspeicher, investk_Wasserstoffspeicher, betriebsk_Wasserstoffspeicher = epc_calc(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['CAPEX'], 
                                                                                               Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['OPEX'], 
                                                                                               Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Amortisierungszeit']) 
# Elektrolyse
epc_Elektrolyse, investk_Elektrolyse, betriebsk_Elektrolyse = epc_calc(Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['CAPEX'], 
                                                                       Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['OPEX'], 
                                                                       Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Amortisierungszeit']) 
# Elektrodenheizkessel
epc_Elektrodenheizkessel, investk_Elektrodenheizkessel, betriebsk_Elektrodenheizkessel = epc_calc(Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['CAPEX'], 
                                                                                                  Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['OPEX'], 
                                                                                                  Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['Amortisierungszeit']) 
# Waermepumpe Abwaerme 
epc_Waermepumpe_Abwaerme, investk_Waermepumpe_Abwaerme, betriebsk_Waermepumpe_Abwaerme = epc_calc(Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['CAPEX'], 
                                                                                                  Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['OPEX'], 
                                                                                                  Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['Amortisierungszeit']) 
# Waermepumpe Fluss
epc_Waermepumpe_Fluss, investk_Waermepumpe_Fluss, betriebsk_Waermepumpe_Fluss = epc_calc(Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['CAPEX'], 
                                                                                         Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['OPEX'], 
                                                                                         Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['Amortisierungszeit']) 
# ptL 
epc_PtL, investk_PtL, betriebsk_PtL = epc_calc(Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['CAPEX'], 
                                               Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['OPEX'], 
                                               Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Amortisierungszeit'])
# Brennstoffzelle
epc_Brennstoffzelle, investk_Brennstoffzelle, betriebsk_Brennstoffzelle = epc_calc(Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['CAPEX'], 
                                                                                   Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['OPEX'], 
                                                                                   Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Amortisierungszeit'])
# Gas- und Dampf-Kraftwerk
epc_GuD, investk_GuD, betriebsk_GuD = epc_calc(Parameter_GuD_2030['GuD']['CAPEX'], 
                                               Parameter_GuD_2030['GuD']['OPEX'], 
                                               Parameter_GuD_2030['GuD']['Amortisierungszeit'])
# Methanisierung
epc_Methanisierung, investk_Methanisierung, betriebsk_Methanisierung = epc_calc(Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['CAPEX'], 
                                               Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['OPEX'], 
                                               Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Amortisierungszeit'])
# Wasserstoffeinspeisung
epc_Wasserstoffeinspeisung, investk_Wasserstoffeinspeisung, betriebsk_Wasserstoffeinspeisung = epc_calc(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['CAPEX'], 
                                                                                                        Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['OPEX'], 
                                                                                                        Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Amortisierungszeit'])
# Biogaseinspeisung_Bestandsanlagen
epc_Biogaseinspeisung_Bestandsanlagen, investk_Biogaseinspeisung_Bestandsanlagen, betriebsk_Biogaseinspeisung_Bestandsanlagen = epc_calc(Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['CAPEX'], 
                                                                                                                                         Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['OPEX'], 
                                                                                                                                         Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['Amortisierungszeit'])
#Biogaseinspeisung Neuanlagen
epc_Biogaseinspeisung_Neuanlagen, investk_Biogaseinspeisung_Neuanlagen, betriebsk_Biogaseinspeisung_Neuanlagen = epc_calc(Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['CAPEX'], 
                                                                                                                          Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['OPEX'], 
                                                                                                                          Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['Amortisierungszeit'])

#%%  
###############################################################################
###############################################################################
###############    Erstellung des Energiesystems   ############################
###############################################################################
###############################################################################

solver = 'gurobi'
debug = False  
solver_verbose = False

logger.define_logging(logfile='oemof_example.log',
                      screen_level=logging.INFO,
                      file_level=logging.DEBUG)

logging.getLogger().setLevel(logging.INFO)
logging.info('Initialize the energy system')
date_time_index = pd.date_range('1/1/2030', periods=number_of_time_steps,freq='H')

energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)

logging.info('Create oemof objects')

###############################################################################
# Erstellung und Verbindung aller Komponenten
###############################################################################

"""
Verbindungsleitungen/Busse zur Bilanzierung von Energiemengen
"""
#------------------------------------------------------------------------------
# Strom Bus                                                                                      # Class Bus sind jetzt in module buses verschoben (solph.buses.Bus)
#------------------------------------------------------------------------------
b_el = solph.buses.Bus(label="Strom")

#------------------------------------------------------------------------------
# Gas Bus
#------------------------------------------------------------------------------
b_gas = solph.buses.Bus(label="Gas")

#------------------------------------------------------------------------------
# Oel/Kraftstoffe Bus
#------------------------------------------------------------------------------
b_oel_kraftstoffe = solph.buses.Bus(label="Oel_Kraftstoffe")

#------------------------------------------------------------------------------
# Biomasse Bus
#------------------------------------------------------------------------------
b_bio = solph.buses.Bus(label="Bio")

#------------------------------------------------------------------------------
# feste Biomasse Bus
#------------------------------------------------------------------------------
b_bioholz = solph.buses.Bus(label="BioHolz")

#------------------------------------------------------------------------------
# Fernwärme Bus
#------------------------------------------------------------------------------
b_fern = solph.buses.Bus(label="Fernwaerme")

#------------------------------------------------------------------------------
# Wasserstoff Bus
#------------------------------------------------------------------------------
b_was = solph.buses.Bus(label="Wasserstoff")

#------------------------------------------------------------------------------
# Festbrennstoff Bus
#------------------------------------------------------------------------------
b_fest=solph.buses.Bus(label="Festbrennstoffe")

# Hinzufügen der Busse zum Energiesystem-Modell 
energysystem.add(b_el, b_gas, b_oel_kraftstoffe, b_bio, b_bioholz, b_fern, b_was, b_fest)

"""
Exporte
"""
#------------------------------------------------------------------------------  
# Export Strom                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Strom', 
    inputs={b_el: solph.Flow(nominal_value = Parameter_Stromnetz_2030['Strom']['Max_Bezugsleistung'],
                             variable_costs = [i*(-1) for i in Preise_2030_Stundenwerte['Strompreis_2030']]
    )}))

#------------------------------------------------------------------------------
# Export Wasserstoff
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Export_Wasserstoff', 
    inputs={b_was: solph.Flow(variable_costs = [i*(-1) for i in Preise_2030_Stundenwerte['Wasserstoffpreis_2030']],
                              nominal_value = Parameter_Wasserstoffnetz_2030['Wasserstoff']['Max_Bezugsleistung']
    )}))

#--------------------------------------------------------------------------
"""
Senken
"""
#------------------------------------------------------------------------------
# Last Strom
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Last_Strom_ges', 
    inputs={b_el: solph.Flow(fix=Last_Strom_Zusammen, 
                             nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Last Biomasse
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Last_Biomasse_ges', 
    inputs={b_fest: solph.Flow(fix=Last_Bio_Zusammen, 
                               nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Last Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Last_Gas_ges', 
    inputs={b_gas: solph.Flow(fix=Last_Gas_Zusammen, 
                              nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Materialbedarf Gas 
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Materialbedarf_Gas', 
    inputs={b_gas: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                              nominal_value=P_nom_Gas_Grundlast_Materialnutzung,
    )}))

#------------------------------------------------------------------------------
# Last Oel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Last_Oel_ges', 
    inputs={b_oel_kraftstoffe: solph.Flow(fix=Last_Oel_Zusammen, 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Last Verkehr
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Last_Verkehr_ges', 
    inputs={b_oel_kraftstoffe: solph.Flow(fix=Last_Verbrenner_Zusammen, 
                                          nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Materialbedarf Oel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Materialbedarf_Oel', 
    inputs={b_oel_kraftstoffe: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                          nominal_value=P_nom_Oel_Grundlast_Materialnutzung,
    )}))

#------------------------------------------------------------------------------
# Last Waerme
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Last_Fernwaerme_ges', 
    inputs={b_fern: solph.Flow(fix=Last_Fernw_Zusammen, 
                               nominal_value=1,
    )}))

#------------------------------------------------------------------------------
# Last Wasserstoff
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='Last_Wasserstoff_ges', 
    inputs={b_was: solph.Flow(fix=Last_H2_Zusammen, 
                              nominal_value=1,
    )}))

"""
Erneuerbare Energiequellen
"""

#------------------------------------------------------------------------------
# Windkraftanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Wind_Erfurt', 
    outputs={b_el: solph.Flow(fix=data_Wind_Erfurt,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_Wind, 
                                                                maximum=Parameter_PV_Wind_2030['Wind']['Potential_Erfurt_Mitte'])
    )}))

energysystem.add(solph.components.Source(
    label='Wind_Nordhausen', 
    outputs={b_el: solph.Flow(fix=data_Wind_Nordhausen,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_Wind, 
                                                                maximum=Parameter_PV_Wind_2030['Wind']['Potential_Nordhausen_Nord'])
    )}))

energysystem.add(solph.components.Source(
    label='Wind_Gera', 
    outputs={b_el: solph.Flow(fix=data_Wind_Gera,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_Wind, 
                                                                maximum=Parameter_PV_Wind_2030['Wind']['Potential_Gera_Ost'])
    )}))

energysystem.add(solph.components.Source(
    label='Wind_Hildburghausen', 
    outputs={b_el: solph.Flow(fix=data_Wind_Hildburghausen,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_Wind, 
                                                                maximum=Parameter_PV_Wind_2030['Wind']['Potential_Hildburghausen_Südwest'])
    )}))
    
#------------------------------------------------------------------------------
# Photovoltaik Aufdachanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_Aufdach_Erfurt', 
    outputs={b_el: solph.Flow(fix=data_PV_Aufdach_Erfurt,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Erfurt_Mitte'])
    )}))    

energysystem.add(solph.components.Source(
    label='PV_Aufdach_Nordhausen', 
    outputs={b_el: solph.Flow(fix=data_PV_Aufdach_Nordhausen,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Nordhausen_Nord'])
    )}))

energysystem.add(solph.components.Source(
    label='PV_Aufdach_Gera', 
    outputs={b_el: solph.Flow(fix=data_PV_Aufdach_Gera,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Gera_Ost'])
    )}))

energysystem.add(solph.components.Source(
    label='PV_Aufdach_Hildburghausen', 
    outputs={b_el: solph.Flow(fix=data_PV_Aufdach_Hildburghausen,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Hildburghausen_Südwest'])
    )}))

#------------------------------------------------------------------------------
# Photovoltaik Freifeldanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='PV_Freifeld_Erfurt', 
    outputs={b_el: solph.Flow(fix=data_PV_Freifeld_Erfurt,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Erfurt_Mitte'])
    )}))

energysystem.add(solph.components.Source(
    label='PV_Freifeld_Nordhausen', 
    outputs={b_el: solph.Flow(fix=data_PV_Freifeld_Nordhausen,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Nordhausen_Nord'])
    )}))

energysystem.add(solph.components.Source(
    label='PV_Freifeld_Gera', 
    outputs={b_el: solph.Flow(fix=data_PV_Freifeld_Gera,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Gera_Ost'])
    )}))

energysystem.add(solph.components.Source(
    label='PV_Freifeld_Hildburghausen', 
    outputs={b_el: solph.Flow(fix=data_PV_Freifeld_Hildburghausen,
                                    custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Hildburghausen_Südwest'])
    )}))

#------------------------------------------------------------------------------
# Wasserkraft
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Wasserkraft', 
    outputs={b_el: solph.Flow(fix=data_Wasserkraft,
                                    custom_attributes={'emission_factor': Parameter_Wasserkraft_2030['Wasserkraft']['EE_Faktor']},
                                    investment=solph.Investment(ep_costs=epc_Wasserkraft, 
                                                                minimum=Parameter_Wasserkraft_2030['Wasserkraft']['Potential'], 
                                                                maximum = Parameter_Wasserkraft_2030['Wasserkraft']['Potential'])
    )}))

#------------------------------------------------------------------------------
# Solarthermie
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='ST', 
    outputs={b_fern: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Solarthermie'], 
                                      custom_attributes={'emission_factor': Parameter_ST_2030['Solarthermie']['EE_Faktor']},
                                      investment=solph.Investment(ep_costs=epc_ST, 
                                                                  maximum=Parameter_ST_2030['Solarthermie']['Potential'])
    )}))

"""
Importe
"""

#------------------------------------------------------------------------------
# Netzbezug
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Strom',
    outputs={b_el: solph.Flow(nominal_value=Parameter_Stromnetz_2030['Strom']['Max_Bezugsleistung'],
                              variable_costs = [i+Parameter_Stromnetz_2030['Strom']['Netzentgelt_Arbeitspreis'] for i in Preise_2030_Stundenwerte['Strompreis_2030']],
                              custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Strom_2030']},
                              
        )}))

#------------------------------------------------------------------------------
# Import Festbrennstoffe
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Festbrennstoffe',
    outputs={b_bio: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                     custom_attributes={'BiogasNeuanlagen_factor': 1},
                               
    )}))

#------------------------------------------------------------------------------
# feste Biomasse
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Holz',
    outputs={b_bioholz: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                         custom_attributes={'Biomasse_factor': 1},
                                   
    )}))

#------------------------------------------------------------------------------
# Import Braunkohle
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Braunkohle',
    outputs={b_fest: solph.Flow(variable_costs = Import_Braunkohlepreis_2030,
                                fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=data_Systemeigenschaften['System']['Menge_Braunkohle']*number_of_time_steps,
                                custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Braunkohle']},
    )}))

#------------------------------------------------------------------------------
# Import Steinkohle
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Steinkohle',
    outputs={b_fest: solph.Flow(variable_costs = Import_Steinkohlepreis_2030,
                                fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                #nominal_value = 1,
                                investment = solph.Investment(ep_costs=0),
                                summed_max=data_Systemeigenschaften['System']['Menge_Steinkohle']*number_of_time_steps,
                                custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Steinkohle']},
                                
    )}))

#------------------------------------------------------------------------------
# Import Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Gas',
    outputs={b_gas: solph.Flow(variable_costs = Import_Erdgaspreis_2030,
                                     custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Erdgas']},
                               
    )}))

#------------------------------------------------------------------------------
# Import Oel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Oel',
    outputs={b_oel_kraftstoffe: solph.Flow(variable_costs = Import_Oelpreis_2030,
                                                 custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Oel']}
                                           
        )}))

#------------------------------------------------------------------------------
# Import Synthetischer Kraftstoffe
#------------------------------------------------------------------------------
energysystem.add(solph.components.Source(
    label='Import_Synt',
    outputs={b_oel_kraftstoffe: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Synthetische_Kraftstoffe_2030'],
        )}))

"""
Energiespeicher
"""

#------------------------------------------------------------------------------
# elektrischer Speicher
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Batterie',
    inputs={b_el: solph.Flow()},
    outputs={b_el: solph.Flow()},
    loss_rate=0,
    inflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Einspeicherwirkungsgrad'],
    outflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Ausspeicherwirkungsgrad'],
    initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Anfangsspeicherlevel'],
    balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['balanced']),
    invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
    invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
    investment = solph.Investment(ep_costs=epc_Natriumspeicher, 
                                    maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Potential'],
                                    )
    ))

#------------------------------------------------------------------------------
# Waermespeicher
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label='Waermespeicher',
    inputs={b_fern: solph.Flow(
                              custom_attributes={'keywordWSP': 1},
                              nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                              #nonconvex=solph.NonConvex()
                                )},
    outputs={b_fern: solph.Flow(
                                custom_attributes={'keywordWSP': 1},
                                nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                #nonconvex=solph.NonConvex()
                                )},
    loss_rate=float(Parameter_Waermespeicher_2030['Waermespeicher']['Verlustrate']/24),
    inflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Einspeicherwirkungsgrad'],
    outflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Ausspeicherwirkungsgrad'],
    initial_storage_level=Parameter_Waermespeicher_2030['Waermespeicher']['Anfangsspeicherlevel'],
    balanced=bool(Parameter_Waermespeicher_2030['Waermespeicher']['balanced']),
    invest_relation_input_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
    invest_relation_output_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
    nominal_storage_capacity = solph.Investment(ep_costs=epc_Waermespeicher, 
                                 )
    ))


#------------------------------------------------------------------------------
# Pumpspeicherkraftwerk
#------------------------------------------------------------------------------
energysystem.add(solph.components.GenericStorage(
    label="Pumpspeicherkraftwerk",
    inputs={b_el: solph.Flow()},
    outputs={b_el: solph.Flow()},
    loss_rate=0,
    balanced=bool(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['balanced']),
    inflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Einspeicherwirkungsgrad'],
    outflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Ausspeicherwirkungsgrad'],
    initial_storage_level=Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Anfangsspeicherlevel'],
    invest_relation_input_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
    invest_relation_output_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
    investment = solph.Investment(ep_costs=epc_Pumpspeicherkraftwerk,
                                  minimum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential_min'],
                                  maximum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential'])
    ))

#------------------------------------------------------------------------------
# Erdgasspeicher
#------------------------------------------------------------------------------ 
energysystem.add(solph.components.GenericStorage(
    label="Erdgasspeicher",
    inputs={b_gas: solph.Flow()},
    outputs={b_gas: solph.Flow()},
    loss_rate=0,
    balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['balanced']),
    inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Einspeicherwirkungsgrad'],
    outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Ausspeicherwirkungsgrad'],
    initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Anfangsspeicherlevel'],
    invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
    invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
    investment = solph.Investment(ep_costs=epc_Erdgasspeicher, 
                                  maximum = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Potential'])    
    ))

#------------------------------------------------------------------------------
# Wasserstoffspeicher
#------------------------------------------------------------------------------    
energysystem.add(solph.components.GenericStorage(
    label="H2speicher",
    inputs={b_was: solph.Flow()},
    outputs={b_was: solph.Flow()},
    loss_rate=0,
    balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['balanced']),
    inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Einspeicherwirkungsgrad'],
    outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Ausspeicherwirkungsgrad'],
    initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Anfangsspeicherlevel'],
    invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
    invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
    investment = solph.Investment(ep_costs=epc_Wasserstoffspeicher, 
                                  maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Potential'])    
    ))

"""
Energiewandler
"""
#------------------------------------------------------------------------------
# Elektrolyse
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Elektrolyse",
    inputs={b_el: solph.Flow()},
    outputs={b_was: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrolyse, 
                                                             maximum=Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Potential']))},
    conversion_factors={b_was: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Wirkungsgrad']},
    ))

#------------------------------------------------------------------------------
# Elektrodenheizkessel
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Elektrodenheizkessel",
    inputs={b_el: solph.Flow()},
    outputs={b_fern: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrodenheizkessel))},
    conversion_factors={b_fern: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['Wirkungsgrad']}    
    ))

#------------------------------------------------------------------------------
# Gas- und Dampfkraftwerk
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='GuD',
    inputs={b_gas: solph.Flow(custom_attributes={'time_factor' :1})},
    outputs={b_el: solph.Flow(investment=solph.Investment(ep_costs=epc_GuD,
                                                          maximum =Parameter_GuD_2030['GuD']['Potential'])),
             b_fern: solph.Flow()},
    conversion_factors={b_el: Parameter_GuD_2030['GuD']['Wirkungsgrad_el'], 
                        b_fern: Parameter_GuD_2030['GuD']['Wirkungsgrad_th']}
    ))

#------------------------------------------------------------------------------
# Brennstoffzelle
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="brezel",
    inputs={b_was: solph.Flow()},
    outputs={b_el: solph.Flow(investment = solph.Investment(ep_costs=epc_Brennstoffzelle, 
                                                            maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Potential']))},
    conversion_factors={b_el: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Wirkungsgrad']}
    ))

#------------------------------------------------------------------------------
# Methanisierung
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Methanisierung",
    inputs={b_was: solph.Flow()},
    outputs={b_gas: solph.Flow(investment = solph.Investment(ep_costs=epc_Methanisierung, 
                                                             maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Potential']))},
    conversion_factors={b_gas: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Wirkungsgrad']}  
    ))

#------------------------------------------------------------------------------
# Biogas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biogas',
    inputs={b_bio: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value=1,
                                    investment = solph.Investment(ep_costs=0),
                                    custom_attributes={'BiogasBestand_factor': Parameter_Biomasse_Biogas_2030['Biogas']['BiogasBestand']})},
                              
    outputs={b_el: solph.Flow(investment=solph.Investment(ep_costs=epc_Biogas), 
                                    custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast']),
             b_fern: solph.Flow(custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                      fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                      #nominal_value= 1
                                      investment = solph.Investment(ep_costs=0)
                                      )},
    conversion_factors={b_el: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_el'], 
                        b_fern: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_th']}
    ))

#------------------------------------------------------------------------------
# Biomasse (zur Stromerzeugung)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_Strom',
    inputs={b_bioholz: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        #nominal_value = 1
                                        investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_el: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                              investment=solph.Investment(ep_costs=epc_Biomasse),
                              custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
    conversion_factors={b_el: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_el']}
    ))        

#------------------------------------------------------------------------------
# Biomasse (zur Waermeerzeugung)
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label='Biomasse_Waerme',
    inputs={b_bioholz: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                       #nominal_value = 1
                                       investment = solph.Investment(ep_costs=0)
                                        )},
    outputs={b_fern: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                investment=solph.Investment(ep_costs=epc_Biomasse),
                                custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
    conversion_factors={b_fern: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_th']}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung mit bereits bestehenden Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogaseinspeisung_Bestandsanlagen",
    inputs={b_bio: solph.Flow(custom_attributes={'BiogasBestand_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['BiogasBestand']},
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                    investment = solph.Investment(ep_costs=0)
                                    #nominal_value = 1
                                    )},
    outputs={b_gas: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                               investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Bestandsanlagen),
                               )},
    conversion_factors={b_gas: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['Wirkungsgrad_el']},
    custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['EE_Faktor']}
    ))

#------------------------------------------------------------------------------
# Biogaseinspeisung ohne bereits bestehende Biogasanlagen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Biogaseinspeisung_Neuanlagen",
    inputs={b_bio: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                    investment = solph.Investment(ep_costs=0)
                                    )},
    outputs={b_gas: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                               investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Neuanlagen),
                               )},
    conversion_factors={b_gas: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['Wirkungsgrad_el']},
    custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['EE_Faktor']}
                                
    ))

# -----------------------------------------------------------------------------
# Wasserstoffeinspeisung
# -----------------------------------------------------------------------------
maximale_Wasserstoffeinspeisung_Lastgang = [None] * len(Last_Gas_Zusammen)
maximale_Wasserstoffeinspeisung=0
for a in range(0, len(Last_Gas_Zusammen)):
    maximale_Wasserstoffeinspeisung_Lastgang[a]=(Last_Gas_Zusammen[a]*(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Potential']))/(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Wirkungsgrad'])
    if maximale_Wasserstoffeinspeisung_Lastgang[a] > maximale_Wasserstoffeinspeisung:
        maximale_Wasserstoffeinspeisung = maximale_Wasserstoffeinspeisung_Lastgang[a]

energysystem.add(solph.components.Converter(
    label='Wasserstoffeinspeisung',
    inputs={b_was: solph.Flow()},
    outputs={b_gas: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang,
                               investment=solph.Investment(ep_costs=epc_Wasserstoffeinspeisung, 
                                                           maximum=max(maximale_Wasserstoffeinspeisung_Lastgang)))}
    ))

#------------------------------------------------------------------------------
# Waermepumpe_Fluss
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Waermepumpe_Fluss",
    inputs={b_el: solph.Flow()},
    outputs={b_fern: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Fluss, 
                                                              maximum=Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['Potential']))},
    conversion_factors={b_fern: Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['COP']},    
    ))

#------------------------------------------------------------------------------
# Waermepumpe_Abwaerme
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="Waermepumpe_Abwaerme",
    inputs={b_el: solph.Flow()},
    outputs={b_fern: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Abwaerme, 
                                                              maximum=Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['Potential']))},
    conversion_factors={b_fern: Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['COP']},    
    ))

#------------------------------------------------------------------------------
# Power-to-Liquid
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="PtL",
    inputs={b_was: solph.Flow()},
    outputs={b_oel_kraftstoffe: solph.Flow(investment = solph.Investment(ep_costs=epc_PtL, 
                                                                         maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Potential']))},
    conversion_factors={b_oel_kraftstoffe: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Wirkungsgrad']}
    ))

#------------------------------------------------------------------------------
# feste Biomasse auf gleichen Bus wie Kohlen
#------------------------------------------------------------------------------
energysystem.add(solph.components.Converter(
    label="BioTransformer",
    inputs={b_bioholz: solph.Flow()},
    outputs={b_fest: solph.Flow()},
    ))

"""
Überschuss Senken
"""
#------------------------------------------------------------------------------
# Überschuss Senke für Strom
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_el2', 
    inputs={b_el: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Gas
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_gas2', 
    inputs={b_gas: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Oel/Kraftstoffe
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_oel_kraftstoffe', 
    inputs={b_oel_kraftstoffe: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Biomasse
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_bio', 
    inputs={b_bio: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Waerme
#------------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_fern', 
    inputs={b_fern: solph.Flow(variable_costs = 10000000
    )}))
#------------------------------------------------------------------------------
# Überschuss Senke für Wasserstoff
#-----------------------------------------------------------------------------
energysystem.add(solph.components.Sink(
    label='excess_b_was2', 
    inputs={b_was: solph.Flow(variable_costs = 10000000
    )}))

##########################################################################
# Optimise the energy system and plot the results
##########################################################################

logging.info('Optimise the energy system')

# initialise the operational model
model = solph.Model(energysystem)

##########################################################################
# Einbindung von Randbedingungen
##########################################################################

#------------------------------------------------------------------------------
# Constraint CO2 Begrenzung 
#------------------------------------------------------------------------------
def CO2_limit(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='CO2_factor',
                           flows=flows,
                           limit=limit)

def emission_factor(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='emission_factor',
                           flows=flows,
                           limit=limit)


# def generic_integral_limit(om, keyword, flows=None, limit=None):
   
#     if flows is None:
#         flows = {}
#         for (i, o) in om.flows:
#             if hasattr(om.flows[i, o], keyword):
#                 flows[(i, o)] = om.flows[i, o]

#     else:
#         for (i, o) in flows:
#             if not hasattr(flows[i, o], keyword):
#                 raise AttributeError(
#                     ('Flow with source: {0} and target: {1} '
#                       'has no attribute {2}.').format(
#                         i.label, o.label, keyword))

#     limit_name = "integral_limit_"+keyword

#     setattr(om, limit_name, po.Expression(
#         expr=sum(om.flow[inflow, outflow,p,t]
#                   * om.timeincrement[t]
#                   * sequence(getattr(flows[inflow, outflow], keyword))[t]
#                   for (inflow, outflow) in flows
#                   for p,t in om.TIMESTEPS)))

#     setattr(om, limit_name+"_constraint", po.Constraint(
#         expr=(getattr(om, limit_name) <= limit)))

#     return om

#------------------------------------------------------------------------------
# Gas- und Dampfkraftwerkseinschränkung
#------------------------------------------------------------------------------

def GuD_time(om, flows=None, limit=None, Starttime=None, Endtime=None):
    

    if flows is None:
        flows = {}
        for (i, o) in om.flows:
            if hasattr(om.flows[i, o], 'time_factor'):
                flows[(i, o)] = om.flows[i, o]

    else:
        for (i, o) in flows:
            if not hasattr(flows[i, o], 'time_factor'):
                raise AttributeError(
                    # ('Flow with source: {0} and target: {1} '
                    #  'has no attribute time_factor.').format(i.label, 
                    #                                              o.label))
                    ('Flow with source: {0} and target: {1} '
                      'has no attribute {2}.').format(i.label,o.label, 'time_factor'))
                
    limit_name = "integral_limit_"+ 'time_factor'
    #reduced_timesteps = [x for x in om.TIMESTEPS if x > Starttime and x < Endtime]

    reduced_timesteps =[]
    for p, t in om.TIMEINDEX:
        if t > Starttime and t < Endtime:
            reduced_timesteps.append(om.TIMEINDEX[t])

    # om.total_GuD =  po.Expression(
    #     expr=sum(om.flow[inflow, outflow, t] * om.timeincrement[t] *
    #              sequence(getattr(flows[inflow, outflow], 'time_factor'))[t]
    #              #flows[inflow, outflow].time_factor
    #              for (inflow, outflow) in flows
    #              for t in reduced_timesteps))
    
    setattr(
            om,
            limit_name,
            po.Expression(
                expr=sum(
                    om.flow[inflow, outflow,p, t]
                    * om.timeincrement[t]
                    * sequence(getattr(flows[inflow, outflow], 'time_factor'))[t]
                    for (inflow, outflow) in flows
                    for p,t in reduced_timesteps
                )
            ),
        )
    
    setattr(
            om,
            limit_name + "_constraint",
            po.Constraint(expr=(getattr(om, limit_name) <= limit)),
        )


    #om.GuD_time = po.Constraint(expr=om.total_GuD <= limit)

    return om


#------------------------------------------------------------------------------
# Constraint BiogasBestand Begrenzung
#------------------------------------------------------------------------------
def BiogasBestand_limit(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='BiogasBestand_factor',
                           flows=flows,
                           limit=limit)
    
#------------------------------------------------------------------------------
# Constraint Biogas Neuanlagen Begrenzung
#------------------------------------------------------------------------------
def BiogasNeuanlagen_limit(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='BiogasNeuanlagen_factor',
                           flows=flows,
                           limit=limit)
    
#------------------------------------------------------------------------------
# Constraint Biomasse Begrenzung
#------------------------------------------------------------------------------
def Biomasse_limit(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='Biomasse_factor',
                           flows=flows,
                           limit=limit)
    
#------------------------------------------------------------------------------
# Speicherverriegelung gegen gleichzeitiges Ein- und Ausspeichern
#------------------------------------------------------------------------------
#constraints.limit_active_flow_count_by_keyword(model, 'keywordWSP', upper_limit=1)

#------------------------------------------------------------------------------
# Bilanziell erneuerbar
#------------------------------------------------------------------------------

SummeLasten=sum(Last_Strom_Zusammen)+sum(Last_Gas_Zusammen)+sum(Last_Oel_Zusammen)+sum(Last_Verbrenner_Zusammen)+sum(Last_Fernw_Zusammen)+sum(Last_H2_Zusammen)

Anteilig_erneuerbar = True

if Anteilig_erneuerbar == True:
    constraints.emission_limit(model, limit=-SummeLasten*0.55)
    GuD_time(model, limit=0, Starttime=1777, Endtime=7656)
    
#------------------------------------------------------------------------------
# Aktivierung der Begrenzungen
#------------------------------------------------------------------------------
CO2_limit(model, limit=data_Systemeigenschaften['System']['CO2_Grenze_2030'])
BiogasBestand_limit(model, limit=Parameter_Biomasse_Biogas_2030['Biogas']['Potential_Summe'])
BiogasNeuanlagen_limit(model, limit=Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['Potential_Summe'])
Biomasse_limit(model, limit=Parameter_Biomasse_Biogas_2030['Biomasse']['Potential_Summe'])

# This is for debugging only. It is not(!) necessary to solve the problem and
# should be set to False to save time and disc space in normal use. For
# debugging the timesteps should be set to 3, to increase the readability of
# the lp-file.
if debug:
    filename = os.path.join(
        solph.helpers.extend_basic_path('lp_files'), 'Energiesystemmodell_Thueringen_2030.lp')
    logging.info('Store lp-file in {0}.'.format(filename))
    model.write(filename, io_options={'symbolic_solver_labels': True})

logging.info('Solve the optimization problem')
model.solve(solver=solver, solve_kwargs={'tee': solver_verbose})
logging.info('Store the energy system with the results.')

# The processing module of the outputlib can be used to extract the results
# from the model transfer them into a homogeneous structured dictionary.

# add results to the energy system to make it possible to store them.
energysystem.results['main'] = solph.processing.results(model)
energysystem.results['meta'] = solph.processing.meta_results(model)

# The default path is the '.oemof' folder in your $HOME directory.
# The default filename is 'es_dump.oemof'.
# You can omit the attributes (as None is the default value) for testing cases.
# You should use unique names/folders for valuable results to avoid
# overwriting.

# store energy system with results
energysystem.dump(dpath=None, filename=None)

#%%
# ****************************************************************************
# ********** PART 2 - Processing the results *********************************
# ****************************************************************************

logging.info('**** The script can be divided into two parts here.')
logging.info('Restore the energy system and the results.')
energysystem = solph.EnergySystem()
energysystem.restore(dpath=None, filename=None)

#%%
# define an alias for shorter calls below (optional)
results = energysystem.results['main']
Strombus = solph.views.node(results, 'Strom')
Gasbus = solph.views.node(results, 'Gas')
Oelbus = solph.views.node(results, 'Oel_Kraftstoffe')
Biobus = solph.views.node(results, 'Bio')
BioHolzbus = solph.views.node(results, 'BioHolz')
Festbrennstoffbus = solph.views.node(results, 'Festbrennstoffe')
Fernwbus = solph.views.node(results, 'Fernwaerme')
Wasserstoffbus = solph.views.node(results, 'Wasserstoff')
Syntbus = solph.views.node(results, 'Synthetische_Kraftstoffe')
Natriumspeicher = solph.views.node(results, 'Batterie')
Waermespeicher_results = solph.views.node(results, 'Waermespeicher')
Pumpspeicherkraftwerk_results = solph.views.node(results, 'Pumpspeicherkraftwerk')
Erdgasspeicher_results = solph.views.node(results, 'Erdgasspeicher')
H2speicher_results = solph.views.node(results, 'H2speicher')



print('-----------------------------------------------------------------------')
print('Energiemengen Strombus: \n' +str(Strombus['sequences'].sum()))
print('-----------------------------------------------------------------------')
print('Energiemengen Gasbus: \n' +str(Gasbus['sequences'].sum()))
print('-----------------------------------------------------------------------')
print('Energiemengen Oelbus: \n' +str(Oelbus['sequences'].sum()))
print('-----------------------------------------------------------------------')
print('Energiemengen Biobus: \n' +str(Biobus['sequences'].sum()))
print('-----------------------------------------------------------------------')
print('Energiemengen BioHolzbus: \n' +str(BioHolzbus['sequences'].sum()))
print('-----------------------------------------------------------------------')
print('Energiemengen Festbrennstoffbus: \n' +str(Festbrennstoffbus['sequences'].sum()))
print('-----------------------------------------------------------------------')
print('Energiemengen Fernwbus: \n' +str(Fernwbus['sequences'].sum()))
print('-----------------------------------------------------------------------')
print('Energiemengen Wasserstoffbus: \n' +str(Wasserstoffbus['sequences'].sum()))
print('-----------------------------------------------------------------------')

#%% Zusammenrechnen der Import- und Exportkosten
Importkosten_Strom = 0
Erloese_Strom = 0
Importkosten_Erdgas = 0 
Importkosten_Oel = 0  
Erloese_Wasserstoff = 0  
Importkosten_Bio = 0 
Importkosten_BioHolz=0
Importkosten_Steinkohle=0
Importkosten_Braunkohle=0
Importkosten_Synt =0

for i in range(0, len(Strombus['sequences'][('Import_Strom','Strom'),'flow'])-1):
    Importkosten_Strom += (Strombus['sequences'][('Import_Strom','Strom'),'flow'][i]) * (Preise_2030_Stundenwerte['Strompreis_2030'][i]+Parameter_Stromnetz_2030['Strom']['Netzentgelt_Arbeitspreis'])
    Erloese_Strom += (Strombus['sequences'][('Strom','Export_Strom'),'flow'][i]) * Preise_2030_Stundenwerte['Strompreis_2030'][i]
    
    Importkosten_Erdgas += (Gasbus['sequences'][('Import_Gas','Gas'),'flow'][i]) * Import_Erdgaspreis_2030[i]
    
    Importkosten_Oel += (Oelbus['sequences'][('Import_Oel','Oel_Kraftstoffe'),'flow'][i]) * Import_Oelpreis_2030[i]
    
    Erloese_Wasserstoff += (Wasserstoffbus['sequences'][('Wasserstoff','Export_Wasserstoff'),'flow'][i]) * Preise_2030_Stundenwerte['Wasserstoffpreis_2030'][i]
    
    Importkosten_Bio += (Biobus['sequences'][('Import_Festbrennstoffe','Bio'),'flow'][i]) * Preise_2030_Stundenwerte['Biomassepreis_2030'][i]
     
    Importkosten_BioHolz += (BioHolzbus['sequences'][('Import_Holz','BioHolz'),'flow'][i]) * Preise_2030_Stundenwerte['Biomassepreis_2030'][i]
        
    Importkosten_Steinkohle += (Festbrennstoffbus['sequences'][('Import_Steinkohle','Festbrennstoffe'),'flow'][i]) * Import_Steinkohlepreis_2030[i]
    Importkosten_Braunkohle += (Festbrennstoffbus['sequences'][('Import_Braunkohle','Festbrennstoffe'),'flow'][i]) * Import_Braunkohlepreis_2030[i]

    Importkosten_Synt += (Oelbus['sequences'][('Import_Synt','Oel_Kraftstoffe'),'flow'][i]) * Preise_2030_Stundenwerte['Synthetische_Kraftstoffe_2030'][i]
    
#%% Berechnung Netznutzung
Spitzenlast=max(Strombus['sequences'][('Import_Strom','Strom'),'flow'])
Stromimport_Summe=(Strombus['sequences'][('Import_Strom','Strom'),'flow']).sum()
Stromnetzbenutzungsdauer=Stromimport_Summe/Spitzenlast
print('Spitzenlast: '+str(round(Spitzenlast,2))+'MW')
print('Stromimport_Summe: '+str(round(Stromimport_Summe,2))+'MWh')
print('Stromnetzbenutzungsdauer: '+str(round(Stromnetzbenutzungsdauer,2))+'h')

#%% Berechnung der Gesamtkosten
#------------------------------------------------------------------------------
# Investitionskostenanteil
#------------------------------------------------------------------------------
Annuitaet_Capex_ges = (
                    (Strombus['scalars'][('PV_Aufdach_Erfurt','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Gera','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Nordhausen','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Hildburghausen','Strom'),'invest']) * investk_PV_Aufdach +
                    (Strombus['scalars'][('PV_Freifeld_Erfurt','Strom'),'invest']+
                             Strombus['scalars'][('PV_Freifeld_Gera','Strom'),'invest']+
                             Strombus['scalars'][('PV_Freifeld_Nordhausen','Strom'),'invest']+
                             Strombus['scalars'][('PV_Freifeld_Hildburghausen','Strom'),'invest']) * investk_PV_Freifeld +
                    (Strombus['scalars'][('Wind_Erfurt','Strom'),'invest']+Strombus['scalars'][('Wind_Gera','Strom'),'invest']+Strombus['scalars'][('Wind_Nordhausen','Strom'),'invest']+Strombus['scalars'][('Wind_Hildburghausen','Strom'),'invest']) * investk_Wind +
                    Strombus['scalars'][('Wasserkraft','Strom'),'invest'] * investk_Wasserkraft + 
                    Strombus['scalars'][('Biogas','Strom'),'invest'] * investk_Biogas +
                    Strombus['scalars'][('Biomasse_Strom','Strom'),'invest'] * investk_Biomasse +
                    Strombus['scalars'][('brezel','Strom'),'invest'] * investk_Brennstoffzelle +
                    Strombus['scalars'][('GuD','Strom'),'invest'] * investk_GuD +
                    Fernwbus['scalars'][('ST','Fernwaerme'),'invest'] * investk_ST + 
                    Fernwbus['scalars'][('Biomasse_Waerme','Fernwaerme'),'invest'] * investk_Biomasse + 
                    Fernwbus['scalars'][('Waermepumpe_Fluss','Fernwaerme'),'invest'] * investk_Waermepumpe_Fluss +
                    Fernwbus['scalars'][('Waermepumpe_Abwaerme','Fernwaerme'),'invest'] * investk_Waermepumpe_Abwaerme +
                    Fernwbus['scalars'][('Elektrodenheizkessel','Fernwaerme'),'invest'] * investk_Elektrodenheizkessel +
                    Natriumspeicher['scalars'][('Batterie','None'),'invest'] * investk_Natriumspeicher +
                    Waermespeicher_results['scalars'][('Waermespeicher','None'),'invest'] * investk_Waermespeicher +
                    Pumpspeicherkraftwerk_results['scalars'][('Pumpspeicherkraftwerk','None'),'invest'] * investk_Pumpspeicherkraftwerk +
                    Erdgasspeicher_results['scalars'][('Erdgasspeicher','None'),'invest'] * investk_Erdgasspeicher +
                    H2speicher_results['scalars'][('H2speicher','None'),'invest'] * investk_Wasserstoffspeicher +
                    Wasserstoffbus['scalars'][('Elektrolyse','Wasserstoff'),'invest'] * investk_Elektrolyse +
                    Gasbus['scalars'][('Wasserstoffeinspeisung','Gas'),'invest'] * investk_Wasserstoffeinspeisung +
                    Gasbus['scalars'][('Biogaseinspeisung_Bestandsanlagen','Gas'),'invest'] * investk_Biogaseinspeisung_Bestandsanlagen +
                    Gasbus['scalars'][('Biogaseinspeisung_Neuanlagen','Gas'),'invest'] * investk_Biogaseinspeisung_Neuanlagen +
                    Gasbus['scalars'][('Methanisierung','Gas'),'invest'] * investk_Methanisierung +
                    Oelbus['scalars'][('PtL','Oel_Kraftstoffe'),'invest'] * investk_PtL
                    )
#------------------------------------------------------------------------------
# Betriebskostenanteil
#------------------------------------------------------------------------------
Opex_ges = (
                    (Strombus['scalars'][('PV_Aufdach_Erfurt','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Gera','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Nordhausen','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Hildburghausen','Strom'),'invest']) * betriebsk_PV_Aufdach +
                    (Strombus['scalars'][('PV_Freifeld_Erfurt','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Gera','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Nordhausen','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Hildburghausen','Strom'),'invest']) * betriebsk_PV_Freifeld +
                    (Strombus['scalars'][('Wind_Erfurt','Strom'),'invest']+Strombus['scalars'][('Wind_Gera','Strom'),'invest']+Strombus['scalars'][('Wind_Nordhausen','Strom'),'invest']+Strombus['scalars'][('Wind_Hildburghausen','Strom'),'invest']) * betriebsk_Wind +
                    Strombus['scalars'][('Wasserkraft','Strom'),'invest'] * betriebsk_Wasserkraft + 
                    Strombus['scalars'][('Biogas','Strom'),'invest'] * betriebsk_Biogas +
                    Strombus['scalars'][('Biomasse_Strom','Strom'),'invest'] * betriebsk_Biomasse +
                    Strombus['scalars'][('brezel','Strom'),'invest'] * betriebsk_Brennstoffzelle +
                    Strombus['scalars'][('GuD','Strom'),'invest'] * betriebsk_GuD +
                    Fernwbus['scalars'][('ST','Fernwaerme'),'invest'] * betriebsk_ST + 
                    Fernwbus['scalars'][('Biomasse_Waerme','Fernwaerme'),'invest'] * betriebsk_Biomasse + 
                    Fernwbus['scalars'][('Waermepumpe_Fluss','Fernwaerme'),'invest'] * betriebsk_Waermepumpe_Fluss +
                    Fernwbus['scalars'][('Waermepumpe_Abwaerme','Fernwaerme'),'invest'] * betriebsk_Waermepumpe_Abwaerme +
                    Fernwbus['scalars'][('Elektrodenheizkessel','Fernwaerme'),'invest'] * betriebsk_Elektrodenheizkessel +
                    Natriumspeicher['scalars'][('Batterie','None'),'invest'] * betriebsk_Natriumspeicher +
                    Waermespeicher_results['scalars'][('Waermespeicher','None'),'invest'] * betriebsk_Waermespeicher +
                    Pumpspeicherkraftwerk_results['scalars'][('Pumpspeicherkraftwerk','None'),'invest'] * betriebsk_Pumpspeicherkraftwerk +
                    Erdgasspeicher_results['scalars'][('Erdgasspeicher','None'),'invest'] * betriebsk_Erdgasspeicher +
                    H2speicher_results['scalars'][('H2speicher','None'),'invest'] * betriebsk_Wasserstoffspeicher +
                    Wasserstoffbus['scalars'][('Elektrolyse','Wasserstoff'),'invest'] * betriebsk_Elektrolyse +
                    Gasbus['scalars'][('Wasserstoffeinspeisung','Gas'),'invest'] * betriebsk_Wasserstoffeinspeisung +
                    Gasbus['scalars'][('Biogaseinspeisung_Bestandsanlagen','Gas'),'invest'] * betriebsk_Biogaseinspeisung_Bestandsanlagen +
                    Gasbus['scalars'][('Biogaseinspeisung_Neuanlagen','Gas'),'invest'] * betriebsk_Biogaseinspeisung_Neuanlagen +
                    Gasbus['scalars'][('Methanisierung','Gas'),'invest'] * betriebsk_Methanisierung +
                    Oelbus['scalars'][('PtL','Oel_Kraftstoffe'),'invest'] * betriebsk_PtL
                    )

#------------------------------------------------------------------------------
# Gesamtkosten
#------------------------------------------------------------------------------

Kosten_ges = Importkosten_Strom + Importkosten_Erdgas + Importkosten_Oel + Importkosten_Bio + Importkosten_BioHolz + Importkosten_Steinkohle + Importkosten_Braunkohle + Importkosten_Synt
Erloese_ges = Erloese_Strom + Erloese_Wasserstoff

gewinn = Erloese_ges - Kosten_ges

Kosten_total = Annuitaet_Capex_ges + Opex_ges - gewinn
Jahresleistungspreis=Parameter_Stromnetz_2030['Strom']['Netzentgelt_Jahresleistungspreis']*Spitzenlast

#%% Visualisierung der Speicherverläufe
#------------------------------------------------------------------------------
# Setzen von Plot-Parametern
#------------------------------------------------------------------------------
fontsizenr = 18
plt.rc('xtick', labelsize=fontsizenr) 
plt.rc('legend', fontsize=fontsizenr-8) 
plt.rc('ytick', labelsize=fontsizenr) 
plt.rc('font', size=fontsizenr) 
plt.rc('axes', titlesize=fontsizenr)     # fontsize of the axes title
plt.rc('axes', labelsize=fontsizenr)    # fontsize of the x and y labels
plt.rcParams.update({'axes.titlesize': fontsizenr+2})
plt.rcParams.update({'font.size': fontsizenr})
plt.rc('text.latex', preamble=r'\usepackage[official]{eurosym}')

if plt is not None:
    fig = plt.figure(figsize=(19.1, 10.5))
    fig.canvas.set_window_title('Speicherverläufe')
    plt.plot(date_time_index,(((Pumpspeicherkraftwerk_results['sequences'][('Pumpspeicherkraftwerk','None'),'storage_content']).dropna()/Pumpspeicherkraftwerk_results['scalars'][('Pumpspeicherkraftwerk','None'),'invest'])*100),label='Pumpspeicher', linewidth=0.5, color='yellow')
    plt.plot(date_time_index,(((Erdgasspeicher_results['sequences'][('Erdgasspeicher','None'),'storage_content']).dropna()/Erdgasspeicher_results['scalars'][('Erdgasspeicher','None'),'invest'])*100),label='Erdgasspeicher')
    plt.plot(date_time_index,(((Natriumspeicher['sequences'][('Batterie','None'),'storage_content']).dropna()/Natriumspeicher['scalars'][('Batterie','None'),'invest'])*100),label='Natriumspeicher', color = 'lightgreen')   
    plt.plot(date_time_index,(((Waermespeicher_results['sequences'][('Waermespeicher','None'),'storage_content']).dropna()/Waermespeicher_results['scalars'][('Waermespeicher','None'),'invest'])*100), label='Waermespeicher')
    plt.grid()
    plt.legend()
    plt.ylabel('Speicherfüllstand in \%')
    plt.xlabel('Zeit')
    plt.title('Speicherverläufe')
    plt.savefig(os.path.join(results_path, name+'_Speicherverläufe.png'))
    
#%% Visualisierung der installierten Leistungen

fig, ax = plt.subplots(figsize=(19.1, 10.5))
fig.canvas.set_window_title('Leistungen in MW')
text = ['PV\_Aufdach',
        'PV\_Freifeld',
        'Wind',
        'Wasserkraft',
        'Biogas\_el',
        'Biomasse\_Strom',
        'Brennstoffzelle',
        'GuD',
        'Solarthermie',
        'Biomasse\_Waerme',
        'WP\_Fluss',
        'WP\_Abwaerme',
        'Elektrodenheizkessel',
        'Elektrolyse',
        'Wasserstoffeinspeisung',
        'Bio2gas\_Bestand',
        'Bio2gas\_Neu',
        'Methanisierung',
        'PtL'
        ]

data = [Strombus['scalars'][('PV_Aufdach_Erfurt','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Gera','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Nordhausen','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Hildburghausen','Strom'),'invest'],
        Strombus['scalars'][('PV_Freifeld_Erfurt','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Gera','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Nordhausen','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Hildburghausen','Strom'),'invest'],
        Strombus['scalars'][('Wind_Erfurt','Strom'),'invest']+Strombus['scalars'][('Wind_Gera','Strom'),'invest']+Strombus['scalars'][('Wind_Nordhausen','Strom'),'invest']+Strombus['scalars'][('Wind_Hildburghausen','Strom'),'invest'],
        Strombus['scalars'][('Wasserkraft','Strom'),'invest'],
        Strombus['scalars'][('Biogas','Strom'),'invest'],
        Strombus['scalars'][('Biomasse_Strom','Strom'),'invest'],
        Strombus['scalars'][('brezel','Strom'),'invest'],
        Strombus['scalars'][('GuD','Strom'),'invest'],
        Fernwbus['scalars'][('ST','Fernwaerme'),'invest'] ,
        Fernwbus['scalars'][('Biomasse_Waerme','Fernwaerme'),'invest'],
        Fernwbus['scalars'][('Waermepumpe_Fluss','Fernwaerme'),'invest'] ,
        Fernwbus['scalars'][('Waermepumpe_Abwaerme','Fernwaerme'),'invest'],
        Fernwbus['scalars'][('Elektrodenheizkessel','Fernwaerme'),'invest'],
        Wasserstoffbus['scalars'][('Elektrolyse','Wasserstoff'),'invest'],
        Gasbus['scalars'][('Wasserstoffeinspeisung','Gas'),'invest'],
        Gasbus['scalars'][('Biogaseinspeisung_Bestandsanlagen','Gas'),'invest'],
        Gasbus['scalars'][('Biogaseinspeisung_Neuanlagen','Gas'),'invest'],
        Gasbus['scalars'][('Methanisierung','Gas'),'invest'],
        Oelbus['scalars'][('PtL','Oel_Kraftstoffe'),'invest']
        ]

bars = plt.bar(text, data, )
xticks_pos = [0.3*patch.get_width() + patch.get_xy()[0] for patch in bars]

plt.xticks(xticks_pos,fontsize=fontsizenr,
           ha='left', rotation=-45)
#plt.tight_layout(pad=2, h_pad=None, w_pad=None, rect=(0, 0, 1, 1))
plt.grid()
label = [ '%.0f' % elem for elem in data ]

for i in range(len(data)):
    if data[i] <0:
        plt.text(x = i-0.1 , y = data[i]-100, s = label[i], size = fontsizenr)
    else:
        plt.text(x = i-0.3 , y = data[i]+3, s = label[i], size = fontsizenr)
plt.title("Leistungen")
plt.ylabel('Leistung in MW')
plt.plot()
plt.savefig(os.path.join(results_path, name+'_alleLeistungen.png'))

#%%
fig.canvas.set_window_title('Strombus_2030')
fig, ax = plt.subplots(figsize=(19.1, 10.5))
Strombus['sequences'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
# plt.legend(
#     loc="upper center", prop={"size": 10}, bbox_to_anchor=(0.44, 1.5), ncol=3
# )
plt.ylabel('Leistung in MW')
plt.legend()
plt.grid()
plt.xlabel('Zeit')
plt.title('Strombus 2030')
plt.show()
#%%
fig.canvas.set_window_title('Fernwaerme_2030')
fig, ax = plt.subplots(figsize=(19.1, 10.5))
Fernwbus['sequences'][('Elektrodenheizkessel','Fernwaerme'),'flow'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
Fernwbus['sequences'][('Fernwaerme','Waermespeicher'),'flow'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
# plt.legend(
#     loc="upper center", prop={"size": 10}, bbox_to_anchor=(0.44, 1.5), ncol=3
# )
plt.ylabel('Leistung in MW')
plt.legend()
plt.grid()
plt.xlabel('Zeit')
plt.title('Fernwaerme 2030')
plt.show()

#%%
# fig.canvas.set_window_title('Strompreis 2030')
# fig, ax = plt.subplots(figsize=(19.1, 10.5))
# Preise_2030_Stundenwerte['Strompreis_2030'].plot(
#     ax=ax, kind="line", drawstyle="steps-post",color ='green'
# )
# Preise_2030_Stundenwerte_alt['Strompreis_2030_brain'].plot(
#     ax=ax, kind="line", drawstyle="steps-post"
# )
# plt.legend()z
# plt.ylabel('Preis in EUR/MWh')
# plt.xlabel('Zeit')
# plt.xlim(0,8760)
# plt.grid()
# plt.title('Strompreis 2030')
# plt.show()
#%% CO2-Berechnung
Emissionen_Gasimport=(Gasbus['sequences'][('Import_Gas', 'Gas'), 'flow'].sum()*data_Systemeigenschaften['System']['Emission_Erdgas']/1000)
Emissionen_Oelimport=(Oelbus['sequences'][('Import_Oel', 'Oel_Kraftstoffe'), 'flow'].sum()*data_Systemeigenschaften['System']['Emission_Oel']/1000)
Emissionen_Stromimport=(Strombus['sequences'][('Import_Strom', 'Strom'), 'flow'].sum()*data_Systemeigenschaften['System']['Emission_Strom_2030']/1000)
Emissionen_Steinkohleimport=(Festbrennstoffbus['sequences'][('Import_Steinkohle', 'Festbrennstoffe'), 'flow'].sum()*data_Systemeigenschaften['System']['Emission_Steinkohle']/1000)
Emissionen_Braunkohleimport=(Festbrennstoffbus['sequences'][('Import_Braunkohle', 'Festbrennstoffe'), 'flow'].sum()*data_Systemeigenschaften['System']['Emission_Braunkohle']/1000)
Summe_Emissionen = Emissionen_Gasimport+Emissionen_Oelimport+Emissionen_Stromimport+Emissionen_Steinkohleimport+Emissionen_Braunkohleimport
  #%% Schreiben von Ergebnisfiles
#------------------------------------------------------------------------------
# Allgemeine Simulationsergebnisse zum Abgleich
#------------------------------------------------------------------------------
NaN=str('------------------------------------------------------------------') 

Ergebnisse = pd.Series([NaN,
                        Strombus['scalars'][('PV_Aufdach_Erfurt','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Gera','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Nordhausen','Strom'),'invest']+Strombus['scalars'][('PV_Aufdach_Hildburghausen','Strom'),'invest'],
                        Strombus['scalars'][('PV_Freifeld_Erfurt','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Gera','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Nordhausen','Strom'),'invest']+Strombus['scalars'][('PV_Freifeld_Hildburghausen','Strom'),'invest'],
                        Strombus['scalars'][('Wind_Erfurt','Strom'),'invest']+Strombus['scalars'][('Wind_Gera','Strom'),'invest']+Strombus['scalars'][('Wind_Nordhausen','Strom'),'invest']+Strombus['scalars'][('Wind_Hildburghausen','Strom'),'invest'],
                        Strombus['scalars'][('Wasserkraft','Strom'),'invest'],
                        Strombus['scalars'][('Biogas','Strom'),'invest'],
                        Strombus['scalars'][('Biomasse_Strom','Strom'),'invest'],
                        Strombus['scalars'][('brezel','Strom'),'invest'],
                        Strombus['scalars'][('GuD','Strom'),'invest'],
                        Fernwbus['scalars'][('ST','Fernwaerme'),'invest'] ,
                        Fernwbus['scalars'][('Biomasse_Waerme','Fernwaerme'),'invest'],
                        Fernwbus['scalars'][('Waermepumpe_Fluss','Fernwaerme'),'invest'] ,
                        Fernwbus['scalars'][('Waermepumpe_Abwaerme','Fernwaerme'),'invest'],
                        Fernwbus['scalars'][('Elektrodenheizkessel','Fernwaerme'),'invest'],
                        Wasserstoffbus['scalars'][('Elektrolyse','Wasserstoff'),'invest'],
                        Gasbus['scalars'][('Wasserstoffeinspeisung','Gas'),'invest'],
                        Gasbus['scalars'][('Biogaseinspeisung_Bestandsanlagen','Gas'),'invest'],
                        Gasbus['scalars'][('Biogaseinspeisung_Neuanlagen','Gas'),'invest'],
                        Gasbus['scalars'][('Methanisierung','Gas'),'invest'],
                        Oelbus['scalars'][('PtL','Oel_Kraftstoffe'),'invest'],
                        NaN,
                        Natriumspeicher['scalars'][('Batterie','None'),'invest'] ,
                        Waermespeicher_results['scalars'][('Waermespeicher','None'),'invest'],
                        Pumpspeicherkraftwerk_results['scalars'][('Pumpspeicherkraftwerk','None'),'invest'] ,
                        Erdgasspeicher_results['scalars'][('Erdgasspeicher','None'),'invest'],
                        H2speicher_results['scalars'][('H2speicher','None'),'invest'],
                        NaN,
                        Emissionen_Gasimport,
                        Emissionen_Oelimport,
                        Emissionen_Stromimport,
                        Emissionen_Steinkohleimport,
                        Emissionen_Braunkohleimport,
                        Summe_Emissionen,
                        NaN,
                        Annuitaet_Capex_ges/1000000,
                        Opex_ges/1000000, 
                        gewinn*(-1)/1000000, 
                        Jahresleistungspreis/1000000, 
                        (Kosten_total+Jahresleistungspreis)/1000000,  
                        NaN,
                        Strombus['sequences'][('Import_Strom','Strom'),'flow'].sum(),
                        Strombus['sequences'][('Strom','Export_Strom'),'flow'].sum()
                        ],
                index = ['Leistungen',
                       'PV_Dach',
                       'PV_Feld',
                       'Wind',
                       'Wasser',
                       'Biogas_el',
                       'Biomasse_Strom',
                       'Brennstoffzelle',
                       'GuD',
                       'Solarthermie',
                       'Biomasse_Waerme',
                       'WP_Fluss',
                       'WP_Abwaerme',
                       'Heizstab',
                       'Elektrolyse',
                       'Wasserstoffeinspeisung',
                       'B2G_Best.',
                       'B2G_Neu',
                       'Methanisierung',
                       'PtL',
                       'Speicherkapazitäten',
                       'Natriumspeicher',
                       'Waermespeicher',
                       'Pumpspeicher',
                       'Erdgasspeicher',
                       'Wasserstoffspeicher',
                       'Emissionen',
                       'Gasemissionen',
                       'Oelemissionen',
                       'Stromemissionen',
                       'Steinkohleemissionen',
                       'Braunkohleemissionen',
                       'Summe aller Emissionen',
                       'Kosten',
                       'Annuitaet', 
                       'OPEX', 
                       'Im-/Export',
                       'Netz', 
                       'Gesamtkosten',
                       'Energiemengen',
                       'Stromimport',
                       'Stromexport'
                       ])

Ergebnisse.to_csv('../results/'+name+'/'+name+'_Ergebnisse.csv', decimal=',')

#------------------------------------------------------------------------------
# Ergebnisse der Busse
#------------------------------------------------------------------------------    
Busse= pd.concat([
                Strombus['sequences'].sum(),
                Gasbus['sequences'].sum(),
                Oelbus['sequences'].sum(),
                Biobus['sequences'].sum(),
                BioHolzbus['sequences'].sum(),
                Festbrennstoffbus['sequences'].sum(),
                Fernwbus['sequences'].sum(),
                Wasserstoffbus['sequences'].sum()
                ])
Busse.to_csv('../results/'+name+'/'+name+'_Busse.csv', decimal=',', sep=';')

Strombus['sequences'].to_csv('../results/'+name+'/'+name+'_Strombus_sequences.csv', decimal=',')
Gasbus['sequences'].to_csv('../results/'+name+'/'+name+'_Gasbus_sequences.csv', decimal=',')
Oelbus['sequences'].to_csv('../results/'+name+'/'+name+'_Oelbus_sequences.csv', decimal=',')
Biobus['sequences'].to_csv('../results/'+name+'/'+name+'_Biobus_sequences.csv', decimal=',')
BioHolzbus['sequences'].to_csv('../results/'+name+'/'+name+'_BioHolzbus_sequences.csv', decimal=',')
Festbrennstoffbus['sequences'].to_csv('../results/'+name+'/'+name+'_Festbrennstoffbus_sequences.csv', decimal=',')
Fernwbus['sequences'].to_csv('../results/'+name+'/'+name+'_Fernwbus_sequences.csv', decimal=',')
Wasserstoffbus['sequences'].to_csv('../results/'+name+'/'+name+'_Wasserstoffbus_sequences.csv', decimal=',')

#------------------------------------------------------------------------------
# Ergebnisse der Speicher
#------------------------------------------------------------------------------
Natriumspeicher['sequences'].to_csv('../results/'+name+'/'+name+'_Natriumspeicher_sequences.csv', decimal=',')
Waermespeicher_results['sequences'].to_csv('../results/'+name+'/'+name+'_Waermespeicher_results_sequences.csv', decimal=',')
Pumpspeicherkraftwerk_results['sequences'].to_csv('../results/'+name+'/'+name+'_Pumpspeicherkraftwerk_results_sequences.csv', decimal=',')
Erdgasspeicher_results['sequences'].to_csv('../results/'+name+'/'+name+'_Erdgasspeicher_results_sequences.csv', decimal=',')
H2speicher_results['sequences'].to_csv('../results/'+name+'/'+name+'_H2speicher_results_sequences.csv', decimal=',')