import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0001"],
        scenario_num = "003",
        years=[2030],# 2040, 2050],
        model_name="BS_regionalization",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "Influence regionalisation to the Thuringen model, minimum potential, and import wood limitations.",
        sim_remarks = "- The old techno-economical parameters are used but the technologies are split according to different regions \n"+
                        "- Grid infrastructure is build precisely to understand the grid exchange.\n"+
                        "- The minimum potential is defined for certain technologies (Wind, PV Open field, PV Rooftop, Hydro power, Pumped hydro storage) \n"+
                        "- Other parameters remain the same [[2030_BS0001_003]] "
                        
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
