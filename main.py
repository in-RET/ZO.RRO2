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
        hypothese = "Influence of newly developed demand time series. **(2024)**",
        sim_remarks = "- The demand time series are developed with various algorithms like stochastic, statistical, 5R1C model etc. \n"+
                        "- In Zorro 1 the standard demand profiles were used for simualtion. The new demand profiles are specifically developed for Thuringia. \n"+                
                        "- Other parameters remain the same [[2030_BS0001_004]] "
                        
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
