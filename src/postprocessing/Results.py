#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  9 01:27:40 2024

@author: Melie
"""
import os
workdir= os.getcwd()
import pandas as pd
from oemof import network, solph
from oemof.tools import economics

# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
#%%

my_path = os.path.abspath(os.path.dirname(__file__))

energysystem = solph.EnergySystem()
energysystem.restore(my_path, os.path.join(workdir, '..', '..', 'dumps', '2030_BS0001', 'BS_regionalization_2030_BS0001.dump'))

results = energysystem.results["main"]

print("Ende")

# store energy system with results
# energysystem.dump(dpath=None, filename=None)


# pfad = os.path.join(my_path, '../02_Zeitreihen/Einspeiseprofile_Stundenwerte.csv')


# ****************************************************************************
# ********** PART 2 - Processing the results *********************************
# ****************************************************************************
#%%
# logging.info('**** The script can be divided into two parts here.')
# logging.info('Restore the energy system and the results.')
# energysystem = solph.EnergySystem()
# energysystem.restore(dpath=None, filename=None)

# #%%
# # define an alias for shorter calls below (optional)
# results = energysystem.results['main']
# Strombus = solph.views.node(results, 'Strom')
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
