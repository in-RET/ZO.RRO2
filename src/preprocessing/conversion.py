# -*- coding: utf-8 -*-
"""
Created on Thu Jul  4 18:22:48 2024

@author: rbala
!!!!!!!!!!!!!!!!!!!!!!!!!!!

CAUTION: 
    
    The script is written to calculate/ process some datas from simulation.
    Please consult the author before altering the script.


!!!!!!!!!!!!!!!!!!!!!!!!!!!
this script consists:
    - function to convert timeseries from any resolution to hourly values, does'nt matter which type of data is given to the funtion (can be a series/DF/list/etc.)' 
    - function to calculate the investment, operating and equivalent periodic costs 
        
"""
import pandas as pd
from oemof.tools import economics
from src.preprocessing.epc import annuity

def convert_into_hourly_values (data, simulation_year, existing_res = '15min'):
    
    # existing_res --> 15min /H/1min
    # data can be provies as a list of series or as a dataframe
           
    if type(data) == list:
        df = pd.DataFrame()
        for y in simulation_year:
            for s in data:
                d_t_index = pd.date_range('1/1/' +str(y), periods = len(data), freq = existing_res)
                df = df.append(s)
            a = df.T
            a = a.set_index(d_t_index)
            a = a.resample('H').mean()
            return(a)
    
    elif type(data) == pd.core.frame.DataFrame:
        for y in simulation_year:
            d_t_index = pd.date_range('1/1/' +str(y), periods = len(data), freq = existing_res)
            data= data.set_index(d_t_index)
            data = data.resample('H').mean()
            return(data)
        

def investment_parameter(data,simulation_year, Model_ID):

    '''
    data : dictionary with all the techno-economical parameters (csv file)
    simulationyear: to choose the specific parameter for the respective simulation year
    
    Function to calculate epc costs and store it as a variable for all technologies
    
    Note: Fix a standard file name format for technology parameters.
    '''   
    T_list = []             # Technology list will be automatically generated based on the file name
    for i in data:
        if i.startswith('Parameter'):
            i = i[10:]
            #i = i[:-5]
            T_list.append(i) 

    my_dict={}
    for name in T_list:
        n = "Parameter_"+ name 
        my_dict[name]= {}
        my_dict[name]['investk'] = annuity(capex=data[n]['investment_costs_'+str(simulation_year)][Model_ID], n=data[n]['lifetime_'+str(simulation_year)][Model_ID], u=data[n]['lifetime_'+str(simulation_year)][Model_ID], wacc=data['System_configurations_2024']['System']['Zinssatz']/100)
        my_dict[name]['betriebsk'] = data[n]['investment_costs_'+str(simulation_year)][Model_ID] * (data[n]['operating_costs_'+str(simulation_year)][Model_ID]/100)
        my_dict[name]['epc'] = my_dict[name]['investk'] + my_dict[name]['betriebsk']
        
    return(my_dict)


def load_profile_scaling(scalars, sequences, YEAR, model_ID, region = True):
    profile = []                             # Sorting only the timeseies from the list of all files in the sequences folder
    for i in sequences: 
        if i.endswith('profile'):
            profile.append(i)
    
    load_profile_nom = {}
    for name in profile:
        load_profile_nom[name]= sequences[name]/sequences[name].sum() # Normalising the timeseries to scale the profile to respective energy demand.
    
    sector = ['electricity', 'gas', 'dist_heating', 'biomass', 'oil', 'material_usage_gas', 'material_usage_biomasse','material_usage_oil', 'H2', 'fuel', 'rechnenzentrum']
    
    region = ['north', 'middle', 'east', 'swest']
    
    demand_profile_dict={}
    
    if model_ID.startswith('BS'):
        sze = 'b'
    elif model_ID.startswith('IS'):
        sze = 'i'
    if YEAR == 2020:
        sze = ''
    else:
        sze =sze
        
    for s in sector:
        demand_profile_dict[s] = {}
        for r in region: 
            """ 
            Total electricity load profile consists of:
                Industry electricity demand - G3 SLP 
                Electricity demand for industry space heating: PtH Heating rod - HA4 
                Electricity demand for industry space heating: PtH Air heatpump - HA4 
                Electricity demand for industry space heating: PtH Geothermal heatpump - HA4 
                Electricity demand for GHD space heating: PtH Heating rod - HA4 
                Electricity demand for GHD space heating: PtH Air heatpump - HA4 
                Electricity demand for GHD space heating: PtH Geothermal heatpump - HA4 
                Electricity demand for industry Process heating: PtH Heating rod - ACS Prozessgas profile  
                Electricity demand for industry Process heating: PtH Air heatpump - ACS Prozessgas profile 
                Electricity demand for industry Process heating: PtH Geothermal heatpump - ACS Prozessgas profile
                Electricity demand for GHD Process heating: PtH Heating rod - ACS Prozessgas profile  
                Electricity demand for GHD Process heating: PtH Air heatpump - ACS Prozessgas profile 
                Electricity demand for GHD Process heating: PtH Geothermal heatpump - ACS Prozessgas profile
                Household electricity demand - RAMP profile
                Electricity demand for household space heating: PtH Heating rod - 5RC profile 
                Electricity demand for household space heating: PtH Air heatpump - 5RC profile
                Electricity demand for household space heating: PtH Geothermal heatpump - 5RC profile
                Electricity demand for household space cooling: Kompressionskälte - 5RC profile 
                Electricity demand for household space cooling: Scorptionskälte- 5RC profile
                Electricity demand for Industry space cooling: Kompressionskälte - 5RC profile 
                Electricity demand for GHD space cooling: Kompressionskälte - 5RC profile 
                Mobility demand Personenverkehr: Car - RAMP
                Mobility demand Personenverkehr: Bus - RAMP
                Mobility demand Personenverkehr: Train - RAMP
                Mobility demand Güterverkehr: Train - RAMP
                Mobility demand Güterverkehr: LKW - base load
            
            Total gas load profile consists of:
                Raumwärme: Heizkessel gas - industry, GHD - HA4 
                Prozesswärme: Heizkessel gas- industy, GHD - ACS Prozessgas profile
                Raumwärme: Heizkessel gas - Household - 5RC profile
                verkehr - PKW verbrenner CNG - Base load
                
            Biomass:
                Raumwärme: Festbrennstoffkessel - industry, GHD - HA4 
                Prozesswärme: Festbrennstoffkessel- industy, GHD - ACS Prozessgas profile
                Raumwärme: Festbrennstoffkessel - Household - 5RC profile
            
            Oil:
                Raumwärme: Heizkessel Oel -  GHD - HA4 
                Prozesswärme: Heizkessel Oel- GHD - ACS Prozessgas profile
                Raumwärme: Heizkessel Oel - Household - 5RC profile
            
            District_heating:
                Raumwärme: Waermeuebergabestation - industry, GHD - HA4 
                Prozesswärme: Waermeuebergabestation- industy, GHD - ACS Prozessgas profile
                Raumwärme: Waermeuebergabestation - Household - 5RC profile
            
            H2:
                Gueterverkehr -PKW, LKW, Schiene : Base load
                Personenverkehr - PKW, LKW, Schiene: Base load
            
            Fuel:
                Gueterverkehr -PKW, LKW, Schiene, Busse : Base load
                Personenverkehr - PKW, LKW, Schiene, Busse: Base load
                
            Material_usage:
                Gas: Baseload
                Oil: baseload
                Biomass: baseload
            
            Rechnenzentrum:
                Electricity: Baseload

            """
            if s == 'electricity':
                                # Load profile * (total demand * (percentage share/100)/ EER) 
                        
                demand_profile_dict[s][r]= ((load_profile_nom['other_demand_profile']['G3'] * (float(scalars['Demand_Industry_' + r]['Strom_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r ]['Strom_' + str(YEAR)+sze]['Elektrogeraete'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Elektrogeraete'])))+
                                                    (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Heizstab'])/100) /float(scalars['Demand_Industry_'+ r ]['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                    (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r ]['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                    (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r ]['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                    (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_GHD_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Heizstab'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                    (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_GHD_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                    (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_GHD_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                    (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r ]['Prozesswaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r ]['Prozesswaerme_' + str(YEAR)+sze]['PtH Heizstab'])/100) /float(scalars['Demand_Industry_'+ r ]['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                    (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r ]['Prozesswaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r ]['Prozesswaerme_' + str(YEAR)+sze]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r ]['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                    (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r ]['Prozesswaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r ]['Prozesswaerme_' + str(YEAR)+sze]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r ]['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                    (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r ]['Prozesswaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Prozesswaerme_' + str(YEAR)+sze]['PtH Heizstab'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                    (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r ]['Prozesswaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Prozesswaerme_' + str(YEAR)+sze]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                    (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r ]['Prozesswaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Prozesswaerme_' + str(YEAR)+sze]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                    (load_profile_nom['other_demand_profile']['G0'] * (float(scalars['Demand_GHD_' + r ]['Strom_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Strom_' + str(YEAR)+sze]['Elektrogeraete'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['Elektrogeraete'])))+
                                                    (load_profile_nom['Electricity_household_demand_profile'][r +'_'+ str(YEAR)] *(float(scalars['Demand_Household_' + r ]['Strom_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r ]['Strom_' + str(YEAR)+sze]['Elektrogeraete'])/100) /float(scalars['Demand_Household_'+ r ]['EER_' + str(YEAR)]['Elektrogeraete'])))+
                                                    (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Heizstab'])/100) /float(scalars['Demand_Household_'+ r ]['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                    (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Household_'+ r ]['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                    (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r ]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Household_'+ r ]['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                    (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_Household_' + r  ]['Klima- und Prozesskaelte_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r ]['Klima- und Prozesskaelte_' + str(YEAR)+sze]['Kompressionskaelte'])/100) /float(scalars['Demand_Household_'+ r ]['EER_' + str(YEAR)]['Kompressionskaelte'])))+
                                                    (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_Industry_' + r ]['Klima- und Prozesskaelte_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r ]['Klima- und Prozesskaelte_' + str(YEAR)+sze]['Kompressionskaelte'])/100) /float(scalars['Demand_Industry_'+ r ]['EER_' + str(YEAR)]['Kompressionskaelte'])))+
                                                    (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_GHD_' + r ]['Klima- und Prozesskaelte_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Klima- und Prozesskaelte_' + str(YEAR)+sze]['Kompressionskaelte'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['Kompressionskaelte'])))+
                                                    (load_profile_nom['Mobility_demand_profile']['car_'+str(YEAR)]* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW - Batterie']))))+
                                                    (load_profile_nom['Mobility_demand_profile']['bus_'+str(YEAR)]* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['Busse - Batterie']))))+
                                                    (load_profile_nom['Mobility_demand_profile']['train_'+str(YEAR)]* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['Schiene - Batterie']))))+
                                                    (load_profile_nom['Mobility_demand_profile']['train_'+str(YEAR)]* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['Schiene - Batterie']))))+
                                                    (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['LKW - Batterie']))))
                                                    )*1000000 # TWh to MWh noch GHD 


            elif s == 'gas':
                if YEAR == 2030:
                    demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Heizkessel Gas'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                 (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Heizkessel Gas'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                 (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r]['Prozesswaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                                 (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r]['Prozesswaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Heizkessel Gas'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                  (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r]['Raumwaerme_'+ str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Heizkessel Gas'])/100) /float(scalars['Demand_Household_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                  (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW Verbrenner CNG']))))
                                                  )*1000000
                else:
                    demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                                 (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Heizkessel Gas'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                               (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                               (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Heizkessel Gas'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas'])))+   
                                               (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Heizkessel Gas'])/100) /float(scalars['Demand_Household_'+ r]['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                 (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW Verbrenner CNG']))))
                                                  )*1000000
                    
            elif s== 'biomass':
                if YEAR == 2030:
                    demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                 (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                            (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Festbrennstoffkessel_1'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel_1'])))+
                                            (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                            (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Household_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))
                                            )*1000000
                else:
                    demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                 (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                 (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Household_'+ r]['EER_' + str(YEAR)]['Festbrennstoffkessel'])))
                                                )*1000000
            elif s== 'oil':
                
                demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r ]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['Heizkessel Oel'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['Heizkessel Oel'])))+
                                             (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r ]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r ]['Prozesswaerme_' + str(YEAR)+sze]['Heizkessel Oel'])/100) /float(scalars['Demand_GHD_'+ r ]['EER_' + str(YEAR)]['Heizkessel Oel'])))+
                                             (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r ]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r ]['Raumwaerme_' + str(YEAR)+sze]['Heizkessel Oel'])/100) /float(scalars['Demand_Household_'+ r ]['EER_' + str(YEAR)]['Heizkessel Oel'])))
                                            )*1000000

            elif s== 'dist_heating':
                demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Waermeuebergabestation'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Waermeuebergabestation'])))+
                                             (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Waermeuebergabestation'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Waermeuebergabestation'])))+
                                        (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Waermeuebergabestation'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Waermeuebergabestation'])))+
                                        (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_GHD_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Waermeuebergabestation'])/100) /float(scalars['Demand_GHD_'+ r]['EER_' + str(YEAR)]['Waermeuebergabestation'])))+
                                        (load_profile_nom['Heat_demand_profile']['Heat+TWW_'+ r] *(float(scalars['Demand_Household_' + r]['Raumwaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Household_'+ r]['Raumwaerme_' + str(YEAR)+sze]['Waermeuebergabestation'])/100) /float(scalars['Demand_Household_'+ r]['EER_' + str(YEAR)]['Waermeuebergabestation'])))
                                        )*1000000

            elif s== 'H2':
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['PKW - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['LKW - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['Schiene - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['LKW - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['Schiene - Wasserstoff']))))+
                                             (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r]['Prozesswaerme_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Prozesswaerme_' + str(YEAR)+sze]['Heizkessel Wasserstoff'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Heizkessel Wasserstoff'])))
                                             )*1000000
            elif s== 'fuel':
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['PKW Verbrenner']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['LKW - Verbrenner']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['Schiene - Verbrenner']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['Busse - Verbrenner']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW Verbrenner']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['LKW - Verbrenner']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['Schiene - Verbrenner']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['Busse - Verbrenner']))))
                                             )*1000000
            
            elif s == 'material_usage_gas':
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']*(float(scalars['Demand_Industry_' + r]['Stoffl. Nutzung_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Stoffl. Nutzung_' + str(YEAR)+sze]['Materialnutzung Gas'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Materialnutzung Gas'])))
                                             )*1000000
            elif s == 'material_usage_oil':
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']*(float(scalars['Demand_Industry_' + r]['Stoffl. Nutzung_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Stoffl. Nutzung_' + str(YEAR)+sze]['Materialnutzung Oel'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Materialnutzung Oel'])))
                                             )*1000000
                
            elif s == 'material_usage_biomasse':
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']*(float(scalars['Demand_Industry_' + r]['Stoffl. Nutzung_'+str(YEAR)+sze]['Summe']) * (float(scalars['Demand_Industry_'+ r]['Stoffl. Nutzung_' + str(YEAR)+sze]['Materialnutzung Biomasse'])/100) /float(scalars['Demand_Industry_'+ r]['EER_' + str(YEAR)]['Materialnutzung Biomasse'])))
                                             )*1000000
            
            elif s == 'rechnenzentrum':
                demand_profile_dict[s][r] = (load_profile_nom['Base_demand_profile']['base_load'] *((float(scalars['Demand_Rechnenzentrum']['electricity_'+str(YEAR)]['Summe'])/4)* (float(scalars['System_configurations_2024']['System']['gesamte_Bundesflaeche'])/100)))*1000000
                
    demand = pd.DataFrame()
    demand['electricity'] = demand_profile_dict['electricity']['north']+demand_profile_dict['electricity']['east']+demand_profile_dict['electricity']['middle']+demand_profile_dict['electricity']['swest']
                                             
    demand['gas'] =demand_profile_dict['gas']['north']+demand_profile_dict['gas']['east']+demand_profile_dict['gas']['middle']+demand_profile_dict['gas']['swest']

    demand['biomass'] =demand_profile_dict['biomass']['north']+demand_profile_dict['biomass']['east']+demand_profile_dict['biomass']['middle']+demand_profile_dict['biomass']['swest']

    demand['oil'] =demand_profile_dict['oil']['north']+demand_profile_dict['oil']['east']+demand_profile_dict['oil']['middle']+demand_profile_dict['oil']['swest']

    demand['dist_heating'] =demand_profile_dict['dist_heating']['north']+demand_profile_dict['dist_heating']['east']+demand_profile_dict['dist_heating']['middle']+demand_profile_dict['dist_heating']['swest']

    demand['H2'] = demand_profile_dict['H2']['north']+demand_profile_dict['H2']['east']+demand_profile_dict['H2']['middle']+demand_profile_dict['H2']['swest']

    demand['fuel'] = demand_profile_dict['fuel']['north']+demand_profile_dict['fuel']['east']+demand_profile_dict['fuel']['middle']+demand_profile_dict['fuel']['swest']

    demand['material_usage_gas'] = demand_profile_dict['material_usage_gas']['north']+demand_profile_dict['material_usage_gas']['east']+demand_profile_dict['material_usage_gas']['middle']+demand_profile_dict['material_usage_gas']['swest']
    demand['material_usage_oil'] = demand_profile_dict['material_usage_oil']['north']+demand_profile_dict['material_usage_oil']['east']+demand_profile_dict['material_usage_oil']['middle']+demand_profile_dict['material_usage_oil']['swest']
    demand['rechnenzentrum'] = demand_profile_dict['rechnenzentrum']['north']+demand_profile_dict['rechnenzentrum']['east']+demand_profile_dict['rechnenzentrum']['middle']+demand_profile_dict['rechnenzentrum']['swest']
    
    print('Demand Electricity: ', demand['electricity'].sum())
    print('Demand Gas: ', demand['gas'].sum())
    
    print('Demand Biomasse: ', demand['biomass'].sum())
    print('Demand Oil: ', demand['oil'].sum())
    
    print('Demand Heat: ', demand['dist_heating'].sum())
    print('Demand H2: ', demand['H2'].sum())
    
    print('Demand Fuel: ', demand['fuel'].sum())
    print('Demand Matrialbedarf Gas: ', demand['material_usage_gas'].sum())
    print('Demand Matrialbedarf Oil: ', demand['material_usage_oil'].sum())
    print('Demand Rechnenzentrum: ', demand['rechnenzentrum'].sum())
    
    if model_ID.startswith('BS_regionalization'):
        print('Region')
        return demand_profile_dict
    else:
        return demand

def CO2_price_addition(scalars,sequences,YEAR, filename):
    data_dict = {}
    
    if YEAR <= 2030:
        data_dict['import_gas_price'] = sequences[filename]['Gas_'+str(YEAR)] + (scalars['System_configurations_2024']['System']['Emission_Erdgas']*sequences[filename]['CO2_'+str(YEAR)])
        data_dict['import_oil_price'] = sequences[filename]['Oil_'+str(YEAR)] + (scalars['System_configurations_2024']['System']['Emission_Oel']*sequences[filename]['CO2_'+str(YEAR)])
        data_dict['import_hard_coal_price'] = sequences[filename]['Hard_coal_'+str(YEAR)] + (scalars['System_configurations_2024']['System']['Emission_Steinkohle']*sequences[filename]['CO2_'+str(YEAR)])
        data_dict['import_brown_coal_price'] = sequences[filename]['Brown_coal_'+str(YEAR)] + (scalars['System_configurations_2024']['System']['Emission_Braunkohle']*sequences[filename]['CO2_'+str(YEAR)])
        data_dict['import_biomass_price'] = sequences[filename]['Biomass_'+ str(YEAR)]
        data_dict['import_synt_fuel_price'] = sequences[filename]['Synthetic_fuel_'+ str(YEAR)]
        #data_dict['import_electricity_price_alt'] = sequences['Energy_price']['Electricity_'+str(YEAR)]
        #data_dict['import_electricity_price_2019'] = sequences['Energy_price']['Electricity_brain_'+str(YEAR)]
        data_dict['import_electricity_price'] = sequences[filename]['Electricity_'+str(YEAR)]
        #data_dict['export_electricity_price_2019'] = [i *(-1) for i in sequences['Energy_price']['Electricity_brain_'+str(YEAR)]]
        data_dict['export_electricity_price'] =  [i *(-1) for i in sequences[filename]['Electricity_'+str(YEAR)]]
        data_dict['export_hydrogen_price'] = [i*(-1) for i in sequences[filename]['Hydrogen_' + str(YEAR)]]
        data_dict['import_hydrogen_price'] = [i+scalars['Hydrogen_grid']['hydrogen']['grid_operating_fee'] for i in sequences[filename]['Hydrogen_' + str(YEAR)]]
        data_dict['grid_operating_fee_old'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee'] for i in sequences['Base_demand_profile']['base_load']]
        data_dict['grid_operating_fee_HöS<2500h'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee_HöS<2500h'] for i in sequences['Base_demand_profile']['base_load']]
        data_dict['grid_operating_fee_HöS>2500h'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee_HöS>2500h'] for i in sequences['Base_demand_profile']['base_load']]
        data_dict['grid_operating_fee_HS<2500h'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee_HS<2500h'] for i in sequences['Base_demand_profile']['base_load']]
        data_dict['grid_operating_fee_HS>2500h'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee_HS>2500h'] for i in sequences['Base_demand_profile']['base_load']]
    else:
        data_dict['import_gas_price'] = sequences[filename]['Gas_'+str(YEAR)] + (scalars['System_configurations_2024']['System']['Emission_Erdgas']*sequences[filename]['CO2_'+str(YEAR)])
        data_dict['import_oil_price'] = sequences[filename]['Oil_'+str(YEAR)] + (scalars['System_configurations_2024']['System']['Emission_Oel']*sequences[filename]['CO2_'+str(YEAR)])
        data_dict['import_hard_coal_price'] = sequences[filename]['Hard_coal_'+str(YEAR)] + (scalars['System_configurations_2024']['System']['Emission_Steinkohle']*sequences[filename]['CO2_'+str(YEAR)])+1000000000     #to make no availability of coal to the optimizer
        data_dict['import_brown_coal_price'] = sequences[filename]['Brown_coal_'+str(YEAR)] + (scalars['System_configurations_2024']['System']['Emission_Braunkohle']*sequences[filename]['CO2_'+str(YEAR)])+1000000000
        data_dict['import_biomass_price'] = sequences[filename]['Biomass_'+ str(YEAR)]
        data_dict['import_synt_fuel_price'] = sequences[filename]['Synthetic_fuel_'+ str(YEAR)]
        # data_dict['import_electricity_price_alt'] = sequences['Energy_price']['Electricity_'+str(YEAR)]
        # data_dict['import_electricity_price_2019'] = sequences['Energy_price']['Electricity_brain_'+str(YEAR)]
        data_dict['import_electricity_price'] = sequences[filename]['Electricity_'+str(YEAR)]
        # data_dict['export_electricity_price_2019'] = [i *(-1) for i in sequences['Energy_price']['Electricity_brain_'+str(YEAR)]]
        data_dict['export_electricity_price'] = [i *(-1) for i in sequences[filename]['Electricity_'+str(YEAR)]]
        data_dict['export_hydrogen_price'] = [i*(-1) for i in sequences[filename]['Hydrogen_' + str(YEAR)]]
        data_dict['import_hydrogen_price'] = [i+scalars['Hydrogen_grid']['hydrogen']['grid_operating_fee'] for i in sequences[filename]['Hydrogen_' + str(YEAR)]]
        data_dict['grid_operating_fee_old'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee'] for i in sequences['Base_demand_profile']['base_load']]
        data_dict['grid_operating_fee_HöS<2500h'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee_HöS<2500h'] for i in sequences['Base_demand_profile']['base_load']]
        data_dict['grid_operating_fee_HöS>2500h'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee_HöS>2500h'] for i in sequences['Base_demand_profile']['base_load']]
        data_dict['grid_operating_fee_HS<2500h'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee_HS<2500h'] for i in sequences['Base_demand_profile']['base_load']]
        data_dict['grid_operating_fee_HS>2500h'] = [i+scalars['Electricity_grid']['electricity']['grid_operating_fee_HS>2500h'] for i in sequences['Base_demand_profile']['base_load']]
    return (data_dict)

def COP_calculation(scalars, T_a, model_ID, YEAR):

    T_VL = [None]*8760
    COP = [None]*8760
    T_VL_L = scalars['Temperature_dist_heat']['T_VL_L_' + str(YEAR)][model_ID]      # Lower limit of Forward temperature
    T_VL_U = scalars['Temperature_dist_heat']['T_VL_U_' + str(YEAR)][model_ID]      # Upper limit of forward temperature
    T_RL = scalars['Temperature_dist_heat']['T_RL_' + str(YEAR)][model_ID]          # Reverse temperature
    T_L = scalars['Temperature_dist_heat']['T_L'][model_ID]                         # Ambient temperature lower limit
    T_U = scalars['Temperature_dist_heat']['T_U'][model_ID]                         # Ambient temperature upper limit
    
    for i in range(len(T_a)):
        if T_a[i] > T_L and T_a[i] < T_U:
            T_VL[i] = T_VL_L - ((T_VL_L - T_VL_U)/(T_U - T_L)) * (T_a[i] - T_L)
        elif T_a[i] <= T_L:
            T_VL[i] = T_VL_L
        elif T_a[i] >= T_U:
            T_VL[i] = T_VL_U
        nu_H = 0.36 #efficiency of heatpump
        COP[i] = nu_H*(T_VL[i]+273.15) / (T_VL[i]-T_RL)
    return pd.Series(COP), pd.Series(T_VL)

    
def Utility_demand_breakdown(scalars, sequences, YEAR, demand_type = 'space_heating_household', region = True):
    profile = []
    for i in sequences:
        if i.endswith('profile'):
            profile.append(i)

    load_profile_nom = {}
    for name in profile:
        load_profile_nom[name] = sequences[name] / sequences[name].sum()

    regions = ['north', 'middle', 'east', 'swest']
    technology_data = {}
    sector_sum = {}
    
    for r in regions:
        technology_data[r] = {}
        
        #------------------------------------------------------- ###### Haushalte #######
        if demand_type == 'space_heating_household':
            technologies = {
                'PtH Heizstab': (
                    load_profile_nom['Heat_demand_profile']['Heat+TWW_' + r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Heizstab'])/100))
                ) * 1000000,
                
                'PtH Luftwaermepumpe': (
                    load_profile_nom['Heat_demand_profile']['Heat+TWW_' + r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100))
                ) * 1000000,
                
                'PtH Erdwaermepumpe': (
                    load_profile_nom['Heat_demand_profile']['Heat+TWW_' + r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100))
                ) * 1000000,
                
                'Solarthermie': (
                    load_profile_nom['feed_in_profile']['Solarthermal'] *
                    (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Solarthermie'])/100))
                ) * 1000000,
                
                'Festbrennstoffkessel': (
                    load_profile_nom['Heat_demand_profile']['Heat+TWW_' + r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100))
                ) * 1000000,
                
                'Heizkessel Gas': (
                    load_profile_nom['Heat_demand_profile']['Heat+TWW_' + r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100))
                ) * 1000000,
                
                'Heizkessel Oel': (
                    load_profile_nom['Heat_demand_profile']['Heat+TWW_' + r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Oel'])/100))
                ) * 1000000,
                
                'Waermeuebergabestation': (
                    load_profile_nom['Heat_demand_profile']['Heat+TWW_' + r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Waermeuebergabestation'])/100))
                ) * 1000000
            }
            
        elif demand_type == 'cooling_household':
            technologies = {
                'Kompressionskaelte': (
                    load_profile_nom['Cooling_demand_profile'][r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Kompressionskaelte'])/100))
                ) * 1000000,
                
                'Sorptionskaelte': (
                    load_profile_nom['Cooling_demand_profile'][r] *
                    (float(scalars['Demand_Household_' + r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Sorptionskaelte'])/100))
                ) * 1000000
            }
            
        elif demand_type == 'electrical_household':
            technologies = {
                'Elektrogeraete': (
                    load_profile_nom['Electricity_household_demand_profile'][r + '_' + str(YEAR)] *
                    (float(scalars['Demand_Household_' + r + '_b']['Strom_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Household_' + r + '_b']['Strom_' + str(YEAR)]['Elektrogeraete'])/100))
                ) * 1000000
            }
            
        #------------------------------------------------------- ###### Industry #######
        elif demand_type == 'space_heating_industry':
            technologies = {
                'PtH Heizstab': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Heizstab'])/100))
                ) * 1000000,
                
                'PtH Luftwaermepumpe': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100))
                ) * 1000000,
                
                'PtH Erdwaermepumpe': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100))
                ) * 1000000,
                
                'Solarthermie': (
                    load_profile_nom['feed_in_profile']['Solarthermal'] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Solarthermie'])/100))
                ) * 1000000,
                
                'Festbrennstoffkessel': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100))
                ) * 1000000,
                
                'Festbrennstoffkessel_1': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel_1'])/100))
                ) * 1000000,
                
                'Heizkessel Gas': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100))
                ) * 1000000,
                
                'Heizkessel Gas_1': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100))
                ) * 1000000,
                
                'Heizkessel Wasserstoff': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Wasserstoff'])/100))
                ) * 1000000,
                
                'Waermeuebergabestation': (
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Waermeuebergabestation'])/100))
                ) * 1000000
            
            }
            
        # -------------------------
        # Process heating (industry)
        # -------------------------
        elif demand_type == 'process_heating_industry':
            technologies = {
                'PtH Heizstab': (
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Heizstab'])/100)
                  ))*1000000,
                
                'PtH Luftwaermepumpe':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) 
                  ))*1000000,
                
                'PtH Erdwaermepumpe':(                
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100)
                  ))*1000000,
                
                'Festbrennstoffkessel_1': (
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel_1'])/100) 
                  ))*1000000,
                
                'Festbrennstoffkessel':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) 
                  ))*1000000,
                
                'Heizkessel Gas':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas'])/100) 
                  ))*1000000,
                
                'Heizkessel Gas_1':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100) 
                  ))*1000000,
                
                'Heizkessel Wasserstoff':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Wasserstoff'])/100) 
                  ))*1000000,
                
                'Waermeuebergabestation':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Waermeuebergabestation'])/100) 
                  ))*1000000 
            }
            
        elif demand_type == 'cooling_industry':
            technologies = {
                'Kompressionskaelte':(
                    load_profile_nom['Cooling_demand_profile'][r] *
                     (float(scalars['Demand_Industry_' + r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_Industry_' + r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Kompressionskaelte'])/100) 
                  )) * 1000000
                }
            
        elif demand_type == 'electrical_industry':
            technologies = {
                'Elektrogeraete':(
                    load_profile_nom['other_demand_profile']['G3'] *
                     (float(scalars['Demand_Industry_' + r + '_b']['Strom_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_Industry_' + r + '_b']['Strom_' + str(YEAR)]['Elektrogeraete'])/100)
                      )) * 1000000
                }
            
        elif demand_type == 'material_usage_industry':
            technologies = {
                'Materialnutzung Gas':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                     (float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Materialnutzung Gas'])/100) 
                  ))*1000000,
                
                'Materialnutzung Biomasse':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                     (float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Materialnutzung Biomasse'])/100) 
                  ))*1000000,
                
                'Materialnutzung Öl':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Materialnutzung Öl'])/100) 
                     ))* 1000000
                }
            
#------------------------------------------------------- ###### GHD #######----------------------------------------------------------------------------
        # -------------------------
        # Space heating (GHD)
        # -------------------------
        elif demand_type == 'space_heating_ghd':
            technologies = {
                'PtH Heizstab':(
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                     (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Heizstab'])/100) 
                  ))*1000000,
                
                'PtH Luftwaermepumpe':(
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) 
                     ))*1000000,
                
                'PtH Erdwaermepumpe':(
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) 
                     ))*1000000,
                
                'Solarthermie':(
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Solarthermie'])/100) 
                     ))*1000000,
                
                'Festbrennstoffkessel':(
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) 
                     ))*1000000,
                
                'Heizkessel Gas':(
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100)
                     ))*1000000,
                
                'Heizkessel Oel':(
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Oel'])/100) 
                     ))*1000000,
                
                'Waermeuebergabestation':(
                    load_profile_nom['Heat_demand_profile']['HA4_' + r] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_' + str(YEAR)]['Waermeuebergabestation'])/100) 
                     )) * 1000000
                
                }

        # -------------------------
        # Process heating (GHD)
        # -------------------------
        elif demand_type == 'process_heating_ghd':
            technologies = {
                'PtH Heizstab':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Heizstab'])/100) 
                     ))*1000000,
                
                'PtH Luftwaermepumpe':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) 
                     ))*1000000,
                
                'PtH Erdwaermepumpe':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                     (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) 
                      ))*1000000,
                    
                'Waermeuebergabestation':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Waermeuebergabestation'])/100) 
                     ))*1000000,
                
                'Festbrennstoffkessel':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                     (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                      (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100)
                      ))*1000000,
                 
                'Heizkessel Gas':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas'])/100) 
                     ))*1000000,
                
                'Heizkessel Oel':(
                    load_profile_nom['other_demand_profile']['Prozessgas'] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Oel'])/100) 
                     ))* 1000000
                }

        # -------------------------
        # Cooling (household / industry / ghd)
        # -------------------------

        elif demand_type == 'cooling_ghd':
            technologies = {
                'Kompressionskaelte':(
                    load_profile_nom['Cooling_demand_profile'][r] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Kompressionskaelte'])/100) 
                  )) * 1000000
                }
            
        # -------------------------
        # Electrical end-use (elektrogeraete) household / ghd / industry
        # -------------------------

        elif demand_type == 'electrical_ghd':
            technologies = {
                'Elektrogeraete':(
                    load_profile_nom['other_demand_profile']['G0'] *
                    (float(scalars['Demand_GHD_' + r + '_b']['Strom_' + str(YEAR)]['Summe']) *
                     (float(scalars['Demand_GHD_' + r + '_b']['Strom_' + str(YEAR)]['Elektrogeraete'])/100) 
                  )) * 1000000
                }
#------------------------------------------------------- ###### Verkehr #######----------------------------------------------------------------------------
        # -------------------------
        # Mobility split: person / goods
        # -------------------------
        elif demand_type == 'mobility_person':
            technologies = {
                'PKW - Batterie':(
                    load_profile_nom['Mobility_demand_profile']['car_' + str(YEAR)] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Summe_NE']) *
                     float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['PKW - Batterie'])
                     ))*1000000,
                
                'PKW - H2':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Summe_NE']) *
                     float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['PKW - H2'])
                     ))*1000000,
                
                'PKW - Verbrenner':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Summe_NE']) *
                     float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['PKW - Verbrenner'])
                     ))*1000000,
                
                'PKW - Verbrenner CNG':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Summe_NE']) *
                     float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['PKW - Verbrenner CNG'])
                     ))*1000000,
                
                'Busse - Batterie':(
                    load_profile_nom['Mobility_demand_profile']['bus_' + str(YEAR)] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Summe_NE']) *
                     (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Busse - Batterie'])
                      )))*1000000,
                
                'Busse - Verbrenner':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Summe_NE']) *
                     float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Busse - Verbrenner'])
                     ))*1000000,
                
                'Schiene - Elektrisch':(
                    load_profile_nom['Mobility_demand_profile']['train_' + str(YEAR)] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Summe_NE']) *
                     (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Schiene - Elektrisch']))
                     ))*1000000,
                
                'Schiene - Verbrenner':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Summe_NE']) *
                     float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Personenverkehr_' + str(YEAR)]['Schiene - Verbrenner'])
                     )) * 1000000
                }

        elif demand_type == 'mobility_goods':
            technologies = {
                'Schiene - Elektrisch_g':(
                    load_profile_nom['Mobility_demand_profile']['train_' + str(YEAR)] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['Summe_NE']) *
                     (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['Schiene - Elektrisch_g']))
                     ))*1000000,
                
                'LKW - H2':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['Summe_NE']) *
                     (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['LKW - H2']))
                     ))*1000000,
                
                'LKW - Verbrenner':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['Summe_NE']) *
                     (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['LKW - Verbrenner']))
                     ))*1000000,
                
                'Schiene - Verbrenner_g':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['Summe_NE']) *
                     (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['Schiene - Verbrenner_g']))
                     ))*1000000,
                
                'LKW - Batterie':(
                    load_profile_nom['Base_demand_profile']['base_load'] *
                    (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['Summe_NE']) *
                     (float(scalars['Demand_Transport_nutzenergie_' + r + '_b']['NE_Gueterverkehr_' + str(YEAR)]['LKW - Batterie']))
                     ))* 1000000
                }
        
        elif demand_type == 'rechnenzentrum':
            technlogies = {
                'Rechnenzentrum':(load_profile_nom['Base_demand_profile']['base_load'] *
                                  (float(scalars['Demand_Rechnenzentrum']['electricity_'+str(YEAR)]['Summe'])/4)
                                  * (float(scalars['System_configurations_2024']['System']['gesamte_Bundesflaeche'])/100)
                                  )*1000000
                    }
            
        else:
            technologies = {}
            print(f"Warning: Demand type '{demand_type}' not implemented in technology breakdown")

        
        region_technology_series = {}
        for tech_name, tech_series in technologies.items():
            technology_data[r][tech_name] = {
                'series': tech_series,
                'max_value': tech_series.max(),
                'min_value': tech_series.min(),
                'max_time': tech_series.idxmax(),
                'total_value': tech_series.sum()
            }
            region_technology_series[tech_name] = tech_series
        
        if technologies:
            sector_sum_series = sum(technologies.values())
            sector_sum[r] = {
                'series': sector_sum_series,
                'max_value': sector_sum_series.max(),
                'min_value': tech_series.min(),
                'max_time': sector_sum_series.idxmax(),
                'total_value': sector_sum_series.sum()
            }
        else:
            sector_sum[r] = {
                'series': pd.Series(0, index=sequences[list(sequences.keys())[0]].index),
                'max_value': 0,
                'min_value': 0,
                'max_time': None,
                'total_value': 0
            }
            
    def sum_all_regions(technology_breakdown, sector_sum, regions):
        """
        Sum technology breakdown and sector sum across all regions
        """
        all_tech_names = set()
        for region_techs in technology_breakdown.values():
            all_tech_names.update(region_techs.keys())
        
        summed_technology_breakdown = {}
        for tech_name in all_tech_names:
            tech_series_list = []
            for r in regions:
                if tech_name in technology_breakdown[r]:
                    tech_series_list.append(technology_breakdown[r][tech_name]['series'])
            
            if tech_series_list:
                summed_series = sum(tech_series_list)
                summed_technology_breakdown[tech_name] = {
                    'series': summed_series,
                    'max_value': summed_series.max(),
                    'min_value': summed_series.min(),
                    'max_time': summed_series.idxmax(),
                    'total_value': summed_series.sum()
                }
        
        sector_series_list = [sector_sum[r]['series'] for r in regions]
        summed_sector_series = sum(sector_series_list)
        
        summed_sector_sum = {
            'series': summed_sector_series,
            'max_value': summed_sector_series.max(),
            'min_value': summed_series.min(),
            'max_time': summed_sector_series.idxmax(),
            'total_value': summed_sector_series.sum()
        }
        
        return {
            'technology_data': summed_technology_breakdown,
            'demand_data': summed_sector_sum
        }

    if region:
        return {
            'technology_data': technology_data,
            'demand_data': sector_sum
        }
    else:
        return sum_all_regions(technology_data, sector_sum, regions)
    
    