import os

import pandas as pd

from os import listdir
from os.path import isfile, join


def readInFiles(folder) -> dict:
    temporaryDict = {}

    for f in listdir(folder):
        if isfile(join(folder, f)) and f.endswith(".csv"):
            sheetname = f.replace(".csv", "")
            sheetdata = pd.read_csv(
                join(folder, f),
                delimiter=";",
                decimal=",",
                index_col="index",
                encoding="unicode_escape",
            )

            temporaryDict[sheetname] = pd.DataFrame(sheetdata)

    return temporaryDict


def createDataFrames() -> (dict, dict):
    dataRoot = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "preprocessing")
    )

    sequenceFolder = os.path.join(dataRoot, "sequences")
    scalarsFolder = os.path.join(dataRoot, "scalars")

    return readInFiles(sequenceFolder), readInFiles(scalarsFolder)
