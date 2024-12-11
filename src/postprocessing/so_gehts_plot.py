# -*- coding: utf-8 -*-
"""
Created on Mon Dec  9 11:47:26 2024

@author: rbala
"""

import matplotlib
import matplotlib.colors as mcolors
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

import os
workdir = os.getcwd()
    
'''Plot default settings'''
fontsizenr=10
dpi_nr = 600
plt.rc('xtick', labelsize=fontsizenr) 
plt.rc('legend', fontsize=fontsizenr-2) 
plt.rc('ytick', labelsize=fontsizenr) 
plt.rc('font', size=fontsizenr) 
plt.rc('axes', titlesize=fontsizenr, labelsize=fontsizenr, axisbelow=True) # fontsize of the axes title #axisbelow=Netz hinter den Säulen
# plt.rc('axes', labelsize=fontsizenr)    # fontsize of the x and y labels
plt.rcParams.update({'axes.titlesize': fontsizenr})
plt.rcParams.update({'font.size': fontsizenr})
plt.rcParams.update({'axes.titlepad': 10})
matplotlib.rcParams['font.family'] = ['sans-serif']
matplotlib.rcParams['font.sans-serif'] = ['News Gothic MT']

cm = 1/2.54  # centimeters in inche
m=100*cm
mm=10**(-3)*m
plt.rcParams.update({'figure.subplot.right':0.975})
plt.rcParams.update({'figure.subplot.left':0.3})
plt.rcParams.update({'figure.subplot.top':0.977})
plt.rcParams.update({'figure.subplot.bottom':0.35})

def so_gehts_bar_plot(csv, permutation, scenario_num):

     
    fig, ax = plt.subplots(figsize=(75*mm, 70*mm))
    fig.canvas.set_window_title('Leistungen Erneuerbare')
    text = ['PV Aufdach',
            'PV Freifeld',
            'Wind',
            'Solarthermie',
            'Wasser',
            'Biogas el.',
            'Biomasse el.',
            'Biomasse th.',
            
            ]
    data = [csv['Leistung']['PV_Dach'],
            csv['Leistung']['PV_Feld'],
            csv['Leistung']['Wind'],
            csv['Leistung']['Solarthermie'],
            csv['Leistung']['Wasser'],
            csv['Leistung']['Biogas_el'],
            csv['Leistung']['Biomasse_Strom'],
            csv['Leistung']['Biomasse_Waerme'],
                     ]
    bars = plt.bar(text, data, color=['#2E74B5'] #"So gehts"-blau
    )
    xlocs, xlabs = plt.xticks()               
    for i, v in enumerate(data):
        plt.text(xlocs[i] -0.25, v + 0.1, str(round(v)))
        
    plt.xticks(
                # xticks_pos,
                fontsize=fontsizenr,
               ha='right',
               rotation=45)

    plt.grid(axis = 'y')

    plt.ylabel('Leistung in MW')
    plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation), scenario_num + '_Leistung_Erneuerbare.png')),dpi=dpi_nr)
        
        
    fig, ax = plt.subplots(figsize=(75*mm, 70*mm))
    fig.canvas.set_window_title('PtX Technologien')
    text = ['Heizstab',
            'WP_Fluss',
            'WP_Abwaerme',
            'Elektrolyse',
            'Methanisierung',
            'GuD',
            'PtL',
            ]
    data = [csv['Leistung']['Heizstab'],
            csv['Leistung']['WP_Fluss'],
            csv['Leistung']['WP_Abwaerme'],
            csv['Leistung']['Elektrolyse'],
            csv['Leistung']['Methanisierung'],
            csv['Leistung']['GuD'],
            csv['Leistung']['PtL'],
                             ]
    bars = plt.bar(text, data, color=['#2E74B5'] #"So gehts"-blau
    )
    xlocs, xlabs = plt.xticks()               
    for i, v in enumerate(data):
        plt.text(xlocs[i] -0.25, v + 0.1, str(round(v)))
        
    plt.xticks(
                # xticks_pos,
                fontsize=fontsizenr,
               ha='right',
               rotation=45)

    plt.grid(axis = 'y')

    plt.ylabel('Leistung in MW')
    plt.savefig(os.path.abspath(os.path.join(workdir, 'figures' , str(permutation), scenario_num + '_PtX-Technologien.png')),dpi=dpi_nr)


    fig, ax = plt.subplots(figsize=(75*mm, 70*mm))
    fig.canvas.set_window_title('Speicherkapazitäten')
    text = ['Natriumspeicher',
            'Waermespeicher',
            'Pumpspeicher',
            'Erdgasspeicher',
            'Wasserstoffspeicher',
            ]
    data = [csv['Leistung']['Natriumspeicher'],
            csv['Leistung']['Waermespeicher'],
            csv['Leistung']['Pumpspeicher'],
            csv['Leistung']['Erdgasspeicher'],
            csv['Leistung']['Wasserstoffspeicher'],
                             ]
    bars = plt.bar(text, data, color=['#2E74B5'] #"So gehts"-blau
    )
    xlocs, xlabs = plt.xticks()               
    for i, v in enumerate(data):
        plt.text(xlocs[i] -0.25, v + 0.1, str(round(v)))
        
    plt.xticks(
                # xticks_pos,
                fontsize=fontsizenr,
               ha='right',
               rotation=45)

    plt.grid(axis = 'y')

    plt.ylabel('Kapazität in MWh')
    plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation), scenario_num + '_Speicherkapazitäten.png')),dpi=dpi_nr)
    
    return 