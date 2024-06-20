from src.models.solve_model import solveModels
import logging

FORMAT = '%(asctime)s %(message)s'

if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format=FORMAT,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    solveModels(
        variations=["A", "B"],
        years=[2025, 2030, 2035, 2040, 2045],
        model_name="basic_example",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Habe fertig!")
