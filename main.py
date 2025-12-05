import logging
from datetime import datetime
from src.models.solve_model import solveModels
start_time = datetime.now()
FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
    
    sim_data, result = solveModels(
        variations=["BS0006"],
        scenario_num = "R05_same_Temp_no_grid_limit_03_12_25",
        years=[2045],# 2040, 2050],
        model_name="BS_regionalization",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "New Basis scenario",
        sim_remarks = "- The techno-economical parameters are updated. \n"+
                        "- All changes made in Basic exapmple by TR is updated in this scenario. \n"+
                        "- Additional BtL Substrat component added. \n"+
                        "- TEN Netzausbauplan, Import-Export Bilanz ab 2030, Rechnenzentrum, Netzverlust usw."
                        
                        
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
    end_time = datetime.now()
    print('Execution time: {}'.format(end_time - start_time))
