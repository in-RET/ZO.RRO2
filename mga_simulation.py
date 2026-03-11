# -*- coding: utf-8 -*-
"""
Created on Tue Feb 17 11:29:10 2026

@author: rbala

Modelling to Generate Alternatives
"""
from pyomo.environ import Expression, Objective, Constraint, maximize, value
from oemof import solph
from energymodels.Basic_example_zorro_1 import Basisszenario_1 as BS_1
from src.preprocessing.constraints import CO2_limit, BiogasBestand_limit, BiogasNeuanlagen_limit,Biomasse_limit, Bilanziell_erneuerbar, GuD_time, import_export_bilanz
import logging
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
start_time = datetime.now()

def run_mga(direction_labels,
            slack: int,
            solver:str,
            gap:int,
            ):
    logging.info("MGA Simulation started")
    years = [2045]
    variations = ['BS0006']
    Anteilig_erneuerbar = True
    model_name="Basic_example_zorro_1"
    
     
    permutations = [str(x) + "_" + y for x in years for y in variations]
    for permutation in permutations:
        logging.info(f"Solve %s", permutation)
        logging.info("Building the energy system")
        YEAR, model_ID = permutation.split("_")
        YEAR = int(YEAR)
    
        energysystem,sim_data = BS_1(permutation)
        model = solph.Model(energysystem)
        logging.info("Applying model constraints")
        if Anteilig_erneuerbar:
           if YEAR <= 2030:
               Bilanziell_erneuerbar(model, sim_data, model_name, factor = 0.55)
           else:
               # Bilanziell_erneuerbar(model, sim_data, model_name, factor =1)
               import_export_bilanz(model, "import_bilanz", "export_bilanz")
        else:
            logging.info("NICHT Bilanziell erneuerbar")
        
        CO2_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['CO2_Grenze_'+str(YEAR)] )
        BiogasBestand_limit(model, limit = sim_data['Parameter']['Parameter_biogas_upgrading_plant']['potential'][model_ID])
        BiogasNeuanlagen_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['Biomasse_sub_tot'])
        Biomasse_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['Holzpotential_tot'])
        GuD_time(model, limit = 0, Starttime = 1777, Endtime= 7656)
        
        model.solve(
            solver=solver,
            cmdline_options={"MIPGap": gap},
            solve_kwargs={"tee": False},
        )
        
        C_opt = value(model.objective)
        baseline_shares = get_energy_shares(model, MGA_group)
        # Rebuild Model for MGA optimization
        model = solph.Model(energysystem)
        
        logging.info("Applying model constraints")
        if Anteilig_erneuerbar:
           if YEAR <= 2030:
               Bilanziell_erneuerbar(model, sim_data, model_name, factor = 0.55)
           else:
               # Bilanziell_erneuerbar(model, sim_data, model_name, factor =1)
               import_export_bilanz(model, "import_bilanz", "export_bilanz")
        else:
            logging.info("NICHT Bilanziell erneuerbar")
        
        CO2_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['CO2_Grenze_'+str(YEAR)] )
        BiogasBestand_limit(model, limit = sim_data['Parameter']['Parameter_biogas_upgrading_plant']['potential'][model_ID])
        BiogasNeuanlagen_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['Biomasse_sub_tot'])
        Biomasse_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['Holzpotential_tot'])
        GuD_time(model, limit = 0, Starttime = 1777, Endtime= 7656)
       
        model.cost_bound = Constraint(
                        expr = model.objective.expr <= C_opt * (1+ slack)
                        )
        
        def mga_expression_rule(m):
            expr = 0
            labels_lower = [lbl.lower() for lbl in direction_labels]
        
            for idx in m.flow:
                i = idx[0]
                o = idx[1]
                t = idx[2]
        
                label_in = str(i.label).lower()
                label_out = str(o.label).lower()
        
                if "__all__" in labels_lower or \
                   label_in in labels_lower or \
                   label_out in labels_lower:
        
                    if hasattr(m, "timeincrement"):
                        expr += m.flow[idx] * m.timeincrement[t]
                    else:
                        expr += m.flow[idx]
        
            return expr


        model.mga_direction = Expression(rule=mga_expression_rule)
        model.original_cost_expr = model.objective.expr
        model.del_component(model.objective)
        model.objective = Objective(
            expr = model.mga_direction,
            sense = maximize
            )
        
        model.solve(
            solver=solver,
            cmdline_options={"MIPGap": gap},
            solve_kwargs={"tee": False},
    )
        
        emissions = value(model.integral_limit_CO2_factor)
        cost = value(model.original_cost_expr)
        
        return {
        "model": model,
        "cost": cost,
        "emissions": emissions,
        "C_opt": C_opt,
        "baseline_shares": baseline_shares
    }

def extract_energy_by_label(model):
    """
    Returns:
        dict {label: total_energy}
    """
    energy = defaultdict(float)

    has_timeincrement = hasattr(model, "timeincrement")

    for idx in model.flow:
        i = idx[0]
        o = idx[1]
        t = idx[2]

        flow_val = value(model.flow[idx])

        if has_timeincrement:
            flow_val *= value(model.timeincrement[t])

        # attribute energy to source component
        label = str(i.label)
        energy[label] += flow_val

    return dict(energy)

def aggregate_energy_groups(energy_dict, group_dict):
    group_energy = {}

    for group, labels in group_dict.items():
        group_energy[group] = sum(
            energy_dict.get(label, 0.0)
            for label in labels
        )

    return group_energy

def compute_energy_shares(group_energy):
    total = sum(group_energy.values())

    if total == 0:
        return {k: 0 for k in group_energy}

    return {k: v / total for k, v in group_energy.items()}

def get_energy_shares(model, group_dict):
    energy = extract_energy_by_label(model)
    grouped = aggregate_energy_groups(energy, group_dict)
    shares = compute_energy_shares(grouped)
    return shares

#%%

MGA_group ={
   
        "renewable_electricity": ['Wind_north',
                                    'Wind_east', 
                                    'Wind_middle',
                                    'Wind_swest',
                                    'PV_rooftop_north',
                                    'PV_rooftop_east',
                                    'PV_rooftop_middle',
                                    'PV_rooftop_swest',
                                    'PV_open_north',
                                    'PV_open_east',
                                    'PV_open_middle',
                                    'PV_open_swest',
                                    'Hydro power plant',
                    ],
        
        "fossil_imports": ['Import_Electricity',
                           'Import_Gas',
                           'Import_Oil',
                           'Import_brown_coal'
                           ],
        
        "bioenergy_systems": ['Import_solid_fuel',
                              'Import_Wood',
                              'Biogas_feedin_existing',
                              'Biogas_feedin_new',
                              'Biogas- BHKW',
                              'Biomasse_elec',
                              'Biomasse_heat',
                              'Biomasse_elec_heat',
                              'BtL_Holz',
                              'BtL_substrat',
                              'BioTransformer'
                              ],
        
        "hydrogen_system":['Import_Hydrogen',
                           'Export_Hydrogen',
                           'Fuelcell',
                           'Electrolysis',
                           'Methanisation',
                           'PtL',
                           'H2_storage'
                           ],
        
        # "heat_generation": ['ST',
        #                     'UW', 
        #                     'AW', 
        #                     'Umgebungsluft',
        #                     'Heatpump_air',
        #                     'Heatpump_water',
        #                     'Heatpump_recovery_heat',
        #                     'Electric boiler',
        #                     'Preheater- WP',
        #                     'Preheater- Electric boiler'
        #                     ],
        
        # "electricity_storage":['Battery',
        #                        'Li-Ion_Battery',
        #                        'Natrium_Battery',
        #                        'Red-OX_Battery'
        #                        ],
        
        # "pumped'_hydro": ['Pumped_hydro_technology',
        #                   'Pumped_hydro_storage',
        #                   'Pumped_hydro_storage_bestand'
        #                   ],
        
        # "thermal_storage": ['Heat storage_dist_heat',
        #                     'Heat storage_seasonal'
        #                     ],
    
        # "Gas": ['GuD', 
        #         'Gas_storage',
        #             ],
        
        # "Electricity_grid": ['Hös<->HS',
        #                      'Grid_losses',
        #                      'Export_Electricity'],
       
        # --- Total infrastructure (all investments) ---
        # "total_capacity": ["__ALL__"]
    }
mga_results = {}
all_shares= {}
for name, labels in MGA_group.items():
    result = run_mga(direction_labels = labels, 
                     slack = 0.1,
                     solver = 'gurobi',
                     gap= 0.0)
    shares = get_energy_shares(result['model'], MGA_group)
    mga_results[name]= result
    all_shares[name]= shares
end_time = datetime.now()
print('Execution time: {}'.format(end_time - start_time))



#%%

data = {
        name: res["cost"]
        for name, res in mga_results.items()
    }

df = pd.Series(data).sort_values(ascending=False)

plt.figure()
df.plot(kind="bar")
plt.ylabel("MGA objective value")
plt.title("MGA technology flexibility")
plt.xticks(rotation=45, ha="right")
plt.tight_layout()
plt.show()


costs = [res["cost"] for res in mga_results.values()]
emissions = [res["emissions"] for res in mga_results.values()]
labels = list(mga_results.keys())

plt.figure()
plt.scatter(costs, emissions)

for x, y, label in zip(costs, emissions, labels):
    plt.text(x, y, label)

plt.xlabel("MGA objective")
plt.ylabel("CO₂ emissions")
plt.title("MGA solution space")
plt.show()

labels = list(mga_results.keys())
values = [res["cost"] for res in mga_results.values()]

angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
values = np.concatenate((values, [values[0]]))
angles = np.concatenate((angles, [angles[0]]))

fig = plt.figure()
ax = fig.add_subplot(111, polar=True)
ax.plot(angles, values)
ax.fill(angles, values, alpha=0.25)

ax.set_xticks(angles[:-1])
ax.set_xticklabels(labels)

plt.title("MGA flexibility radar")
plt.show()

share_comparison = {
    "cost_opt": result["baseline_shares"],
    **{name: get_energy_shares(res["model"], MGA_group)
       for name, res in mga_results.items()}
}
