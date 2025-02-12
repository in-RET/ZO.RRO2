# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 16:08:46 2024

@author: rbala
"""

import matplotlib.colors as mcolors
import matplotlib
#from src.preprocessing.location import Location
from src .preprocessing.conversion import investment_parameter
from src.preprocessing.files import read_input_files
from src.postprocessing.export_results import export_csv_region, grid_energy_map, export_csv
import numpy as np
import matplotlib.image as mpimg
from oemof.tools import economics
from oemof import network, solph
import pandas as pd
import os
workdir = os.getcwd()
try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None


# name = os.path.basename(__file__)
# name = name.replace(".py", "")
# my_path = os.path.abspath(os.path.dirname(__file__))
# %%

my_path = os.path.abspath(os.path.dirname(__file__))

energysystem = solph.EnergySystem()
energysystem.restore(my_path, os.path.join(workdir,
                                           'dumps', '2030_BS0001', 'Basic_example_zorro_1_2030_BS0001_005.dump'))
YEAR = 2030
model_ID = 'BS0001'
# model_name '_' years '_' variations '.dump'
# img_path = os.path.abspath(os.path.join(os.getcwd(),
# 'figures','Thuringia_karte_mit_Landkreisen_dull.png'))
# img=mpimg.imread(img_path)
# plt.show()
sequences = read_input_files(
    folder_name='data/sequences', sub_folder_name=None)
scalars = read_input_files(folder_name='data/scalars', sub_folder_name=None)
#demand = load_profile_scaling(scalars,sequences, YEAR, region=False)
#demand = zorro_1_loadprofile_scaling(YEAR, new_profile=True)
epc_costs = investment_parameter(scalars, YEAR, model_ID)
results = energysystem.results["main"]
year = [2030, 2040, 2050]
#sim_data = sim_data
#csv=export_csv(results, 2030, '2030_BS0001', 'Basic_example_zorro_1_2030_BS0001', '005', sim_data)
#export = export_csv_region(results, 2030 , '2030_BS0001', 'BS_regionalization_2030_BS0001')
#grid_energy_map(results,'2030_BS0001', 'BS_regionalization_2030_BS0001')

b_el = solph.views.node(results, 'Electricity')
b_gas = solph.views.node(results, 'Gas')
b_oil = solph.views.node(results, 'Oil_fuel')
b_bio = solph.views.node(results, 'Biomass')
b_bioWood = solph.views.node(results, 'BioWood')
b_solidf = solph.views.node(results, 'Solidfuel')
b_dist_heat = solph.views.node(results, 'District heating')
b_H2 = solph.views.node(results, 'Hydrogen')
#Syntbus = solph.views.node(results, 'Synthetische_Kraftstoffe')
Battery = solph.views.node(results, 'Battery')
Heat_storage = solph.views.node(results, 'Heat storage')
Pumped_hydro_storage = solph.views.node(results, 'Pumped_hydro_storage')
Gas_storage = solph.views.node(results, 'Gas_storage')
H2_storage = solph.views.node(results, 'H2_storage')


class Location(object):
    
    def __init__(self, file_path_hour, file_path_min):
        
        #Import Wetterdaten
        'Read Latitude and Longitude values from Weather file'
        input_file = pd.read_csv(file_path_hour, sep =' ', nrows=1, skiprows=1,decimal = ',', header = None)
        L = input_file.dropna(axis = 1, how = 'all').T.reset_index(drop= True).T
        self.latitude= L.iloc[0,0]
        self.longitude = L.iloc[0,1]
        self.altitude = L.iloc[0,2]
        self.weather_data_hour = pd.read_csv(file_path_hour, sep =',', skiprows=3,decimal = '.',encoding = 'unicode_escape')
        self.weather_data_min = pd.read_csv(file_path_min, sep ='\t', skiprows=2,decimal = '.',encoding = 'unicode_escape')
        
    def Wind_feed_in_profile(self, simulation_year,H):
        
        # Import power curve of the Wind turbines
        
        inputfile_Windanlage = os.path.abspath(os.path.join(workdir, './','data/scalars','Wind_powercurve.csv'))
        Windanlagen = pd.read_csv(inputfile_Windanlage,sep=";", decimal=',',encoding='latin-1')
        p_Anlage = Windanlagen['Enercon E101']
        
        v_Wind = self.weather_data_min['FF']
        h_m = 10                             # Wind speed from Meteonorm is measured at 10 m high
        H = H                           # Tower height of a Wind turbine
        
        
        """
        Exponenten (g):
            Open land (Water, Grass or farm field, coastal areas, deserts, etc.): 0.16  
            Terrain with obstacles up to 15m (forests, settlements, cities, etc.): 0.28
            Terrain with large obstacles (large cities, etc.): 0.40
        """
        g = 0.28
        
        v_Wind_corr = v_Wind* (H/h_m)**g     # Corrected wind speed at the turbine height of the wind turbine (Hellmans Exponent formula)
        v_Wind_corr[v_Wind_corr>25] = 0      # All wind speeds above 25m/s (cut-off speed) and v = zero are set to 1 to obtain power value=0
        v_Wind_corr[v_Wind_corr == 0] = 0
        v_Wind_corr = round(v_Wind_corr,2)
        
        "The power curve is interpolated to get the finer values between min and max wind speeds"
        v_Anlage_int = pd.Series(np.arange(0,25.1,0.01))
        v_Anlage = Windanlagen['velocity']
        p_Anlage_int = round(pd.Series(np.interp(v_Anlage_int, v_Anlage, p_Anlage)),2) 
        Anlagedaten = pd.DataFrame()
        Anlagedaten['Velocity'] = v_Anlage_int
        Anlagedaten['Leistung'] = p_Anlage_int
        Anlagedaten =Anlagedaten.set_index(round(v_Anlage_int,2)) # A dataframe is created for easy access for the Interpolated power curve of the wind turbine
        
        E_Wind=[None]* len(v_Wind)
        i=0
        for i in range (len(v_Wind)):
            j = v_Wind_corr[i]
            E_Wind[i] = Anlagedaten['Leistung'][j]         # in kWh
            i += 1    

        E_Wind_df= pd.DataFrame(E_Wind)
        Wind_Ertrag = E_Wind_df/max(p_Anlage_int) # kWh/KWp
        #Wind_Ertrag_sum = sum(Wind_Ertrag[0])/60
        Wind_Ertrag = Wind_Ertrag.rename(columns = { 0: 'Wind_feed_in'})
        date_time_index = pd.date_range('1/1/' +str(simulation_year), periods = len(v_Wind), freq = '1min')# need a dummy index to resample the dataframe
        Wind_Ertrag = Wind_Ertrag.set_index(date_time_index)
        Wind_Ertrag = Wind_Ertrag.resample('1H').mean() # The feed in profile is resampled to hourly resolution
        Wind_Ertrag = (Wind_Ertrag/int(Wind_Ertrag.sum()))*2300
        Wind_Ertrag = Wind_Ertrag.reset_index()
        self.Wind_feed_in_profile = Wind_Ertrag
        

Weather_dir = os.path.abspath(os.path.join(workdir, 'data', 'weatherdata'))
middle = Location(os.path.join(Weather_dir, 'Erfurt_Binderslebn-hour.csv'),
                  os.path.join(Weather_dir, 'Erfurt_Binderslebn-min.dat'))
north = Location(os.path.join(Weather_dir, 'Nordhausen-hour.csv'),
                 os.path.join(Weather_dir, 'Nordhausen-min.dat'))
swest = Location(os.path.join(Weather_dir, 'Hildburghausen-hour.csv'),
                 os.path.join(Weather_dir, 'Hildburghausen-min.dat'))
east = Location(os.path.join(Weather_dir, 'Gera-Leumnitz-hour.csv'),
                os.path.join(Weather_dir, 'Gera-Leumnitz-min.dat'))

T_a = ((north.weather_data_hour[' Ta'] + east.weather_data_hour[' Ta'] +
       middle.weather_data_hour[' Ta'] + swest.weather_data_hour[' Ta'])/4)

Planing_region = [middle, north, swest, east]
""" Simulate Wind feed-in profile for the desired location """
for L in Planing_region:
    if L == middle:
        H = 122.2
    elif L == north:
        H = 98
    elif L == swest:
        H = 23.15
    elif L == east:
        H = 63.6
    L.Wind_feed_in_profile(YEAR,H)
    #print(L.Wind_feed_in_profile['Wind_feed_in'].sum())
# %%

linie = pd.DataFrame()
linie['Erfurt'] = sorted(sequences['feed_in_profile']['Wind_middle'], reverse= True)
linie['Hildburghausen'] = sorted(sequences['feed_in_profile']['Wind_swest'], reverse= True)
linie['Nord'] = sorted(sequences['feed_in_profile']['Wind_north'], reverse= True)
linie['Jena'] = sorted(sequences['feed_in_profile']['Wind_east'], reverse= True)
figsize = (19.1, 10.5)
ax = linie.plot.line(figsize=(19.1, 10.5), fontsize = 20) 
                        #width=1)
#ax= p.plot.line(stacked=True, fontsize = 20, color = 'orange') 
plt.xticks(rotation=0)

#plt.xticks([0,744,1416,2160,2880,3624,4344,5088,5832,6552,7296,8016],['1.1.','1.2.','1.3.','1.4.','1.5.','1.6.','1.7.','1.8.','1.9.','1.10.','1.11.','1.12.'])
#plt.xlabel(year)
plt.title('Einspeiseprofil', fontsize = 20)
plt.ylabel('Leistung in MW', fontsize = 20)
plt.show()


linie_n = pd.DataFrame()
linie_n['Erfurt'] = sorted(middle.Wind_feed_in_profile['Wind_feed_in'], reverse= True)
linie_n['Hildburghausen'] = sorted(swest.Wind_feed_in_profile['Wind_feed_in'], reverse= True)
linie_n['Nord'] = sorted(north.Wind_feed_in_profile['Wind_feed_in'], reverse= True)
linie_n['Jena'] = sorted(east.Wind_feed_in_profile['Wind_feed_in'], reverse= True)
figsize = (19.1, 10.5)
ax = linie_n.plot.line(figsize=(19.1, 10.5), fontsize = 20) 
                        #width=1)
#ax= p.plot.line(stacked=True, fontsize = 20, color = 'orange') 
plt.xticks(rotation=0)

#plt.xticks([0,744,1416,2160,2880,3624,4344,5088,5832,6552,7296,8016],['1.1.','1.2.','1.3.','1.4.','1.5.','1.6.','1.7.','1.8.','1.9.','1.10.','1.11.','1.12.'])
#plt.xlabel(year)
plt.title('Einspeiseprofil', fontsize = 20)
plt.ylabel('Leistung in MW', fontsize = 20)
plt.show()
#%%


fig, ax = plt.subplots(figsize=(19.1, 10.5))
sequences['feed_in_profile']['Wind_east'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
sequences['feed_in_profile']['Wind_north'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
sequences['feed_in_profile']['Wind_swest'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
sequences['feed_in_profile']['Wind_middle'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
# plt.legend(
#     loc="upper center", prop={"size": 10}, bbox_to_anchor=(0.44, 1.5), ncol=3
# )
plt.ylabel('Leistung in MW')
plt.legend()
plt.grid()
plt.xlabel('Zeit')
plt.show()


fig, ax = plt.subplots(figsize=(19.1, 10.5))
middle.Wind_feed_in_profile['Wind_feed_in'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
north.Wind_feed_in_profile['Wind_feed_in'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
swest.Wind_feed_in_profile['Wind_feed_in'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
east.Wind_feed_in_profile['Wind_feed_in'].dropna().plot(
    ax=ax, kind="line", drawstyle="steps-post"
)
# plt.legend(
#     loc="upper center", prop={"size": 10}, bbox_to_anchor=(0.44, 1.5), ncol=3
# )
plt.ylabel('Leistung in MW')
plt.legend()
plt.grid()
plt.xlabel('Zeit')
plt.show()

#%%

def COP(scalars, T_a, model_ID, YEAR):

    T_VL = [None]*8760
    COP = [None]*8760
    T_VL_L = scalars['Temperature_dist_heat']['T_VL_L_' + str(YEAR)][model_ID]
    T_VL_U = scalars['Temperature_dist_heat']['T_VL_U_' + str(YEAR)][model_ID]
    T_RL = scalars['Temperature_dist_heat']['T_RL_' + str(YEAR)][model_ID]
    T_L = scalars['Temperature_dist_heat']['T_L'][model_ID]
    T_U = scalars['Temperature_dist_heat']['T_U'][model_ID]
    
    for i in range(len(T_a)):
        if T_a[i] > T_L and T_a[i] < T_U:
            T_VL[i] = T_VL_L - ((T_VL_L - T_VL_U)/(T_U - T_L)) * (T_a[i] - T_L)
        elif T_a[i] <= T_L:
            T_VL[i] = T_VL_L
        elif T_a[i] >= T_U:
            T_VL[i] = T_VL_U
        nu_H = 0.36
        COP[i] = nu_H*(T_VL[i]+273.15) / (T_VL[i]-T_RL)
    return pd.Series(COP)
    
COP = COP(scalars, T_a, model_ID, YEAR)