import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0001"],
        scenario_num = "004",
        years=[2030],# 2040, 2050],
        model_name="Basic_example_zorro_1",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "Influence of new PV feed-in profiles developed using PVlib",
        sim_remarks = "- The PV feed-in profiles were developed with the help of PVlib package (open-source). The weather data is acquired from Meteonorm at 10 m height "+
                        "and previouly was imported in PVsyst to develop the energy yield timeseries. PVlib uses a different algorithm but the same module and inverter specifications were implemented in PVlib to get similar energy yield.\n"+
                        "- Other parameters remain the same [[2030_BS0001_003]]"
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
