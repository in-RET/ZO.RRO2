import logging

from src.models.solve_model import solveModels

FORMAT = "%(asctime)s %(message)s"

if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO, format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    sim_data, result,csv = solveModels(
        variations=["BS0001"],
        scenario_num = "008",
        years=[2030],# 2040, 2050],
        model_name="Basic_example_zorro_1",
        solver="gurobi",
        gap=0.0,
        solver_output=False,
        print_graph=False,
        Anteilig_erneuerbar = True,
        hypothese = "Influence of Biomass Heizkraftwerk statt Kraftwerk",
        sim_remarks = "- Previously in ZORRO I biomass Kraftwerk was implemented which produces only electricity. \n"+
                        "- The analysis from Lynn Vincent proves that there is no technology at the moment in thüringen which produces only electricity. "+
                        "Hence the component is replaced by a Biomass Heizkraftwerk which produces electricty and heat. \n"+
                        "- Other parameters remain the same [[2030_BS0001_006]]"
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
