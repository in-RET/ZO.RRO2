import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0006"],
        scenario_num = "Original",
        years=[2045],# 2040, 2050],
        model_name='BS', #"BS_regionalization",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "Influence of new techno-economical parameter in regionalization scenario",
        sim_remarks = "- The techno-economical parameters are updated. \n"+
                        "- Loss rate defined for seasonal heat storage\n"+
                        "- Pumped hydro storage split into storage and technology \n"+
                        "- Weather dependent COP's are added only to the Air heatpumps \n"+
                        "- Other parameters remain the same [[2030_BS0001_003]] "
                        
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
