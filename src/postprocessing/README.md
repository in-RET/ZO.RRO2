# Postprocessing Overview
The postprocessing folder is dedicated to analyzing, exporting, and visualizing the results after running the model. 
It contains scripts that handle various tasks, such as exporting data, generating plots, and calculating costs. 
The folder also includes utilities for efficiently processing the dump files and extracting key insights.

## Python Scripts Overview
### Export Results (export_results.py)
This script contains functions for exporting results into CSV files. It supports basic example results and also handles regionalization with fixed variables.
the variable are specifically defined for this project.
  - *export_csv()*: Exports the basic example results into CSV format.
  - *export_csv_region()*: Exports the regionalized results for different regions, with fixed input variables for consistency.
  - *grid_energy_map()*: Map to visualize energy exchange between regions

### Plot Energy System (plot_energysystem.py)
This module utilizes Graphviz to generate a visual representation of the energy system. It allows you to inspect the connection between components and buses.
  - *draw_energy_system()* - Generates a Graphviz plot showing the relationships between components, buses, and their flows in the energy system. 
    This helps in understanding the structure and interactions within the system.
### Plotting (plot.py)
Contains functions for creating various types of plots for better visualization of results.
  - *heat_maps()* - Generates heatmaps, useful for visualizing energy consumption or generation over time.
    **To be defined:**
  - *plot_bar()* - Creates bar plots for comparing values across categories, such as energy generation from different sources.
  - *plot_line()* - Produces line plots to show trends, such as energy demand or system costs over time.
  - *plot_pie()* - Creates pie charts for visualizing the distribution of energy sources or costs.
  - *plot_scatter()* - Generates scatter plots to examine relationships between variables.

### Utilities for Dump Files (utils_dump.py)
This script includes helper functions for postprocessing dump files. 
It simplifies the calculation of various costs and key metrics without needing to specify variables manually.
  - *get_dump_file_path(), load_resultsfrom_dump()* : Read the dump file for all scenarios.
  - *interpret_results()* - Store the scalars and sequences seperation for the flow from the bus to a component and from a component to a bus.
  - *calculate_investment_cost()* - Computes the investment costs and operating costs of the system based on the components and their respective characteristics.
  - *clean_sequence_data()* - Replaces teh last row with the ffill method adn saves as a series.
  - *calc_energyimport_cost(), calc_energyexport_cost()* - Automatically extracts and calculates the prices for energy imports and exports based on the dump file data.
    
