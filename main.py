import logging
from datetime import datetime
from src.models.solve_model import solveModels
start_time = datetime.now()
FORMAT = "%(asctime)s %(message)s"


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    years = [2045]#, 2035, 2040, 2045]
    for y in years:
        sim_data, result, sim_result, sys_cost, energy_model = solveModels(
            variations=["BS0006"],
            scenario_num = "MVB",
            years=[y],# 2040, 2050],
            model_name="basic_example_zorro_1_BE",#"Basic_example_zorro_backward_pathway",#'BS_regionalization',,#,#"test_Basic_example_zorro_1_utility_energy",
            solver="gurobi",
            gap=0.0,
            solver_output=False,
            print_graph=False,
            Anteilig_erneuerbar = True,
            hypothese = "Modelerweiterung auf Nutzenergie",
            sim_remarks = "- The techno-economical parameters are updated. \n"+
                            "- All changes made in Basic exapmple by TR is updated in this scenario. \n"+
                            "- Additional BtL Substrat component added. \n"+
                            "- TEN Netzausbauplan, Import-Export Bilanz ab 2030, Rechnenzentrum, Netzverlust usw."
                            
                            
        )
        print("Simulation done for year: " + str(y))

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
    end_time = datetime.now()
    print('Execution time: {}'.format(end_time - start_time))
