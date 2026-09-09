# -*- coding: utf-8 -*-
"""
Created on Thu Aug 13 13:25:08 2026

@author: rbala
"""
import numpy as np
import pandas as pd
from oemof import solph
from src.postprocessing.utils_dump import get_dump_file_path,load_results_from_dump
from energymodels.basic_example_zorro_1_BE import Basisszenario_1 as BS_1_BE


dump_path = get_dump_file_path(2045, 'BS0006', 'Basic_example_zorro_1_BE', 'BE_imp_exp_neu_2')
es, model = load_results_from_dump(dump_path)


dict_costs = {"investment costs": {}, "variable costs": {}, "profits": {}}


dict_costs = {"investment costs": {}, "variable costs": {}, "profits": {}}


def __cost_calculation(energysystem, results) -> pd.DataFrame:
    for node in energysystem.nodes:
        for item in node.outputs.data.values():
            
            if item.investment:
                # Speicher wird zweimal aufgeführt, weil invest nicht im Flow() steht
                # jetzt nur noch einmal
                investcosts = (
                    item.investment.ep_costs[0]
                    * solph.views.node(results, item.input)["scalars"].iloc[0]
                    + item.investment.offset[0]
                    if (
                        len(item.investment.offset) > 0
                        and solph.views.node(results, item.input)["scalars"].iloc[0]
                        > 0.0
                    )
                    else 0
                )
                dict_costs["investment costs"].update(
                    {
                        "("
                        + str(item.input)
                        + ", "
                        + str(item.output)
                        + ")": investcosts
                    }
                )
                    # sum_investcosts += investcosts

            if hasattr(item, "variable_costs"):

                if not all(v == 0 for v in item.variable_costs):
            
                    # ==============================================================
                    # GET ACTUAL FLOW
                    # ==============================================================
            
                    flow = np.asarray(
                        solph.views.node(
                            results,
                            item.output
                        )["sequences"][
                            (item.input, item.output),
                            "flow"
                        ],
                        dtype=float
                    )
            
                    # ==============================================================
                    # GET VARIABLE COSTS
                    # ==============================================================
            
                    variable_costs = np.asarray(
                        pd.Series(item.variable_costs),
                        dtype=float
                    )
            
                    print(
                        f"{item.input} -> {item.output}: "
                        f"flow = {len(flow)}, "
                        f"variable_costs = {len(variable_costs)}, "
                        f"flow NaNs = {np.isnan(flow).sum()}"
                    )
            
                    # ==============================================================
                    # MAKE LENGTHS IDENTICAL
                    # ==============================================================
            
                    n_len = min(
                        len(flow),
                        len(variable_costs)
                    )
            
                    flow = flow[:n_len]
                    variable_costs = variable_costs[:n_len]
            
                    # ==============================================================
                    # HANDLE NaN FLOWS
                    # ==============================================================
            
                    # Only fill NaNs that actually exist.
                    # Here we use the previous timestep.
                    flow = pd.Series(flow).ffill().to_numpy()
            
                    # ==============================================================
                    # PROFITS
                    # ==============================================================
            
                    if all(
                        val <= 0
                        for val in variable_costs
                    ):
            
                        erloese = np.multiply(
                            flow,
                            variable_costs
                        )
            
                        dict_costs["profits"].update(
                            {
                                "("
                                + str(item.input)
                                + ", "
                                + str(item.output)
                                + ")":
                                sum(erloese)
                            }
                        )
            
                    # ==============================================================
                    # VARIABLE COSTS
                    # ==============================================================
            
                    else:
            
                        line = np.multiply(
                            flow,
                            variable_costs
                        )
            
                        dict_costs["variable costs"].update(
                            {
                                "("
                                + str(item.input)
                                + ", "
                                + str(item.output)
                                + ")":
                                sum(line)
                            }
                        )

    return pd.DataFrame(dict_costs)

def cost_calculation_from_dump(dump_path: str, dump_file: str) -> pd.DataFrame:
    energysystem = solph.EnergySystem()
    energysystem.restore(filename=dump_file, dpath=dump_path)

    return __cost_calculation(energysystem, energysystem.results["main"])


def cost_calculation_from_energysystem(energysystem) -> pd.DataFrame:
    return __cost_calculation(energysystem, energysystem.results["main"])


def cost_calculation_from_es_and_results(energysystem, results) -> pd.DataFrame:
    return __cost_calculation(energysystem, results)
            
#%%
cost = cost_calculation_from_energysystem(es)