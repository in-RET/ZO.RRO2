# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 14:11:09 2025

Module to collect useful functions for economic calculation.

This file is part of project ZO.RRO II, Hochschule Nordhausen (Hinderrike Hauer-Berghuis). 

SPDX-License-Identifier: MIT

@author: rbala
"""


def annuity(capex, n, wacc, u=None, cost_decrease=0):
    r"""Calculates the annuity of an initial investment 'capex', considering
    the cost of capital 'wacc' during a project horizon 'n'

    In case of a single initial investment, the employed formula reads:

    .. math::
        \text{annuity} = \text{capex} \cdot
            \frac{(\text{wacc} \cdot (1+\text{wacc})^n)}
            {((1 + \text{wacc})^n - 1)}

    In case of longer lifetime of technology than horizon of the analysis (e.g. pumped hydrostorage) at fixed intervals
    'u', the formula yields:

    .. math::
        \text{annuity} = \text{capex} \cdot
                  \frac{(\text{wacc} \cdot (1+\text{wacc})^n)}
                  {((1 + \text{wacc})^n - 1)} \cdot \left(
                  1 - \frac{u - n}{u \cdot (1+\text{wacc})^n}
                  

    Parameters
    ----------
    capex : float
        Capital expenditure for first investment. Net Present Value (NPV) or
        Net Present Cost (NPC) of investment
    n : int
        Horizon of the analysis, or number of years the annuity wants to be
        obtained for (n>=1)
    wacc : float
        Weighted average cost of capital (0<wacc<1)
    u : int
        Lifetime of the investigated investment. Might be larger than the
        analysis horizon, 'n', meaning it will have a residual value.
        Takes value 'n' if not specified otherwise (u>=1)
    Returns
    -------
    float
        annuity
    """
    if u is None:
        u = n

    if (
        (n < 1)
        or (wacc < 0 or wacc > 1)
        or (u < 1)
        ):
        raise ValueError("Input arguments for 'annuity' out of bounds!")
        
    # if u>n: # 
    #     return (
    #         capex
    #         * (wacc * (1 + wacc) ** n)
    #         / ((1 + wacc) ** n - 1)
    #         * (
    #             1 - (u - n) / (u * (1 + wacc) ** n)
    #             )
    #     )
    # else:
    #     n = u
        
    #     return (
    #         capex
    #         * (wacc * (1 + wacc) ** n)
    #         / ((1 + wacc) ** n - 1)
    #         * (
    #             1 - (u - n) / (u * (1 + wacc) ** n)
    #             )
    #     )
        
    if u <= n:
        n = u

    # Gemeinsame Formel
    return (
        capex
        * (wacc * (1 + wacc) ** n)
        / ((1 + wacc) ** n - 1)
        * (1 - (u - n) / (u * (1 + wacc) ** n))
    )