import logging
import os

import pandas as pd
from oemof import solph

from energymodels.BS_regionalization import BS_regionalization
from src.models.automatic_cost_calc import cost_calculation_from_es_and_results
from src.postprocessing.plot_energysystemgraph import draw_energy_system
from src.postprocessing.export_results import export_csv_region, grid_energy_map, export_csv
from src.preprocessing.constraints import CO2_limit, BiogasBestand_limit, BiogasNeuanlagen_limit,Biomasse_limit, Bilanziell_erneuerbar


def solveModels(
    variations: [str],
    years: [int],
    model_name: str,
    solver: str = "gurobi",
    gap: float = 0.005,
    solver_output: bool = True,
    print_graph: bool = False,
    Anteilig_erneuerbar:bool = True,
):

    # Hier steht ein Code kommentar
    permutations = [str(x) + "_" + y for x in years for y in variations]
    print(permutations)

    for permutation in permutations:
        DUMP_PATH = os.path.abspath(os.path.join(os.getcwd(), "dumps", permutation))
        FIGURE_PATH = os.path.abspath(os.path.join(os.getcwd(), "figures", permutation))
        YEAR, model_ID = permutation.split("_")
        YEAR = int(YEAR)
        os.makedirs(DUMP_PATH, exist_ok=True)
        os.makedirs(FIGURE_PATH, exist_ok=True)

        logging.info(f"Solve %s", permutation)
        logging.info("Building the energy system")
        energysystem,sim_data = BS_regionalization(permutation)

        if print_graph:
            draw_energy_system(
                energy_system=energysystem,
                filepath=os.path.join(
                    FIGURE_PATH, model_name + "_" + str(permutation) + ".pdf"
                ),
                legend=False,
            )

        model = solph.Model(energysystem)
        
        logging.info("Applying model constraints")
        if Anteilig_erneuerbar:
            Bilanziell_erneuerbar(model, sim_data)
        
        CO2_limit(model, limit = sim_data['Parameter']['System_configurations']['System']['CO2_Grenze_'+str(YEAR)])
        BiogasBestand_limit(model, limit = sim_data['Parameter']['Parameter_biogas_upgrading_plant']['potential'][model_ID])
        BiogasNeuanlagen_limit(model, limit = sim_data['Parameter']['Parameter_biomethane_injection_plant']['potential'][model_ID])
        Biomasse_limit(model, limit = sim_data['Parameter']['Parameter_biomass_heating_plant']['potential'][model_ID])
        
        logging.info("Solve the model")
        model.solve(
            solver=solver,
            cmdline_options={"MIPGap": gap},
            solve_kwargs={"tee": solver_output},
        )

        logging.info("Berechne automatische Kosten")

        result = cost_calculation_from_es_and_results(
            energysystem=energysystem,
            results=solph.processing.results(model),
        )

        df_costs = pd.DataFrame(result)

        energysystem.results["main"] = solph.processing.results(model)
        # energysystem.results['meta'] = solph.processing.meta_results(model) % TODO: Why is it bugging?
        energysystem.results["costs"] = df_costs.to_dict()

        energysystem.dump(
            dpath=DUMP_PATH, filename=model_name + "_" + str(permutation) + ".dump"
        )
        
        if model_name == 'BS_regionalization':
            export_csv_region(energysystem.results["main"], YEAR, permutation, model_name)
            grid_energy_map(energysystem.results["main"],permutation, model_name)
        else:
            export_csv(energysystem.results["main"], YEAR, permutation, model_name)
        
        
        return sim_data,result
