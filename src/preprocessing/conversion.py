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
        my_dict[name]['investk'] = economics.annuity(capex=data[n]['investment_costs_'+str(simulation_year)][Model_ID], n=data[n]['lifetime_'+str(simulation_year)][Model_ID], wacc=data['System_configurations']['System']['Zinssatz']/100)
        my_dict[name]['betriebsk'] = data[n]['investment_costs_'+str(simulation_year)][Model_ID] * (data[n]['operating_costs_'+str(simulation_year)][Model_ID]/100)
        my_dict[name]['epc'] = my_dict[name]['investk'] + my_dict[name]['betriebsk']
        
    return(my_dict)


def load_profile_scaling(scalars, sequences, YEAR):
    profile = []                             # Sorting only the timeseies from the list of all files in the sequences folder
    for i in sequences: 
        if i.endswith('profile'):
            profile.append(i)
    
    load_profile_nom = {}
    for name in profile:
        load_profile_nom[name]= sequences[name]/sequences[name].sum() # Normalising the timeseries to scale the profile to respective energy demand.
    
    sector = ['electricity', 'gas', 'dist_heating', 'biomass', 'oil', 'material_usage_gas', 'material_usage_biomasse','material_usage_oil', 'H2', 'fuel']
    region = ['north', 'middle', 'east', 'swest']
    demand_profile_dict={}
        
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

            """
            if s == 'electricity':
                                # Load profile * (total demand * (percentage share/100)/ EER) 
                        
                    demand_profile_dict[s][r]= ((load_profile_nom['other_demand_profile']['G3'] * (float(scalars['Demand_Industry_' + r + '_b']['Strom_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Strom_' + str(YEAR)]['Elektrogeraete'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Elektrogeraete'])))+
                                                (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Heizstab'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Heizstab'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                (load_profile_nom['Heat_demand_profile']['HA4_'+ r] *(float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Heizstab'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Heizstab'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                (load_profile_nom['other_demand_profile']['G0'] * (float(scalars['Demand_GHD_' + r + '_b']['Strom_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Strom_' + str(YEAR)]['Elektrogeraete'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Elektrogeraete'])))+
                                                (load_profile_nom['Electricity_household_demand_profile'][r +'_'+ str(YEAR)] *(float(scalars['Demand_Household_' + r + '_b']['Strom_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Strom_' + str(YEAR)]['Elektrogeraete'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Elektrogeraete'])))+
                                                (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Heizstab'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['PtH Heizstab'])))+
                                                (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Luftwaermepumpe'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['PtH Luftwaermepumpe'])))+
                                                (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['PtH Erdwaermepumpe'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['PtH Erdwaermepumpe'])))+
                                                (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_Household_' + r + '_b']['Klima- und Prozesskaelte_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Kompressionskaelte'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Kompressionskaelte'])))+
                                                (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_Household_' + r + '_b']['Klima- und Prozesskaelte_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Sorptionskaelte'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Sorptionskaelte'])))+
                                                (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_Industry_' + r + '_b']['Klima- und Prozesskaelte_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Kompressionskaelte'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Kompressionskaelte'])))+
                                                (load_profile_nom['Cooling_demand_profile'][r] *(float(scalars['Demand_GHD_' + r + '_b']['Klima- und Prozesskaelte_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Klima- und Prozesskaelte_' + str(YEAR)]['Kompressionskaelte'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Kompressionskaelte'])))+
                                                (load_profile_nom['Mobility_demand_profile']['car_'+str(YEAR)]* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW - Batterie']))))+
                                                (load_profile_nom['Mobility_demand_profile']['bus_'+str(YEAR)]* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['Busse - Batterie']))))+
                                                (load_profile_nom['Mobility_demand_profile']['train_'+str(YEAR)]* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['Schiene - Batterie']))))+
                                                (load_profile_nom['Mobility_demand_profile']['train_'+str(YEAR)]* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['Schiene - Batterie']))))+
                                                (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['LKW - Batterie']))))
                                                )*1000000 # TWh to MWh noch GHD 
           
            
            elif s == 'gas':
                if YEAR == 2030:
                    demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                 (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                 (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                                 (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                  (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                  (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW Verbrenner CNG']))))
                                                  )*1000000
                else:
                    demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                                 (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                               (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas_1'])))+
                                               (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))+   
                                               (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Gas'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Gas'])))+
                                                 (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW Verbrenner CNG']))))
                                                  )*1000000
                    
            elif s== 'biomass':
                if YEAR == 2030:
                    demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                 (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                            (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel_1'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel_1'])))+
                                            (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                            (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))
                                            *1000000)
                else:
                    demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                 (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                 (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))+
                                                (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Festbrennstoffkessel'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Festbrennstoffkessel'])))
                                                *1000000)
            elif s== 'oil':
                
                demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Oel'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Oel'])))+
                                             (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Heizkessel Oel'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Oel'])))+
                                             (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Heizkessel Oel'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Heizkessel Oel'])))
                                            *1000000)
            
            elif s== 'dist_heating':
                demand_profile_dict[s][r] = ((load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_Industry_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Waermeuebergabestation'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Waermeuebergabestation'])))+
                                             (load_profile_nom['Heat_demand_profile']['HA4_'+ r]* (float(scalars['Demand_GHD_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Waermeuebergabestation'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Waermeuebergabestation'])))+
                                        (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_Industry_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Waermeuebergabestation'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Waermeuebergabestation'])))+
                                        (load_profile_nom['other_demand_profile']['Prozessgas'] *(float(scalars['Demand_GHD_' + r + '_b']['Prozesswaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_GHD_'+ r + '_b']['Prozesswaerme_' + str(YEAR)]['Waermeuebergabestation'])/100) /float(scalars['Demand_GHD_'+ r + '_b']['EER_' + str(YEAR)]['Waermeuebergabestation'])))+
                                        (load_profile_nom['Heat_demand_profile']['Household_'+ r] *(float(scalars['Demand_Household_' + r + '_b']['Raumwaerme_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Household_'+ r + '_b']['Raumwaerme_' + str(YEAR)]['Waermeuebergabestation'])/100) /float(scalars['Demand_Household_'+ r + '_b']['EER_' + str(YEAR)]['Waermeuebergabestation'])))
                                        *1000000)
            
            elif s== 'H2':
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['PKW - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['LKW - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Gueterverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Gueterverkehr_'+str(YEAR)]['Schiene - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['PKW - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['LKW - Wasserstoff']))))+
                                             (load_profile_nom['Base_demand_profile']['base_load']* (float(scalars['Demand_Transport_endenergie_'+ r + '_b']['Personenverkehr_'+str(YEAR)]['Summe'])*(float(scalars['Demand_Transport_endenergie_'+r+'_b']['Personenverkehr_'+str(YEAR)]['Schiene - Wasserstoff']))))
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
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']*(float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Materialnutzung Gas'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Materialnutzung Gas'])))
                                             )*1000000
            elif s == 'material_usage_oil':
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']*(float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Materialnutzung Öl'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Materialnutzung Öl'])))
                                             )*1000000
                
            elif s == 'material_usage_biomasse':
                demand_profile_dict[s][r] = ((load_profile_nom['Base_demand_profile']['base_load']*(float(scalars['Demand_Industry_' + r + '_b']['Stoffl. Nutzung_'+str(YEAR)]['Summe']) * (float(scalars['Demand_Industry_'+ r + '_b']['Stoffl. Nutzung_' + str(YEAR)]['Materialnutzung Biomasse'])/100) /float(scalars['Demand_Industry_'+ r + '_b']['EER_' + str(YEAR)]['Materialnutzung Biomasse'])))
                                             )*1000000
                
    return (demand_profile_dict)

def CO2_price_addition(scalars,sequences,YEAR):
    data_dict = {}
    
    if YEAR <= 2030:
        data_dict['import_gas_price'] = sequences['Energy_price']['Gas_'+str(YEAR)] + (scalars['System_configurations']['System']['Emission_Erdgas']*scalars['System_configurations']['System']['CO2_Preis_'+str(YEAR)])
        data_dict['import_oil_price'] = sequences['Energy_price']['Oil_'+str(YEAR)] + (scalars['System_configurations']['System']['Emission_Oel']*scalars['System_configurations']['System']['CO2_Preis_'+str(YEAR)])
        data_dict['import_hard_coal_price'] = sequences['Energy_price']['Hard_coal_'+str(YEAR)] + (scalars['System_configurations']['System']['Emission_Steinkohle']*scalars['System_configurations']['System']['CO2_Preis_'+str(YEAR)])
        data_dict['import_brown_coal_price'] = sequences['Energy_price']['Brown_coal_'+str(YEAR)] + (scalars['System_configurations']['System']['Emission_Braunkohle']*scalars['System_configurations']['System']['CO2_Preis_'+str(YEAR)])
    
    else:
        data_dict['import_gas_price'] = sequences['Energy_price']['Gas_'+str(YEAR)] + (scalars['System_configurations']['System']['Emission_Erdgas']*scalars['System_configurations']['System']['CO2_Preis_'+str(YEAR)])
        data_dict['import_oil_price'] = sequences['Energy_price']['Oil_'+str(YEAR)] + (scalars['System_configurations']['System']['Emission_Oel']*scalars['System_configurations']['System']['CO2_Preis_'+str(YEAR)])
    
    
    return (data_dict)