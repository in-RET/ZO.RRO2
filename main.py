import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0001"],
        scenario_num = "ref",
        years=[2030],# 2040, 2050],
        model_name="Basic_example_zorro_1",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "This is a reference scenario with all the final components defined in the flow chart.",
        sim_remarks = "- This scenario is used as reference fro the labels and results format. \n"+
                        "- The results in this scenario will not make any sense, so no need of analysing."
                        "- New simulation will be done from the start with this scenario as reference."
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
