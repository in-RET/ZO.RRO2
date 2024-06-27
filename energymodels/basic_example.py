import os

import pandas as pd

from oemof import solph, network
from oemof.tools import economics

from src.preprocessing.create_input_dataframe import createDataFrames


def basic_example(PERMUATION: str) -> solph.EnergySystem:
    YEAR, VARIATION = PERMUATION.split("_")
    YEAR = int(YEAR)
    sequences, scalars = createDataFrames()

    # ------------------------------------------------------------------------------
    # Hilfskonstanten
    # ------------------------------------------------------------------------------
    PTH_TECHNOLOGIEN = scalars["Technik_PtH"]
    PTH_ZEITREIHEN = sequences["Zeitreihen_PtH"]
    EINSPEISE_ZEITREIHEN = sequences["Einspeisung"]
    LAST_ZEITREIHEN = sequences["Lasten"]
    STROMPREISE = sequences["Strompreise"]

    # ------------------------------------------------------------------------------
    # Parametrisierung
    # ------------------------------------------------------------------------------
    # ------------------------------------------------------------------------------
    # NETZAUSBAU
    # ------------------------------------------------------------------------------
    AMORT_WP_NETZAUSBAU = PTH_TECHNOLOGIEN["WP_Luftwaerme"][
        "Amortisationszeit_Netzausbau"
    ]
    ZINSSATZ_WP_NETZAUSBAU = PTH_TECHNOLOGIEN["WP_Luftwaerme"]["Zinssatz"] / 100

    NETZAUSBAUKOSTEN = (
        PTH_TECHNOLOGIEN["WP_Luftwaerme"]["Kosten_Fernwaermenetzausbau"]
        * PTH_TECHNOLOGIEN["WP_Luftwaerme"]["Laenge_Fernwaermeleitung"]
    )
    A_WP_NETZAUSBAU = economics.annuity(
        capex=NETZAUSBAUKOSTEN, n=AMORT_WP_NETZAUSBAU, wacc=ZINSSATZ_WP_NETZAUSBAU
    )

    # ------------------------------------------------------------------------------
    # STROMNETZ
    # ------------------------------------------------------------------------------
    IMPORT_STROMPREIS_BOERSE = STROMPREISE[str(PERMUATION)]
    MAX_LEISTUNG_STROMTRAFO = 300
    EPC_STROMTRAFO = 188720  # EUR/MW

    # ------------------------------------------------------------------------------
    # Modellbildung
    # ------------------------------------------------------------------------------
    date_time_index = pd.date_range("1/1/2025", periods=8760, freq="h")
    energysystem = solph.EnergySystem(
        timeindex=date_time_index, infer_last_interval=False
    )

    # ------------------------------------------------------------------------------
    # Busse
    # ------------------------------------------------------------------------------
    b_el = network.Node(label="Strom_Netz")
    b_el_eigenerzeugung = network.Node(label="Strom_Eigenerzeugung")
    b_fern = network.Node(label="Fernwaerme")
    b_abwaerme_luftwaerme = network.Node(label="Bus_Abwaermepotential_Luftwaerme")

    energysystem.add(b_el, b_el_eigenerzeugung, b_fern, b_abwaerme_luftwaerme)

    # ------------------------------------------------------------------------------
    # Importe
    # ------------------------------------------------------------------------------
    energysystem.add(
        solph.components.Source(
            label="Import_Strom",
            outputs={
                b_el: solph.Flow(
                    nominal_value=solph.Investment(
                        ep_costs=EPC_STROMTRAFO, maximum=MAX_LEISTUNG_STROMTRAFO
                    ),
                    variable_costs=IMPORT_STROMPREIS_BOERSE,
                )
            },
        )
    )

    # ------------------------------------------------------------------------------
    # PV
    # ------------------------------------------------------------------------------
    CAPEX_PV = PTH_TECHNOLOGIEN["PV"]["CAPEX Erzeugeranlagen"]
    OPEX_PV = PTH_TECHNOLOGIEN["PV"]["OPEX Erzeugeranlagen"] / 100
    AMORT_A_PV = PTH_TECHNOLOGIEN["PV"]["Amortisierungszeitraum"]
    ZINSSATZ_PV = PTH_TECHNOLOGIEN["PV"]["Zinssatz"] / 100

    A_PV = economics.annuity(capex=CAPEX_PV, n=AMORT_A_PV, wacc=ZINSSATZ_PV)
    B_PV = CAPEX_PV * OPEX_PV
    EPC_PV = A_PV + B_PV

    MAX_LEISTUNG_PV = PTH_TECHNOLOGIEN["PV"]["max_Leistung"]
    MIN_LEISTUNG_PV = PTH_TECHNOLOGIEN["PV"]["min_Leistung"]

    energysystem.add(
        solph.components.Source(
            label="PV",
            outputs={
                b_el_eigenerzeugung: solph.Flow(
                    fix=EINSPEISE_ZEITREIHEN["pv"],
                    # custom_attributes = {"emission_factor": 1*(-1)},
                    nominal_value=solph.Investment(
                        ep_costs=EPC_PV, maximum=MAX_LEISTUNG_PV
                    ),
                )
            },
        )
    )

    # ------------------------------------------------------------------------------
    # WIND
    # ------------------------------------------------------------------------------
    MAX_LEISTUNG_WIND = 100  # MW
    EINSPEISEKOSTEN_WIND = 70  # EUR/MWh

    energysystem.add(
        solph.components.Source(
            label="Wind",
            outputs={
                b_el_eigenerzeugung: solph.Flow(
                    fix=EINSPEISE_ZEITREIHEN["wind"],
                    # custom_attributes = {"emission_factor": 1*(-1)}
                    variable_costs=EINSPEISEKOSTEN_WIND,
                    nominal_value=solph.Investment(maximum=MAX_LEISTUNG_WIND),
                )
            },
        )
    )

    # ------------------------------------------------------------------------------
    # Lasten
    # ------------------------------------------------------------------------------
    energysystem.add(
        solph.components.Sink(
            label="Last_Strom",
            inputs={
                b_el: solph.Flow(
                    fix=LAST_ZEITREIHEN["strom"],
                    nominal_value=1,
                    # custom_attributes={"emission_factor": 1}
                )
            },
        )
    )

    energysystem.add(
        solph.components.Sink(
            label="Last_Heisswasser",
            inputs={
                b_fern: solph.Flow(
                    fix=LAST_ZEITREIHEN["fernwaerme"],
                    nominal_value=1,
                    # custom_attributes={"emission_factor": 0.5},
                )
            },
        )
    )

    # ------------------------------------------------------------------------------
    # Überschüsse
    # ------------------------------------------------------------------------------
    energysystem.add(
        solph.components.Sink(
            label="Ueberschuss_Eigenerzeugung",
            inputs={b_el_eigenerzeugung: solph.Flow()},
        )
    )

    energysystem.add(
        solph.components.Sink(label="Ueberschuss_Strom", inputs={b_el: solph.Flow()})
    )

    energysystem.add(
        solph.components.Sink(
            label="Ueberschuss_Fernwaerme", inputs={b_fern: solph.Flow()}
        )
    )

    # ------------------------------------------------------------------------------
    # Netztrafos
    # ------------------------------------------------------------------------------
    energysystem.add(
        solph.components.Converter(
            label="Trafo_Eigenerzeugung_Netz",
            inputs={b_el_eigenerzeugung: solph.Flow()},
            outputs={b_el: solph.Flow(variable_costs=18)},
        )
    )

    # ------------------------------------------------------------------------------
    # Wärmepumpen
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # LUFTWAERME WAERMEPUMPE
    # ------------------------------------------------------------------------------
    CAPEX_LUFTWAERME_ERZEUGERANLAGEN = PTH_TECHNOLOGIEN["WP_Luftwaerme"][
        "CAPEX Erzeugeranlagen"
    ]
    CAPEX_LUFTWAERME_NEBENANLAGEN = PTH_TECHNOLOGIEN["WP_Luftwaerme"][
        "CAPEX Nebenanlagen"
    ]
    OPEX_LUFTWAERME_ERZEUGERANLAGEN = (
        PTH_TECHNOLOGIEN["WP_Luftwaerme"]["OPEX Erzeugeranlagen"] / 100
    )
    OPEX_LUFTWAERME_NEBENANLAGEN = (
        PTH_TECHNOLOGIEN["WP_Luftwaerme"]["OPEX Nebenanlagen"] / 100
    )
    AMORT_A_WP = PTH_TECHNOLOGIEN["WP_Luftwaerme"]["Amortisierungszeitraum"]
    ZINSSATZ_WP = PTH_TECHNOLOGIEN["WP_Luftwaerme"]["Zinssatz"] / 100

    A_LUFTWAERME_ERZEUGERANLAGEN = economics.annuity(
        capex=CAPEX_LUFTWAERME_ERZEUGERANLAGEN, n=AMORT_A_WP, wacc=ZINSSATZ_WP
    )
    B_LUFTWAERME_ERZEUGERANLAGEN = (
        CAPEX_LUFTWAERME_ERZEUGERANLAGEN * OPEX_LUFTWAERME_ERZEUGERANLAGEN
    )
    EPC_LUFTWAERME_ERZEUGERANLAGEN = (
        A_LUFTWAERME_ERZEUGERANLAGEN + B_LUFTWAERME_ERZEUGERANLAGEN
    )

    A_LUFTWAERME_NEBENANLAGEN = economics.annuity(
        capex=CAPEX_LUFTWAERME_NEBENANLAGEN, n=AMORT_A_WP, wacc=ZINSSATZ_WP
    )
    B_LUFTWAERME_NEBENANLAGEN = (
        CAPEX_LUFTWAERME_NEBENANLAGEN * OPEX_LUFTWAERME_NEBENANLAGEN
    )
    EPC_LUFTWAERME_NEBENANLAGEN = A_LUFTWAERME_NEBENANLAGEN + B_LUFTWAERME_NEBENANLAGEN

    EPC_LUFTWAERME = (
        EPC_LUFTWAERME_ERZEUGERANLAGEN + EPC_LUFTWAERME_NEBENANLAGEN + A_WP_NETZAUSBAU
    )
    MAX_LEISTUNG_LUFTWAERME = PTH_TECHNOLOGIEN["WP_Luftwaerme"]["max_Leistung"]
    CONV_FACT_EL_LUFTWAERME = PTH_ZEITREIHEN["conversion_factor_WP_Luftwaerme_el"]
    CONV_FACT_TH_LUFTWAERME = PTH_ZEITREIHEN["conversion_factor_WP_Luftwaerme_th"]
    ABWAERME_POTENTIAL_LUFTWAERME = PTH_ZEITREIHEN["AbwaermePotenzial_Luftwaerme"]

    if YEAR < 2040:
        energysystem.add(
            solph.components.Source(
                label="Abwaermepotential_Luftwaerme",
                outputs={
                    b_abwaerme_luftwaerme: solph.Flow(
                        nominal_value=1, fix=ABWAERME_POTENTIAL_LUFTWAERME
                    )
                },
            )
        )

        energysystem.add(
            solph.components.Converter(
                label="WP_Luftwaerme",
                inputs={b_el: solph.Flow(), b_abwaerme_luftwaerme: solph.Flow()},
                outputs={
                    b_fern: solph.Flow(
                        nominal_value=solph.Investment(
                            ep_costs=EPC_LUFTWAERME, maximum=MAX_LEISTUNG_LUFTWAERME
                        ),
                        custom_attributes={"emission_factor": 1 * (-1)},
                    )
                },
                conversion_factors={
                    b_el: CONV_FACT_EL_LUFTWAERME,
                    b_abwaerme_luftwaerme: CONV_FACT_TH_LUFTWAERME,
                },
            )
        )

    # ------------------------------------------------------------------------------
    # INDUSTRIE WAERMEPUMPE
    # ------------------------------------------------------------------------------
    CAPEX_INDUSTRIE_ERZEUGERANLAGEN = PTH_TECHNOLOGIEN["WP_Industrie"][
        "CAPEX Erzeugeranlagen"
    ]
    CAPEX_INDUSTRIE_NEBENANLAGEN = PTH_TECHNOLOGIEN["WP_Industrie"][
        "CAPEX Nebenanlagen"
    ]
    OPEX_INDUSTRIE_ERZEUGERANLAGEN = (
        PTH_TECHNOLOGIEN["WP_Industrie"]["OPEX Erzeugeranlagen"] / 100
    )
    OPEX_INDUSTRIE_NEBENANLAGEN = (
        PTH_TECHNOLOGIEN["WP_Industrie"]["OPEX Nebenanlagen"] / 100
    )
    AMORT_A_WP = PTH_TECHNOLOGIEN["WP_Industrie"]["Amortisierungszeitraum"]
    ZINSSATZ_WP = PTH_TECHNOLOGIEN["WP_Industrie"]["Zinssatz"] / 100

    A_INDUSTRIE_ERZEUGERANLAGEN = economics.annuity(
        capex=CAPEX_INDUSTRIE_ERZEUGERANLAGEN, n=AMORT_A_WP, wacc=ZINSSATZ_WP
    )
    B_INDUSTRIE_ERZEUGERANLAGEN = (
        CAPEX_INDUSTRIE_ERZEUGERANLAGEN * OPEX_INDUSTRIE_ERZEUGERANLAGEN
    )
    EPC_INDUSTRIE_ERZEUGERANLAGEN = (
        A_INDUSTRIE_ERZEUGERANLAGEN + B_INDUSTRIE_ERZEUGERANLAGEN
    )

    A_INDUSTRIE_NEBENANLAGEN = economics.annuity(
        capex=CAPEX_INDUSTRIE_NEBENANLAGEN, n=AMORT_A_WP, wacc=ZINSSATZ_WP
    )
    B_INDUSTRIE_NEBENANLAGEN = (
        CAPEX_INDUSTRIE_NEBENANLAGEN * OPEX_INDUSTRIE_NEBENANLAGEN
    )
    EPC_INDUSTRIE_NEBENANLAGEN = A_INDUSTRIE_NEBENANLAGEN + B_INDUSTRIE_NEBENANLAGEN

    EPC_INDUSTRIE = (
        EPC_INDUSTRIE_ERZEUGERANLAGEN + EPC_INDUSTRIE_NEBENANLAGEN + A_WP_NETZAUSBAU
    )
    MAX_LEISTUNG_INDUSTRIE = PTH_TECHNOLOGIEN["WP_Industrie"]["max_Leistung"]
    COP_WP_INDUSTRIE = PTH_ZEITREIHEN["COP_WP_Luftwaerme"]

    if YEAR > 2025:
        energysystem.add(
            solph.components.Converter(
                label="WP_Industrie",
                inputs={b_el: solph.Flow()},
                outputs={
                    b_fern: solph.Flow(
                        nominal_value=solph.Investment(
                            ep_costs=EPC_INDUSTRIE, maximum=MAX_LEISTUNG_INDUSTRIE
                        ),
                        custom_attributes={"emission_factor": 1 * (-1)},
                    )
                },
                conversion_factors={b_fern: COP_WP_INDUSTRIE},
            )
        )

    # ------------------------------------------------------------------------------
    # Elektrodenheizkessel
    # ------------------------------------------------------------------------------
    CAPEX_EHK = PTH_TECHNOLOGIEN["Elektrodenheizkessel"]["CAPEX Erzeugeranlagen"]
    OPEX_EHK = PTH_TECHNOLOGIEN["Elektrodenheizkessel"]["OPEX Erzeugeranlagen"] / 100
    AMORT_A_EHK = PTH_TECHNOLOGIEN["Elektrodenheizkessel"]["Amortisierungszeitraum"]
    ZINSSATZ_EHK = PTH_TECHNOLOGIEN["Elektrodenheizkessel"]["Zinssatz"] / 100
    A_EHK = economics.annuity(capex=CAPEX_EHK, n=AMORT_A_EHK, wacc=ZINSSATZ_EHK)
    B_EHK = 8200000 * OPEX_EHK
    EPC_EHK = A_EHK + B_EHK

    ETA_EHK = PTH_TECHNOLOGIEN["Elektrodenheizkessel"]["Wirkungsgrad_el"]
    MAX_LEISTUNG_EHK = PTH_TECHNOLOGIEN["Elektrodenheizkessel"]["max_Leistung"]

    energysystem.add(
        solph.components.Converter(
            label="Elektrodenheizkessel",
            inputs={b_el_eigenerzeugung: solph.Flow()},
            outputs={
                b_fern: solph.Flow(
                    nominal_value=solph.Investment(
                        ep_costs=EPC_EHK, maximum=MAX_LEISTUNG_EHK
                    ),
                )
            },
            conversion_factors={b_fern: ETA_EHK},
        )
    )

    return energysystem
