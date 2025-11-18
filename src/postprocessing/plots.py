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
from oemof import solph
from src.preprocessing.files import read_input_files
from src.postprocessing.utils_dump import prepare_two_day_data
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
from matplotlib import gridspec
import os
workdir = os.getcwd()


def heat_maps(data_dict,YEAR,permutation,scenario_num,profile_type,sector = None):
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
        plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation),scenario_num, sector + '_'+ profile_type + '_Heatmap.png')),dpi=800)
    
    elif profile_type == 'PV_Rooftop':
        sector = ['PV_Rooftop_North', 'PV_Rooftop_Middle', 'PV_Rooftop_East', 'PV_Rooftop_Swest']
        for i, data in enumerate([data['PV_Rooftop_North'].to_frame(),data['PV_Rooftop_Middle'].to_frame(),data['PV_Rooftop_East'].to_frame(),data['PV_Rooftop_Swest'].to_frame()]):
            for j, month in enumerate(range(1,13)):
                heat_maps_subplot(data, sector[i], month, YEAR, axes[i,j], cmap= 'cividis')
                axes[0,j].set_title(month_title[j], fontsize = 14)  
            axes[i,0].set_ylabel(region[i], fontsize = 14) 
        plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation),scenario_num, profile_type + '_Heatmap.png')),dpi=800)
        return min_value, max_value
            
    elif profile_type == 'PV_Openfield':
        sector = ['PV_Openfield_North', 'PV_Openfield_Middle', 'PV_Openfield_East', 'PV_Openfield_Swest']
        for i, data in enumerate([data['PV_Openfield_North'].to_frame(),data['PV_Openfield_Middle'].to_frame(),data['PV_Openfield_East'].to_frame(),data['PV_Openfield_Swest'].to_frame()]):
            for j, month in enumerate(range(1,13)):
                heat_maps_subplot(data, sector[i], month, YEAR, axes[i,j], cmap='cividis')
                axes[0,j].set_title(month_title[j], fontsize = 14) 
            axes[i,0].set_ylabel(region[i], fontsize = 14)
        plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation),scenario_num, profile_type + '_Heatmap.png')),dpi=800)
        return min_value, max_value
    
    elif profile_type == 'Wind':
        sector = ['Wind_North', 'Wind_Middle', 'Wind_East', 'Wind_Swest']
        for i, data in enumerate([data['Wind_North'].to_frame(),data['Wind_Middle'].to_frame(),data['Wind_East'].to_frame(),data['Wind_Swest'].to_frame()]):
            for j, month in enumerate(range(1,13)):
                heat_maps_subplot(data, sector[i], month, YEAR, axes[i,j], cmap= 'coolwarm')
                axes[0,j].set_title(month_title[j], fontsize = 14)
            axes[i,0].set_ylabel(region[i], fontsize = 14)
        plt.savefig(os.path.abspath(os.path.join(workdir, 'figures', str(permutation),scenario_num, profile_type + '_Heatmap.png')),dpi=800)
        return min_value, max_value
    
def grid_energy_map(results, permutation, model_name, scenario_num):
    
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name=None)
    b_el_n = solph.views.node(results, 'Electricity_n')
    b_el_s = solph.views.node(results, 'Electricity_s')
    b_el_e = solph.views.node(results, 'Electricity_e')
    b_el_m = solph.views.node(results, 'Electricity_m')
    hs_north_flow = b_el_n['sequences'][('HS<->North', 'Electricity_n'), 'flow']/1000 #in GWh 
    north_hs_flow = b_el_n['sequences'][('Electricity_n', 'HS<->North'), 'flow']/1000 
    hs_middle_flow = b_el_m['sequences'][('HS<->Middle', 'Electricity_m'), 'flow']/1000 
    middle_hs_flow = b_el_m['sequences'][('Electricity_m', 'HS<->Middle'), 'flow']/1000 
    hs_east_flow = b_el_e['sequences'][('HS<->East', 'Electricity_e'), 'flow']/1000 
    east_hs_flow = b_el_e['sequences'][('Electricity_e', 'HS<->East'), 'flow']/1000 
    hs_swest_flow = b_el_s['sequences'][('HS<->Swest', 'Electricity_s'), 'flow']/1000 
    swest_hs_flow = b_el_s['sequences'][('Electricity_s', 'HS<->Swest'), 'flow']/1000 
    middle_north_flow = b_el_m['sequences'][('Electricity_m', 'North<->Middle'), 'flow']/1000 
    north_middle_flow = b_el_n['sequences'][('Electricity_n', 'North<->Middle'), 'flow']/1000 
    middle_east_flow = b_el_m['sequences'][('Electricity_m', 'East<->Middle'), 'flow']/1000 
    east_middle_flow = b_el_e['sequences'][('Electricity_e', 'East<->Middle'), 'flow']/1000 
    middle_swest_flow = b_el_m['sequences'][('Electricity_m', 'Middle<->Swest'), 'flow']/1000 
    swest_middle_flow = b_el_s['sequences'][('Electricity_s', 'Middle<->Swest'), 'flow']/1000 
    
    all_flows = [
    hs_north_flow, north_hs_flow, hs_middle_flow, middle_hs_flow,
    hs_east_flow, east_hs_flow, hs_swest_flow, swest_hs_flow,
    middle_north_flow, north_middle_flow, middle_east_flow, east_middle_flow,
    middle_swest_flow, swest_middle_flow
]

    y_min = min(flow.min() for flow in all_flows) * 1.1  # 10% padding
    y_max = max(flow.max() for flow in all_flows) * 1.1  # 10% padding
    
    time_index = hs_north_flow.index
    fig = plt.figure(figsize=(22, 12)) 
    gs = gridspec.GridSpec(3, 3, width_ratios=[2, 1, 1]) 
    
    ##### Grid map with arrows ######## 
    
    ax0 = fig.add_subplot(gs[:2, 0]) 
    img_path = os.path.abspath(os.path.join(os.getcwd(), 'figures', 'Thuringia_karte_mit_Landkreisen_dull.png')) 
    img = mpimg.imread(img_path) 
    ax0.imshow(img) 
    ax0.axis('off') 
    x_1 = [120,130,400,410,250,260,690,700] 
    y_1 = [440,500,340,400,100,160,440,500] 
    z_1 = [60,-60,60,-60,60,-60,60,-60] 
    #Coordinates for green arrows 
    x_2 = [280,255,350,385,510,555] 
    y_2 = [460,510,230,275,420,465] 
    z_2 = [50,-50,50,-50,50,-50] 
    w_2 = [-35,35,30,-30,40,-40] 
    for x, y, z in zip(x_1, y_1, z_1): 
        ax0.arrow(x, y, 0, z, head_width=22, width=8, length_includes_head=True, shape='right', color='red') 
    
    for x, y, w, z in zip(x_2, y_2, w_2, z_2): 
        ax0.arrow(x, y, w, z, head_width=22, width=8, length_includes_head=True, shape='right', color='green') 
    
    ax0.text(200, 140, str(round(hs_north_flow.sum())), fontsize = 12) 
    ax0.text(275,120, str(round(north_hs_flow.sum())), fontsize = 12) 
    #Netzbezug: Middle 
    ax0.text(340,385, str(round(hs_middle_flow.sum())), fontsize = 12) 
    ax0.text(425,360, str(round(middle_hs_flow.sum())), fontsize = 12) 
    #Netzbezug: East 
    ax0.text(630,485, str(round(hs_east_flow.sum())), fontsize = 12) 
    ax0.text(720,465, str(round(east_hs_flow.sum())), fontsize = 12) 
    #Netzbezug: Swest 
    ax0.text(70,485, str(round(hs_swest_flow.sum())), fontsize = 12) 
    ax0.text(140,465, str(round(swest_hs_flow.sum())), fontsize = 12) 
    #Netzaustausch: Middle <-> Swest 
    ax0.text(200,500, str(round(middle_swest_flow.sum())), fontsize = 12) 
    ax0.text(300,475, str(round(swest_middle_flow.sum())), fontsize = 12) 
    #Netzaustausch: Middle <-> North 
    ax0.text(370,230, str(round(middle_north_flow.sum())), fontsize = 12) 
    ax0.text(320,280, str(round(north_middle_flow.sum())), fontsize = 12) 
    #Netzaustausch: Middle <-> East 
    ax0.text(500,475, str(round(middle_east_flow.sum())), fontsize = 12) 
    ax0.text(550,425, str(round(east_middle_flow.sum())), fontsize = 12) 
    ax0.text(720, 600, '*The values are in GWh', fontsize=12) 
    red_patch = mpatches.Patch(color='red', label='Transformer Hös<->HS') 
    green_patch = mpatches.Patch(color='green', label='Connection between regions') 
    ax0.legend(handles=[red_patch, green_patch], loc='lower right') 
    
    ax1 = fig.add_subplot(gs[0, 1])  # North
    ax2 = fig.add_subplot(gs[0, 2], sharex=ax1, sharey=ax1)  # Middle
    ax3 = fig.add_subplot(gs[1, 1], sharex=ax1, sharey=ax1)  # Swest
    ax4 = fig.add_subplot(gs[1, 2], sharex=ax1, sharey=ax1)  # East
    ax5 = fig.add_subplot(gs[2, 1], sharex=ax1, sharey=ax1)  # North <-> Middle
    ax6 = fig.add_subplot(gs[2, 2], sharex=ax1, sharey=ax1)  # East <-> Middle
    ax7 = fig.add_subplot(gs[2, 0], sharex=ax1, sharey=ax1)  # Middle <-> Swest
    
    line_axes = [ax1, ax2, ax3, ax4, ax5, ax6, ax7]
    
    titles = [
        'North Flows (MWh)',
        'Middle Flows (MWh)', 
        'Swest Flows (MWh)',
        'East Flows (MWh)',
        'North <-> Middle (MWh)',
        'East <-> Middle (MWh)',
        'Middle <-> Swest (MWh)'
    ]
    
    # Data for each subplot
    plot_data = [
        (north_hs_flow.values*(-1), hs_north_flow.values, 'North -> HS', 'HS -> North'),
        (middle_hs_flow.values*(-1), hs_middle_flow.values, 'Middle -> HS', 'HS -> Middle'),
        (swest_hs_flow.values*(-1), hs_swest_flow.values, 'Swest -> HS', 'HS -> Swest'),
        (east_hs_flow.values*(-1), hs_east_flow.values, 'East -> HS', 'HS -> East'),
        (north_middle_flow.values*(-1), middle_north_flow.values, 'North -> Middle', 'Middle -> North'),
        (east_middle_flow.values*(-1), middle_east_flow.values, 'East -> Middle', 'Middle -> East'),
        (middle_swest_flow.values*(-1), swest_middle_flow.values, 'Middle -> Swest', 'Swest -> Middle')
    ]
    
    for ax, (data1, data2, label1, label2), title in zip(line_axes, plot_data, titles):
        ax.plot(time_index, data1, label=label1, color='blue')
        ax.plot(time_index, data2, label=label2, color='orange')
        ax.set_title(title)
        ax.legend(fontsize=12)
        ax.grid(True)
        ax.tick_params(axis='x', labelrotation=45, labelsize=12)
    
    # Set initial limits for all shared axes
    ax1.set_xlim(time_index[0], time_index[-1])
    ax1.set_ylim(y_max*(-1), y_max)
    
    # North region flow plot 
    # ax1 = fig.add_subplot(gs[0, 1]) 
    # ax1.plot(time_index, north_hs_flow.values*(-1), label='North -> HS', color='blue') 
    # ax1.plot(time_index, hs_north_flow.values, label='HS -> North', color='orange') 
    # ax1.set_title('North Flows (MWh)') 
    # ax1.legend(fontsize = 12) 
    # ax1.set_xlim(time_index[0], time_index[-1])  # Fixed x-axis
    # ax1.set_ylim(y_max*(-1), y_max)
    # ax1.tick_params(axis='x', labelrotation=45, labelsize = 12) 
    # ax1.grid(True) 
    
    # # Middle region flow plot 
    # ax2 = fig.add_subplot(gs[0, 2]) 
    # ax2.plot(time_index, middle_hs_flow.values*(-1), label='Middle -> HS', color='blue') 
    # ax2.plot(time_index, hs_middle_flow.values, label='HS -> Middle', color='orange') 
    # ax2.set_title('Middle Flows (MWh)') 
    # ax2.legend(fontsize = 12)
    # ax2.set_xlim(time_index[0], time_index[-1])  # Fixed x-axis
    # ax2.set_ylim(y_max*(-1), y_max)
    # ax2.tick_params(axis='x', labelrotation=45,labelsize = 12) 
    # ax2.grid(True) 
    
    # #Swest 
    # ax3 = fig.add_subplot(gs[1, 1]) 
    # ax3.plot(time_index, swest_hs_flow.values*(-1), label='Swest -> HS', color='blue') 
    # ax3.plot(time_index, hs_swest_flow.values, label='HS -> Swest', color='orange') 
    # ax3.set_title('Swest Flows (MWh)') 
    # ax3.legend(fontsize = 12) 
    # ax3.set_xlim(time_index[0], time_index[-1])  # Fixed x-axis
    # ax3.set_ylim(y_max*(-1), y_max)
    # ax3.tick_params(axis='x', labelrotation=45,labelsize = 12) 
    # ax3.grid(True) 
    
    # #East 
    # ax4 = fig.add_subplot(gs[1, 2]) 
    # ax4.plot(time_index, east_hs_flow.values*(-1), label='East -> HS', color='blue') 
    # ax4.plot(time_index, hs_east_flow.values, label='HS -> East', color='orange') 
    # ax4.set_title('East Flows (MWh)') 
    # ax4.legend(fontsize = 12) 
    # ax4.set_xlim(time_index[0], time_index[-1])  # Fixed x-axis
    # ax4.set_ylim(y_max*(-1), y_max)
    # ax4.tick_params(axis='x', labelrotation=45,labelsize = 12) 
    # ax4.grid(True) 
    
    # #Leitung north- middle 
    # ax5 = fig.add_subplot(gs[2, 1]) 
    # ax5.plot(time_index, north_middle_flow.values*(-1), label='North -> Middle', color='blue') 
    # ax5.plot(time_index, middle_north_flow.values, label='Middle -> North', color='orange') 
    # ax5.set_title('North <-> Middle (MWh)') 
    # ax5.legend(fontsize = 12) 
    # ax5.set_xlim(time_index[0], time_index[-1])  # Fixed x-axis
    # ax5.set_ylim(y_max*(-1), y_max)
    # ax5.tick_params(axis='x', labelrotation=45,labelsize = 12) 
    # ax5.grid(True) 
    
    # ax6 = fig.add_subplot(gs[2, 2]) 
    # ax6.plot(time_index, east_middle_flow.values*(-1), label='East -> Middle', color='blue') 
    # ax6.plot(time_index, middle_east_flow.values, label='Middle -> East', color='orange') 
    # ax6.set_title('East <-> Middle (MWh)') 
    # ax6.legend(fontsize = 12) 
    # ax6.set_xlim(time_index[0], time_index[-1])  # Fixed x-axis
    # ax6.set_ylim(y_max*(-1), y_max)
    # ax6.tick_params(axis='x', labelrotation=45,labelsize = 12) 
    # ax6.grid(True) 
    
    # ax7 = fig.add_subplot(gs[2,0]) 
    # ax7.plot(time_index, middle_swest_flow.values*(-1), label='Middle -> Swest', color='blue') 
    # ax7.plot(time_index, swest_middle_flow.values, label='Swest -> Middle', color='orange') 
    # ax7.set_title('Middle <-> Swest (MWh)') 
    # ax7.legend(fontsize = 12) 
    # ax7.set_xlim(time_index[0], time_index[-1])  
    # ax7.set_ylim(y_max*(-1), y_max)
    # ax7.tick_params(axis='x', labelrotation=45,labelsize = 12) 
    # ax7.grid(True) 
    
    plt.setp(ax1.get_xticklabels(), visible=False)
    plt.setp(ax2.get_xticklabels(), visible=False)
    plt.setp(ax3.get_xticklabels(), visible=False)
    plt.setp(ax4.get_xticklabels(), visible=False)
    
    # Table for Overview of maximum value and predefined value 
    flows_sum = { 
        'North <-> HS' :(north_hs_flow + hs_north_flow), 
        'Middle <-> HS': (middle_hs_flow + hs_middle_flow), 
        'East <-> HS': (east_hs_flow + hs_east_flow), 
        'Swest <-> HS':(swest_hs_flow + hs_swest_flow), 
        'North <-> Middle':(north_middle_flow + middle_north_flow), 
        'East <-> Middle':(east_middle_flow + middle_east_flow), 
        'Swest <-> Middle':(swest_middle_flow + middle_swest_flow)} 
    
    flow_max = { region: flows_sum[region].max() for region in flows_sum} 
    max_def = { 
        'North <-> HS' :scalars['Electricity_grid']['electricity']['max_power_north'], 
        'Middle <-> HS': scalars['Electricity_grid']['electricity']['max_power_middle'], 
        'East <-> HS': scalars['Electricity_grid']['electricity']['max_power_east'], 
        'Swest <-> HS':scalars['Electricity_grid']['electricity']['max_power_swest'], 
        'North <-> Middle':scalars['Electricity_grid']['electricity']['connection_north_middle'], 
        'East <-> Middle':scalars['Electricity_grid']['electricity']['connection_east_middle'], 
        'Swest <-> Middle':scalars['Electricity_grid']['electricity']['connection_middle_swest'] 
        } 
    names =['North <-> HS','Middle <-> HS','East <-> HS','Swest <-> HS','North <-> Middle','East <-> Middle','Swest <-> Middle']
    
    table_text = "                 Limit (MW) | Max (MW)\n"
    table_text += "-" * 25 + "\n"
    for reg in names:
        limit = f"{max_def[reg]:.1f}"
        maximum = f"{flow_max[reg]*1000:.1f}"
        table_text += f"{reg:<20} {limit:>6}   {maximum:>6}\n"
    
    ax0.text(580,0, table_text, fontsize =12, family = 'monospace', verticalalignment = 'top')
        
    plt.tight_layout() 
    plt.savefig(os.path.join(os.getcwd(), 'figures', permutation, model_name + "_" + scenario_num + '_grid_and_subplots.png'), dpi=500) 
    plt.show()      

def create_consistent_color_mapping(summarized_bus_sequences, summarized_component_sequences):
    """
    Create a consistent color mapping for all technologies across all scenarios
    """
    all_technologies = set()
    
    for scenario in summarized_bus_sequences.keys():
        # Technologies in bus sequences (components receiving from buses)
        for bus, components in summarized_bus_sequences[scenario].items():
            all_technologies.update(components.keys())
        
        # Technologies in component sequences (components sending to buses)
        for component, buses in summarized_component_sequences[scenario].items():
            all_technologies.add(component)
    technologies_sorted = sorted(list(all_technologies))
    colors = plt.cm.tab20(np.linspace(0, 1, len(technologies_sorted)))
    
    color_mapping = dict(zip(technologies_sorted, colors))
    
    print(f"Created color mapping for {len(technologies_sorted)} technologies:")
    for tech, color in list(color_mapping.items())[:10]: 
        print(f"  {tech}: {color}")
    if len(technologies_sorted) > 10:
        print(f"  ... and {len(technologies_sorted) - 10} more")
    
    return color_mapping
    
def plot_bus_energy_flows(summarized_bus_sequences, summarized_component_sequences, scenarios=None, days=2):
    """
    Plot line plots for bus energy flows as subplots
    
    Parameters:
    -----------
    summarized_bus_sequences : dict
        Summarized sequences in format: scenario -> bus -> component -> sequence
    summarized_component_sequences : dict
        Summarized sequences in format: scenario -> component -> bus -> sequence  
    scenarios : list, optional
        Specific scenarios to plot (default: all)
    days : int
        Number of days to sum for plotting
    """
    
    if scenarios is None:
        scenarios = list(summarized_bus_sequences.keys())
    
    # Prepare two-day data
    print("Preparing two-day data...")
    bus_two_day = prepare_two_day_data(summarized_bus_sequences, days)
    component_two_day = prepare_two_day_data(summarized_component_sequences, days)
    
    color_mapping = create_consistent_color_mapping(summarized_bus_sequences, summarized_component_sequences)
    for scenario in scenarios:
        if scenario not in bus_two_day or scenario not in component_two_day:
            print(f"Scenario {scenario} not found in data")
            continue
            
        print(f"Plotting scenario: {scenario}")
        
        all_buses = set()
        all_buses.update(bus_two_day[scenario].keys())
        for component, bus_data in component_two_day[scenario].items():
            all_buses.update(bus_data.keys())
        
        for bus in sorted(all_buses):
            # Create figure with subplots that share x-axis
            fig, axes = plt.subplots(2, 1, figsize=(16, 12), sharex=True)
            ax1, ax2 = axes
            
            # Plot TO Bus
            to_bus_data = []
            to_bus_labels = []
            to_bus_colors = []
            
            for component, bus_data in component_two_day[scenario].items():
                if bus in bus_data:
                    to_bus_data.append(bus_data[bus])
                    to_bus_labels.append(component)
                    to_bus_colors.append(color_mapping.get(component, 'gray'))
            
            if to_bus_data:
                to_bus_array = np.array(to_bus_data)
                time_periods = range(len(to_bus_array[0]))
                ax1.stackplot(time_periods, to_bus_array, labels=to_bus_labels, 
                             colors=to_bus_colors, alpha=0.85)
                total_to_bus = np.sum(to_bus_array, axis=0)
                ax1.plot(time_periods, total_to_bus, 'k-', linewidth=2.5, alpha=0.9, label='Total')
                
                ax1.set_title(f'Energy TO Bus {bus} ({scenario})', fontsize=14, fontweight='bold')
                ax1.set_ylabel('Energy (MWh)', fontsize=12)
                ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax1.grid(True, alpha=0.3)
                ax1.set_ylim(bottom=0)
                ax1.set_xlim(0,days-1)
            
            # Plot FROM Bus
            from_bus_data = []
            from_bus_labels = []
            from_bus_colors = []
            
            if bus in bus_two_day[scenario]:
                for component, two_day_values in bus_two_day[scenario][bus].items():
                    from_bus_data.append(two_day_values)
                    from_bus_labels.append(component)
                    from_bus_colors.append(color_mapping.get(component, 'gray'))
            
            if from_bus_data:
                from_bus_array = np.array(from_bus_data)
                time_periods = range(len(from_bus_array[0]))
                ax2.stackplot(time_periods, from_bus_array, labels=from_bus_labels, 
                             colors=from_bus_colors, alpha=0.85)
                total_from_bus = np.sum(from_bus_array, axis=0)
                ax2.plot(time_periods, total_from_bus, 'k-', linewidth=2.5, alpha=0.9, label='Total')
                
                ax2.set_title(f'Energy FROM Bus {bus} ({scenario})', fontsize=14, fontweight='bold')
                ax2.set_ylabel('Energy (MWh)', fontsize=12)
                ax2.set_xlabel('2-Day Periods', fontsize=12)
                ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                ax2.grid(True, alpha=0.3)
                ax2.set_ylim(bottom=0)
                ax2.set_xlim(0,days-1)
            
            plt.tight_layout()
            plt.show()
