import os

import pandas as pd
from oemof import network, solph
from oemof.tools import economics

from src.preprocessing.create_input_dataframe import createDataFrames


def basic_example(PERMUATION: str) -> solph.EnergySystem:
    YEAR, VARIATION = PERMUATION.split("_")
    YEAR = int(YEAR)
    sequences, scalars = createDataFrames()

    # ------------------------------------------------------------------------------
    # Hilfskonstanten
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Parametrisierung
    # ------------------------------------------------------------------------------

    # ------------------------------------------------------------------------------
    # Modellbildung
    # ------------------------------------------------------------------------------
    date_time_index = pd.date_range("1/1/2025", periods=8760, freq="h")
    energysystem = solph.EnergySystem(
        timeindex=date_time_index, infer_last_interval=False
    )

    el = solph.Bus(label="el")

    energysystem.add(el)

    energysystem.add(
        solph.components.Sink(
            inputs={el: solph.Flow(nominal_value=10)},
        )
    )

    energysystem.add(
        solph.components.Source(
            outputs={el: solph.Flow()},
        )
    )

    return energysystem
