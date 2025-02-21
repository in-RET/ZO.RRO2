# Docs Folder Overview
This document provides an overview of the docs directory in the ZO.RRO2 repository. 
The docs folder contains essential documentation related to the project, including scenario descriptions, input data, and results in the form of markdown files.

## Folder Description
### obsidian_vault
This folder is structured as a vault for Obsidian, a powerful markdown-based note-taking tool that helps organize and link project documentation. 
It enables easy navigation, linking between documents, and visualization of relationships between different scenarios.
### scenarios
This subfolder contains markdown (.md) files that document individual scenarios in the energy system model. Each scenario file includes:
  - *Scenario description*: Explains the purpose, assumptions, and objectives of the scenario.
  - *Input data*: List the specific time-series used for simulation in form of heat maps.
  - *Results*: Contains key outputs, performance indicators, and insights from the scenario run.

These files provide a structured way to track different modeling cases and their respective inputs/outputs.
### model_tracking_overview.md
Under the scenarios folder, on can find model_tracking_overview.md file. This markdown file serves as a quick reference guide to track different scenarios. It includes:
  - A summary table listing different scenarios.
  - Key input parameters and variations between scenarios.
  - Links to individual scenario markdown files for detailed information.

This file is useful for quickly identifying how different cases were set up and comparing results across multiple scenarios.
## Notes
If using Obsidian, open the obsidian_vault/ folder within the app to enable advanced linking and visualization features.
Keep scenario markdown files updated with relevant input data and results to maintain clear documentation.
The model_tracking_overview.md file should be updated **manually** whenever new scenarios are added or modified.

*This documentation folder is crucial for maintaining clarity in scenario management and tracking the evolution of the ZO.RRO2 energy system model.*
