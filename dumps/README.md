# Simulation dumps Folder Overview
The dumps folder contains the simulation dump files, which store the energy system results for post-processing. 
These files are essential for analyzing and extracting insights from model simulations.

## Folder names
Each subfolder follows the naming patter:
```
<Year of Simulation>_<Model_ID>
```
  - **Year of Simulation**: The year for which the model was run.
  - **Model ID**: A unique identifier for the specific model configuration(techno-economical parameters).
The directories are created automatically after the respective simulation.

## Contents
Each subfolder contains multiple dump files (.dump), which store detailed energy system results. These files can be interpreted using the oemof package or pickle.
These files are generated during simulations and are used for post-processing, visualization, and further analysis.
## Usage
  - **Post-processing**: Load dump files in Python for analyzing energy system performance.
  - **Result validation**: Compare outputs from different simulation years or model configurations.
  - **Debugging**: Investigate inconsistencies in system behavior by inspecting stored results.

To access teh results:
```
from oemof import solph

def load_results_from_dump(dump_path):
    energysystem = solph.EnergySystem()
    energysystem.restore(my_path, dump_path)
    return energysystem.results["main"]
```
OR
```
import pickle

with open(dump_path,"rb") as file:
  data = pickle.load(file)

print(data)
```
