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
        hypothese = "Influence of new biomass price due to less availability of trees. **(2024)**",
        sim_remarks = "- Due to abundance of trees the Hackholzschnitzel price keeps increasing with time. New prices were taken from Deutsche Pelletinstitute \n"+
                        "- Hackschnitzel A2 class:\n Price- 35.6€/MWh \n Source link: https://www.depi.de/p/1622b2bc-85fc-4f7a-b3df-7da7a1cc7828 \n"+                
                        "- Other parameters remain the same [[2030_BS0001_001]] "
                        
    )

    # %TODO: Auswertung der Dump-Daten (csv-daten erstellen, automatische grafiken etc.)

    print("Hab's fertig!")
