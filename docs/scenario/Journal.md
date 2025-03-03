
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
- Checklist Basis Scenario every component parameters and variables[CHECKLIST]


# To-Dos

- [ ] find grid operating fee for Höchspannungsnetz
- [x] modify read_input_files functions because of new OEP csv file structure
- [ ] clarify grid operating fee for both grids
- [x] Remove parameter storage heat block
- [ ] basis scenario final run with new blocks (simulation number 009)
- [x] Doc string for function and read me file for github for each folder level (bis 21.02)
- [ ] PVGIS --- SARAH 3, ERA 5..... NASA POWer For SWC


Markdown:

List: for properties als meta data " List mit --- und ---"
Release verlinken bei jedem Simulationverlauf
Input daten
parametern
output
Plots nur mit Links
Logseq als vergleich markdown datei schauen
Bilder einmal auf geringer Auflösung und einmal hochaufgelöst


"Influence of Higher level grid, seperating Goldistal(pumped storge and splitting heat storages",
        sim_remarks = "- Previously in ZORRO I gird and storages were not well defined. \n"+
                        "- The grid is classified into Höchste- und Hochspannung to obtain a clean comparision with the regionalisation model. "+
                        "- Hence the component pumped hydro storage is split into two, where the Golistal is connected to teh higest grid level. \n"+
                        "- The heat storages are sub classified into seasonal and district heating storages. \n"+
                        "- Additionally a preheater is connected to the seasonal storage tank to give the heat at necessary temperature back to the district heating network. \n"+
                        "- Other parameters remain the same [[2030_BS0001_008]]"