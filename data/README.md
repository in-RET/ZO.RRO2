# Data Folder Overview
This document provides an overview of the data directory in the ZO.RRO2 repository. 
The data folder contains essential input datasets required for energy system modeling, including component parameters, time-series data, and weather information.

## Folder Description
### scalars
This directory contains static input parameters for different components in the energy system model. These parameters include:
  - **Component input parameters**: Defines fixed attributes for different energy system components.
  - **Techno-economic parameters**: Includes cost data, efficiency rates, and other economic factors influencing system performance.
### sequences
This directory stores time-series data, which represents variations over time for different energy system inputs. Key datasets include:
  - **Load profiles**: Time-series data representing electricity or heat demand patterns.
  - **Energy prices**: Historical or forecasted energy market prices.
  - **Other time-series data**: Includes renewable energy generation profiles, external constraints, or additional system inputs.
### weather_data
This directory contains raw weather datasets used for energy system modeling. 
The weather data is extracted from Meteonorm and represents the climatic conditions of the planning region.
  - **Raw weather data**: Direct output from Meteonorm for a test reference year (TRY) in hourly and minutely resoulution.
#### Usage of Weather Data
  - *Inside the model*: Used to compute feed-in profiles for renewable energy sources like solar PV and wind turbines.
  - *Outside the model*: Used for generating load profiles that depend on temperature and other climatic conditions.
## Notes
  - Ensure that all datasets are correctly formatted before use in the model.
  - If new data is added, it should follow the existing structure and format to maintain consistency.

This structured data repository enables efficient and accurate modeling of energy systems in the ZO.RRO2 project.
