# -*- coding: utf-8 -*-
"""
Created on Thu Jan 15 14:16:54 2026

@author: rbala

help funtion for plots
"""
from oemof import solph
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from matplotlib.lines import Line2D
import os
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from openpyxl import load_workbook
workdir = os.getcwd()

def interpret_results(results):          
    bus_sequences = {}
    bus_scalars = {}
    component_sequences = {}
    component_scalars = {}
    component_bus_mapping = {}
    
    # Iterate through results to classify flows for Bus, Source, Converter, etc.
    for key, value in results.items():
        component_name = str(key[1].label) if key[1] else "None"  # Extract component name (e.g., Source, Converter, etc.)
        
        if isinstance(key[0], solph.Bus):
            bus_name = str(key[0].label)  # Extract bus name
            
            if component_name != "None":
                component_bus_mapping[component_name] = bus_name
            
            # Extract sequences for Bus
            if isinstance(value, dict) and "sequences" in value:
                if bus_name not in bus_sequences:
                    bus_sequences[bus_name] = {}
                bus_sequences[bus_name][component_name] = value["sequences"]
    
            # Extract scalar values for Bus
            elif isinstance(value, (int, float)):
                if bus_name not in bus_scalars:
                    bus_scalars[bus_name] = {}
                bus_scalars[bus_name][component_name] = value["scalars"]["total"]
    
        
        elif isinstance(key[0], (solph.components.Source, solph.components.Link, solph.components.Converter, solph.components.Sink, solph.components.GenericStorage)):
            component_name = str(key[0].label)  # Extract component name
            component_obj = key[0]
            connected_bus = "None"
            
            if hasattr(component_obj, 'outputs'):
                # Sources, Converters - connected via outputs
                output_buses = list(component_obj.outputs.keys())
                if output_buses:
                    connected_bus = str(output_buses[0].label)
            
            elif hasattr(component_obj, 'inputs'):
                # Sinks - connected via inputs  
                input_buses = list(component_obj.inputs.keys())
                if input_buses:
                    connected_bus = str(input_buses[0].label)
            
            component_bus_mapping[component_name] = connected_bus
            
            # Extract sequences for Component
            if isinstance(value, dict):
                if "scalars" in value:
                    total_value = value["scalars"].get("total", 0)
            
                    if component_name not in component_scalars:
                        component_scalars[component_name] = {}
            
                    component_scalars[component_name][str(key[1].label) if key[1] else "None"] = total_value
            
                if "sequences" in value:
                    sequence_data = value["sequences"]
            
                    # You can choose to store sequences in a separate dictionary or process as needed
                    if component_name not in component_sequences:
                        component_sequences[component_name] = {}
            
                    component_sequences[component_name][str(key[1].label) if key[1] else "None"] = sequence_data

    return bus_sequences, bus_scalars, component_sequences, component_scalars, component_bus_mapping

def create_combined_bus_component_dfs(bus_sequences, component_sequences, energysystem):
    """Create combined DataFrames showing flows to/from each bus"""
    combined_dfs = {}
    
    for bus_name, components in bus_sequences.items():
        combined_data = {}
        
        # Add flows FROM bus TO components (outputs)
        for component_name, sequence_data in components.items():
            flow_values = extract_flow_values(sequence_data)
            if flow_values is not None:
                # Output from bus to component
                combined_data[f"OUT: {component_name}"] = flow_values
        
        # Add flows FROM components TO bus (inputs)
        for component_name, targets in component_sequences.items():
            for target_name, sequence_data in targets.items():
                if str(target_name) == bus_name:
                    flow_values = extract_flow_values(sequence_data)
                    if flow_values is not None:
                        # Input from component to bus
                        combined_data[f"IN: {component_name}"] = flow_values
        
        if combined_data:
            time_index = energysystem.timeindex
            min_length = min(len(arr) for arr in combined_data.values())
            
            if min_length != len(time_index):
                time_index = time_index[:min_length]

            for key in combined_data.keys():
                combined_data[key] = combined_data[key][:min_length]
            
            combined_dfs[bus_name] = pd.DataFrame(combined_data, index=time_index[:min_length])
    
    return combined_dfs

def extract_flow_values(sequence_data):
    """Helper function to extract flow values from sequence data"""
    if hasattr(sequence_data, 'values'):
        flow_values = sequence_data.values
    elif isinstance(sequence_data, dict):
        flow_data = sequence_data.get('flow', None)
        if flow_data is not None and hasattr(flow_data, 'values'):
            flow_values = flow_data.values
        else:
            return None
    else:
        return None
    
    # Ensure we have a 1D array
    if hasattr(flow_values, 'shape'):
        if len(flow_values.shape) == 1:
            return flow_values
        elif len(flow_values.shape) == 2:
            return flow_values[:, 0]
        else:
            try:
                return flow_values.flatten()
            except:
                return None
    return None


def categorize_for_sequence(category_list, combined_df):
    categorized_dict = {}
    
    for bus_name, df in combined_df.items():
        df_cat = df.copy()
        
        # Helper function to categorize columns
        def categorize_columns(prefix):
            groups = {}
            prefix_cols = [col for col in df_cat.columns if col.startswith(prefix)]
            
            for col in prefix_cols:
                col_upper = col.upper()
                cat_found = None
                
                for category, patterns in category_list.items():
                    for pattern in patterns:
                        if pattern.upper() in col_upper:
                            cat_found = category
                            break
                    if cat_found:
                        break
                
                if cat_found:
                    group_name = f'{prefix}{cat_found}'
                    groups.setdefault(group_name, []).append(col)
                else:
                    groups[col] = [col]
            
            return groups
        
        # Process IN and OUT columns
        in_groups = categorize_columns('IN: ')
        out_groups = categorize_columns('OUT: ')
        
        # Aggregate grouped columns
        def aggregate_groups(groups_dict):
            for group_name, cols in groups_dict.items():
                if len(cols) > 1:
                    df_cat[group_name] = df_cat[cols].sum(axis=1)
                    df_cat.drop(columns=cols, inplace=True)
                elif group_name != cols[0]:
                    df_cat.rename(columns={cols[0]: group_name}, inplace=True)
        
        aggregate_groups(in_groups)
        aggregate_groups(out_groups)
        
        # Add to categorized dictionary
        categorized_dict[bus_name] = df_cat
    
    return categorized_dict

def rename_index_with_category(df, category_list, case_sensitive=False):
    """
    Rename DataFrame index using category_list and sum values for components
    that map to the same category.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with component names as index
    category_list : dict
        Dictionary mapping category names to list of component patterns
    case_sensitive : bool
        Whether matching should be case-sensitive (default: False)
    
    Returns:
    --------
    pandas.DataFrame: DataFrame with renamed index (categories as index)
    """
    
    df_renamed = df.copy()
    
    pattern_to_category = {}
    for category, patterns in category_list.items():
        for pattern in patterns:
            if case_sensitive:
                pattern_to_category[pattern] = category
            else:
                pattern_to_category[pattern.lower()] = category
    
    def find_category(component_name):
        if case_sensitive:
            search_name = component_name
        else:
            search_name = component_name.lower()
        
        for pattern, category in pattern_to_category.items():
            if pattern == search_name:
                return category
        
        for pattern, category in pattern_to_category.items():
            if pattern in search_name:
                return category
        
        return component_name
    
    index_mapping = {}
    for idx in df_renamed.index:
        category = find_category(str(idx))
        index_mapping[idx] = category

    df_renamed['_category'] = df_renamed.index.map(index_mapping)
    numeric_cols = df_renamed.select_dtypes(include=[np.number]).columns.tolist()
    
    # If we have MultiIndex or specific column structure
    if '_category' in df_renamed.columns:
        df_grouped = df_renamed.groupby('_category')[numeric_cols].sum()
        
        df_renamed = df_renamed.drop(columns=['_category'])
    else:
        df_grouped = df_renamed
    
    return df_grouped

def create_barplot_dict(df_original, kategorien_dict):
    """Erstellt ein Dictionary mit DataFrames für jede Kategorie"""
    
    kategorie_dict = {}
    
    for kategorie, komponenten_liste in kategorien_dict.items():
        komponenten_in_kategorie = [k for k in komponenten_liste if k in df_original.index]
        
        if komponenten_in_kategorie:
            kategorie_dict[kategorie] = df_original.loc[komponenten_in_kategorie]
    
    zugeordnete_komponenten = []
    for komps in kategorie_dict.values():
        zugeordnete_komponenten.extend(list(komps.index))
    
    sonstige_komponenten = [k for k in df_original.index if k not in zugeordnete_komponenten]
    
    if sonstige_komponenten:
        kategorie_dict['Sonstige'] = df_original.loc[sonstige_komponenten]
    
    return kategorie_dict

def scalars_bar_plot(bar_plot_dict, Category_color_mapping, Technology_color_mapping, fig_title = None,
                     fontsize = 14, figsize = (14,7), figure_bg_color = '#159A3433',axes_bg_color='#159A3400'):
    
    years = bar_plot_dict[next(iter(bar_plot_dict))].columns.astype(int)
    x = np.arange(len(years))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(figure_bg_color)
    ax.set_facecolor(axes_bg_color)
    # LEFT BAR
    bottom_cat = np.zeros(len(years))
    total_per_year = np.zeros(len(years))
    cat_handles = {}
    # first compute totals
    for df in bar_plot_dict.values():
        total_per_year += df.sum(axis=0).values
    
    for cat, df in bar_plot_dict.items():
        values = df.sum(axis=0).values
        bars = ax.bar(x - width/2, values, width,
                      bottom=bottom_cat,
                      label=cat,
                      color=Category_color_mapping.get(cat, '#A9A9A9'))
        
        cat_handles[cat] = bars[0]
    
        # percentage annotations
        for i, v in enumerate(values):
            if v > 0:
                perc = v / total_per_year[i] * 100
                y = bottom_cat[i] + v / 2
                ax.annotate(f"{perc:.0f}%",
                            xy=(x[i] - width/2, y),
                            xytext=(x[i] - width*1, y),
                            arrowprops=dict(arrowstyle="-", lw=0.8),
                            ha="right", va="center", fontsize=fontsize)
    
        bottom_cat += values
    
    # RIGHT BAR
    bottom_tech = np.zeros(len(years))
    tech_handles = {}
    tech_totals = np.zeros(len(years))
    
    for cat, df in bar_plot_dict.items():
        for tech in df.index:
            tech_key = tech.upper().replace("Ä","AE").replace("Ö","OE").replace("Ü","UE")
            color = Technology_color_mapping.get(tech_key, Technology_color_mapping['DEFAULT'])
            values = df.loc[tech].values
            bars = ax.bar(x + width/2, values, width,
                           bottom=bottom_tech,
                           color=color,
                           label=tech)
            bottom_tech += values
            tech_totals += values
            tech_handles[tech] = bars[0]
    
    for i, total in enumerate(tech_totals):
        ax.text(x[i], total * 1.01, f"{total:.0f}"+" MW",
                ha="center", va="bottom", fontsize=fontsize, fontweight="bold")
    

    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_ylabel("Leistung in MW", fontsize =fontsize)
    ax.set_xlabel("Simulationsjahr", fontsize =fontsize)
    ax.set_title(fig_title, fontsize = fontsize, fontweight = 'bold')
    ax.set_ylim(0, max(tech_totals)*1.1)
    ax.tick_params(axis='y', labelsize=fontsize-2)
    ax.tick_params(axis='x', labelsize=fontsize-2)
                         
    combined_handles = []
    combined_labels = []
    
    combined_handles.append(Line2D([0], [0], color='none'))
    combined_labels.append("Kategorien (linke Balken)")
    
    for name, handle in reversed(list(cat_handles.items())):
        combined_handles.append(handle)
        combined_labels.append(name)
    
    combined_handles.append(Line2D([0], [0], color='none'))
    combined_labels.append("")
    
    combined_handles.append(Line2D([0], [0], color='none'))
    combined_labels.append("Technologien (rechte Balken)")
    
    for name, handle in reversed(list(tech_handles.items())):
        combined_handles.append(handle)
        combined_labels.append(name)
    
    legend = ax.legend(combined_handles, combined_labels,
                       bbox_to_anchor=(1.02, 1),
                       loc="upper left",
                       frameon=False,
                       fontsize=fontsize)
    
    for text in legend.get_texts():
        if text.get_text() in ["Kategorien (linke Balken)", "Technologien (rechte Balken)"]:
            text.set_weight("bold")
    
    plt.tight_layout()#rect = (0.072,0.088,0.711,0.957))
                             
    plt.show()

def plot_bus_flows(combined_dfs, bus_name, inflow_plot_title, outflow_plot_title, COLOR_MAPPING, 
                   start_date=None, end_date=None, figsize=(14, 10), title_fontsize=14, 
                   label_fontsize=10, figure_bg_color='#159A3433', axes_bg_color='#159A3400',
                   sort_by_flh=True, capacity_dict=None, labels_with_info = True):
    def calculate_full_load_hours(column_name, component_type="IN"):
        """
        Calculate full load hours for a component using the FULL YEAR data
        
        component_name: Name without IN: or OUT: prefix
        component_type: "IN" or "OUT" to determine which dataset to use
        """
        # Get the full year data (not filtered)
        if is_electricity_bus:
            if component_type == "IN":
                full_df = combined_dfs.get('ElectricityIn', pd.DataFrame())
            else:
                full_df = combined_dfs.get('ElectricityOut', pd.DataFrame())
        else:
            full_df = combined_dfs.get(bus_name, pd.DataFrame())
        
        if full_df.empty or column_name not in full_df.columns:
            return 0
        
        if col == 'OUT: Grid Loss':
            component_series = ((combined_dfs.get('ElectricityIn', pd.DataFrame()))['OUT: Netzverluste']
                                - (combined_dfs.get('ElectricityOut', pd.DataFrame()))['IN: Netzverluste'])
        component_series = full_df[column_name]
        
        component_name = column_name[4:] if component_type == "IN" else column_name[5:]

        # Get capacity if available
        capacity = None
        if capacity_dict:
            for key in capacity_dict:
                if key in component_name:
                    capacity = capacity_dict[key]
                    break
        
        if capacity is None:
            capacity = component_series.max()
        
        if capacity == 0:
            return 0
        
        total_energy = component_series.sum()
        flh = total_energy / capacity
        
        return flh
    
    is_electricity_bus = bus_name.startswith('Electricity')
    if is_electricity_bus:
        electricity_in_bus = 'ElectricityIn' if 'ElectricityIn' in combined_dfs else None
        electricity_out_bus = 'ElectricityOut' if 'ElectricityOut' in combined_dfs else None
        if not electricity_in_bus or not electricity_out_bus:
            print(f"Required buses not found. Need both 'ElectricityIn' and 'ElectricityOut'")
            print(f"Available buses: {list(combined_dfs.keys())}")
            return
        
        df_in = combined_dfs[electricity_in_bus].copy()
        df_out = combined_dfs[electricity_out_bus].copy()
        
        if start_date or end_date:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            
            if start_date and not end_date:
                end_date = df_in.index[-1]
            elif end_date and not start_date:
                start_date = df_in.index[0]
            
            if end_date:
                end_date = end_date + pd.Timedelta(days=1)
            
            mask_in = (df_in.index >= start_date) & (df_in.index < end_date)
            mask_out = (df_out.index >= start_date) & (df_out.index < end_date)
            
            df_in = df_in[mask_in]
            df_out= df_out[mask_out] 
            
            common_index = df_in.index.intersection(df_out.index)
            if len(common_index) == 0:
                print("No overlapping time periods between ElectricityIn and ElectricityOut buses")
                return
            
            df_in = df_in.loc[common_index]
            df_out = df_out.loc[common_index]
            
            if df_in.empty or df_out.empty:
                print(f"No data available for Electricity buses in the specified date range")
                return
            
            # Get IN and OUT columns
            in_columns = [col for col in df_in.columns if col.startswith('IN:')]
            out_columns = [col for col in df_out.columns if col.startswith('OUT:')]
            
            if not in_columns:
                print(f"No IN flows found for {electricity_in_bus}")
                return
            if not out_columns:
                print(f"No OUT flows found for {electricity_out_bus}")
                return
    else: 
        if bus_name not in combined_dfs:
            print(f"Bus '{bus_name}' not found in combined DataFrames")
            return
        df = combined_dfs[bus_name].copy()
        
        # Filter by date range if specified
        if start_date or end_date:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            
            if start_date and not end_date:
                end_date = df.index[-1]
            elif end_date and not start_date:
                start_date = df.index[0]
            
            if end_date:
                end_date = end_date + pd.Timedelta(days=1)
            
            mask = (df.index >= start_date) & (df.index < end_date)
            df = df[mask]
        
        if df.empty:
            print(f"No data available for bus '{bus_name}' in the specified date range")
            return
        
        # Separate IN and OUT flows
        in_columns = [col for col in df.columns if col.startswith('IN:')]
        out_columns = [col for col in df.columns if col.startswith('OUT:')]
        
        if not in_columns and not out_columns:
            print(f"No IN or OUT flows found for bus '{bus_name}'")
            return
        
        df_in = df[in_columns] if in_columns else pd.DataFrame()
        df_out = df[out_columns] if out_columns else pd.DataFrame()
        
    # Create subplots
    fig, axes = plt.subplots(2, 1, figsize=figsize, sharex=True)
    fig.patch.set_facecolor(figure_bg_color)
    
    # Helper function to get color - FIXED VERSION
    def get_component_color(full_column_name):
        """
        Get color for a component based on the column name
        """
        if ': ' in full_column_name:
            component = full_column_name.split(': ')[1].upper()
        else:
            component = full_column_name.upper()
        
        if component in COLOR_MAPPING:
            return COLOR_MAPPING[component]
        
        for key, color in COLOR_MAPPING.items():
            if key in component:
                return color
        
        # For components with underscores or specific patterns
        component_parts = component.split('_')
        for part in component_parts:
            if part in COLOR_MAPPING:
                return COLOR_MAPPING[part]
        return COLOR_MAPPING['DEFAULT']
    
    ax1 = axes[0]
    ax1.set_facecolor(axes_bg_color)
    ax1.set_frame_on(False)
    
    if not df_in.empty and len(in_columns) > 0:    
        if sort_by_flh:
            flh_dict_in = {}
            for col in in_columns:
                flh_dict_in[col] = calculate_full_load_hours(col, "IN")

            sorted_columns = sorted(in_columns, key=lambda x: flh_dict_in.get(x, 0), reverse=True)
            df_in_sorted = df_in[sorted_columns]
            if labels_with_info:
                in_labels = [f"{col[4:]} ({flh_dict_in[col]:.0f}h)" for col in df_in_sorted.columns]
            else:
                in_labels = [col[4:] for col in df_in_sorted.columns]
        else:
            df_in_sorted = df_in[in_columns].reindex(sorted(in_columns), axis=1)
            component_means = df_in_sorted.mean()
            sorted_columns = component_means.sort_values(ascending=False).index.tolist()
            df_in_sorted = df_in_sorted[sorted_columns]
            in_labels = [col[4:] for col in df_in_sorted.columns]
        
        in_colors = [get_component_color(col) for col in df_in_sorted.columns]
        
        ax1.stackplot(df_in_sorted.index, df_in_sorted.T.values, 
                     labels=in_labels, 
                     colors=in_colors,  # Explicitly pass colors
                     alpha=0.85)
        
        # Add total IN flow line
        total_in = df_in_sorted.sum(axis=1)
        ax1.plot(df_in_sorted.index, total_in, 'k-', linewidth=2, alpha=0.9, label='Gesamt IN')
        
        # Customize plot
        ax1.set_title(inflow_plot_title, fontsize=title_fontsize, fontweight='bold')
        ax1.set_ylabel('', fontsize=label_fontsize)
        ax1.yaxis.set_label_coords(-0.05, 1.05)  
        ax1.text(0, 1.02, '[MWh/h]', transform=ax1.transAxes, 
                 fontsize=label_fontsize, ha='right', va='bottom')
        ax1.grid(True, alpha=1, linestyle='-')
        ax1.set_xlim(start_date, end_date - pd.Timedelta(days=1))
        # Add legend inside plot
        handles_in, labels_in = ax1.get_legend_handles_labels()
        handles_in.reverse()
        labels_in.reverse()
        ax1.legend(handles_in, labels_in, loc='upper left', fontsize=label_fontsize-2, 
          bbox_to_anchor=(1.02, 1), borderaxespad=0.)
        
    ax2 = axes[1]
    ax2.set_facecolor(axes_bg_color)
    ax2.set_frame_on(False)
    
    if not df_out.empty and len(out_columns) > 0:
        df_out_sorted = df_out[out_columns].reindex(sorted(out_columns), axis=1)
        total_out = df_out_sorted.sum(axis=1)  
        
        if is_electricity_bus and 'total_in' in locals():
            grid_loss = total_in - total_out
            grid_loss = grid_loss.clip(lower=0)
            grid_loss_df = pd.DataFrame({'OUT: Grid Loss': grid_loss}, index=df_out_sorted.index)
            df_out_with_loss = pd.concat([df_out_sorted, grid_loss_df], axis=1)
            
            if sort_by_flh:
                flh_dict_out = {}
                for col in df_out_sorted.columns:
                    flh_dict_out[col] = calculate_full_load_hours(col, "OUT")
                
                #grid_loss_flh = calculate_full_load_hours('OUT: Grid Loss', "OUT")
                grid_loss_flh = (
                                (combined_dfs['ElectricityIn']['OUT: Netzverluste'] - combined_dfs['ElectricityOut']['IN: Netzverluste'])/
                                (combined_dfs['ElectricityIn']['OUT: Netzverluste'] - combined_dfs['ElectricityOut']['IN: Netzverluste']).max()).sum()
                flh_dict_out['OUT: Grid Loss'] = grid_loss_flh
                
                # Sort all columns by FLH in descending order
                out_cols_with_loss = list(df_out_sorted.columns) + ['OUT: Grid Loss']
                sorted_columns = sorted(out_cols_with_loss, 
                                      key=lambda x: flh_dict_out.get(x, 0), 
                                      reverse=True)
                df_out_sorted_final = df_out_with_loss[sorted_columns]
                if labels_with_info:
                    out_labels = [f"{col[5:]} ({flh_dict_out[col]:.0f}h)" for col in df_out_sorted_final.columns]
                else:
                    out_labels = [col[5:] for col in df_out_sorted_final.columns]
                    
            else:
                # Original sorting by mean values
                component_means = df_out_with_loss.mean()
                sorted_columns = component_means.sort_values(ascending=False).index.tolist()
                df_out_sorted_final = df_out_with_loss[sorted_columns]
                out_labels = [col[5:] for col in df_out_sorted_final.columns]
            
            out_colors = [get_component_color(col) for col in df_out_sorted_final.columns]
        
            ax2.stackplot(df_out_sorted_final.index, df_out_sorted_final.T.values, 
                         labels=out_labels, 
                         colors=out_colors,  # Explicitly pass colors
                         alpha=0.85)
            
            total_out_with_loss = df_out_sorted_final.sum(axis=1)
            ax2.plot(df_out_sorted_final.index, total_out_with_loss, 'k-', linewidth=2, alpha=0.9, label='Gesamt OUT')
        
        else:
            # No grid loss calculation for non-electricity buses
            if sort_by_flh:
                flh_dict_out = {}
                for col in out_columns:
                    flh_dict_out[col] = calculate_full_load_hours(col, "OUT")
                
                sorted_columns = sorted(out_columns, 
                                      key=lambda x: flh_dict_out.get(x, 0), 
                                      reverse=True)
                df_out_sorted_final = df_out[sorted_columns]
                
                if labels_with_info:
                    out_labels = [f"{col[5:]} ({flh_dict_out[col]:.0f}h)" for col in df_out_sorted_final.columns]
                else:
                    out_labels = [col[5:] for col in df_out_sorted_final.columns]
            else:
                # Original sorting by mean values in descending order
                component_means = df_out_sorted.mean()
                sorted_columns = component_means.sort_values(ascending=False).index.tolist()
                df_out_sorted_final = df_out_sorted[sorted_columns]
                out_labels = [col[5:] for col in df_out_sorted_final.columns]
            
            out_colors = [get_component_color(col) for col in df_out_sorted_final.columns]
            
            ax2.stackplot(df_out_sorted_final.index, df_out_sorted_final.T.values, 
                         labels=out_labels, 
                         colors=out_colors,
                         alpha=0.85)
            
            ax2.plot(df_out_sorted_final.index, total_out, 'k-', linewidth=2, alpha=0.9, label='Total OUT')
            
        ax2.set_title(outflow_plot_title, fontsize=title_fontsize, fontweight='bold')
        ax2.set_ylabel('', fontsize=label_fontsize)
        ax2.yaxis.set_label_coords(-0.05, 1.02)  
        ax2.text(0, 1.02, '[MWh/h]', transform=ax2.transAxes, 
                 fontsize=label_fontsize, ha='right', va='bottom')
        ax2.set_xlabel('Zeit', fontsize=label_fontsize)
        ax2.grid(True, alpha=1, linestyle='-')
        ax2.set_xlim(start_date, end_date - pd.Timedelta(days=1))
        # Add legend inside plot
        handles_out, labels_out = ax2.get_legend_handles_labels()
        handles_out.reverse()
        labels_out.reverse()
        ax2.legend(handles_out, labels_out, loc='upper left', fontsize=label_fontsize-2, 
          bbox_to_anchor=(1.02, 1), borderaxespad=0.)
        ax2.text(1.02, 0.05, "Info: (Zahlen in Klammern = Jahresvolllaststunden)",
         transform=ax2.transAxes, fontsize=label_fontsize-2, ha="left", va="top", clip_on = False)
        
    
    if 'total_in' in locals():
        if is_electricity_bus and 'df_out_with_loss' in locals():
            max_in = total_in.max()
            max_out_with_loss = df_out_with_loss.sum(axis=1).max()
            y_max = max(max_in, max_out_with_loss) * 1.1  
        elif 'total_out' in locals():
            max_in = total_in.max()
            max_out = total_out.max()
            y_max = max(max_in, max_out) * 1.1  
        else:
            y_max = total_in.max() * 1.1

        ax1.set_ylim(0, y_max)
        ax2.set_ylim(0, y_max)
        ax1.tick_params(axis='y', labelsize=label_fontsize-2)
        ax2.tick_params(axis='y', labelsize=label_fontsize-2)
    
    # Format x-axis
    ax_bottom = axes[1] 
    
    # Set date formatting
    if is_electricity_bus and 'df_out_with_loss' in locals():
        date_df = df_out_with_loss
    elif not df_out.empty:
        date_df = df_out_sorted
    else:
        date_df = df_in_sorted
    
    if not date_df.empty:
        date_range = (date_df.index[-1] - date_df.index[0]).days
        if date_range <= 7:
            ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.\n%H:%M'))
            ax_bottom.xaxis.set_major_locator(mdates.DayLocator())
        elif date_range <= 31:
            ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter('%Y.%m.%d'))
            ax_bottom.xaxis.set_major_locator(mdates.WeekdayLocator())
        else:
            ax_bottom.xaxis.set_major_formatter(mdates.DateFormatter('%Y.%m.%d'))
            ax_bottom.xaxis.set_major_locator(mdates.MonthLocator())
    
    plt.xticks(rotation=45, fontsize=label_fontsize-2)
    #plt.tight_layout(rect=[0, 0, 0.85, 0.96])
    plt.tight_layout()
    plt.show()
    #plt.savefig(os.path.join(workdir, 'figures', 'Abschlussbericht', 'sequence.svg'), dpi = 800)
    
    fig_1, ax_1 = plt.subplots(figsize=figsize)
    inflow = df_in_sorted
    outflow = df_out_sorted_final*-1
    
    ax_1.stackplot(df_in_sorted.index, df_in_sorted.T.values, 
                 labels=in_labels, 
                 colors=in_colors,  # Explicitly pass colors
                 alpha=0.85)

    # Plot outflows (negative)
    ax_1.stackplot(df_out_sorted_final.index, df_out_sorted_final.T.values*-1, 
                 labels=out_labels, 
                 colors=out_colors,  # Explicitly pass colors
                 alpha=0.85)
    
    ax_1.axhline(0, color='black', linewidth=1)
    ax_1.set_title(f"{inflow_plot_title} & {outflow_plot_title}")
    ax_1.set_ylabel("Leistung [MW]")
    ax_1.legend(loc="upper left", bbox_to_anchor=(1, 1))
    plt.tight_layout()
    plt.show()
    return fig, axes, fig_1, ax_1

def create_bus_dataframes(bus_sequences, energysystem):
    """Convert bus sequences to DataFrames with proper time index"""
    bus_dfs = {}
    
    for bus_name, components in bus_sequences.items():
        bus_data = {}
        
        for component_name, sequence_data in components.items():
            # Extract the actual flow values from the sequence data
            if hasattr(sequence_data, 'values'):
                # If it's a pandas Series or similar with .values attribute
                flow_values = sequence_data.values
            elif isinstance(sequence_data, dict):
                # If it's a dictionary, get the flow data
                flow_data = sequence_data.get('flow', None)
                if flow_data is not None and hasattr(flow_data, 'values'):
                    flow_values = flow_data.values
                else:
                    continue  # Skip if no valid flow data
            else:
                continue  # Skip if we can't extract values
            
            # Ensure we have a 1D array
            if hasattr(flow_values, 'shape') and len(flow_values.shape) == 1:
                bus_data[f"{bus_name} -> {component_name}"] = flow_values
            else:
                # If it's 2D, take the first column or flatten
                try:
                    if hasattr(flow_values, 'shape') and len(flow_values.shape) == 2:
                        bus_data[f"{bus_name} -> {component_name}"] = flow_values[:, 0]
                    else:
                        bus_data[f"{bus_name} -> {component_name}"] = flow_values.flatten()
                except:
                    continue
        
        if bus_data:
            # Use energysystem timeindex
            time_index = energysystem.timeindex
            
            # Ensure all arrays have the same length
            min_length = min(len(arr) for arr in bus_data.values())
            if min_length != len(time_index):
                time_index = time_index[:min_length]
                
            # Truncate all arrays to the same length
            for key in bus_data.keys():
                bus_data[key] = bus_data[key][:min_length]
            
            # Create DataFrame
            bus_dfs[bus_name] = pd.DataFrame(bus_data, index=time_index[:min_length])
    
    return bus_dfs

def create_component_dataframes(component_sequences, energysystem):
    """Convert component sequences to DataFrames"""
    component_dfs = {}
    
    for component_name, targets in component_sequences.items():
        component_data = {}
        
        for target_name, sequence_data in targets.items():
            if str(target_name) == 'None':
                continue
            
            if hasattr(sequence_data, 'values'):
                # If it's a pandas Series or similar with .values attribute
                flow_values = sequence_data.values
            elif isinstance(sequence_data, dict):
                # If it's a dictionary, get the flow data
                flow_data = sequence_data.get('flow', None)
                if flow_data is not None and hasattr(flow_data, 'values'):
                    flow_values = flow_data.values
                else:
                    continue  # Skip if no valid flow data
            else:
                continue  # Skip if we can't extract values
            
            # Ensure we have a 1D array
            if hasattr(flow_values, 'shape') and len(flow_values.shape) == 1:
                component_data[f"{component_name} -> {target_name}"] = flow_values
            else:
                # If it's 2D, take the first column or flatten
                try:
                    if hasattr(flow_values, 'shape') and len(flow_values.shape) == 2:
                        component_data[f"{component_name} -> {target_name}"] = flow_values[:, 0]
                    else:
                        component_data[f"{component_name} -> {target_name}"] = flow_values.flatten()
                except:
                    print(f"Could not process data for {component_name} -> {target_name}")
                    continue
        
        if component_data:
            # Use energysystem timeindex
            time_index = energysystem.timeindex
            
            # Ensure all arrays have the same length
            min_length = min(len(arr) for arr in component_data.values())
            if min_length != len(time_index):
                print(f"Data length mismatch for component {component_name}. Truncating to {min_length} points.")
                time_index = time_index[:min_length]
                
            # Truncate all arrays to the same length
            for key in component_data.keys():
                component_data[key] = component_data[key][:min_length]
            
            # Create DataFrame
            component_dfs[component_name] = pd.DataFrame(component_data, index=time_index[:min_length])
    
    return component_dfs

def extract_sankey_flow_data(bus_dfs, component_dfs, component_bus_mapping, group_similar=True):
    """
    Extract flow data from Sankey diagrams as a clean DataFrame
    
    Parameters:
    -----------
    bus_dfs : dict
        Dictionary of bus DataFrames
    component_dfs : dict
        Dictionary of component DataFrames
    component_bus_mapping : dict
        Mapping of components to buses
    group_similar : bool, default=True
        Whether to group similar components (ending with _n, _s, _m, _e)
    
    Returns:
    --------
    pd.DataFrame with columns: ['source', 'target', 'value', 'flow_type']
    """
    
    flows = []
    
    
    def group_name(name):
        """Group similar components by removing _n, _s, _m, _e suffixes"""
        if group_similar and name.endswith(('_n', '_s', '_m', '_e')):
            return name[:-2]  # Remove last 2 characters
        return name
    
    # Process COMPONENT DataFrames (components → buses) - INCOMING FLOWS
    for component_name, df in component_dfs.items():
        grouped_component = group_name(component_name)
        
        for column in df.columns:
            if ' -> ' in column:
                parts = column.split(' -> ')
                if len(parts) == 2:
                    from_node, to_node = parts
                    
                    # Skip if to_node is None
                    if to_node == 'None':
                        continue
            
                    grouped_from = group_name(from_node)
                    grouped_to = group_name(to_node)
                    
                    # Calculate total flow (sum over all time steps)
                    total_flow = df[column].sum()
                    
                    if pd.notna(total_flow):
                        flows.append({
                            'source': grouped_from,
                            'target': grouped_to,
                            'value': total_flow,
                            'flow_type': 'incoming',
                            'original_source': from_node,
                            'original_target': to_node,
                            'original_component': component_name
                        })
    
    # Process BUS DataFrames (buses → components) - OUTGOING FLOWS
    for bus_name, df in bus_dfs.items():
        grouped_bus = group_name(bus_name)
        
        for column in df.columns:
            if ' -> ' in column:
                parts = column.split(' -> ')
                if len(parts) == 2:
                    from_node, to_node = parts
                
                    grouped_from = group_name(from_node)
                    grouped_to = group_name(to_node)
                    
                    # Calculate total flow
                    total_flow = df[column].sum()
                    
                    if pd.notna(total_flow):
                        comp_name = to_node if 'bus' not in to_node.lower() else from_node
                        
                        flows.append({
                            'source': grouped_from,
                            'target': grouped_to,
                            'value': total_flow,
                            'flow_type': 'outgoing',
                            'original_source': from_node,
                            'original_target': to_node,
                            'original_component': comp_name
                        })

    df_flows = pd.DataFrame(flows)
    
    if len(df_flows) == 0:
        print("Warning: No flows found!")
        return pd.DataFrame(columns=['source', 'target', 'value', 'flow_type'])
    
    # Group by source, target to combine any duplicates after grouping
    if group_similar:
        grouped = df_flows.groupby(['source', 'target', 'flow_type']).agg({
            'value': 'sum'
        }).reset_index()
        return grouped
    else:
        # Return with original names
        return df_flows[['source', 'target', 'value', 'flow_type']]

def adjust_column_width_for_all_sheets(wb):
    for sheet in wb.sheetnames: 
        current_sheet = wb[sheet]
        for col in current_sheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            current_sheet.column_dimensions[column].width = adjusted_width
def create_sankey_excel(model_data: dict, output_file: str):
    
    if os.path.exists(output_file):
        wb = load_workbook(output_file)
        mode = "a"
    else:
        wb = None
        mode = "w"
        
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        if wb:
            writer.book = wb
            
        for model_name, df in model_data.items():
            df.to_excel(writer, sheet_name=model_name, startrow=1, index=False)

    wb = load_workbook(output_file)
    model_names= [s for s in wb.sheetnames if s != "Main"]
    
    if "Main" in wb.sheetnames:
        del wb["Main"]
    
    main_sheet = wb.create_sheet("Main", 0)
    main_sheet["A1"] = "Info: Use the drop down box to select the scenario"
    main_sheet['A3'] = "Select Scenario:"
    # Store dropdown values in hidden helper column
    for i, name in enumerate(model_names, start=1):
        main_sheet[f"Z{i}"] = name

    dv = DataValidation(
        type="list",
        formula1=f"=Z1:Z{len(model_names)}",
        allow_blank=False
    )
    main_sheet.add_data_validation(dv)
    dv.add("B3")
    main_sheet["B3"] = model_names[0]
    
    main_sheet["A5"] = "Displaying data for:"
    main_sheet["B5"] = '=INDIRECT("\'"&B3&"\'!A1")'
    
    for model_name, df in model_data.items():
        ws = wb[model_name]
        ws["A1"] = model_name  
    
    sample_df = next(iter(model_data.values()))
    max_rows = len(sample_df) + 1  # +1 because headers exist
    max_cols = len(sample_df.columns)

    start_row_main = 7

    for r in range(2, max_rows + 2):
        for c in range(1, max_cols + 1):
            col_letter = get_column_letter(c)
            formula = f'=INDIRECT("\'"&$B$3&"\'!{col_letter}{r}")'
            main_sheet.cell(
                row=start_row_main + r - 2,
                column=c,
                value=formula
            )

    # Hide helper column
    main_sheet.column_dimensions["Z"].hidden = True
    adjust_column_width_for_all_sheets(wb)
    wb.save(output_file)
