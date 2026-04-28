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
save_dir_morris = os.path.join(workdir,'dumps', 'SALIB', f'results_morris_{len(result_morris)}.joblib')
output_morris, analyse_morris, result_morris, output_names, problem = joblib.load(save_dir_morris)
# Read MC results
save_dir_mc = os.path.join(workdir,'dumps', 'SALIB', f'results_mc_{len(result_mc)}.joblib')
output_mc, result_mc, problem = joblib.load(save_dir_mc)


#%% Morris


for j, out in enumerate(output_names):
    Si = analyse_morris[j]
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

# Trendmultiplot
for j, out in enumerate(output_names):
    n_cols = 3
    n_rows = math.ceil(len(problem['names']) / n_cols)
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows),sharey=True)
    axes = axes.flatten()
    
    for i, col in enumerate(problem['names']):
        ax = axes[i]
    
        ax.scatter(result_morris[col], result_morris[out])
    
        z = np.polyfit(result_morris[col], result_morris[out], 1)
        p = np.poly1d(z)
        ax.plot(result_morris[col], p(result_morris[col]))
    
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
corr_matrix = result_morris.corr()

labels = result_morris.columns.tolist()
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