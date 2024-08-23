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
        inputs={b_was: solph.Flow(fix=Last_H2_Zusammen, 
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
    
    

    return energysystem
