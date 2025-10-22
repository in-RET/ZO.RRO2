import logging
from datetime import datetime
from src.models.solve_model import solveModels
start_time = datetime.now()
FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result = solveModels(
        variations=["BS0006"],
        scenario_num = "test_sim",
        years=[2030],# 2040, 2050],
        model_name='Basic_example_zorro_1_utility_energy',
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = False,
        hypothese = "Regionalisation of the new Basis scenario",
        sim_remarks = "- The techno-economical parameters are updated. \n"+
                        "- All changes made in BAsic exapmple by TR is updated in this scenario"
                        
                        
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
    end_time = datetime.now()
    print('Execution time: {}'.format(end_time - start_time))
