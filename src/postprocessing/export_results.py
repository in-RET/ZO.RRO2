# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 14:13:49 2024

@author: rbala
CAUTION: 
    
    The script is written in a way to automize the generation of csv files after simulation.
    Please consult the author before altering the script.


!!!!!!!!!!!!!!!!!!!!!!!!!!!
this script consists:
    - the function to export CSV files in a specific format to have a overview of the results.
    
"""

from oemof import solph
import pandas as pd
import os
workdir= os.getcwd()
from src.preprocessing.files import read_input_files
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.patches as mpatches

def export_csv_region(results, YEAR, permutation, model_name):
    CSV_PATH = os.path.abspath(os.path.join(os.getcwd(), "results", permutation))
    os.makedirs(CSV_PATH, exist_ok=True)
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    region = ['n','s', 'e', 'm']
    Region_csv = pd.DataFrame()
    for r in region:
        b_el = solph.views.node(results, 'Electricity_'+ r)
        b_gas = solph.views.node(results, 'Gas_'+ r)
        b_oil = solph.views.node(results, 'Oil_fuel_'+ r)
        b_bio = solph.views.node(results, 'Biomass_'+ r)
        b_bioWood = solph.views.node(results, 'BioWood_'+ r)
        b_solidf = solph.views.node(results, 'Solidfuel_'+ r)
        b_dist_heat = solph.views.node(results, 'District heating_' + r)
        b_H2 = solph.views.node(results, 'Hydrogen_' + r)
        #Syntbus = solph.views.node(results, 'Synthetische_Kraftstoffe')
        Battery = solph.views.node(results, 'Battery_'+ r)
        Heat_storage = solph.views.node(results, 'Heat storage_'+ r)
        Pumped_hydro_storage = solph.views.node(results, 'Pumped_hydro_storage_' + r)
        Gas_storage = solph.views.node(results, 'Gas_storage_'+ r)
        H2_storage = solph.views.node(results, 'H2_storage_'+ r)
        
        Emissionen_Gasimport=(b_gas['sequences'][('Import_Gas_'+ r, 'Gas_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Erdgas']/1000)
        Emissionen_Oelimport=(b_oil['sequences'][('Import_Oil_'+r, 'Oil_fuel_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Oel']/1000)
        Emissionen_Steinkohleimport=(b_solidf['sequences'][('Import_hard_coal_'+r, 'Solidfuel_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Steinkohle']/1000)
        Emissionen_Braunkohleimport=(b_solidf['sequences'][('Import_brown_coal_'+r, 'Solidfuel_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Braunkohle']/1000)
        
#------------------------------------------------------------------------------
# Allgemeine Simulationsergebnisse zum Abgleich
#------------------------------------------------------------------------------
        NaN=str('------------------------------------------------------------------') 
        if r == 'n':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->North', 'Electricity_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->North','Electricity_'+r),'flow'].sum()
        elif r == 'm':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->Middle', 'Electricity_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->Middle','Electricity_'+r),'flow'].sum()
        elif r == 'e':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->East', 'Electricity_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->East','Electricity_'+r),'flow'].sum()
        elif r == 's':
            Emissionen_Stromimport=(b_el['sequences'][('HS<->Swest', 'Electricity_'+r), 'flow'].sum()*scalars['System_configurations']['System']['Emission_Strom_'+ str(YEAR)]/1000)
            import_el = b_el['sequences'][('HS<->Swest','Electricity_'+r),'flow'].sum()
            
        Summe_Emissionen = Emissionen_Gasimport+Emissionen_Oelimport+Emissionen_Stromimport+Emissionen_Steinkohleimport+Emissionen_Braunkohleimport
        Ergebnisse = pd.Series([NaN,
                        b_el['scalars'][('PV_rooftop_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('PV_open_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Wind_'+ r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Hydro power plant_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Biogas_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Biomasse_elec_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('Fuelcell_'+r,'Electricity_'+r),'invest'],
                        b_el['scalars'][('GuD_'+r,'Electricity_'+r),'invest'],
                        b_dist_heat['scalars'][('ST_'+ r,'District heating_'+r),'invest'] ,
                        b_dist_heat['scalars'][('Biomasse_heat_'+r,'District heating_'+r),'invest'],
                        b_dist_heat['scalars'][('Heatpump_water_'+r,'District heating_'+r),'invest'] ,
                        b_dist_heat['scalars'][('Heatpump_air_'+r,'District heating_'+r),'invest'],
                        b_dist_heat['scalars'][('Electric boiler_'+r,'District heating_'+r),'invest'],
                        b_H2['scalars'][('Electrolysis_'+r,'Hydrogen_'+r),'invest'],
                        b_gas['scalars'][('Hydrogen_feedin_'+r,'Gas_'+r),'invest'],
                        b_gas['scalars'][('Biogas_feedin_existing_'+r,'Gas_'+r),'invest'],
                        b_gas['scalars'][('Biogas_feedin_new_'+r,'Gas_'+r),'invest'],
                        b_gas['scalars'][('Methanisation_'+r,'Gas_'+r),'invest'],
                        b_oil['scalars'][('PtL_'+r,'Oil_fuel_'+r),'invest'],
                        NaN,
                        Battery['scalars'][('Battery_'+r,'None'),'invest'] ,
                        Heat_storage['scalars'][('Heat storage_'+r,'None'),'invest'],
                        Pumped_hydro_storage['scalars'][('Pumped_hydro_storage_'+r,'None'),'invest'] ,
                        Gas_storage['scalars'][('Gas_storage_'+r,'None'),'invest'],
                        H2_storage['scalars'][('H2_storage_'+r,'None'),'invest'],
                        NaN,
                        Emissionen_Gasimport,
                        Emissionen_Oelimport,
                        Emissionen_Stromimport,
                        Emissionen_Steinkohleimport,
                        Emissionen_Braunkohleimport,
                        Summe_Emissionen,
                        NaN,
                        import_el,
                        b_el['sequences'][('Electricity_'+r,'Export_Electricity_'+r),'flow'].sum()
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
                       'Energiemengen',
                       'Stromimport',
                       'Stromexport'
                       ])
        
        if r == 'n':
            Region_csv['north'] = Ergebnisse
        elif r =='m':
            Region_csv['middle'] = Ergebnisse
        elif r =='e':
            Region_csv['east'] = Ergebnisse
        elif r =='s':
            Region_csv['swest'] = Ergebnisse
            
            
    Region_csv['summe'] = Region_csv['north']+Region_csv['middle'] +Region_csv['east'] +Region_csv['swest']     
    Region_csv.applymap(lambda x: str(x).replace('.', ',')).to_csv(CSV_PATH + '/'+ model_name +"_"+ permutation + ".csv", sep = ';')
    return Region_csv

def grid_energy_map(results, permutation, model_name):
    
    b_el_n = solph.views.node(results, 'Electricity_n')
    b_el_s = solph.views.node(results, 'Electricity_s')
    b_el_e = solph.views.node(results, 'Electricity_e')
    b_el_m = solph.views.node(results, 'Electricity_m')

    # Energiemengen in GWh
    em_hs_n = b_el_n['sequences'][('HS<->North', 'Electricity_n'), 'flow'].sum()/1000   #in GWh
    em_n_hs = b_el_n['sequences'][('Electricity_n', 'HS<->North'), 'flow'].sum()/1000
    em_hs_m = b_el_m['sequences'][('HS<->Middle', 'Electricity_m'), 'flow'].sum()/1000
    em_m_hs = b_el_m['sequences'][('Electricity_m', 'HS<->Middle'), 'flow'].sum()/1000
    em_hs_e = b_el_e['sequences'][('HS<->East', 'Electricity_e'), 'flow'].sum()/1000
    em_e_hs = b_el_e['sequences'][('Electricity_e', 'HS<->East'), 'flow'].sum()/1000
    em_hs_s = b_el_s['sequences'][('HS<->Swest', 'Electricity_s'), 'flow'].sum()/1000
    em_s_hs = b_el_s['sequences'][('Electricity_s', 'HS<->Swest'), 'flow'].sum()/1000
    em_m_n = b_el_m['sequences'][('Electricity_m', 'North<->Middel'), 'flow'].sum()/1000
    em_n_m = b_el_n['sequences'][('Electricity_n', 'North<->Middel'), 'flow'].sum()/1000
    em_m_e = b_el_m['sequences'][('Electricity_m', 'East<->Middel'), 'flow'].sum()/1000
    em_e_m = b_el_e['sequences'][('Electricity_e', 'East<->Middel'), 'flow'].sum()/1000
    em_m_s = b_el_m['sequences'][('Electricity_m', 'Middel<->Swest'), 'flow'].sum()/1000
    em_s_m = b_el_s['sequences'][('Electricity_s', 'Middel<->Swest'), 'flow'].sum()/1000
    fig, ax = plt.subplots(figsize=(19.1, 10.5))
    img_path = os.path.abspath(os.path.join(os.getcwd(), 
                         'figures','Thuringia_karte_mit_Landkreisen_35.png'))
    img=mpimg.imread(img_path)
    imgplot=plt.imshow(img)
    imgplot.axes.get_xaxis().set_visible(False)
    imgplot.axes.get_yaxis().set_visible(False)
    
    # Coordinates for red arrows
    x_1 = [120,130,400,410,250,260,690,700]
    y_1 = [440,500,340,400,100,160,440,500]
    z_1 = [60,-60,60,-60,60,-60,60,-60]

    for x,y,z in zip(x_1, y_1,z_1):
        plt.arrow(x ,y,0,z,
                      head_width= 22,
                      width = 8,
                      length_includes_head=True,
                      shape= 'right',
                      color= 'red',
                      ec='red') 
    #Coordinates for green arrows
    x_2 = [280,255,350,385,510,555]
    y_2 = [460,510,230,275,420,465]
    z_2 = [50,-50,50,-50,50,-50]
    w_2 = [-35,35,30,-30,40,-40]

    for x,y,w,z in zip(x_2,y_2,w_2,z_2):
        plt.arrow(x,y,w,z,
                  head_width= 22,
                  width = 8,
                  length_includes_head=True,
                  shape= 'right',
                  color= 'green',
                  ec='green')

    #Netzbezug: North    
    plt.text(200, 140, str(round(em_hs_n)), fontsize = 12)
    plt.text(275,120, str(round(em_n_hs)), fontsize = 12)
    #Netzbezug: Middle
    plt.text(340,385, str(round(em_hs_m)), fontsize = 12)
    plt.text(425,360, str(round(em_m_hs)), fontsize = 12)
    #Netzbezug: East  
    plt.text(630,485, str(round(em_hs_e)), fontsize = 12)
    plt.text(720,465, str(round(em_e_hs)), fontsize = 12)
    #Netzbezug: Swest  
    plt.text(70,485, str(round(em_hs_s)), fontsize = 12)
    plt.text(140,465, str(round(em_s_hs)), fontsize = 12)
    #Netzaustausch: Middle <-> Swest
    plt.text(200,500, str(round(em_m_s)), fontsize = 12)
    plt.text(300,475, str(round(em_s_m)), fontsize = 12)
    #Netzaustausch: Middle <-> North
    plt.text(370,230, str(round(em_m_n)), fontsize = 12)
    plt.text(320,280, str(round(em_n_m)), fontsize = 12)
    #Netzaustausch: Middle <-> East
    plt.text(500,475, str(round(em_m_e)), fontsize = 12)
    plt.text(550,425, str(round(em_e_m)), fontsize = 12)
    plt.text(790,70, '*The values are in GWh', fontsize = 10)
    red_patch = mpatches.Patch(color='red', label='Transformer Hös<->HS')
    green_patch = mpatches.Patch(color='green', label='Connection between regions')
    plt.legend(handles=[red_patch, green_patch])
    #plt.locator_params(nbins=20)
    #plt.grid()
    plt.show()
       
    plt.savefig(os.path.join(os.getcwd(), 'figures',permutation,  model_name+'_grid.png'), dpi=500)
    