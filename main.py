import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0001"],
        scenario_num = "001",
        years=[2030],# 2040, 2050],
        model_name="Basic_example_zorro_1",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "Influence of new oemof.solph version",
        sim_remarks = "- BS in new oemof.solph version \n"+
                        "- Transfer into new file and project structure."
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
