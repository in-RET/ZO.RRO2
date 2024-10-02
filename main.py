import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    solveModels(
        variations=["BS0001"],
        years=[2030],# 2040, 2050],
        model_name="BS_regionalization",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Habe fertig!")
