import logging
import os

import pandas as pd
import numpy as np
from oemof import solph
from pyomo.environ import Constraint, value
from energymodels.BS_regionalization import BS_regionalization
from energymodels.test_Basic_example_zorro_1_utility_energy import Basisszenario_1_Nutz 
from energymodels.Basic_example_zorro_pathway import Basisszenario_pathway
from energymodels.Basic_example_zorro_backward_pathway import Basisszenario_pathway_B
from energymodels.Basic_example_zorro_1 import Basisszenario_1 as BS_1
from energymodels.basic_example_zorro_1_BE import Basisszenario_1 as BS_1_BE
from src.models.automatic_cost_calc import cost_calculation_from_es_and_results
from src.postprocessing.plot_energysystemgraph import draw_energy_system
from src.postprocessing.export_results import export_csv_region, grid_energy_map, export_csv
from src.preprocessing.constraints import CO2_limit, BiogasBestand_limit, BiogasNeuanlagen_limit,Biomasse_limit, Bilanziell_erneuerbar, GuD_time, import_export_bilanz, blackout
from docs.scenario.create_md_file import create_simulation_doc
from src.postprocessing.so_gehts_plot import so_gehts_bar_plot
from src.postprocessing.plots import heat_maps
from oemof.solph.constraints import limit_active_flow_count_by_keyword
from datetime import datetime
def solveModels(
    variations: [str],
    scenario_num :str,
    hypothese: str,
    sim_remarks: str,
    years: [int],
    model_name: str,
    solver: str = "gurobi",
    gap: float = 0.005,
    solver_output: bool = True,
    print_graph: bool = False,
    Anteilig_erneuerbar:bool = True,
):

    # Hier steht ein Code kommentar
    permutations = [str(x) + "_" + y for x in years for y in variations]
    #print(permutations)

    for permutation in permutations:
        if scenario_num == "SALIB":
            DUMP_PATH = os.path.abspath(os.path.join(os.getcwd(), "dumps", scenario_num, permutation))
        else:
            DUMP_PATH = os.path.abspath(os.path.join(os.getcwd(), "dumps", permutation))
        FIGURE_PATH = os.path.abspath(os.path.join(os.getcwd(), "figures", permutation, scenario_num))
        YEAR, model_ID = permutation.split("_")
        YEAR = int(YEAR)
        os.makedirs(DUMP_PATH, exist_ok=True)
        os.makedirs(FIGURE_PATH, exist_ok=True)

        logging.info(f"Solve %s", permutation)
        logging.info("Building the energy system")
        if model_name.startswith('BS_regionalization'):
            energysystem,sim_data = BS_regionalization(permutation, model_name)
        elif model_name.endswith('utility_energy'):
            energysystem,sim_data = Basisszenario_1_Nutz(permutation)
        # elif model_name.endswith('pathway'):
        #     energysystem,sim_data = Basisszenario_pathway(permutation)
        elif model_name.endswith('backward_pathway'):
            energysystem,sim_data = Basisszenario_pathway_B(permutation)
        elif model_name.endswith('BE'):
            energysystem,sim_data = BS_1_BE(permutation)    
        else:
            energysystem,sim_data = BS_1(permutation)
        if print_graph:
            draw_energy_system(
                energy_system=energysystem,
                filepath=os.path.join(
                    FIGURE_PATH, model_name + "_" + str(permutation) + ".pdf"
                ),
                legend=False,
            )
        
            
        model = solph.Model(energysystem)
        
        logging.info("Applying model constraints")
        if Anteilig_erneuerbar:
           if YEAR <= 2030:
               Bilanziell_erneuerbar(model, sim_data, model_name, factor = 0.55)
           else:
               # Bilanziell_erneuerbar(model, sim_data, model_name, factor =1)
               import_export_bilanz(model, "import_bilanz", "export_bilanz")
        else:
            logging.info("NICHT Bilanziell erneuerbar")
        
        CO2_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['CO2_Grenze_'+str(YEAR)] )
        BiogasBestand_limit(model, limit = sim_data['Parameter']['Parameter_biogas_upgrading_plant']['potential'][model_ID])
        BiogasNeuanlagen_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['Biomasse_sub_tot'])
        Biomasse_limit(model, limit = sim_data['Parameter']['System_configurations_2024']['System']['Holzpotential_tot'])
        GuD_time(model, limit = 0, Starttime = 1777, Endtime= 7656)
        
        def date_to_hour(year, month, day, hour=0):
            date = datetime(year, month, day, hour)
            days_since = (date - datetime(year, 1, 1)).days
            return days_since * 24 + hour
        
        #blackout(model, 'grid_cutoff', limit = 0, Starttime = date_to_hour(YEAR, 6, 24, 0), Endtime= date_to_hour(YEAR, 7, 9, 0))
    
        logging.info("Solve the model")
        model.solve(
            solver=solver,
            cmdline_options={"MIPGap": gap},
            solve_kwargs={"tee": solver_output},
        )
        
        Cost_opt = value(model.objective)
        import pyomo as po
        #print("Import:", value(model.integral_limit_import_bilanz))
        #print("Export:", value(model.integral_limit_export_bilanz))
        logging.info("Calculating costs")

        result = cost_calculation_from_es_and_results(
            energysystem=energysystem,
            results=solph.processing.results(model),
        )

        df_costs = pd.DataFrame(result)

        energysystem.results["main"] = solph.processing.results(model)
        #energysystem.results['meta'] = solph.processing.meta_results(model) % TODO: Why is it bugging?
        energysystem.results["costs"] = df_costs.to_dict()

        energysystem.dump(
            dpath= DUMP_PATH, filename=model_name + "_" + str(permutation) + "_" + scenario_num + ".dump"
        )
        
        logging.info("Export overview - CSV file")
        if model_name == 'BS_regionalization':
            #export_csv_region(energysystem.results["main"], YEAR, permutation, model_name, scenario_num)
            #grid_energy_map(energysystem.results["main"],permutation, model_name, scenario_num)
            print('Postprocessing should be done seperately')
        else:
            csv=None
            logging.info("Plotting different plots")
            #so_gehts_bar_plot(csv, permutation, scenario_num)
            profile = []#'Wind', 'PV_Rooftop','PV_Openfield', 'loadprofile']
            
            for i in range (len(profile)):
                profile_type = profile[i]
                if profile_type =='loadprofile':
                    sector = ['electricity', 'gas', 'oil', 'dist_heating', 'biomass']
                    for j in range(len(sector)):
                        heat_maps(sim_data,YEAR,permutation,scenario_num, profile_type= profile_type,sector=sector[j])
                else:
                    sector = None
                    heat_maps(sim_data,YEAR,permutation, scenario_num, profile_type= profile_type,sector=None)
        logging.info("Creating simulation doc...")    
        #create_simulation_doc(permutation,scenario_num, hypothese, sim_remarks,csv)
        
        return sim_data,result, energysystem.results["main"], Cost_opt,model
