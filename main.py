import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0001"],
        scenario_num = "005",
        years=[2030],# 2040, 2050],
        model_name="Basic_example_zorro_1",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "Influence of new load profiles developed using open-source tools like RAMP, RAMP mobility, RC building simulator....",
        sim_remarks = "- The load profiles were developed with the help of several open-source packages to make it more dynamic in comparison to the Standart loadprofiles. The weather data is acquired from Meteonorm at 10 m height "+
                        "for the planing regions imported in the tools to deelop synthetic load profiles. Most tools work with stochastic algorithm to develop the time series. \n"+
                        "- Other parameters remain the same [[2030_BS0001_004]]"
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
