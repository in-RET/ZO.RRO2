# Preprocessing Folder Overview
The preprocessing is responsible for preparing and processing the input data that is used by the energy system model.
It contains scripts that handle constraints, data conversion, load profile scaling, CO2 price adjustments, and other preprocessing steps necessary for simulating the energy system model.
This folder includes functions to convert data to appropriate time resolutions, calculate investment parameters, scale load profiles to meet energy demands, and ensure that input data is ready for system analysis. 
It also includes calculations for CO2 prices, heat pump performance, and energy feed-in profiles for renewable generation technologies such as wind and PV.

## Scripts Overview
### Constraints (constraints.py)
This script defines various constraints used in the model, mostly sourced from oemof (Open Energy Modelling Framework). 
Constraints are crucial for restricting the behavior of the model according to real-world limits and technical specifications. 
These constraints ensure the model’s decisions adhere to the energy system’s realistic capabilities.

###  Conversion (conversion.py)
This module includes functions for converting input data into the appropriate format and time resolution for the energy system model. 
It automates several crucial preprocessing tasks to ensure the model’s data inputs are standardized.
  - *convert_to_hourly_resolution()*: Converts input data from daily, monthly, or other resolutions into hourly data, ensuring compatibility with the time-stepping approach used by the model.
  - *calculate_investment_parameters()*: Automatically calculates the EPC (economical periodic costs) costs for energy system components based on CSV files containing investment parameters.
  - *scale_load_profiles()*: Scales the load profiles according to the respective energy demand for each time period.
                           This ensures that the energy demand across different energy carriers (e.g., electricity, heat, gas) is aligned and can be aggregated as required.
  - *co2_price_addition()*: Adds CO2 prices to the import/export price calculations, ensuring that carbon pricing is considered in economic evaluations.
  - *COP_calculation()*: Calculates the Coefficient of Performance (COP) for heat pumps, which reflects the heat pump's energy efficiency, allowing the model to account for its heating performance.

### Files (files.py)
This script is responsible for reading input data files from the specified directory. 
The input data typically includes CSV files containing parameter values, historical load data, energy prices, and technology-specific parameters.
  - *read_input_files()*: Reads all the input files from a specified directory and parses them into appropriate data structures (e.g., pandas DataFrames or dictionaries).

### Location (location.py)
This module defines the location settings for each planning region and calculates renewable energy feed-in profiles based on the geographical location. 
It handles wind and solar generation profiles using location-based data.

  - *location()*: Defines the planning region and its geographical attributes, including latitude, longitude, altitude, and any other location-specific parameters based on weather data
  - *wind_feed_in_profile()*: Uses Hellmann's Exponent formula to calculate wind generation profiles based on wind speed and location.
  - *pv_feed_in_profile()*: Uses PVlib to calculate the solar feed-in profiles based on solar irradiance data and other relevant location-based parameters.
                                    
