# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 11:22:32 2026

@author: rbala

Parallel Simulation
"""
from datetime import datetime
import numpy as np
import pandas as pd
from multiprocessing import Pool
import multiprocessing as mp
mp.set_start_method("spawn", force=True)
from tqdm import tqdm

# SALib
from SALib.sample.morris import sample
from SALib.analyze.morris import analyze
from src.models.solve_model import solveModels
import energymodels.Basic_example_zorro_1 as be
import src.preprocessing.files as file_module
import warnings
warnings.filterwarnings("ignore")
import joblib
import os
workdir = os.getcwd()

# PARAMETER CONFIG
Sim_Morris = True
Sim_MC = False
max_workers = 4
model_ID = 'BS0006'
year = 2045
Morris_runs = 1
model_name = "Basic_example_zorro_1"
param_config = {
    "demand_HH_waerme": [0.8, 1.2],
    "person_mob": [0 , 1],  #0--> BS 1-->voll elek
    "capex_batterie": [0.8, 1.2],
    "capex_heat_storage": [0.8, 1.2],
    "capex_PtL/BtL": [0.8, 1.2],
    "potential_wind": [0.8, 1.2],
    "potential_pv": [0.8, 1.2],
    "potential_biomasse": [0.8, 1.2],
    "pv_flh": [0.8, 1.2],
    "wind_flh": [0.8, 1.2],
    "import_H2/fuel": [0.8, 1.2],
    "import_electricity_price": [0.8, 1.2],
    "import_biomasse": [1, 1.2]  # kann nur teuer werden
}
names = list(param_config.keys())
MC_runs = ((len(names)+1) * Morris_runs)

problem = {
    "num_vars": len(names),
    "names": names,
    "bounds": [param_config[k] for k in names]
}


# KPI
def extract_RES(result):
    output = {
        'wind': 0,
        'pv': 0,
        'stromspeicher': 0,
        'waermespeicher': 0}

    for k, v in result.items():
        k_str = str(k).lower()

        try:
            if "scalars" in v and "invest" in v["scalars"]:
                val = v["scalars"]["invest"]
    
                if "wind" in k_str:
                    output["wind"] += val
                elif "pv" in k_str:
                    output["pv"] += val
                elif "battery" in k_str and 'none' in k_str:
                    output['stromspeicher'] += val
                elif "heat storage" in k_str and 'none' in k_str:
                    output['waermespeicher'] += val
    
        except Exception:
            pass

    return pd.DataFrame([output])


# SINGLE RUN FUNCTION 

def run_single(X):

    CURRENT_PARAMS = dict(zip(names, X))

    # Local patch
    original_read = file_module.read_input_files

    def patched_read_input_files(folder_name, sub_folder_name=None):
        data = original_read(folder_name, sub_folder_name)
        #print('Patch active')
        
        if folder_name == 'data/scalars':
            for key, df in data.items():
                if not isinstance(df, pd.DataFrame):
                    continue
                key_lower = key.lower()
                if "parameter_storage_electricity" in key_lower and "pumped_hydro" not in key_lower:
                    df_mod = df.copy()
                    for col in df_mod.columns:
                        if "investment" in col.lower():
                            df_mod[col] *= CURRENT_PARAMS["capex_batterie"]
                    data[key] = df_mod
                    
                elif "parameter_storage_heat_seasonal" in key_lower:
                    df_mod = df.copy()
                    for col in df_mod.columns:
                        if "investment" in col.lower():
                            df_mod[col] *= CURRENT_PARAMS["capex_heat_storage"]
                    data[key] = df_mod
                
                elif "parameter_power_to_liquid" in key_lower or "parameter_biomass_to_liquid" in key_lower:
                    df_mod = df.copy()
                    for col in df_mod.columns:
                        if "investment" in col.lower():
                            df_mod[col] *= CURRENT_PARAMS["capex_PtL/BtL"]
                    data[key] = df_mod
                
                elif "parameter_onshore_wind" in key_lower:
                    df_mod = df.copy()
                    for col in df_mod.columns:
                        if "potential" in col.lower():
                            df_mod[col] *= CURRENT_PARAMS["potential_wind"]
                    data[key] = df_mod
                
                elif "parameter_field_photovoltaic" in key_lower:
                    df_mod = df.copy()
                    for col in df_mod.columns:
                        if "potential" in col.lower():
                            df_mod[col] *= CURRENT_PARAMS["potential_pv"]
                    data[key] = df_mod
                
                elif "system_configurations_2024" in key_lower:
                    df_mod = df.copy()
                    for col in df_mod.columns:
                        if "System" in col.lower():
                            df_mod[col]['Biomasse_sub_tot'] *= CURRENT_PARAMS["potential_biomasse"]
                            df_mod[col]['Holzpotential_tot'] *= CURRENT_PARAMS["potential_biomasse"]
                    data[key] = df_mod
           
                elif "demand_household" in key_lower:
                    df_mod = df.copy()
                    mask = df_mod.columns.str.startswith("Raumwaerme")
                    df_mod.loc['Summe',mask] *= CURRENT_PARAMS["demand_HH_waerme"]
                    data[key] = df_mod
               
                elif "demand_transport_endenergie" in key_lower:
                    df_mod = df.copy()
                    x = CURRENT_PARAMS["person_mob"] 
                    base_cols = [c for c in df_mod.columns if c.startswith("Personenverkehr")]
                    base = df_mod[base_cols].replace([np.inf, -np.inf], np.nan).fillna(0)
                    emob = df_mod["Voll_Emob"].replace([np.inf, -np.inf], np.nan).fillna(0)
                    emob_df = pd.DataFrame(
                        np.repeat(emob.values[:, None], len(base_cols), axis=1),
                        index=df_mod.index,
                        columns=base_cols
                    )

                    # linear interpolation
                    df_mod.loc[:, base_cols] = (1 - x) * base + x * emob_df
                    data[key] = df_mod
                
            

        if folder_name == 'data/sequences':
            for key, df in data.items():
                if not isinstance(df, pd.DataFrame):
                    continue
                key_lower = key.lower()

                if "feed_in" in key.lower():
                    df_mod = df.copy()
                    for col in df_mod.columns:
                        if 'pv' in col.lower():
                            df_mod[col] *= CURRENT_PARAMS["pv_flh"]
                        elif 'wind' in col.lower():
                            df_mod[col] *= CURRENT_PARAMS["wind_flh"]
                        data[key] = df_mod

                elif "energy_price" in key.lower():
                    df_mod = df.copy()
                    for col in df_mod.columns:
                        if "hydrogen" in col.lower() or "synthetic_fuel" in col.lower():
                            df_mod[col] *= CURRENT_PARAMS["import_H2/fuel"]
                        elif "electricity" in col.lower():
                            df_mod[col] *= CURRENT_PARAMS['import_electricity_price']
                        elif "biomass" in col.lower():
                            df_mod[col] *= CURRENT_PARAMS['import_biomasse']
                        data[key] = df_mod 
        
        return data

    # Patch inside process
    file_module.read_input_files = patched_read_input_files
    be.read_input_files = patched_read_input_files

    sim_data,cost, result = solveModels(
        variations=[model_ID],
        scenario_num="Senitivity_analysis",
        years=[year], 
        model_name= model_name,
        solver="gurobi",
        Anteilig_erneuerbar = True,
        hypothese="ZORRO Konferenz",
        sim_remarks=str(CURRENT_PARAMS),
        solver_output=False
    )
    #restore original data
    file_module.read_input_files = original_read
    be.read_input_files = original_read
    return {
        "params": CURRENT_PARAMS,
        "cost": cost[["investment costs", "variable costs", "profits"]].sum().sum(),
        "df_KPI": safe_extract_result(result)
    }
def safe_extract_result(result):
    try:
        return extract_RES(result)
    except Exception:
        return pd.DataFrame([{
            'wind': np.nan,
            'pv': np.nan,
            'stromspeicher': np.nan,
            'waermespeicher': np.nan
        }])
# PARALLEL EXECUTION FUNCTION
def run_parallel(param_values, max_workers=6):
    with Pool(max_workers) as p:
        outputs = list(tqdm(p.imap(run_single, param_values), total=len(param_values)))
    return outputs



#%% -------------------------------
def main_Morris():

# MORRIS ANALYSIS
# -------------------------------
    param_values_morris = sample(problem, N= Morris_runs, num_levels=4)
    output_names = None
    print("Running Morris ...")
    
    outputs_morris = run_parallel(param_values_morris, max_workers=max_workers)
    if output_names is None:
        output_names = outputs_morris[0]["df_KPI"].columns.tolist() + ["cost"]
        
    Y_morris = np.array([list(o["df_KPI"].iloc[0].values) + [o["cost"]] for o in outputs_morris])
    #results_morris = [o["result"] for o in outputs_morris]
    cost_morris = np.array([o["cost"] for o in outputs_morris])
    params_morris = [o["params"] for o in outputs_morris]

    Si_list=[]
    for j, out in enumerate(output_names):
        Y_single = Y_morris[:, j]
        Si = analyze(problem, param_values_morris, Y_single)
        Si_list.append(Si)
    
    df_morris = pd.DataFrame(param_values_morris, columns=problem['names'])
    for j, out in enumerate(output_names):
        df_morris[out] = Y_morris[:, j]
    
    return outputs_morris, Si_list, df_morris, output_names
    
    

    #%% -------------------------------
    # MONTE CARLO SAMPLING
    # -------------------------------
def main_Monte_Carlo():
    def sample_mc(param_config, N):
        samples = []
        for _ in range(N):
            row = []
            keys = list(param_config.keys())
            for k in keys:
                low, high = param_config[k]
                row.append(np.random.uniform(low, high))
            samples.append(row)
        return np.array(samples)
    
    
    param_values_mc = sample_mc(param_config, MC_runs)
    
    print("Running Monte Carlo ...")
    outputs_mc = run_parallel(param_values_mc, max_workers=max_workers)
    Y_mc = np.array([list(o["df_KPI"].iloc[0].values) + [o["cost"]] for o in outputs_mc])
    cost_mc = np.array([o["cost"] for o in outputs_mc])
    params_mc = [o["params"] for o in outputs_mc]
    
    # Combine results
    df_mc = pd.DataFrame(params_mc)
    for j, out in enumerate(output_names):
        df_mc[out] = Y_mc[:, j]
    
    return  outputs_mc, df_mc
    
    #%%
if __name__ == "__main__": 
    start_time = datetime.now()
    FORMAT = "%(asctime)s %(message)s"
    print('Simulation Start time: {}'.format(start_time))
    if Sim_Morris:
        output_morris, analyse_morris, result_morris, output_names = main_Morris()
        save_dir_morris = os.path.join(workdir,'dumps', 'SALIB', f'results_morris_{len(result_morris)}.joblib')
        joblib.dump((output_morris, analyse_morris, result_morris, output_names, problem),save_dir_morris)
    
    if Sim_MC:
        output_mc, result_mc = main_Monte_Carlo()
        save_dir_mc = os.path.join(workdir,'dumps', 'SALIB', f'results_mc_{len(result_mc)}.joblib')
        joblib.dump((output_mc, result_mc, problem),save_dir_mc)
    
    end_time = datetime.now()
    print('Execution time: {}'.format(end_time - start_time))
    




