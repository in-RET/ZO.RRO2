import logging
import os

import pandas as pd
from oemof import solph

from energymodels.basic_example import basic_example
from src.models.automatic_cost_calc import cost_calculation_from_es_and_results
from src.postprocessing.plot_energysystemgraph import draw_energy_system


def solveModels(
    variations: [int],
    years: [int],
    model_name: str,
    solver: str = "gurobi",
    gap: float = 0.005,
    solver_output: bool = True,
    print_graph: bool = False,
):

    # Hier steht ein Code kommentar
    permutations = [str(x) + "_" + y for x in years for y in variations]
    print(permutations)

    for permutation in permutations:
        DUMP_PATH = os.path.abspath(os.path.join(os.getcwd(), "dumps", permutation))
        FIGURE_PATH = os.path.abspath(os.path.join(os.getcwd(), "figures", permutation))

        os.makedirs(DUMP_PATH, exist_ok=True)
        os.makedirs(FIGURE_PATH, exist_ok=True)

        logging.info(f"Löse %s", permutation)
        energysystem = basic_example(permutation)

        if print_graph:
            draw_energy_system(
                energy_system=energysystem,
                filepath=os.path.join(
                    FIGURE_PATH, model_name + "_" + str(permutation) + ".pdf"
                ),
                legend=False,
            )

        model = solph.Model(energysystem)
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
