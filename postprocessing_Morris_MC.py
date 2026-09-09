# -*- coding: utf-8 -*-
"""
Created on Tue Apr 28 10:26:09 2026

@author: rbala

Auswertung Morris und Monte Carlo
"""
import joblib
import os
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import partial_dependence
from adjustText import adjust_text
from scipy.interpolate import griddata
import seaborn as sns
workdir = os.getcwd()

# Read Morris results
save_dir_morris = os.path.join(workdir,'dumps', 'SALIB', f'results_morris_1400.joblib')
output_morris, analyse_morris, result_morris, output_names, problem = joblib.load(save_dir_morris)
#Read MC results
save_dir_mc = os.path.join(workdir,'dumps', 'SALIB', f'results_mc_1400.joblib')
output_mc, result_mc, problem_mc = joblib.load(save_dir_mc)
# result_mc = pd.read_csv(os.path.join(save_dir_mc,'Result_mc_14.csv'), sep = ';', decimal =',', index_col= 0)


# =========================================================
# STYLE
# =========================================================
sns.set_theme(style="whitegrid", context="talk")

parameter_groups = {
    "Renewables": [
        "wind_flh",
        "pv_flh",
        "potential_wind",
        "potential_pv",
        "potential_biomasse"
    ],

    "Storage": [
        "capex_batterie",
        "capex_heat_storage"
    ],

    "Imports": [
        "import_biomasse",
        "import_H2/fuel",
        "import_electricity_price"
    ],

    "Demand": [
        "demand_HH_waerme",
        "person_mob"
    ],

    "Other": [
        "capex_PtL/BtL",  
    ]
}

group_colors = {
    "Renewables": "#1f77b4",
    "Storage": "#ff7f0e",
    "Imports": "#d62728",
    "Demand": "#2ca02c",
    "Other": "#9467bd"
}
figure_bg_color = '#159A3433'
axes_bg_color   = '#159A3400'

plt.rcParams['figure.facecolor'] = figure_bg_color
#plt.rcParams['axes.facecolor'] = axes_bg_color
plt.rcParams['savefig.facecolor'] = figure_bg_color
#plt.rcParams['legend.facecolor'] = axes_bg_color
plt.rcParams['legend.framealpha'] = 0

def get_group_and_color(param):

    for group, params in parameter_groups.items():
        if param in params:
            return group, group_colors[group]

    return "Other", "gray"

# TORNADO PLOTS

for j, out in enumerate(output_names):
    Si = analyse_morris[j]
    df_sens = pd.DataFrame({
        "parameter": problem["names"],
        "mu_star": Si["mu_star"],
        "sigma": Si["sigma"]
    })

    # normalize
    df_sens["normalized"] = (
        df_sens["mu_star"] /
        df_sens["mu_star"].max()
    ) * 100

    df_sens["group"] = df_sens["parameter"].apply(lambda x: get_group_and_color(x)[0])
    df_sens["color"] = df_sens["parameter"].apply(lambda x: get_group_and_color(x)[1])

    df_sens = df_sens.sort_values("normalized")

    plt.figure(figsize=(10, 7))
    
    plt.barh(df_sens["parameter"],df_sens["normalized"],color=df_sens["color"])
    plt.xlabel(f"Normalized influence on {out} (%)")
    plt.ylabel("")
    plt.title(f"Morris Tornado Plot — {out}")
    plt.grid(axis="x", alpha=0.3)

    handles = []
    for group, color in group_colors.items():
        handles.append(plt.Line2D(
                                    [0],
                                    [0],
                                    color=color,
                                    lw=8,
                                    label=group
                                    )
            )
    plt.legend(
                handles=handles,
                bbox_to_anchor=(1.02, 1),
                loc="upper left"
    )

    plt.tight_layout()
    
    plt.show()

# Parameter plot Morris
    # Normalize sigma for bubble size
    size = (Si["sigma"] / np.max(Si["sigma"])) * 1800
    colors = []

    for param in problem["names"]:
        _, color = get_group_and_color(param)
        colors.append(color)

    plt.figure(figsize=(11, 8))
    plt.scatter(
            Si["mu"],
            Si["mu_star"],
            s=size,
            c=colors,
            alpha=0.75,
            edgecolors="black",
            linewidths=0.8
            )

    texts = []
    for i, name in enumerate(problem["names"]):
        texts.append(plt.text(
                            Si["mu"][i],
                            Si["mu_star"][i],
                            name,
                            fontsize=10
                            )
                    )

    adjust_text(texts,arrowprops=dict(arrowstyle="->", color="gray", lw=0.8))

    plt.axvline(0,color="black",linewidth=1)
    plt.axhline(np.mean(Si["mu_star"]),linestyle="--", color="gray",linewidth=1.5,label="Mean μ*")
    plt.xlabel("μ")
    plt.ylabel("μ*")
    plt.title(f"Morris Sensitivity — {out}")
    plt.grid(alpha=0.3)
    handles = []
    for group, color in group_colors.items():
        handles.append(plt.Line2D(
                                    [0],
                                    [0],
                                    marker='o',
                                    color='w',
                                    label=group,
                                    markerfacecolor=color,
                                    markersize=12
                                    )
                        )
    plt.legend(handles=handles, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.show()
    
# Trendmultiplot
    n_cols = 3
    n_rows = math.ceil(len(problem['names']) / n_cols)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows), sharey=True)
    axes = axes.flatten()

    for i, col in enumerate(problem['names']):
        ax = axes[i]
        _, color = get_group_and_color(col)

        ax.scatter(result_morris[col], result_morris[out], alpha=0.6, color=color)
        # regression
        z = np.polyfit(result_morris[col], result_morris[out], 1)
        p = np.poly1d(z)
        ax.plot(result_morris[col], p(result_morris[col]),linewidth=2)
        ax.set_title(col)
        ax.set_xlabel("Scaling factor")
        ax.set_ylabel(out)
        ax.grid(alpha=0.3)

    # remove empty axes
    for k in range(len(problem['names']),len(axes)):
        fig.delaxes(axes[k])

    plt.suptitle(f"Parameter Trends — {out}", fontsize=18,y=0.99)
    plt.tight_layout()
    plt.show()

# Heat plot all combined
heatmap_df = pd.DataFrame(index=problem["names"])

for j, out in enumerate(output_names):

    Si = analyse_morris[j]
    normalized = (Si["mu_star"] / np.max(Si["mu_star"])) * 100
    heatmap_df[out] = normalized
heatmap_df["mean"] = heatmap_df.mean(axis=1)
heatmap_df = heatmap_df.sort_values("mean", ascending=False)
heatmap_df = heatmap_df.drop(columns="mean")

plt.figure(figsize=(12, 8))
sns.heatmap(
        heatmap_df,
        cmap="viridis",
        annot=True,
        fmt=".1f",
        linewidths=0.5,
        cbar_kws={
            "label": "Normalized μ* (%)"
            }
        )
plt.title("Morris Sensitivity Summary")
plt.xlabel("Analysed Outputs")
plt.ylabel("Parameters")
plt.tight_layout()
plt.show()

#Correlation matrix
input_cols = problem["names"]
output_cols = output_names
corr_matrix = result_morris.corr()
corr_io = corr_matrix.loc[input_cols, output_cols]

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(corr_io,
            annot=True,
            cmap="coolwarm",
            center=0,
            fmt=".2f",
            linewidths=0.5,
            cbar_kws={"label": "Correlation"},
            ax=ax
            )

ax.set_title("Input–Output Correlation Matrix",
             fontsize=18,
             fontweight='bold'
             )
ax.set_xlabel("Outputs")
ax.set_ylabel("Input Parameters")
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()


#%% Post analysis


# -------------------------------
# 2D RESPONSE SURFACE
# -------------------------------
for j, out in enumerate(output_names):
    Si = analyse_morris[j]
    df_sens = pd.DataFrame({
        "parameter": problem["names"],
        "mu_star": Si["mu_star"],
    })

    top2 = df_sens.sort_values("mu_star", ascending=False)["parameter"].values[:2]

    x = result_mc[top2[0]]
    y = result_mc[top2[1]]
    z = result_mc[out]

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
    
# -------------------------
# All Histograms + Importances #understand uncertainity (Histogram)
# -------------------------

n_outputs = len(output_names)
fig, axes = plt.subplots(n_outputs, 2, figsize=(14, 5 * n_outputs))

if n_outputs == 1:
    axes = [axes]

models = {}

for i, out in enumerate(output_names):
    # Correlation
    corr = result_mc[problem["names"] + [out]].corr()[out].drop(out)
    print(f"\n{out}")
    print(corr.sort_values())

    # Train model
    model = RandomForestRegressor()
    model.fit(result_mc[problem["names"]], result_mc[out])
    models[out] = model

    # Histogram
    result_mc[out].hist(bins=20, ax=axes[i][0])
    axes[i][0].set_title(f"{out} Histogram")

    # Feature Importance
    importance = pd.Series(model.feature_importances_, index=problem["names"])
    importance.sort_values().plot(kind="barh", ax=axes[i][1])
    axes[i][1].set_title(f"{out} Feature Importance")

plt.tight_layout()
plt.show()
# -------------------------
# PDP for each output
# -------------------------
for out in output_names:
    model = models[out]

    n_features = len(problem["names"])
    n_cols = 3
    n_rows = math.ceil(n_features / n_cols)

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 5 * n_rows))
    axes = axes.flatten()
    global_ymin = float("inf")
    global_ymax = float("-inf")
    for j, feature in enumerate(problem["names"]):
        pd_result = partial_dependence(
            model,
            result_mc[problem["names"]],
            [feature]
        )

        x = pd_result["grid_values"][0]
        y = pd_result["average"][0]
        global_ymin = min(global_ymin, y.min())
        global_ymax = max(global_ymax, y.max())
        y_ticks = np.linspace(global_ymin, global_ymax, 3)
        axes[j].plot(x, y)
        axes[j].set_title(f"{out}: {feature}")
        axes[j].set_xlabel(feature)
        #axes[j].set_ylabel(out)
        axes[j].set_ylim(global_ymin, global_ymax)
        axes[j].set_yticks(y_ticks)
        axes[j].grid()
    for k in range(j + 1, len(axes)):
        axes[k].set_visible(False)

    plt.tight_layout()
    plt.show()
    
#%%
importance_df=pd.DataFrame(index=problem["names"])

for out in output_names:

    model=models[out]

    importance_df[out]=model.feature_importances_
importance_df["mean"] = importance_df.mean(axis=1)
importance_df=importance_df.sort_values(
    by='mean',
    ascending=False
)*100

plt.figure(figsize=(10,8))

sns.heatmap(
    importance_df,
    cmap='viridis',
    annot=True
)

plt.title(
    "Feature importance across outputs"
)

plt.xlabel("Outputs")
plt.ylabel("Parameters")

plt.show()

#%% PDP detalliet

# from sklearn.inspection import PartialDependenceDisplay

# for out in output_names:

#     model=models[out]

#     fig,ax=plt.subplots(
#         figsize=(12,8)
#     )

#     PartialDependenceDisplay.from_estimator(
#         model,
#         result_mc[problem["names"]],
#         features=problem["names"][:],
#         kind="both",
#         ax=ax
#     )

#     plt.suptitle(out)
#     plt.tight_layout()
#     plt.show()
    
#%%

# Bilder für Präsentation


def translate_param(param_name):
    """Übersetzt englische Parameternamen ins Deutsche"""
    translations = {
        # Renewables
        "wind_flh": "Volllaststunden Wind",
        "pv_flh": "Volllaststunden PV", 
        "potential_wind": "Windpotenzial (Flächenkulisse)",
        "potential_pv": "PV-Potenzial (Flächenkulisse)",
        "potential_biomasse": "Biomassepotenzial",
        
        # Storage
        "capex_batterie": "Investitionskosten Batteriespeicher",
        "capex_heat_storage": "Investitionskosten Wärmespeicher",
        
        # Imports
        "import_biomasse": "Importpreis Biomasse",
        "import_H2/fuel": "Importpreis H2 / synth. Kraftstoff",
        "import_electricity_price": "Strom-Importpreis",
        
        # Demand
        "demand_HH_waerme": "Wärmebedarf Haushalt",
        "person_mob": "Personenmobilität (Verkehrsnachfrage)",
        
        # Other
        "capex_PtL/BtL": "Investitionskosten PtL/BtL",
    }
    return translations.get(param_name, param_name)

problem_names_de = [translate_param(p) for p in problem["names"]]

def create_evidence_chain(analyse_morris, problem, output_names, result_mc, models, plot_para):
   
    output_mapping = {
        'Optimierte Wind-Leistung': 'wind',
        'Optimierte PV-Leistung': 'pv',
        'Optimierte Stromspeicher-Kapazität': 'stromspeicher',
        'Optimierte Wärmespeicher-Kapazität': 'waermespeicher',
        'Gesamtsystemkosten': 'cost'
        }

    cost_outputs ='cost'
    target_output = output_mapping.get(plot_para, output_names[0])
    if target_output in output_names:
        index = output_names.index(target_output)
    else:
        print(f"Warnung: {target_output} nicht gefunden. Verwende ersten Output.")
        index = 0
        
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # MORRIS PLOT: Kritische Parameter
    ax1 = axes[0]
    parameter_de = [translate_param(p) for p in problem["names"]]

    df_temp = pd.DataFrame({
        'Parameter_de': parameter_de,
        'Parameter_orig': problem["names"],
        'mu_star': analyse_morris[index]['mu_star'],
        'mu_star_conf': analyse_morris[index]['mu_star_conf']
        })
    df_temp = df_temp.sort_values('mu_star', ascending=True)

    # Farben: Top 3 rot, Rest orange
    colors = [
        '#d62728' if i >= len(df_temp) - 3 else '#ff7f0e'
        for i in range(len(df_temp))
    ]
    
    ax1.barh(
        df_temp['Parameter_de'],
        df_temp['mu_star'],
        xerr=df_temp['mu_star_conf'],
        color=colors,
        capsize=3,
        error_kw={
            'elinewidth': 1.2,
            'ecolor': 'black'
        }
    )
    
    ax1.set_xlabel('Einflussstärke (μ*)', fontsize=12)
    ax1.set_title(
        f'1. KRITISCHE PARAMETER\nFür {plot_para.upper()}',
        fontsize=12,
        fontweight='bold'
    )
    
    ax1.tick_params(axis='y', labelsize=12)
    ax1.grid(axis='x', alpha=0.3)
    
    # PDP PLOT: Wie wirken die Top 2 Parameter?

    ax2 = axes[1]
    
    top2_params = df_temp.nlargest(3, 'mu_star')['Parameter_orig'].values
    
    # Farben für die Linien
    pdp_colors = ['#d62728', '#1f77b4', '#8b5a2b']
    
    for i, param in enumerate(top2_params):
        if output_names[index] in models:
            model = models[output_names[index]]
            
            pd_result = partial_dependence(
                model,
                result_mc[problem["names"]],
                [param]
            )
            
            x = pd_result['grid_values'][0]
            y = pd_result['average'][0]
            
            if 'cost' in target_output.lower():
                y = y / 1_000_000 
            
            param_de = translate_param(param)
            ax2.plot(x, y, color=pdp_colors[i], linewidth=3, label=param_de)
            
            # 95% Konfidenzintervall
            if 'values' in pd_result and len(pd_result['values']) > 1:
                y_lower = np.percentile(pd_result['values'][0], 2.5, axis=0)
                y_upper = np.percentile(pd_result['values'][0], 97.5, axis=0)
                if 'cost' in target_output.lower():
                    y_lower = y_lower / 1_000_000
                    y_upper = y_upper / 1_000_000
                ax2.fill_between(x, y_lower, y_upper, alpha=0.2, color=pdp_colors[i])
    
    # Referenzlinien für heute und Ziel (passen Sie Werte an)
    median_wert = result_mc[output_names[index]].median()
    mean_wert = result_mc[output_names[index]].mean()
    if 'cost' in target_output.lower():
        median_wert = median_wert / 1_000_000
        mean_wert = mean_wert / 1_000_000
        einheit = "Mio. €"
    elif "leistung" in plot_para.lower():
        einheit = "MW" 
    elif "kapazität" in plot_para.lower():
        einheit = "MWh"
    else:
        einheit = ""
    
    ax2.axhline(y=median_wert, color='gray', linestyle='--', 
                label=f'Median (1400 Sim.): {median_wert:.1f} {einheit}', alpha=0.7)
    ax2.axhline(y=mean_wert, color='green', linestyle='--', 
                label=f'Mittelwert: {mean_wert:.1f} {einheit}', linewidth=2, alpha=0.7)
    
    ax2.set_xlabel('Skalierungsfaktor (1 = Basiswert)', fontsize=12)
    ax2.set_ylabel(f'{plot_para} in {einheit}', fontsize=12)
    ax2.set_title('2. WIE PARAMETER WIRKEN\nPartielle Abhängigkeit (PDP)', fontsize=12, fontweight='bold')
    ax2.legend(loc='best', fontsize=9)
    num_xticks_plot2 = 7  
    x_ticks = np.linspace(x.min(), x.max(), num_xticks_plot2)
    ax2.set_xticks(x_ticks)
    ax2.set_xticklabels([f'{x:.2f}' for x in x_ticks], rotation=45, ha='right')
    ax2.grid(alpha=0.3)
    
    # UNSICHERHEIT: Monte Carlo Verteilung
    ax3 = axes[2]
    
    mc_results = result_mc[output_names[index]].values
    n_sims = len(mc_results)
    
    if 'cost' in target_output.lower():
        mc_results = mc_results / 1_000_000
        einheit_y = "Mio. €"
        x_label = f'{plot_para} in Mio. €'
    elif "leistung" in plot_para.lower():
        einheit_y = "MW" 
        x_label = f'{plot_para} in {einheit_y}' if einheit_y else plot_para
    elif "kapazität" in plot_para.lower():
        einheit_y = "MWh"
        x_label = f'{plot_para} in {einheit_y}' if einheit_y else plot_para
    else:
        einheit_y = ""
        x_label = f'{plot_para} in {einheit_y}' if einheit_y else plot_para
    
    
    # Histogramm
    ax3.hist(mc_results, bins=20, color='#2ca02c', alpha=0.7, edgecolor='black', density=False)
    
    # Statistiken
    mean_val = np.mean(mc_results)
    median_val = np.median(mc_results)
    p5, p95 = np.percentile(mc_results, [5, 95])
    
    # Linien für Mittelwert und Perzentile
    ax3.axvline(x=mean_val, color='red', linestyle='--', linewidth=2, 
                label=f'Mittelwert: {mean_val:.1f}')
    ax3.axvline(x=median_val, color='blue', linestyle=':', linewidth=2, 
                label=f'Median: {median_val:.1f}')
    ax3.axvline(x=p5, color='orange', linestyle=':', linewidth=1.5, alpha=0.7)
    ax3.axvline(x=p95, color='orange', linestyle=':', linewidth=1.5, alpha=0.7, 
                label=f'90% KI: {p5:.1f} - {p95:.1f}')
    
    ax3.fill_betweenx([0, ax3.get_ylim()[1]], p5, p95, alpha=0.2, color='orange')
    
    
    ax3.set_xlabel(x_label, fontsize=11)
    ax3.set_ylabel('Anzahl der Simulationen', fontsize=12)
    ax3.set_title(f'3. UNSICHERHEIT\n{plot_para}\naus 1.400 Simulationen', fontsize=12, fontweight='bold')
    ax3.legend(loc='best', fontsize=8)
    num_xticks_plot3 = 7
    x_ticks_hist = np.linspace(mc_results.min(), mc_results.max(), num_xticks_plot3)
    ax3.set_xticks(x_ticks_hist)
    ax3.set_xticklabels([f'{x:.0f}' for x in x_ticks_hist], rotation=45, ha='right')
    ax3.grid(alpha=0.3)
    
    # Gesamttitel
    plt.suptitle(f'BEWEISKETTE: Analyse für {plot_para}', 
                fontsize=16, fontweight='bold')#, y=1.02)
    plt.tight_layout()
    plt.show()
     
    return df_temp, mc_results


for parameter in ['Optimierte Wind-Leistung', 'Optimierte PV-Leistung', 
                  'Optimierte Stromspeicher-Kapazität', 'Optimierte Wärmespeicher-Kapazität', 
                  'Gesamtsystemkosten']:

    df_top, mc_dist = create_evidence_chain(
                                            analyse_morris=analyse_morris,
                                            problem=problem,
                                            output_names=output_names,
                                            result_mc=result_mc,
                                            models=models,  
                                            plot_para=parameter
                                )
