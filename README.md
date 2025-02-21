# Zero Carbon Cross Energy System - Phase 2 (ZO.RRO II)

Welcome to the ZO.RRO2 repository. This document provides an overview of the project's structure, including directories and key files, to help you navigate and understand the contents of this repository.

## Directory and File Descriptions
  - github/workflows: Contains GitHub Actions workflow files for continuous integration and deployment
  - run: Houses configuration files for development environment setups
  - coverage: Stores code coverage reports generated from test suites
  - data: Intended for datasets used by the project
  - docs: Contains project documentation, scenario description and markdown files for each scenario. This folder can be used to track the project using obsidian
  - energymodels: Includes energy system models (eg. Basic example, Basic example regionilized...)
  - figures: Holds graphical outputs such as plots and diagrams.
  - notebooks: Consists of Jupyter notebooks for exploratory data analysis and prototyping
  - results: Contains results from simulations or analyses
  - src: The main source code directory for the project's Python modules
  - coveragerc: Configuration file for coverage.py, specifying rules for measuring code coverage
  - gitignore: Specifies files and directories to be ignored by Git version control
  - pre-commit-config.yaml: Configuration for pre-commit hooks to maintain code quality
  - LICENSE: The project's license file, detailing terms of use and distribution
  - README.md: This file provides an overview and instructions for the repository
  - main.py: The main executable script that serves as the entry point for the project
  - mkdocs.yml: Configuration file for MkDocs, a static site generator for project documentation
  - requirements.txt: Lists Python dependencies required for the project

## Programming Parameter
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/6ea8d776d6a849a6a2dbfec3f16506a8)](https://app.codacy.com/gh/in-RET/ZO.RRO2/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/6ea8d776d6a849a6a2dbfec3f16506a8)](https://app.codacy.com/gh/in-RET/ZO.RRO2/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_coverage)

### Clone the repository
```
git clone https://github.com/in-RET/ZO.RRO2.git
cd ZO.RRO2
```
### Creating a virtual Environment
```python3 -m venv venv
source venv/Scripts/activate
```
### Install dependencies
All required python packages are named in the file "requirements.txt". 
If you create a new environment use
```
pip install -r requirements.txt
```
to setup all dependencies.

## Project Overview
## Thuringian energy research project ZO.RRO II supports industrial companies in designing a climate-friendly energy supply

In order to optimize the use of energy resources and thus reduce CO2 emissions, a consortium of the Nordhausen University of Applied Sciences (HSN) and the Thuringian Renewable Energies Network (ThEEN) e.V. has come together in Thuringia.
The initial results from the project, called ZO.RRO (Zero Carbon Cross Energy System), have made an impression, and one of the co-initiators - HSN's Institute for Renewable Energy Technology - was awarded the Thuringian "Digital and Open-Source Award".

The much-cited study ["So geht's - How Thuringia can become climate-neutral (...)"](https://umwelt.thueringen.de/fileadmin/user_upload/So_gehts_Buchblock_Druck.pdf) by Prof. Dr.-Ing. Viktor Wesselak, Professor of Regenerative Energy Technology at Nordhausen University of Applied Sciences, was further developed.
After the scientists in the ZO.RRO I project in November 2021 showed transformation paths to 2050, calculations were carried out in the continuation with the energy system modeling for climate neutrality in the Free State by 2035.
The researchers conclude that by calculation, climate neutrality is also feasible and affordable sooner, although the simulation tool does not factor in the time required for the processes of land allocation, skilled labor acquisition, and permitting of renewable energy facilities.
In the meantime, the first phase of concept development has been completed, and the project will be continued in Phase II with funding from the Thuringian Ministry for the Environment, Energy and Nature Conservation (TMUEN).

### Project Goal

The objective of the current demonstration phase is to holistically optimize the energy supply of Thuringian industrial companies to prove their carbon footprint and to reduce it.
In the ZO.RRO II state project, the open-source software is used as a third tool for the demonstrator companies to determine the economically and ecologically optimal climate-neutral energy supply.
Similar to the case study of Thuringia, scenarios are developed step by step together with the companies according to their targets, which show how the energy demand can be met at any time.
Suitable options, for example, are the use of (additional) photovoltaics in combination with energy storage, the use of heat pumps and electromobility.
ZO.RRO additionally considers the possibility of demand side management in order to be able to react even better to future price fluctuations.
This refers to an adjustment of energy consumption in which temporally independent production stages take place when sufficient low-cost, renewable energy is available.

* detailed measurements to evaluate suitable options in energy supply
* identification of hidden savings potentials and largest CO2 sources
* economic and ecological evaluation of individual plants
* verification of CO2 footprint and sustainable development
* optimization of the design of new plants and supply concepts (e.g. by using photovoltaics, energy storage, flexibility potentials, electromobility)

## Lincense
This project is licensed under the MIT License. See the LICENSE file for more details.

*Note*: This overview is based on the repository structure as of February 21, 2025. For the most up-to-date information, please refer to the repository.
