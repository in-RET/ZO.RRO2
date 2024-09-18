# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 17:09:11 2024

@author: rbala
!!!!!!!!!!!!!!!!!!!!!!!!!!!

CAUTION: 
    
    The script is written in a way to automize the generation of feed-in profiles and store all variables in a class.
    Please consult the author before altering the script.


!!!!!!!!!!!!!!!!!!!!!!!!!!!
this script consists:
    - the function to read the standard output weather data from METEONORM in proper format and store the location specific parameters as variables
    - funtion to generate Wind/PV feed-in profile for different locations
    
"""
import pandas as pd
import numpy as np
import os
workdir= os.getcwd()
import pvlib
from pvlib.pvsystem import PVSystem, FixedMount, Array, pvwatts_losses
from pvlib.location import Location as pv_loc
from pvlib.modelchain import ModelChain
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

import warnings
warnings.filterwarnings('ignore')
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
        
    def Wind_feed_in_profile(self, simulation_year):
        
        # Import power curve of the Wind turbines
        
        inputfile_Windanlage = os.path.abspath(os.path.join(workdir, './','data/scalars','Wind_powercurve.csv'))
        Windanlagen = pd.read_csv(inputfile_Windanlage,sep=";", decimal=',',encoding='latin-1')
        p_Anlage = Windanlagen['Enercon E101']
        
        v_Wind = self.weather_data_min['FF']
        h_m = 10                             # Wind speed from Meteonorm is measured at 10 m high
        H = 150                              # Tower height of a Wind turbine
        
        
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
        Wind_Ertrag = Wind_Ertrag.rename(columns = { 0: 'Einspeise_Wind'})
        date_time_index = pd.date_range('1/1/' +str(simulation_year), periods = len(v_Wind), freq = '1min')# need a dummy index to resample the dataframe
        Wind_Ertrag = Wind_Ertrag.set_index(date_time_index)
        Wind_Ertrag = Wind_Ertrag.resample('1H').mean() # The feed in profile is resampled to hourly resolution
        self.Wind_feed_in_profile = Wind_Ertrag
        
    def PV_feed_in_profile(self, simulation_year):
        
        """ Define the coordinates fro PVlib """
        
        location = pv_loc(latitude= self.latitude, longitude= self.longitude, altitude= self.altitude, tz = 'Europe/Berlin')
        
        """ Create seperate weather format for PVlib"""
        
        weather_dict = { 'ghi' : self.weather_data_hour['G_Gh'],
                        'dhi': self.weather_data_hour['G_Dh'],
                        'dni': self.weather_data_hour['G_Bn'],
                        'Temperature': self.weather_data_hour[' Ta'],
                        'Wind Speed': self.weather_data_hour[' FF']}
        date_time_index = pd.date_range('1/1/' +str(simulation_year), periods = len(self.weather_data_hour), freq = 'H')
        weather = pd.DataFrame.from_dict(weather_dict)
        weather.index = date_time_index
        
        """ Get the module and inverter specifications from SAM 
         Module and inverter are fixed for the system CEC modules (but can be changed from the module dictionary (CEC_module))
        """

        CEC_module = pvlib.pvsystem.retrieve_sam('CECMod')
        cec_inverters = pvlib.pvsystem.retrieve_sam('CECInverter')
        module = CEC_module['Canadian_Solar_Inc__CS6X_300M']               # Module and inverter  are fixed for the system CEC modules (but can be changed from the module dictionary (CEC_module))
        inverter = cec_inverters['Power_One__PVI_6000_OUTD_US__277V_']     
        
        """ 
        Model parameters can be chose from the following:
                        - 'open_rack_glass_glass
                        - 'close_mount_glass_glass'
                        - 'open_rack_glass_polymer'
                        - 'insulated_back_glass_polymer'
                        
        Racking model (Open filed or roof top):
                        - 'open_rack'
                        - 'close_mount'
                        - 'insulated_back'
        """
        model_parameter = 'open_rack_glass_glass'#
        racking_model_open_field = 'open_rack'
        racking_model_rooftop = 'close_mount'
        temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm'][model_parameter]
        
        # Define system parameters
        """The system parameters are fixed for the model"""
        surface_tilt = 30
        surface_azimuth = 180   # South facing
        capacity = 6.6   # in kWp
        plant_capacity = capacity*1000 # in Wh for PVlib calculation
        mount = FixedMount(surface_tilt, surface_azimuth)    
                      
        #no_of_modules = int(plant_capacity/module.STC)

        array = Array(
                      mount= mount,
                      #albedo,
                      #surface_type,
                      module = module,
                      module_parameters = module,
                      temperature_model_parameters= temperature_model_parameters,
                      modules_per_string =11 , strings=2 ,
                      #array_losses_parameters= 
                      )

        system_openfield = PVSystem(
                          arrays = [array],
                          surface_tilt = surface_tilt,
                          surface_azimuth = surface_azimuth,
                          module = module,
                          module_parameters = module,
                          inverter = inverter,
                          inverter_parameters = inverter,
                          racking_model= racking_model_open_field,
                          temperature_model_parameters = temperature_model_parameters,
                          losses_parameters = pvwatts_losses()
                          )
        
        system_rooftop = PVSystem(
                          arrays = [array],
                          surface_tilt = surface_tilt,
                          surface_azimuth = surface_azimuth,
                          module = module,
                          module_parameters = module,
                          inverter = inverter,
                          inverter_parameters = inverter,
                          racking_model= racking_model_rooftop,
                          temperature_model_parameters = temperature_model_parameters,
                          losses_parameters = pvwatts_losses()
                          )

        mc_openfield = ModelChain(system_openfield, location,aoi_model="no_loss", spectral_model="no_loss")
        mc_rooftop = ModelChain(system_rooftop, location,aoi_model="no_loss", spectral_model="no_loss")
        mc_openfield.run_model(weather)
        mc_rooftop.run_model(weather)
       
        # Accessing the results
        ## Openfield    
        DC_annual = mc_openfield.results.dc.p_mp
        DC_power = pd.DataFrame(data = DC_annual/1000)
        DC_power.columns = ['DC_Power']
        DC_power_nom = DC_power/capacity
        self.PV_DC_power_openfield = DC_power
        
        AC_annual_1 = mc_openfield.results.ac
        AC_power_1 = pd.DataFrame(data = AC_annual_1/1000)
        AC_power_1.columns = ['AC_Power']
        AC_power_1[AC_power_1<0]= 0                         # Due to system losses you get a small negative value which is neglected by setting the value to zero 
        AC_power_nom_1 = AC_power_1/capacity
        self.PV_AC_power_openfield = AC_power_1
        self.PV_feed_in_profile_openfield = (AC_power_nom_1/int(AC_power_nom_1.sum()))*950
        self.PV_full_load_hours_openfield = int(AC_power_nom_1.sum())
        
        ## Rooftop    
        DC_annual = mc_rooftop.results.dc.p_mp
        DC_power = pd.DataFrame(data = DC_annual/1000)
        DC_power.columns = ['DC_Power']
        DC_power_nom = DC_power/capacity
        self.PV_DC_power_rooftop = DC_power
        
        AC_annual_2 = mc_rooftop.results.ac
        AC_power = pd.DataFrame(data = AC_annual_2/1000)
        AC_power.columns = ['AC_Power']
        AC_power[AC_power<0]= 0                         # Due to system losses you get a small negative value which is neglected by setting the value to zero 
        AC_power_nom = AC_power/capacity
        self.PV_AC_power_rooftop = AC_power
        self.PV_feed_in_profile_rooftop = (AC_power_nom/int(AC_power_nom.sum()))*915
        self.PV_full_load_hours_rooftop = int(AC_power_nom.sum())