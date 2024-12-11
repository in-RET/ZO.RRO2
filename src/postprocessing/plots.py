# -*- coding: utf-8 -*-
"""
Created on Wed Dec 11 14:23:05 2024

@author: rbala
"""
import matplotlib.colors as mc
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.cm import ScalarMappable
import os
workdir = os.getcwd()


def heat_maps(data_dict,YEAR,permutation,profile_type, sector = None):
    """
    data_dict: dict with all the simulation data like load profiles, epc_costs, parameter......
    YEAR: simulation year
    profile_type: loadprofile, PV_Rooftop, PV_Openfield, Wind
    region: if profile_type == PV/Wind feed in, region should be specified 
            regions: north, east, middle, swest
    sector: for loadprofiles, sector should be specified
            sector: electricity, oil, gas, dist_heating,biomass, H2,fuel, material_usage_gas, material_usage_oil
    """
    
    date_time_index = pd.date_range("1/1/"+ str(YEAR), periods=8760, freq="h")
    month_title = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    if profile_type == 'loadprofile':
        data = data_dict['Loadprofiles']
        min_value = data[sector].min()
        max_value = data[sector].max()
        sector = sector
        fig,axes = plt.subplots(1,12, figsize = (19.1,10.5), sharey = True)
        fig.subplots_adjust(left = 0.05, right = 0.98, top = 0.9, hspace = 0.08, wspace = 0.04)
        fig.subplots_adjust(bottom=0.15)
        
        #Create a new axis to contain the color bar. Values are: (x cords for left border,
        #y cords for bottom border, width, height)
        cbar_ax = fig.add_axes([0.3, 0.05, 0.4, 0.025])
        
        norm = mc.Normalize(min_value, max_value)
        
        #create the colorbar and set it horizontal
        
        cb=fig.colorbar(ScalarMappable(norm = norm, cmap='magma'),
                        cax = cbar_ax,
                        orientation = 'horizontal')
        
        cb.ax.xaxis.set_tick_params(size=0)
        cb.set_label('Power Consumption in MW', size = 12)
        fig.text( 0.5,0.1, 'Day', ha='center', va= 'center', fontsize =14)
        fig.text( 0.02,0.5, 'Hour Commencing', ha='center', va= 'center',rotation = 'vertical', fontsize =14)
        
        fig.suptitle('Energy Consumption - ' + sector, fontsize = 20, y= 0.97)
        
    elif profile_type == 'PV_Rooftop' or profile_type == 'PV_Openfield' or profile_type == 'Wind':
        data = pd.DataFrame()
        region = ['North','East', 'Middle', 'Swest']
        for r in region:
            data['PV_Rooftop_'+ r] = data_dict[r].PV_feed_in_profile_rooftop
            data['PV_Openfield_'+ r] =  data_dict[r].PV_feed_in_profile_openfield
            data['Wind_'+ r] =  data_dict[r].Wind_feed_in_profile['Wind_feed_in'].values
        min_value = 0
        max_value = 1    
        data = data.reset_index(drop=True)
        fig,axes = plt.subplots(4,12, figsize = (19.1,10.5), sharey = True)
    #data['date'] = date_time_index
        fig.subplots_adjust(left = 0.055, right = 0.96, top = 0.895, hspace = 0.12, wspace = 0.07)
        fig.subplots_adjust(bottom=0.14)
        cbar_ax = fig.add_axes([0.3, 0.05, 0.4, 0.025])
        norm = mc.Normalize(min_value, max_value)
        #create the colorbar and set it horizontal
        if profile_type == 'PV_Rooftop' or profile_type == 'PV_Openfield':
            cmap = 'cividis'
        elif profile_type =='Wind':
            cmap = 'coolwarm'
        cb=fig.colorbar(ScalarMappable(norm = norm, cmap=cmap),
                        cax = cbar_ax,
                        orientation = 'horizontal')
        
        cb.ax.xaxis.set_tick_params(size=0)
        cb.set_label('Normalized energy production', size = 12)
        fig.text( 0.5,0.1, 'Day', ha='center', va= 'center', fontsize =14)
        fig.text( 0.02,0.5, 'Hour Commencing', ha='center', va= 'center',rotation = 'vertical', fontsize =14)
        
        plt.suptitle('Feed-in Profile - ' + profile_type, fontsize = 20, y= 0.97)
    
    def heat_maps_subplot(data,sector, month, year, ax, cmap='magma'):
        
        data['date'] = date_time_index
              
        subset = data[(data['date'].dt.year == year) & (data['date'].dt.month == month)]
        hour = subset['date'].dt.hour
        day = subset['date'].dt.day
        profile = subset[sector]
        profile = profile.values.reshape(24, len(day.unique()), order = 'F')
        
        xgrid = np.arange(day.max()+1) + 1
        ygrid= np.arange(25)
        
        ax.pcolormesh(xgrid, ygrid, profile, cmap=cmap, vmin = min_value, vmax = max_value)
        ax.set_ylim(24,0)            # Invert the vertical axis
        ax.yaxis.set_ticks([i for i in range(24)])
        ax.xaxis.set_ticks([10,20,30])
        ax.yaxis.set_tick_params(length=0)
        ax.xaxis.set_tick_params(length=0)
        ax.set_frame_on(False)   # Remove all spines
        if profile_type == 'PV_Rooftop' or profile_type == 'PV_Openfield' or profile_type == 'Wind':
            ax.yaxis.set_ticks([0,4,8,12,16,20,23])
            ax.xaxis.set_ticks([10,20,30])
       
    if profile_type == 'loadprofile':
        for j, month in enumerate(range(1,13)):
            heat_maps_subplot(data, sector, month, YEAR, axes[j])
            axes[j].set_title(month_title[j], fontsize = 14)
        plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation), sector + '_'+ profile_type + '_Heatmap.png')),dpi=800)
    
    elif profile_type == 'PV_Rooftop':
        sector = ['PV_Rooftop_North', 'PV_Rooftop_Middle', 'PV_Rooftop_East', 'PV_Rooftop_Swest']
        for i, data in enumerate([data['PV_Rooftop_North'].to_frame(),data['PV_Rooftop_Middle'].to_frame(),data['PV_Rooftop_East'].to_frame(),data['PV_Rooftop_Swest'].to_frame()]):
            for j, month in enumerate(range(1,13)):
                heat_maps_subplot(data, sector[i], month, YEAR, axes[i,j], cmap= 'cividis')
                axes[0,j].set_title(month_title[j], fontsize = 14)  
            axes[i,0].set_ylabel(region[i], fontsize = 14) 
        plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation), profile_type + '_Heatmap.png')),dpi=800)
        return min_value, max_value
            
    elif profile_type == 'PV_Openfield':
        sector = ['PV_Openfield_North', 'PV_Openfield_Middle', 'PV_Openfield_East', 'PV_Openfield_Swest']
        for i, data in enumerate([data['PV_Openfield_North'].to_frame(),data['PV_Openfield_Middle'].to_frame(),data['PV_Openfield_East'].to_frame(),data['PV_Openfield_Swest'].to_frame()]):
            for j, month in enumerate(range(1,13)):
                heat_maps_subplot(data, sector[i], month, YEAR, axes[i,j], cmap='cividis')
                axes[0,j].set_title(month_title[j], fontsize = 14) 
            axes[i,0].set_ylabel(region[i], fontsize = 14)
        plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation), profile_type + '_Heatmap.png')),dpi=800)
        return min_value, max_value
    
    elif profile_type == 'Wind':
        sector = ['Wind_North', 'Wind_Middle', 'Wind_East', 'Wind_Swest']
        for i, data in enumerate([data['Wind_North'].to_frame(),data['Wind_Middle'].to_frame(),data['Wind_East'].to_frame(),data['Wind_Swest'].to_frame()]):
            for j, month in enumerate(range(1,13)):
                heat_maps_subplot(data, sector[i], month, YEAR, axes[i,j], cmap= 'coolwarm')
                axes[0,j].set_title(month_title[j], fontsize = 14)
            axes[i,0].set_ylabel(region[i], fontsize = 14)
        plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation), profile_type + '_Heatmap.png')),dpi=800)
        return min_value, max_value
    
        