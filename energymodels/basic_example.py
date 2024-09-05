import os

import pandas as pd
from oemof import network, solph
from oemof.tools import economics

from src.preprocessing.create_input_dataframe import createDataFrames
from src.preprocessing.files import read_input_files, conversion 


def basic_example(PERMUATION: str) -> solph.EnergySystem:
    YEAR, VARIATION = PERMUATION.split("_")
    YEAR = int(YEAR)
    sequences = read_input_files(folder_name = 'data/sequences', sub_folder_name='00_ZORRO_I_old_sequences')
    scalars = read_input_files(folder_name = 'data/scalars', sub_folder_name='00_ZORRO_I_old_scalars')

    # ------------------------------------------------------------------------------
    # Hilfskonstanten
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Parametrisierung
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Modellbildung
    # ------------------------------------------------------------------------------
    date_time_index = pd.date_range("1/1/"+ str(YEAR), periods=8760, freq="h")
    energysystem = solph.EnergySystem(
        timeindex=date_time_index, infer_last_interval=False
    )
    
    """
    Defining connecting lines/buses for balancing energy quantities
    """
    #------------------------------------------------------------------------------
    # Electricity Bus                                                                                      # Class Bus sind jetzt in module buses verschoben (solph.buses.Bus)
    #------------------------------------------------------------------------------
    b_el = solph.buses.Bus(label="Electricity")
    #------------------------------------------------------------------------------
    # Gas Bus
    #------------------------------------------------------------------------------
    b_gas = solph.buses.Bus(label="Gas")
    #------------------------------------------------------------------------------
    # Oil/fuel Bus
    #------------------------------------------------------------------------------
    b_oil_fuel = solph.buses.Bus(label="Oil_fuel")
    #------------------------------------------------------------------------------
    # Biomass Bus
    #------------------------------------------------------------------------------
    b_bio = solph.buses.Bus(label="Biomass")
    #------------------------------------------------------------------------------
    # Solid Biomass Bus
    #------------------------------------------------------------------------------
    b_bioWood = solph.buses.Bus(label="BioWood")
    #------------------------------------------------------------------------------
    # District heating Bus
    #------------------------------------------------------------------------------
    b_dist_heat = solph.buses.Bus(label="District heating")
    #------------------------------------------------------------------------------
    # Hydrogen Bus
    #------------------------------------------------------------------------------
    b_H2 = solph.buses.Bus(label="Hydrogen")
    #------------------------------------------------------------------------------
    # Solidfuel Bus
    #------------------------------------------------------------------------------
    b_solidf = solph.buses.Bus(label="Solidfuel")

    # Hinzufügen der Busse zum Energiesystem-Modell 
    energysystem.add(b_el, b_gas, b_oil_fuel, b_bio, b_bioWood, b_dist_heat, b_H2, b_solidf)
    
    """
    Export block
    """
    #------------------------------------------------------------------------------  
    # Electricity export                                                                           #  Class Sink sind jetzt in module components verschoben (solph.components.Sink)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Electricity', 
        inputs={b_el: solph.Flow(nominal_value = scalars['Parameter_Stromnetz_' + str(YEAR)]['Strom']['Max_Bezugsleistung'],
                                 variable_costs = [i*(-1) for i in sequences['Preise_2030_Stundenwerte']['Strompreis_2030']]
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen export
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Export_Hydrogen', 
        inputs={b_H2: solph.Flow(nominal_value = scalars['Parameter_Wasserstoffnetz_'+ str(YEAR)]['Wasserstoff']['Max_Bezugsleistung'],
                                 variable_costs = [i*(-1) for i in sequences['Preise_2030_Stundenwerte']['Wasserstoffpreis_2030']]
                                  
        )}))
    
    """
    Defining final energy demand as Sinks
    """
    #------------------------------------------------------------------------------
    # Electricity demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Electricity_demand_total', 
        inputs={b_el: solph.Flow(fix=Last_Strom_Zusammen, 
                                 nominal_value=1,
        )}))
    #------------------------------------------------------------------------------
    # Biomass demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Biomass_demand_total', 
        inputs={b_solidf: solph.Flow(fix=Last_Bio_Zusammen, 
                                   nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Gas demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Gas_demand_total', 
        inputs={b_gas: solph.Flow(fix=Last_Gas_Zusammen, 
                                  nominal_value=1,
        )}))
    
    #------------------------------------------------------------------------------
    # Material demand: Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Gas', 
        inputs={b_gas: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                  nominal_value=P_nom_Gas_Grundlast_Materialnutzung,
        )}))

    #------------------------------------------------------------------------------
    # Oil demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Oil_demand_total', 
        inputs={b_oil_fuel: solph.Flow(fix=Last_Oel_Zusammen, 
                                              nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Mobility demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Mobility_demand_total', 
        inputs={b_oil_fuel: solph.Flow(fix=Last_Verbrenner_Zusammen, 
                                              nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Material demand: Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Material_demand_Oil', 
        inputs={b_oil_fuel: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                              nominal_value=P_nom_Oel_Grundlast_Materialnutzung,
        )}))

    #------------------------------------------------------------------------------
    # Heat demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Heat_demand_total', 
        inputs={b_dist_heat: solph.Flow(fix=Last_Fernw_Zusammen, 
                                   nominal_value=1,
        )}))

    #------------------------------------------------------------------------------
    # Hydrogen demand
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='Hydrogen_demand_total', 
        inputs={b_H2: solph.Flow(fix=Last_H2_Zusammen, 
                                  nominal_value=1,
        )}))
    
    """
    Renewable Energy sources
    """
    #------------------------------------------------------------------------------
    # Wind power plants
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Wind_Erfurt', 
        outputs={b_el: solph.Flow(fix=data_Wind_Erfurt,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wind, 
                                                                    maximum=Parameter_PV_Wind_2030['Wind']['Potential_Erfurt_Mitte'])
        )}))

    energysystem.add(solph.components.Source(
        label='Wind_Nordhausen', 
        outputs={b_el: solph.Flow(fix=data_Wind_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wind, 
                                                                    maximum=Parameter_PV_Wind_2030['Wind']['Potential_Nordhausen_Nord'])
        )}))

    energysystem.add(solph.components.Source(
        label='Wind_Gera', 
        outputs={b_el: solph.Flow(fix=data_Wind_Gera,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wind, 
                                                                    maximum=Parameter_PV_Wind_2030['Wind']['Potential_Gera_Ost'])
        )}))

    energysystem.add(solph.components.Source(
        label='Wind_Hildburghausen', 
        outputs={b_el: solph.Flow(fix=data_Wind_Hildburghausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['Wind']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wind, 
                                                                    maximum=Parameter_PV_Wind_2030['Wind']['Potential_Hildburghausen_Südwest'])
        )}))
    
    #------------------------------------------------------------------------------
    # Photovoltaic Rooftop systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_rooftop_Erfurt', 
        outputs={b_el: solph.Flow(fix=data_PV_Aufdach_Erfurt,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Erfurt_Mitte'])
        )}))    

    energysystem.add(solph.components.Source(
        label='PV_rooftop_Nordhausen', 
        outputs={b_el: solph.Flow(fix=data_PV_Aufdach_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Nordhausen_Nord'])
        )}))

    energysystem.add(solph.components.Source(
        label='PV_rooftop_Gera', 
        outputs={b_el: solph.Flow(fix=data_PV_Aufdach_Gera,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Gera_Ost'])
        )}))

    energysystem.add(solph.components.Source(
        label='PV_rooftop_Hildburghausen', 
        outputs={b_el: solph.Flow(fix=data_PV_Aufdach_Hildburghausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Aufdach']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Aufdach, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Aufdach']['Potential_Hildburghausen_Südwest'])
        )}))

    #------------------------------------------------------------------------------
    # Photovoltaic Openfield systems
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='PV_Freifeld_Erfurt', 
        outputs={b_el: solph.Flow(fix=data_PV_Freifeld_Erfurt,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Erfurt_Mitte'])
        )}))

    energysystem.add(solph.components.Source(
        label='PV_Freifeld_Nordhausen', 
        outputs={b_el: solph.Flow(fix=data_PV_Freifeld_Nordhausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Nordhausen_Nord'])
        )}))

    energysystem.add(solph.components.Source(
        label='PV_Freifeld_Gera', 
        outputs={b_el: solph.Flow(fix=data_PV_Freifeld_Gera,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Gera_Ost'])
        )}))

    energysystem.add(solph.components.Source(
        label='PV_Freifeld_Hildburghausen', 
        outputs={b_el: solph.Flow(fix=data_PV_Freifeld_Hildburghausen,
                                        custom_attributes={'emission_factor': Parameter_PV_Wind_2030['PV_Freifeld']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_PV_Freifeld, 
                                                                    maximum=Parameter_PV_Wind_2030['PV_Freifeld']['Potential_Hildburghausen_Südwest'])
        )}))
    
    
    #------------------------------------------------------------------------------
    # Hydroenergy
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Hydro power plant', 
        outputs={b_el: solph.Flow(fix=data_Wasserkraft,
                                        custom_attributes={'emission_factor': Parameter_Wasserkraft_2030['Wasserkraft']['EE_Faktor']},
                                        investment=solph.Investment(ep_costs=epc_Wasserkraft, 
                                                                    minimum=Parameter_Wasserkraft_2030['Wasserkraft']['Potential'], 
                                                                    maximum = Parameter_Wasserkraft_2030['Wasserkraft']['Potential'])
        )}))
    
    #------------------------------------------------------------------------------
    # Solar thermal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='ST', 
        outputs={b_dist_heat: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Solarthermie'], 
                                          custom_attributes={'emission_factor': Parameter_ST_2030['Solarthermie']['EE_Faktor']},
                                          investment=solph.Investment(ep_costs=epc_ST, 
                                                                      maximum=Parameter_ST_2030['Solarthermie']['Potential'])
        )}))
    
    """
    Imports
    """
    
    #------------------------------------------------------------------------------
    # Electricity import from grid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Electricity',
        outputs={b_el: solph.Flow(nominal_value=Parameter_Stromnetz_2030['Strom']['Max_Bezugsleistung'],
                                  variable_costs = [i+Parameter_Stromnetz_2030['Strom']['Netzentgelt_Arbeitspreis'] for i in Preise_2030_Stundenwerte['Strompreis_2030']],
                                  custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Strom_2030']},
                                  
            )}))
    
    #------------------------------------------------------------------------------
    # Import Solid fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_solid_fuel',
        outputs={b_bio: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                         custom_attributes={'BiogasNeuanlagen_factor': 1},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # solid Biomass
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Wood',
        outputs={b_bioWood: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Biomassepreis_2030'],
                                             custom_attributes={'Biomasse_factor': 1},
                                       
        )}))
    
    #------------------------------------------------------------------------------
    # Import Brown-coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_brown_coal',
        outputs={b_solidf: solph.Flow(variable_costs = Import_Braunkohlepreis_2030,
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=data_Systemeigenschaften['System']['Menge_Braunkohle']*number_of_time_steps,
                                    custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Braunkohle']},
        )}))
    
    #------------------------------------------------------------------------------
    # Import hard coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_hard_coal',
        outputs={b_solidf: solph.Flow(variable_costs = Import_Steinkohlepreis_2030,
                                    fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                    #nominal_value = 1,
                                    investment = solph.Investment(ep_costs=0),
                                    summed_max=data_Systemeigenschaften['System']['Menge_Steinkohle']*number_of_time_steps,
                                    custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Steinkohle']},
                                    
        )}))
    
    #------------------------------------------------------------------------------
    # Import Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Gas',
        outputs={b_gas: solph.Flow(variable_costs = Import_Erdgaspreis_2030,
                                         custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Erdgas']},
                                   
        )}))
    
    #------------------------------------------------------------------------------
    # Import Oil
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Oil',
        outputs={b_oil_fuel: solph.Flow(variable_costs = Import_Oelpreis_2030,
                                                     custom_attributes={'CO2_factor': data_Systemeigenschaften['System']['Emission_Oel']}
                                               
            )}))
    
    #------------------------------------------------------------------------------
    # Import Synthetic fuel
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Source(
        label='Import_Synthetic_fuel',
        outputs={b_oil_fuel: solph.Flow(variable_costs = Preise_2030_Stundenwerte['Synthetische_Kraftstoffe_2030'],
            )}))
    
    """
    Energy storage
    """
    
    #------------------------------------------------------------------------------
    # Electricity storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Battery',
        inputs={b_el: solph.Flow()},
        outputs={b_el: solph.Flow()},
        loss_rate=0,
        inflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Natriumspeicher, 
                                        maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Natriumspeicher']['Potential'],
                                        )
        ))
    
    #------------------------------------------------------------------------------
    # Heat storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label='Heat storage',
        inputs={b_dist_heat: solph.Flow(
                                  custom_attributes={'keywordWSP': 1},
                                  nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                  #nonconvex=solph.NonConvex()
                                    )},
        outputs={b_dist_heat: solph.Flow(
                                    custom_attributes={'keywordWSP': 1},
                                    nominal_value=float(Parameter_Waermespeicher_2030['Waermespeicher']['Potential']/Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
                                    #nonconvex=solph.NonConvex()
                                    )},
        loss_rate=float(Parameter_Waermespeicher_2030['Waermespeicher']['Verlustrate']/24),
        inflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor=Parameter_Waermespeicher_2030['Waermespeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Waermespeicher_2030['Waermespeicher']['Anfangsspeicherlevel'],
        balanced=bool(Parameter_Waermespeicher_2030['Waermespeicher']['balanced']),
        invest_relation_input_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Waermespeicher_2030['Waermespeicher']['inverse_C_Rate']),
        nominal_storage_capacity = solph.Investment(ep_costs=epc_Waermespeicher, 
                                     )
        ))
    
    
    #------------------------------------------------------------------------------
    # Pumped hydro storage
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.GenericStorage(
        label="Pumped_hydro_storage",
        inputs={b_el: solph.Flow()},
        outputs={b_el: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['balanced']),
        inflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Pumpspeicherkraftwerk,
                                      minimum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential_min'],
                                      maximum = Parameter_Pumpspeicher_2030['Pumpspeicherkraftwerk']['Potential'])
        ))
    
    #------------------------------------------------------------------------------
    # Gas storage
    #------------------------------------------------------------------------------ 
    energysystem.add(solph.components.GenericStorage(
        label="Gas storage",
        inputs={b_gas: solph.Flow()},
        outputs={b_gas: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Erdgasspeicher, 
                                      maximum = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Erdgasspeicher']['Potential'])    
        ))
    
    #------------------------------------------------------------------------------
    # H2 Storage
    #------------------------------------------------------------------------------    
    energysystem.add(solph.components.GenericStorage(
        label="H2_storage",
        inputs={b_H2: solph.Flow()},
        outputs={b_H2: solph.Flow()},
        loss_rate=0,
        balanced=bool(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['balanced']),
        inflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Einspeicherwirkungsgrad'],
        outflow_conversion_factor = Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Ausspeicherwirkungsgrad'],
        initial_storage_level=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Anfangsspeicherlevel'],
        invest_relation_input_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        invest_relation_output_capacity = 1/(Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['inverse_C_Rate']),
        investment = solph.Investment(ep_costs=epc_Wasserstoffspeicher, 
                                      maximum=Parameter_Natrium_Erdgas_Wasserstoffspeicher_2030['Wasserstoffspeicher']['Potential'])    
        ))
    
    """
    Transformers
    """
    #------------------------------------------------------------------------------
    # Elektrolysis
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Elektrolysis",
        inputs={b_el: solph.Flow()},
        outputs={b_H2: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrolyse, 
                                                                 maximum=Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Potential']))},
        conversion_factors={b_H2: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrolyse']['Wirkungsgrad']},
        ))
    
    #------------------------------------------------------------------------------
    # Electric boiler
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Electric boiler",
        inputs={b_el: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(ep_costs=epc_Elektrodenheizkessel))},
        conversion_factors={b_dist_heat: Parameter_Elektrolyse_Elektrodenheizkessel_2030['Elektrodenheizkessel']['Wirkungsgrad']}    
        ))
    
    #------------------------------------------------------------------------------
    # Gas and Steam turbine
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='GuD',
        inputs={b_gas: solph.Flow(custom_attributes={'time_factor' :1})},
        outputs={b_el: solph.Flow(investment=solph.Investment(ep_costs=epc_GuD,
                                                              maximum =Parameter_GuD_2030['GuD']['Potential'])),
                 b_dist_heat: solph.Flow()},
        conversion_factors={b_el: Parameter_GuD_2030['GuD']['Wirkungsgrad_el'], 
                            b_dist_heat: Parameter_GuD_2030['GuD']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Fuel cells
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="fuelcell",
        inputs={b_H2: solph.Flow()},
        outputs={b_el: solph.Flow(investment = solph.Investment(ep_costs=epc_Brennstoffzelle, 
                                                                maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Potential']))},
        conversion_factors={b_el: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Brennstoffzelle']['Wirkungsgrad']}
        ))
    
    #------------------------------------------------------------------------------
    # Methanisation
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Methanisation",
        inputs={b_H2: solph.Flow()},
        outputs={b_gas: solph.Flow(investment = solph.Investment(ep_costs=epc_Methanisierung, 
                                                                 maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Potential']))},
        conversion_factors={b_gas: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['Methanisierung']['Wirkungsgrad']}  
        ))
    
    #------------------------------------------------------------------------------
    # Biogas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biogas',
        inputs={b_bio: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'], 
                                        #nominal_value=1,
                                        investment = solph.Investment(ep_costs=0),
                                        custom_attributes={'BiogasBestand_factor': Parameter_Biomasse_Biogas_2030['Biogas']['BiogasBestand']})},
                                  
        outputs={b_el: solph.Flow(investment=solph.Investment(ep_costs=epc_Biogas), 
                                        custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast']),
                 b_dist_heat: solph.Flow(custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biogas']['EE_Faktor']},
                                          fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                          #nominal_value= 1
                                          investment = solph.Investment(ep_costs=0)
                                          )},
        conversion_factors={b_el: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_el'], 
                            b_dist_heat: Parameter_Biomasse_Biogas_2030['Biogas']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biomasse (for electricty production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_elec',
        inputs={b_bioWood: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                            #nominal_value = 1
                                            investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_el: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                  investment=solph.Investment(ep_costs=epc_Biomasse),
                                  custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_el: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_el']}
        ))        
    
    #------------------------------------------------------------------------------
    # Biomasse (for heat production)
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label='Biomasse_heat',
        inputs={b_bioWood: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                           #nominal_value = 1
                                           investment = solph.Investment(ep_costs=0)
                                            )},
        outputs={b_dist_heat: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                    investment=solph.Investment(ep_costs=epc_Biomasse),
                                    custom_attributes={'emission_factor': Parameter_Biomasse_Biogas_2030['Biomasse']['EE_Faktor']})},
        conversion_factors={b_dist_heat: Parameter_Biomasse_Biogas_2030['Biomasse']['Wirkungsgrad_th']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung mit bereits bestehenden Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feedin_existing",
        inputs={b_bio: solph.Flow(custom_attributes={'BiogasBestand_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['BiogasBestand']},
                                        fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        #nominal_value = 1
                                        )},
        outputs={b_gas: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Bestandsanlagen),
                                   )},
        conversion_factors={b_gas: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Bestandsanlagen']['EE_Faktor']}
        ))
    
    #------------------------------------------------------------------------------
    # Biogaseinspeisung ohne bereits bestehende Biogasanlagen
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Biogas_feed_in_new",
        inputs={b_bio: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                        investment = solph.Investment(ep_costs=0)
                                        )},
        outputs={b_gas: solph.Flow(fix=Einspeiseprofile_Stundenwerte['Grundlast'],
                                   investment = solph.Investment(ep_costs=epc_Biogaseinspeisung_Neuanlagen),
                                   )},
        conversion_factors={b_gas: Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['Wirkungsgrad_el']},
        custom_attributes={'emission_factor': Parameter_Biogaseinspeisung_2030['Biogaseinspeisung_Neuanlagen']['EE_Faktor']}
                                    
        ))
    
    # -----------------------------------------------------------------------------
    # Hydroden feed-in
    # -----------------------------------------------------------------------------
    maximale_Wasserstoffeinspeisung_Lastgang = [None] * len(Last_Gas_Zusammen)
    maximale_Wasserstoffeinspeisung=0
    for a in range(0, len(Last_Gas_Zusammen)):
        maximale_Wasserstoffeinspeisung_Lastgang[a]=(Last_Gas_Zusammen[a]*(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Potential']))/(Parameter_Wasserstoffeinspeisung_2030['Wasserstoffeinspeisung']['Wirkungsgrad'])
        if maximale_Wasserstoffeinspeisung_Lastgang[a] > maximale_Wasserstoffeinspeisung:
            maximale_Wasserstoffeinspeisung = maximale_Wasserstoffeinspeisung_Lastgang[a]
    
    energysystem.add(solph.components.Converter(
        label='Hydrogen_feedin',
        inputs={b_H2: solph.Flow()},
        outputs={b_gas: solph.Flow(fix=maximale_Wasserstoffeinspeisung_Lastgang,
                                   investment=solph.Investment(ep_costs=epc_Wasserstoffeinspeisung, 
                                                               maximum=max(maximale_Wasserstoffeinspeisung_Lastgang)))}
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump_river
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_water",
        inputs={b_el: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Fluss, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['Potential']))},
        conversion_factors={b_dist_heat: Parameter_Waermepumpen_2030['Waermepumpe_Fluss']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Heatpump: Recovery heat
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="Heatpump_air",
        inputs={b_el: solph.Flow()},
        outputs={b_dist_heat: solph.Flow(investment = solph.Investment(ep_costs=epc_Waermepumpe_Abwaerme, 
                                                                  maximum=Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['Potential']))},
        conversion_factors={b_dist_heat: Parameter_Waermepumpen_2030['Waermepumpe_Abwaerme']['COP']},    
        ))
    
    #------------------------------------------------------------------------------
    # Power-to-Liquid
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="PtL",
        inputs={b_H2: solph.Flow()},
        outputs={b_oil_fuel: solph.Flow(investment = solph.Investment(ep_costs=epc_PtL, 
                                                                             maximum=Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Potential']))},
        conversion_factors={b_oil_fuel: Parameter_Brennstoffzelle_Methanisierung_PtL_2030['PtL']['Wirkungsgrad']}
        ))
    
    #------------------------------------------------------------------------------
    # Solid biomass in the same bus as coal
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Converter(
        label="BioTransformer",
        inputs={b_bioWood: solph.Flow()},
        outputs={b_solidf: solph.Flow()},
        ))
    
    """
    Excess energy capture sinks 
    """
    #------------------------------------------------------------------------------
    # Überschuss Senke für Strom
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_el', 
        inputs={b_el: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Gas
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_gas2', 
        inputs={b_gas: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Oel/Kraftstoffe
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_oil_fuel', 
        inputs={b_oil_fuel: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Biomasse
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_bio', 
        inputs={b_bio: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Waerme
    #------------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_distheat', 
        inputs={b_dist_heat: solph.Flow(variable_costs = 10000000
        )}))
    #------------------------------------------------------------------------------
    # Überschuss Senke für Wasserstoff
    #-----------------------------------------------------------------------------
    energysystem.add(solph.components.Sink(
        label='excess_b_H2', 
        inputs={b_H2: solph.Flow(variable_costs = 10000000
        )}))
    
    
    
    return energysystem
