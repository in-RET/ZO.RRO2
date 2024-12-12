import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0001"],
        scenario_num = "003",
        years=[2030],# 2040, 2050],
        model_name="Basic_example_zorro_1",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "Influence of new Wind feed-in profiles developed using Hellman's exponent",
        sim_remarks = "- The Wind feed-in profiles are developed with the help of Hellman's height formula. The weather data is acquired from Meteonorm at 10 m height "+
                        "and the wind speed is exponentially scaled up to the hub height (150 m).\n"+
                        "- The power curve of the Enercon E101 turbine was used to develop the energy yield. \n"+
                        "- Other parameters remain the same [[2030_BS0001_001]]"
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
