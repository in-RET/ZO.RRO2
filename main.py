import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0001"],
        scenario_num = "006",
        years=[2030],# 2040, 2050],
        model_name="Basic_example_zorro_1",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "Influence of an addtional Hydrogen import and a new component to produce synthetic fuel from Biomass",
        sim_remarks = "- New hydrogen import block with variable cost (grid usage cost, production and transportation cost) \n"+
                        "- Biomass to liquid component to produce syn. fuel"
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
