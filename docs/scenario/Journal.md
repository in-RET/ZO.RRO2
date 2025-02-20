
# Visualisation
## Flow chart-
- last updated 18.12.24
- Changes:
	- **Source**
		- Import Hydrogen
	- **Transformer**
		- Biogaseinspeisung-Bestand : Name Change **Biogasaufbereitungsanlage**
		- Biogaseinspeisung-Neu: Name change **Biomethaneinspeisungsanlage**
		- Biomass to Liquid (new)
		- Biomasse-strom: Biomasse Heizkraftwerk (produces electricity and heat not just electricity)
		- Biomasse- Warme: Name change **Biomasse- Heizwerk**
		- Luftwärmerpumpe (new)
		- Luftwärmepumpe-Abwärme (mit abwärme potential new)
		- Erdwärmepumpe- Fluss : mit umweltwärme as input
	- **Storage**
		- statt ein Wärmespeicher: Saisonaler-, Fernwärmespeicher (Saisonaler mit Nachheizung)
	- **Consumer**
		- nichts geändert
## Graphs
## Model tracking
# Programming

hab bis 12.02. schritt nach schritt die Änderungen dokumentiert [[Model tracking overview]]

- Stromnetzabbildung für die Regionalisierung geändert am 12.02. 
- Postprocessing (automatic procesing from dumpfile without fixed variable)
	- [x] dumpfile analysis
	- [ ] graph funtion 
	- [x] investment cost
	- [x] operating cost
	- [x] import/Export cost
	- [ ] emission
	

# To-Dos

- [ ] find grid operating fee for Höchspannungsnetz
- [x] modify read_input_files functions because of new OEP csv file structure
- [ ] clarify grid operating fee for both grids
- [x] Remove parameter storage heat block
- [ ] basis scenario final run with new blocks (simulation number 009)
- [ ] Doc string for function and read me file for github for each folder level (bis 21.02)