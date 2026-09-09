# -*- coding: utf-8 -*-
"""
Created on Fri Jul  3 09:01:06 2026

@author: rbala

System Resilienz with Technology inclusion/exclusion and near optimal analysis.
"""

from pyomo.environ import Expression, Objective, Constraint, maximize, value
from oemof import solph
import copy
import os
import numpy as np
import logging

from src.preprocessing.constraints import CO2_limit, BiogasBestand_limit, BiogasNeuanlagen_limit,Biomasse_limit, Bilanziell_erneuerbar, GuD_time, import_export_bilanz

#Basis scenario
def solve_BS(energysystem, constraints_fn, solver, gap):
    model = solph.Model(energysystem)

    constraints_fn(model)

    model.solve(
        solver=solver,
        cmdline_options={"MIPGap": gap},
        solve_kwargs={"tee": False},
    )

    return model


def apply_exclusions(model, excluded_labels):
    """
    Excludes technologies by forcing their flows to zero.
    
    """
    for (key, flow_var) in model.flow.items():

        i = key[0]
        o = key[1]
        t = key[2]

        label_in = str(i.label)
        label_out = str(o.label)

        if label_in in excluded_labels or label_out in excluded_labels:
            flow_var.fix(0.0)

    return model

def apply_constraints(model, sim_data, model_name, YEAR, model_ID):
    
    if YEAR <= 2030:
        Bilanziell_erneuerbar(model, sim_data, model_name, factor = 0.55)
    else:
        # Bilanziell_erneuerbar(model, sim_data, model_name, factor =1)
        import_export_bilanz(model, "import_bilanz", "export_bilanz")

    CO2_limit(model, limit=sim_data['Parameter']['System_configurations_2024']['System']['CO2_Grenze_'+str(YEAR)])
    BiogasBestand_limit(model, limit=sim_data['Parameter']['Parameter_biogas_upgrading_plant']['potential'][model_ID])
    BiogasNeuanlagen_limit(model, limit=sim_data['Parameter']['System_configurations_2024']['System']['Biomasse_sub_tot'])
    Biomasse_limit(model, limit=sim_data['Parameter']['System_configurations_2024']['System']['Holzpotential_tot'])
    GuD_time(model, limit=0, Starttime=1777, Endtime=7656)

    return model

def solve_scenario(energysystem, sim_data, YEAR, model_ID,
                   solver, gap, excluded=None):

    model = solph.Model(energysystem)
    model = apply_constraints(model, sim_data, "model", YEAR, model_ID)

    if excluded:
        model = apply_exclusions(model, excluded)

    model.solve(
        solver=solver,
        cmdline_options={"MIPGap": gap},
        solve_kwargs={"tee": False},
    )

    return model

def extract_metrics(model):
    return {
        "cost": value(model.objective),
        "co2": value(getattr(model, "integral_limit_CO2_factor", 0)),
    }

def run_mga(model, direction_labels, slack, solver, gap):

    C_opt = value(model.objective)
    
    import copy
    #mga_model = model
    cost_bound = C_opt * (1 + slack)
   
    model.cost_constraint = Constraint(
        expr= model.objective.expr <= cost_bound
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
                   
               if hasattr(i, 'investment') and hasattr(i.investment, 'capacity'):
                   expr += i.investment.capacity
               else:
                   if hasattr(m, "timeincrement"):
                       expr += m.flow[idx] * m.timeincrement[t]
                   else:
                       expr += m.flow[idx]
    
        return expr
    
    model.del_component('objective')
    model.objective = Objective(rule= mga_expression_rule, sense=maximize)

    model.solve(
        solver=solver,
        cmdline_options={"MIPGap": gap},
        solve_kwargs={"tee": False},
    )
    
    
    return model

def solve_and_store(energysystem, model, model_name, permutation, scenario_name, DUMP_PATH):

    energysystem.results["main"] = solph.processing.results(model)

    energysystem.dump(
        dpath=DUMP_PATH,
        filename=f"{model_name}_{permutation}_{scenario_name}.dump"
    )

def run_full_analysis(direction_groups, exclusions_list, slack, solver, gap, DUMP_PATH):
    from energymodels.Basic_example_zorro_1 import Basisszenario_1 as BS_1
    results_summary = {}

    YEARS = [2045]
    VARIATIONS = ["BS0006"]
    scenario_counter = 0
    for YEAR in YEARS:
        for VAR in VARIATIONS:

            permutation = f"{YEAR}_{VAR}"

            energysystem, sim_data = BS_1(permutation)
            model_name = "Basic_example_zorro_1"
            YEAR_int = int(YEAR)
            scenario_name = 'baseline'
            model_ID = VAR

            baseline_model = solve_scenario(
                energysystem,
                sim_data,
                YEAR_int,
                model_ID,
                solver,
                gap,
                excluded=None
            )
            
            solve_and_store(energysystem, baseline_model, model_name, permutation, scenario_name, DUMP_PATH)

            baseline_metrics = extract_metrics(baseline_model)

            results_summary["baseline"] = baseline_metrics

            
            for exclusion_name, excluded_techs in exclusions_list.items():

                logging.info(f"Running exclusion: {exclusion_name}")
                energysystem_copy, sim_data_copy = BS_1(permutation)

                model = solve_scenario(energysystem_copy, sim_data_copy, YEAR_int, model_ID, solver, gap, excluded=excluded_techs)
                solve_and_store(energysystem_copy, model, model_name, permutation, exclusion_name, DUMP_PATH)
                
                metrics = extract_metrics(model)

                results_summary[exclusion_name] = metrics
                
                scenario_counter += 1

                # try:
                #     for name, labels in direction_groups.items():
                        
                #         mga_model = run_mga(
                #             model=model,
                #             direction_labels=labels,
                #             slack=slack,
                #             solver=solver,
                #             gap=gap
                #         )
                                            
                #         solve_and_store(energysystem_copy, mga_model, "MGA_" + name+"_"+ model_name, permutation, exclusion_name, DUMP_PATH)
                        #results_summary[exclusion_name][f"MGA_{name}"] = value(mga_model.objective)
                # except Exception as e:
                #     logging.warning(f"MGA failed for {exclusion_name}: {e}")
                

    return results_summary

#%%

exclusions_list = {
    
    "wind_partial": [np.random.choice(["Wind_north", "Wind_east", "Wind_middle", "Wind_swest"])],
    
    "pv_partial": [np.random.choice(["PV_open_north", "PV_open_east"])],
    
    "no_hydro": ["Hydro power plant"],
    
    "import_partial": [np.random.choice(["Import_Electricity", "Import_Gas", "Import_Oil", "Import_Wood", "Import_solid_fuel", "Import_Synthetic_fuel"])],
    "no_biogas": ["Biogas_feedin_existing", "Biogas_feedin_new", "Biogas- BHKW"],
    "no_biofuels": ["BtL_Holz", "BtL_substrat"],
    
    "no_electrolysis": ["Electrolysis"],
    
     "no_PtL": ["PtL"],

     "no_battery": ["Battery", "Li-Ion_Battery", "Natrium_Battery", "Red-OX_Battery"],

     "no_heat_storage": ["Heat storage_dist_heat","Heat storage_seasonal"],
     "no_electric_boiler": ["Electric boiler","Preheater- Electric boiler"],
     "no_flexibility_options": ["Battery", "H2_storage", "Heat storage_seasonal"],
}


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
        
        "heat_generation": ['ST',
                            'UW', 
                            'AW', 
                            'Umgebungsluft',
                            'Heatpump_air',
                            'Heatpump_water',
                            'Heatpump_recovery_heat',
                            'Electric boiler',
                            'Preheater- WP',
                            'Preheater- Electric boiler'
                            ],
        
        "electricity_storage":['Battery',
                               'Li-Ion_Battery',
                               'Natrium_Battery',
                               'Red-OX_Battery'
                               ],
        
        "pumped_hydro": ['Pumped_hydro_technology',
                          'Pumped_hydro_storage',
                          'Pumped_hydro_storage_bestand'
                          ],
        
        "thermal_storage": ['Heat storage_dist_heat',
                            'Heat storage_seasonal'
                            ],
    
        "Gas": ['GuD', 
                'Gas_storage',
                    ],
        
        "Electricity_grid": ['Hös<->HS',
                             'Grid_losses',
                             'Export_Electricity'],
       
        # --- Total infrastructure (all investments) ---
        #"total_capacity": ["__all__"]
    }

DUMP_PATH = os.path.abspath(os.path.join(os.getcwd(), "dumps", "MGA"))
results = run_full_analysis(
    direction_groups=MGA_group,
    exclusions_list=exclusions_list,
    slack=0.1,
    solver="gurobi",
    gap=0.0,
    DUMP_PATH=DUMP_PATH
)