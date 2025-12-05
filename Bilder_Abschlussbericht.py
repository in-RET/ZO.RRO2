# -*- coding: utf-8 -*-
"""
Created on Mon Dec  1 15:30:57 2025

@author: rbala
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pickle
from matplotlib import cm
import seaborn as sns
from datetime import datetime
from src.postprocessing.utils_dump import get_dump_file_path,load_results_from_dump
from datetime import datetime, timedelta

scenarios =['Ref_BS_RK_25_11_25']
year = 2030
variation = "BS0006"
model_name = "BS"#"_regionalization"   

plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 12

for scenario_num in scenarios:
    print("Loading results...")
    dump_path = get_dump_file_path(year, variation, model_name, scenario_num)
    es, model = load_results_from_dump(dump_path)

    print("Extracting results...")   
    flows = {}
    capacities={}
    flow_descriptions = {}
    
    for node_label, node_data in model.items():
        if isinstance(node_data, dict) and 'sequences' in node_data:
            for flow_label, flow_series in node_data['sequences'].items():
                if isinstance(flow_series, pd.Series):
                    flow_key = f"{node_label}_{flow_label}"
                    flows[flow_key] = flow_series
                    flow_descriptions[flow_key] = {
                        'node': node_label,
                        'flow': flow_label,
                        'type': 'Unknown'
                        
                    }
        if isinstance(node_data, dict) and 'scalars' in node_data:
            for scalar_label, scalar_value in node_data['scalars'].items():
                if 'invest' in scalar_label.lower() or 'capacity' in scalar_label.lower():
                    if isinstance(scalar_value, (int, float, np.number)):
                        capacities[node_label] = float(scalar_value)
    
    print("CATEGORIZING FLOWS")
     
    # First, let's find all unique node types
    categories = {
    'Wind': [],
    'PV': [],
    'Hydro': [],
    'Biomass': [],
    'Gas': [],
    'Heat': [],
    'Demand': [],
    'Storage': [],
    'Import': [],
    'Export': [],
    'Excess': [],
    'Losses': [],
    'Other': []
    }
    
    for flow_key, flow_data in flows.items():
        flow_lower = flow_key.lower()
        
        categorized = False
        for category, keywords in [
            ('Wind', ['wind']),
            ('PV', ['pv', 'solar']),
            ('Hydro', ['hydro']),
            ('Biomass', ['biogas', 'biomass', 'bio']),
            ('Gas', ['gas', 'gud']),
            ('Heat', ['heat', 'thermal', 'boiler', 'heatpump']),
            ('Demand', ['demand']),
            ('Storage', ['storage', 'battery']),
            ('Import', ['import']),
            ('Export', ['export']),
            ('Excess', ['excess']),
            ('Losses', ['netzverluste']),
        ]:
            if any(keyword in flow_lower for keyword in keywords):
                categories[category].append((flow_key, flow_data))
                categorized = True
                break
        
        if not categorized:
            categories['Other'].append((flow_key, flow_data))
            
    def create_electricity_plot_simple(start_date=None, end_date=None, save_suffix=''):
        """
        Simple electricity plot that works with any data structure
        """
        
        print(f"\nCreating electricity plot for date range: {start_date} to {end_date}")
        
        if not flows:
            print("  No flows found!")
            return None, None
        
        # Get time index from any flow
        sample_flow = list(flows.values())[0]
        time_index = sample_flow.index
        
        print(f"  Time range in data: {time_index[0]} to {time_index[-1]}")
        
        # ============================================
        # GROUP GENERATION FLOWS
        # ============================================
        
        generation_data = {}
        
        # Wind generation
        wind_flows = categories['Wind']
        if wind_flows:
            wind_df = pd.DataFrame({k: v for k, v in wind_flows}, index=time_index)
            generation_data['Wind'] = wind_df.sum(axis=1)
            print(f"  Found {len(wind_flows)} wind flows")
        
        # PV generation
        pv_flows = categories['PV']
        if pv_flows:
            pv_df = pd.DataFrame({k: v for k, v in pv_flows}, index=time_index)
            generation_data['Solar PV'] = pv_df.sum(axis=1)
            print(f"  Found {len(pv_flows)} PV flows")
        
        # Hydro generation
        hydro_flows = categories['Hydro']
        if hydro_flows:
            hydro_df = pd.DataFrame({k: v for k, v in hydro_flows}, index=time_index)
            generation_data['Hydro'] = hydro_df.sum(axis=1)
            print(f"  Found {len(hydro_flows)} hydro flows")
        
        # Biomass generation
        biomass_flows = categories['Biomass']
        if biomass_flows:
            biomass_df = pd.DataFrame({k: v for k, v in biomass_flows}, index=time_index)
            generation_data['Biomass'] = biomass_df.sum(axis=1)
            print(f"  Found {len(biomass_flows)} biomass flows")
        
        # Gas generation
        gas_flows = categories['Gas']
        if gas_flows:
            gas_df = pd.DataFrame({k: v for k, v in gas_flows}, index=time_index)
            generation_data['Gas'] = gas_df.sum(axis=1)
            print(f"  Found {len(gas_flows)} gas flows")
        
        # ============================================
        # GROUP CONSUMPTION FLOWS
        # ============================================
        
        consumption_data = {}
        
        # Electricity demand
        demand_flows = [f for f in categories['Demand'] if 'electricity' in f[0].lower()]
        if demand_flows:
            demand_df = pd.DataFrame({k: v for k, v in demand_flows}, index=time_index)
            consumption_data['Electricity Demand'] = demand_df.sum(axis=1)
            print(f"  Found {len(demand_flows)} electricity demand flows")
        
        # Heat-related electricity consumption
        heat_flows = [f for f in categories['Heat'] if any(keyword in f[0].lower() for keyword in ['electric', 'el'])]
        if heat_flows:
            heat_df = pd.DataFrame({k: v for k, v in heat_flows}, index=time_index)
            consumption_data['Heating'] = heat_df.sum(axis=1)
            print(f"  Found {len(heat_flows)} heating electricity flows")
        
        # Import/Export
        import_flows = categories['Import']
        if import_flows:
            import_df = pd.DataFrame({k: v for k, v in import_flows}, index=time_index)
            consumption_data['Import'] = import_df.sum(axis=1)
            print(f"  Found {len(import_flows)} import flows")
        
        export_flows = categories['Export']
        if export_flows:
            export_df = pd.DataFrame({k: v for k, v in export_flows}, index=time_index)
            consumption_data['Export'] = export_df.sum(axis=1)
            print(f"  Found {len(export_flows)} export flows")
        
        # Excess
        excess_flows = categories['Excess']
        if excess_flows:
            excess_df = pd.DataFrame({k: v for k, v in excess_flows}, index=time_index)
            consumption_data['Excess'] = excess_df.sum(axis=1)
            print(f"  Found {len(excess_flows)} excess flows")
        
        loss_flows = categories['Losses']
        if loss_flows:
            loss_df = pd.DataFrame({k: v for k, v in loss_flows}, index=time_index)
            consumption_data['Losses'] = loss_df.sum(axis=1)
            print(f"  Found {len(loss_flows)} loss flows")
        
        # ============================================
        # CREATE DATAFRAMES
        # ============================================
        
        if generation_data:
            df_gen = pd.DataFrame(generation_data, index=time_index)
        else:
            df_gen = pd.DataFrame(index=time_index)
        
        if consumption_data:
            df_cons = pd.DataFrame(consumption_data, index=time_index)
        else:
            df_cons = pd.DataFrame(index=time_index)
        
        # ============================================
        # APPLY DATE FILTER
        # ============================================
        
        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            
            # Include the entire end date
            end_date = end_date + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            
            mask = (time_index >= start_date) & (time_index <= end_date)
            date_range_str = f" ({start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')})"
            
            if not df_gen.empty:
                df_gen = df_gen.loc[mask]
            if not df_cons.empty:
                df_cons = df_cons.loc[mask]
        else:
            date_range_str = ""
        
        # ============================================
        # CREATE PLOT
        # ============================================
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
        
        # Colors
        gen_colors = {
            'Wind': '#3498db',
            'Solar PV': '#f1c40f',
            'Hydro': '#1abc9c',
            'Biomass': '#27ae60',
            'Gas': '#e74c3c'
        }
        
        cons_colors = {
            'Electricity Demand': '#2c3e50',
            'Heating': '#e67e22',
            'Import': '#9b59b6',
            'Export': '#2ecc71',
            'Excess': '#95a5a6'
        }
        
        # ============================================
        # TOP SUBPLOT: GENERATION
        # ============================================
        
        if not df_gen.empty and df_gen.sum().sum() > 0:
            # Plot as area chart
            bottom = np.zeros(len(df_gen))
            for col in df_gen.columns:
                values = df_gen[col].values
                color = gen_colors.get(col, '#cccccc')
                ax1.fill_between(df_gen.index, bottom, bottom + values,
                               label=col, color=color, alpha=0.8,
                               edgecolor='white', linewidth=0.5)
                bottom += values
            
            ax1.set_ylabel('Generation [MW]', fontsize=12)
            ax1.set_title(f'Hourly Electricity Generation{date_range_str}', 
                          fontsize=14, fontweight='bold')
            ax1.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
            
            # Format x-axis
            if len(df_gen) <= 168:  # 1 week or less
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%H:%M'))
                ax1.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            elif len(df_gen) <= 744:  # 1 month or less
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
                ax1.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            else:
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                ax1.xaxis.set_major_locator(mdates.MonthLocator())
            
            ax1.grid(True, alpha=0.3)
            
            # Add statistics
            total_gen = df_gen.sum().sum()
            ax1.text(0.02, 0.98, f'Total: {total_gen:,.0f} MWh',
                     transform=ax1.transAxes, fontsize=11, verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            print(f"  → Total generation: {total_gen:,.0f} MWh")
            for col in df_gen.columns:
                col_total = df_gen[col].sum()
                share = col_total / total_gen * 100 if total_gen > 0 else 0
                print(f"    → {col}: {col_total:,.0f} MWh ({share:.1f}%)")
        else:
            ax1.text(0.5, 0.5, 'No generation data found',
                     horizontalalignment='center', verticalalignment='center',
                     transform=ax1.transAxes, fontsize=12)
            ax1.set_title(f'Hourly Electricity Generation{date_range_str}',
                          fontsize=14, fontweight='bold')
            print("  → No generation data found")
        
        # ============================================
        # BOTTOM SUBPLOT: CONSUMPTION
        # ============================================
        
        if not df_cons.empty and df_cons.sum().sum() > 0:
            # Plot as area chart
            bottom = np.zeros(len(df_cons))
            for col in df_cons.columns:
                values = df_cons[col].values
                color = cons_colors.get(col, '#cccccc')
                ax2.fill_between(df_cons.index, bottom, bottom + values,
                               label=col, color=color, alpha=0.8,
                               edgecolor='white', linewidth=0.5)
                bottom += values
            
            ax2.set_ylabel('Consumption [MW]', fontsize=12)
            ax2.set_title(f'Hourly Electricity Consumption{date_range_str}',
                          fontsize=14, fontweight='bold')
            ax2.legend(loc='upper left', bbox_to_anchor=(1.05, 1))
            
            # Format x-axis
            if len(df_cons) <= 168:
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%H:%M'))
                ax2.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            elif len(df_cons) <= 744:
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
                ax2.xaxis.set_major_locator(mdates.DayLocator(interval=2))
            else:
                ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                ax2.xaxis.set_major_locator(mdates.MonthLocator())
            
            ax2.grid(True, alpha=0.3)
            
            # Add statistics
            total_cons = df_cons.sum().sum()
            ax2.text(0.02, 0.98, f'Total: {total_cons:,.0f} MWh',
                     transform=ax2.transAxes, fontsize=11, verticalalignment='top',
                     bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            
            print(f"  → Total consumption: {total_cons:,.0f} MWh")
            for col in df_cons.columns:
                col_total = df_cons[col].sum()
                share = col_total / total_cons * 100 if total_cons > 0 else 0
                print(f"    → {col}: {col_total:,.0f} MWh ({share:.1f}%)")
        else:
            ax2.text(0.5, 0.5, 'No consumption data found',
                     horizontalalignment='center', verticalalignment='center',
                     transform=ax2.transAxes, fontsize=12)
            ax2.set_title(f'Hourly Electricity Consumption{date_range_str}',
                          fontsize=14, fontweight='bold')
            print("  → No consumption data found")
        
        plt.suptitle('Electricity Balance', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        
        # Save plot
        if save_suffix:
            filename = f'01_electricity_{save_suffix}.png'
        else:
            filename = '01_electricity_full_year.png'
        
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.show()
        
        print(f"\n  → Plot saved as: {filename}")
        
        return df_gen, df_cons
    
    # ============================================
    # 6. CREATE AND TEST PLOTS
    # ============================================
    
    print("\n" + "="*60)
    print("CREATING ELECTRICITY PLOTS")
    print("="*60)
    
    if flows:
        # Get time index
        sample_flow = list(flows.values())[0]
        time_index = sample_flow.index
        
        print(f"Data time range: {time_index[0]} to {time_index[-1]}")
        print(f"Total hours: {len(time_index)}")
        
        # Test 1: Full year
        print("\n1. Creating full year plot...")
        df_gen_full, df_cons_full = create_electricity_plot_simple(save_suffix='full_year')
        
        # Test 2: First week
        print("\n2. Creating first week plot...")
        start_week1 = time_index[0].strftime('%Y-%m-%d')
        end_week1 = (time_index[0] + timedelta(days=6)).strftime('%Y-%m-%d')
        df_gen_week1, df_cons_week1 = create_electricity_plot_simple(
            start_date=start_week1,
            end_date=end_week1,
            save_suffix='week1'
        )
        
        # Test 3: Summer week (find a date in June-August)
        print("\n3. Creating summer week plot...")
        summer_dates = [dt for dt in time_index if 6 <= dt.month <= 8]
        if summer_dates:
            start_summer = summer_dates[0].strftime('%Y-%m-%d')
            end_summer = (summer_dates[0] + timedelta(days=6)).strftime('%Y-%m-%d')
            df_gen_summer, df_cons_summer = create_electricity_plot_simple(
                start_date=start_summer,
                end_date=end_summer,
                save_suffix='summer_week'
            )
        
        # Test 4: Winter week (find a date in December-February)
        print("\n4. Creating winter week plot...")
        winter_dates = [dt for dt in time_index if dt.month in [12, 1, 2]]
        if winter_dates:
            start_winter = winter_dates[0].strftime('%Y-%m-%d')
            end_winter = (winter_dates[0] + timedelta(days=6)).strftime('%Y-%m-%d')
            df_gen_winter, df_cons_winter = create_electricity_plot_simple(
                start_date=start_winter,
                end_date=end_winter,
                save_suffix='winter_week'
            )
        
        # Test 5: Custom date range (modify as needed)
        print("\n5. Creating custom 3-day plot...")
        # Use a date in the middle of the year
        mid_idx = len(time_index) // 2
        start_custom = time_index[mid_idx].strftime('%Y-%m-%d')
        end_custom = (time_index[mid_idx] + timedelta(days=2)).strftime('%Y-%m-%d')
        df_gen_custom, df_cons_custom = create_electricity_plot_simple(
            start_date=start_custom,
            end_date=end_custom,
            save_suffix='custom_3days'
        )