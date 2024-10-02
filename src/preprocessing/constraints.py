# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 11:21:33 2024

@author: rbala
"""
from oemof.solph import constraints
import pyomo.environ as po
from oemof.solph._plumbing import sequence 

#------------------------------------------------------------------------------
# Constraint CO2 Begrenzung 
#------------------------------------------------------------------------------
def CO2_limit(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='CO2_factor',
                           flows=flows,
                           limit=limit)

def emission_factor(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='emission_factor',
                           flows=flows,
                           limit=limit)


# def generic_integral_limit(om, keyword, flows=None, limit=None):
   
#     if flows is None:
#         flows = {}
#         for (i, o) in om.flows:
#             if hasattr(om.flows[i, o], keyword):
#                 flows[(i, o)] = om.flows[i, o]

#     else:
#         for (i, o) in flows:
#             if not hasattr(flows[i, o], keyword):
#                 raise AttributeError(
#                     ('Flow with source: {0} and target: {1} '
#                       'has no attribute {2}.').format(
#                         i.label, o.label, keyword))

#     limit_name = "integral_limit_"+keyword

#     setattr(om, limit_name, po.Expression(
#         expr=sum(om.flow[inflow, outflow,p,t]
#                   * om.timeincrement[t]
#                   * sequence(getattr(flows[inflow, outflow], keyword))[t]
#                   for (inflow, outflow) in flows
#                   for p,t in om.TIMESTEPS)))

#     setattr(om, limit_name+"_constraint", po.Constraint(
#         expr=(getattr(om, limit_name) <= limit)))

#     return om

#------------------------------------------------------------------------------
# Gas- und Dampfkraftwerkseinschränkung
#------------------------------------------------------------------------------

def GuD_time(om, flows=None, limit=None, Starttime=None, Endtime=None):
    

    if flows is None:
        flows = {}
        for (i, o) in om.flows:
            if hasattr(om.flows[i, o], 'time_factor'):
                flows[(i, o)] = om.flows[i, o]

    else:
        for (i, o) in flows:
            if not hasattr(flows[i, o], 'time_factor'):
                raise AttributeError(
                    # ('Flow with source: {0} and target: {1} '
                    #  'has no attribute time_factor.').format(i.label, 
                    #                                              o.label))
                    ('Flow with source: {0} and target: {1} '
                      'has no attribute {2}.').format(i.label,o.label, 'time_factor'))
                
    limit_name = "integral_limit_"+ 'time_factor'
    #reduced_timesteps = [x for x in om.TIMESTEPS if x > Starttime and x < Endtime]

    reduced_timesteps =[]
    for p, t in om.TIMEINDEX:
        if t > Starttime and t < Endtime:
            reduced_timesteps.append(om.TIMEINDEX[t])

    # om.total_GuD =  po.Expression(
    #     expr=sum(om.flow[inflow, outflow, t] * om.timeincrement[t] *
    #              sequence(getattr(flows[inflow, outflow], 'time_factor'))[t]
    #              #flows[inflow, outflow].time_factor
    #              for (inflow, outflow) in flows
    #              for t in reduced_timesteps))
    
    setattr(
            om,
            limit_name,
            po.Expression(
                expr=sum(
                    om.flow[inflow, outflow,p, t]
                    * om.timeincrement[t]
                    * sequence(getattr(flows[inflow, outflow], 'time_factor'))[t]
                    for (inflow, outflow) in flows
                    for p,t in reduced_timesteps
                )
            ),
        )
    
    setattr(
            om,
            limit_name + "_constraint",
            po.Constraint(expr=(getattr(om, limit_name) <= limit)),
        )


    #om.GuD_time = po.Constraint(expr=om.total_GuD <= limit)

    return om


#------------------------------------------------------------------------------
# Constraint BiogasBestand Begrenzung
#------------------------------------------------------------------------------
def BiogasBestand_limit(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='BiogasBestand_factor',
                           flows=flows,
                           limit=limit)
    
#------------------------------------------------------------------------------
# Constraint Biogas Neuanlagen Begrenzung
#------------------------------------------------------------------------------
def BiogasNeuanlagen_limit(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='BiogasNeuanlagen_factor',
                           flows=flows,
                           limit=limit)
    
#------------------------------------------------------------------------------
# Constraint Biomasse Begrenzung
#------------------------------------------------------------------------------
def Biomasse_limit(om, flows=None, limit=None):

    constraints.generic_integral_limit(om,
                           keyword='Biomasse_factor',
                           flows=flows,
                           limit=limit)