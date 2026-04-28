# -*- coding: utf-8 -*-
"""
Created on Wed Apr 15 11:22:32 2026

@author: rbala

Parallel Simulation
"""
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from adjustText import adjust_text
from multiprocessing import Pool
import multiprocessing as mp
mp.set_start_method("spawn", force=True)
from tqdm import tqdm
import seaborn as sns
# SALib
from SALib.sample.morris import sample
from SALib.analyze.morris import analyze
import math
from src.models.solve_model import solveModels
import energymodels.Basic_example_zorro_1 as be
import src.preprocessing.files as file_module
import warnings
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import partial_dependence
warnings.filterwarnings("ignore")
import joblib
import os
workdir = os.getcwd()

# PARAMETER CONFIG
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
def main():

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
    
    for j, out in enumerate(output_names):
        Si = Si_list[j]
        df_sens = pd.DataFrame({
            "parameter": problem["names"],
            "mu_star": Si["mu_star"]
        }).sort_values("mu_star")

        df_sens["normalized"] = df_sens["mu_star"] / df_sens["mu_star"].max() * 100

        plt.figure()
        plt.barh(df_sens["parameter"], df_sens["normalized"])
        plt.xlabel(f"Influence on {out} (%)")
        plt.title(f"Tornado (Morris) - {out}")
        plt.grid()
        plt.show()
    
    # Parameter plot Morris
    # Normalize sigma for bubble size
        size = (Si["sigma"] / Si["sigma"].max()) * 1000

        plt.figure(figsize=(10,7))
        plt.scatter(Si["mu"], Si["mu_star"], s=size)

        texts = []
        for i, name in enumerate(problem["names"]):
            texts.append(
                plt.text(Si["mu"][i], Si["mu_star"][i], name)
            )
        
        adjust_text(texts, arrowprops=dict(arrowstyle="->", color='gray'))

        plt.axvline(0)
        plt.axhline(np.mean(Si["mu_star"]), linestyle='--')

        plt.xlabel("μ")
        plt.ylabel("μ*")
        plt.title(f"Morris Sensitivity - {out}")
        plt.grid()
        plt.show()
    
    df_morris = pd.DataFrame(param_values_morris, columns=problem['names'])
    #df_morris['cost'] = cost_morris
    
    # Trendmultiplot
    for j, out in enumerate(output_names):
        df_morris[out] = Y_morris[:, j]
        n_cols = 3
        n_rows = math.ceil(len(problem['names']) / n_cols)
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows),sharey=True)
        axes = axes.flatten()
        
        for i, col in enumerate(problem['names']):
            ax = axes[i]
        
            ax.scatter(df_morris[col], df_morris[out])
        
            z = np.polyfit(df_morris[col], df_morris[out], 1)
            p = np.poly1d(z)
            ax.plot(df_morris[col], p(df_morris[col]))
        
            ax.set_title(col)
            ax.set_xlabel("Scaling factor")
            ax.set_ylabel(out)
            ax.grid()
        
        for k in range(len(problem['names']), len(axes)):
            fig.delaxes(axes[k])
        
        plt.tight_layout()
        plt.suptitle(out, y=1.02)
        plt.show()

        #Correlation matrix
    corr_matrix = df_morris.corr()
    
    labels = df_morris.columns.tolist()
    plt.figure(figsize=(10,8))
    plt.imshow(corr_matrix, interpolation='none')
    plt.colorbar()
    
    plt.xticks(range(len(labels)), labels, rotation=90, fontsize=10)
    plt.yticks(range(len(labels)), labels, fontsize=10)
    
    plt.title("Correlation Matrix")
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(12,10))
    sns.heatmap(
        corr_matrix,
        annot=True,
        cmap="coolwarm",
        center=0,
        fmt=".2f",
        square=True
    )
    
    plt.title("Correlation Matrix")
    plt.xticks(rotation=90)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.show()
    
    
    #%% -------------------------------
    # MONTE CARLO SAMPLING
    # -------------------------------
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
    # output_names = outputs_mc[0]["df_KPI"].columns.tolist()
    # output_names.append("cost")
    Y_mc = np.array([list(o["df_KPI"].iloc[0].values) + [o["cost"]] for o in outputs_mc])
    #results_mc = [o["result"] for o in outputs_mc]
    cost_mc = np.array([o["cost"] for o in outputs_mc])
    params_mc = [o["params"] for o in outputs_mc]
    
    # Combine results
    df_mc = pd.DataFrame(params_mc)
    for j, out in enumerate(output_names):
        df_mc[out] = Y_mc[:, j]
    
    # -------------------------------
    # 2D RESPONSE SURFACE
    # -------------------------------
    for j, out in enumerate(output_names):
        Si = Si_list[j]
        df_sens = pd.DataFrame({
            "parameter": problem["names"],
            "mu_star": Si["mu_star"],
        })

        top2 = df_sens.sort_values("mu_star", ascending=False)["parameter"].values[:2]
    
        x = df_mc[top2[0]]
        y = df_mc[top2[1]]
        z = df_mc[out]
    
        xi = np.linspace(x.min(), x.max(), 30)
        yi = np.linspace(y.min(), y.max(), 30)
        xi, yi = np.meshgrid(xi, yi)
    
        zi = griddata((x, y), z, (xi, yi), method='linear')
    
        plt.figure()
        cp = plt.contourf(xi, yi, zi, levels=20)
        plt.colorbar(cp)
    
        plt.xlabel(top2[0])
        plt.ylabel(top2[1])
        plt.title(f"2D Response Surface - {out}")
        plt.grid()
        plt.show()

    return Si_list, df_morris, df_mc, output_names
    
    #%%
if __name__ == "__main__": 
    start_time = datetime.now()
    FORMAT = "%(asctime)s %(message)s"
    print('Simulation Start time: {}'.format(start_time))
    analyse_morris, result_morris, result_mc, output_names = main()
    save_dir = os.path.join(workdir,'dumps', 'SALIB', f'results_morris_{len(result_mc)}.joblib')
    joblib.dump((analyse_morris, result_morris, result_mc, output_names),save_dir)
    end_time = datetime.now()
    print('Execution time: {}'.format(end_time - start_time))
    
#%% Post analysis
    
# -------------------------
# All Histograms + Importances #understand uncertainity (Histogram)
# -------------------------

# n_outputs = len(output_names)
# fig, axes = plt.subplots(n_outputs, 2, figsize=(14, 5 * n_outputs))

# if n_outputs == 1:
#     axes = [axes]

# models = {}

# for i, out in enumerate(output_names):
#     # Correlation
#     corr = result_mc[problem["names"] + [out]].corr()[out].drop(out)
#     print(f"\n{out}")
#     print(corr.sort_values())

#     # Train model
#     model = RandomForestRegressor()
#     model.fit(result_mc[problem["names"]], result_mc[out])
#     models[out] = model

#     # Histogram
#     result_mc[out].hist(bins=20, ax=axes[i][0])
#     axes[i][0].set_title(f"{out} Histogram")

#     # Feature Importance
#     importance = pd.Series(model.feature_importances_, index=problem["names"])
#     importance.sort_values().plot(kind="barh", ax=axes[i][1])
#     axes[i][1].set_title(f"{out} Feature Importance")

# plt.tight_layout()
# plt.show()
# # -------------------------
# # PDP for each output
# # -------------------------
# for out in output_names:
#     model = models[out]

#     n_features = len(problem["names"])
#     n_cols = 3
#     n_rows = math.ceil(n_features / n_cols)

#     fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5 * n_rows))
#     axes = axes.flatten()
#     global_ymin = float("inf")
#     global_ymax = float("-inf")
#     for j, feature in enumerate(problem["names"]):
#         pd_result = partial_dependence(
#             model,
#             result_mc[problem["names"]],
#             [feature]
#         )

#         x = pd_result["grid_values"][0]
#         y = pd_result["average"][0]
#         global_ymin = min(global_ymin, y.min())
#         global_ymax = max(global_ymax, y.max())
#         y_ticks = np.linspace(global_ymin, global_ymax, 3)
#         axes[j].plot(x, y)
#         axes[j].set_title(f"{out}: {feature}")
#         axes[j].set_xlabel(feature)
#         #axes[j].set_ylabel(out)
#         axes[j].set_ylim(global_ymin, global_ymax)
#         axes[j].set_yticks(y_ticks)
#         axes[j].grid()
#     for k in range(j + 1, len(axes)):
#         axes[k].set_visible(False)

#     plt.tight_layout()
#     plt.show()



