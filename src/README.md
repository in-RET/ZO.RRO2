# Source Code Overview
The src folder contains the core source code for the ZO.RRO2 energy system model. 
This includes scripts for data handling, energy system modeling, optimization, and post-processing. 
The folder is structured to maintain modularity and clarity, ensuring easy navigation and extensibility.

## Folder Overview

### models
This folder contains the core model solver that executes the optimization process.
  - **solve_model.py** - Runs the simulation and solves the energy system model for different variations and years. 
    It processes scenario configurations, applies constraints, and optimizes the system based on predefined parameters.

### Preprocessing 
Handles data preparation, constraint definition, and feed-in profile generation before running the model.
  - **Data handling** → Loads, cleans, and structures input datasets, including energy demand, generation profiles, and market prices.
  - **Profile generation** → Generates renewable energy feed-in profiles based on weather data.
  - **Constraint definition** → Defines system constraints (e.g., capacity limits, operational rules) for the optimization model.

### Postprocessing 
Performs result analysis, cost calculations, and visualization after model execution.
    - Extracts key performance indicators from the simulation output.
    - Computes total system costs, energy costs, and financial metrics.
    - Generates plots and visual representations of energy flows, demand profiles, and system costs.
    - Extracts specific results for further analysis or reporting.

## Note
The src folder is structured to ensure a systematic and efficient workflow for running and analyzing energy system simulations. 
It follows a logical flow from preprocessing → model execution → postprocessing, making it easy to adapt for different energy scenarios.
