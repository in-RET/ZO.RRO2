# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 16:08:46 2024

@author: rbala
"""

from oemof.tools import economics
from oemof import network, solph
import pandas as pd
import os
workdir = os.getcwd()
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
from src.postprocessing.export_results import export_csv_region, grid_energy_map


# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
# %%

# my_path = os.path.abspath(os.path.dirname(__file__))

# energysystem = solph.EnergySystem()
# energysystem.restore(my_path, os.path.join(workdir, 
#                      'dumps', '2030_BS0001', 'BS_regionalization_2030_BS0001.dump'))

# # model_name '_' years '_' variations '.dump'
# img_path = os.path.abspath(os.path.join(os.getcwd(), 
#                      'figures','Thuringia_karte_mit_Landkreisen_dull.png'))
# img=mpimg.imread(img_path)
# plt.show()
# results = energysystem.results["main"]
# year = [2030,2040,2050]

# export = export_csv_region(results, 2030 , '2030_BS0001', 'BS_regionalization_2030_BS0001')
# grid_energy_map(results,'2030_BS0001', 'BS_regionalization_2030_BS0001')

# region = ['n','s', 'e', 'm']
# Region_csv = pd.DataFrame()
# for r in region:
#     b_el = solph.views.node(results, 'Electricity_'+ r)
#     b_gas = solph.views.node(results, 'Gas_'+ r)
#     b_oil = solph.views.node(results, 'Oil_fuel_'+ r)
#     b_bio = solph.views.node(results, 'Biomass_'+ r)
#     b_bioWood = solph.views.node(results, 'BioWood_'+ r)
#     b_solidf = solph.views.node(results, 'Solidfuel_'+ r)
#     b_dist_heat = solph.views.node(results, 'District heating_' + r)
#     b_H2 = solph.views.node(results, 'Hydrogen_' + r)
#     #Syntbus = solph.views.node(results, 'Synthetische_Kraftstoffe')
#     Battery = solph.views.node(results, 'Battery_'+ r)
#     Heat_storage = solph.views.node(results, 'Heat storage_'+ r)
#     Pumped_hydro_storage = solph.views.node(results, 'Pumped_hydro_storage_' + r)
#     Gas_storage = solph.views.node(results, 'Gas_storage_'+ r)
#     H2_storage = solph.views.node(results, 'H2_storage_'+ r)
    

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

YEAR = 2030
Zeitreihen = os.path.abspath(os.path.join(workdir,'./', 'data/sequences','00_ZORRO_I_old_sequences'))                # pfad für Zeitreihen und Eingangsdaten als variable --> besser nachzufolgen im script.
Eingangsdaten = os.path.abspath(os.path.join(workdir,'./', 'data/scalars','00_ZORRO_I_old_scalars'))
number_of_time_steps = 8760

'Eingangsdaten'
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_Industrie_'+str(YEAR)+'.csv')
data_Industrie = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_Industrie_Prozesswaerme_'+str(YEAR)+'.csv')
data_Industrie_Prozesswaerme = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_GHD_'+str(YEAR)+'.csv')
data_GHD = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_Haushalte_'+str(YEAR)+'.csv')
data_Haushalte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Eingangsdaten, 'Nutzenergiebereitstellung_Verkehr_'+str(YEAR)+'.csv')
data_Verkehr = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', index_col = 'index', decimal=',')
###############################################################################
pfad = os.path.join(Zeitreihen,'Lastprofile_Stundenwerte.csv')
Lastprofile_Stundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',')
###############################################################################
pfad = os.path.join(Zeitreihen,'Lastprofile_Viertelstundenwerte.csv')
Lastprofile_Viertelstundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',')
###############################################################################
pfad = os.path.join(Zeitreihen,'Einspeiseprofile_Stundenwerte.csv')
Einspeiseprofile_Stundenwerte = pd.read_csv(pfad, encoding = 'unicode_escape', sep=';', decimal=',')
###############################################################################


data_G3 = [None]*number_of_time_steps
data_G0 = [None]*number_of_time_steps
data_H0 = [None]*number_of_time_steps

i = 0
for a in range(0, number_of_time_steps):
    Summe_data_G3 = 0
    Summe_data_G0 = 0
    Summe_data_H0 = 0
    #Bilde die Summe von 4 Werten hintereinander (den Werten von 4 Viertelstunden, sprich einer Stunde)
    for k in range(0, 4):
        Summe_data_G3 += (Lastprofile_Viertelstundenwerte['G3'][i])*4
        Summe_data_G0 += (Lastprofile_Viertelstundenwerte['G0'][i])*4
        Summe_data_H0 += (Lastprofile_Viertelstundenwerte['H0'][i])*4
        i += 1
    data_G3[a] = Summe_data_G3/4
    data_G0[a] = Summe_data_G0/4
    data_H0[a] = Summe_data_H0/4
    

Lastprofile_Stundenwerte['H0'] = data_H0
Lastprofile_Stundenwerte['G0'] = data_G0
Lastprofile_Stundenwerte['G3'] = data_G3
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
data = pd.DataFrame()

#    Zusammenfassung der Lasten auf die Busse
data['electricity'] =(((P_nom_Strom_G3_gesamt * Lastprofile_Stundenwerte['G3'])) 
                       + ((P_nom_Strom_HA4_gesamt * Lastprofile_Stundenwerte['HA4'])) 
                       + ((P_nom_Strom_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'])) 
                       + ((P_nom_Strom_G0_gesamt * Lastprofile_Stundenwerte['G0'])) 
                       + ((P_nom_Strom_H0_gesamt * Lastprofile_Stundenwerte['H0'])) 
                       + ((P_nom_Strom_T24_gesamt * Lastprofile_Stundenwerte['T24'])) 
                       + ((P_nom_Strom_Grundlast_gesamt * Einspeiseprofile_Stundenwerte['Grundlast']))
                                           )

data['gas'] =(((P_nom_Gas_HA4_gesamt * Lastprofile_Stundenwerte['HA4'])) 
                     + ((P_nom_Gas_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'])) 
                     + ((P_nom_Gas_Grundlast_gesamt * Einspeiseprofile_Stundenwerte['Grundlast'])) 
                     + ((P_nom_Gas_T24_gesamt * Lastprofile_Stundenwerte['T24'])))

data['biomass'] =(((P_nom_Bio_HA4_gesamt * Lastprofile_Stundenwerte['HA4'])) 
                     + ((P_nom_Bio_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas']))  
                     + ((P_nom_Bio_T24_gesamt * Lastprofile_Stundenwerte['T24'])))

data['oil'] =(((P_nom_Oel_HA4_gesamt * Lastprofile_Stundenwerte['HA4']))
                     + ((P_nom_Oel_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'])) 
                     + ((P_nom_Oel_T24_gesamt * Lastprofile_Stundenwerte['T24'])))

data['dist_heating'] =(((P_nom_Fernw_HA4_gesamt * Lastprofile_Stundenwerte['HA4']))
                       + ((P_nom_Fernw_Prozessgas_gesamt * Lastprofile_Stundenwerte['Prozessgas'])) 
                       + ((P_nom_Fernw_T24_gesamt * Lastprofile_Stundenwerte['T24'])))

data['H2'] = ((P_nom_Verkehr_Wasserstoff_gesamt * Einspeiseprofile_Stundenwerte['Grundlast']))

data['fuel'] = ((P_nom_Verkehr_Verbrenner_sonst_gesamt * Einspeiseprofile_Stundenwerte['Grundlast']))

data['material_usage_gas'] = P_nom_Gas_Grundlast_Materialnutzung * Einspeiseprofile_Stundenwerte['Grundlast']
data['material_usage_oil'] = P_nom_Oel_Grundlast_Materialnutzung * Einspeiseprofile_Stundenwerte['Grundlast']