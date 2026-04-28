# -*- coding: utf-8 -*-
"""
Created on Thu Apr  9 11:49:41 2026

@author: rbala

ZORRO Abschluss Konferenz

Thema: " Wie viel EE braucht Thüringen und woher wissen wir das?"

"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import math
# SALib implementation (Ein Versuch)
from SALib.sample.morris import sample
from SALib.analyze.morris import analyze

from src.models.solve_model import solveModels
import energymodels.Basic_example_zorro_1 as be
import src.preprocessing.files as file_module
import seaborn as sns
from adjustText import adjust_text

# PROBLEM DEFINITION (SALib)
model_ID = 'BS0006'
year = 2045
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

#%%
problem = {
        'num_vars': len(param_config),
        'names': list(param_config.keys()),
        'bounds': [param_config[k] for k in param_config]

}

# Input data Modification
CURRENT_PARAMS = {}
original_read = file_module.read_input_files

def patched_read_input_files(folder_name, sub_folder_name=None):
    data = original_read(folder_name, sub_folder_name)
    print('Patch active')
    
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

file_module.read_input_files = patched_read_input_files
be.read_input_files = patched_read_input_files

#KPI

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

#%% MORRIS Method (SALib)

param_values = sample(problem, N=1, num_levels=4)
Y = []
costs = {}
for i, X in enumerate(param_values):

    CURRENT_PARAMS = dict(zip(problem["names"], X))
    print(f"Morris Run {i+1}/{len(param_values)}")
    
    sim_data, cost, result = solveModels(
        variations=[model_ID],
        scenario_num="SALIB",
        years=[year], 
        model_name= model_name,
        solver="gurobi",
        Anteilig_erneuerbar = True,
        hypothese="Morris",
        sim_remarks=str(CURRENT_PARAMS),
        solver_output=False
    )
    costs[f'Run_{i}'] = cost[["investment costs", "variable costs", "profits"]].sum().sum()
    
    df_out = extract_RES(result)
    Y.append(df_out.iloc[0].values)

Y = np.array(Y)
output_names = df_out.columns.tolist()
#%%
Si_list=[]
for j, out in enumerate(output_names):
    Y_single = Y[:, j]
    Si = analyze(problem, param_values, Y_single)
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

#%%
df = pd.DataFrame(param_values[:len(Y)], columns=problem['names'])

# Trendmultiplot
for j, out in enumerate(output_names):

    df[out] = Y[:, j]
    n_cols = 3
    n_rows = math.ceil(len(problem['names']) / n_cols)
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows),sharey=True)
    axes = axes.flatten()

    for i, col in enumerate(problem['names']):
        ax = axes[i]

        ax.scatter(df[col], df[out])

        z = np.polyfit(df[col], df[out], 1)
        p = np.poly1d(z)
        ax.plot(df[col], p(df[col]))

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
corr_matrix = df.corr()

labels = df.columns.tolist()
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


#%%
#----------------------------------------------------------------------------------------------------
#################                Monte Carlo                     ###################################
#----------------------------------------------------------------------------------------------------

def sample_mc(param_config, N):
    samples = []
    for _ in range(N):
        row = []
        for p in param_config.values():
            low, high = p[0],p[1] 
            row.append(np.random.uniform(low, high))
        samples.append(row)
    return np.array(samples)

MC_runs = 10
mc_results =[]
costs_MC ={}
param_values_mc = sample_mc(param_config, MC_runs)

for i, X in enumerate(param_values_mc):

    CURRENT_PARAMS = dict(zip(problem["names"], X))
    print(f"MC Run {i+1}/{MC_runs}")
    
    sim_data, cost, result = solveModels(
        variations=[model_ID],
        scenario_num="MC",
        years=[year], 
        model_name= model_name,
        solver="gurobi",
        Anteilig_erneuerbar = True,
        hypothese="Surface Monte Carlo",
        sim_remarks=str(CURRENT_PARAMS),
        solver_output=False
    )
    costs_MC[f'Run_{i}'] = cost[["investment costs", "variable costs", "profits"]].sum().sum()
    df_out_mc = extract_RES(result)
    row = {**CURRENT_PARAMS}
    for col in output_names:
        row[col] = df_out_mc.iloc[0][col]
    mc_results.append(row)

df_MC = pd.DataFrame(mc_results)

for j, out in enumerate(output_names):
    
    Si = Si_list[j]
    df_sens = pd.DataFrame({
        "parameter": problem["names"],
        "mu_star": Si["mu_star"],
    })

    top2 = df_sens.sort_values("mu_star", ascending=False)["parameter"].values[:2]

    x = df_MC[top2[0]]
    y = df_MC[top2[1]]
    z = df_MC[out]

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

#%%

