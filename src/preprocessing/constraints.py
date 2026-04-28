# -*- coding: utf-8 -*-
"""
Created on Wed Oct  2 11:21:33 2024

@author: rbala
"""
from oemof.solph import constraints
import pyomo.environ as po
from oemof.solph._plumbing import sequence 
import warnings
warnings.filterwarnings("ignore")

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
    

def calculate_keyword_limit_sum(om, keyword_limit, flows=None):
    flows_limit = _check_and_set_flows(om, flows, keyword_limit)
    limit_sum = sum(
        om.flow[inflow, outflow, p, t]
        * om.timeincrement[t]
        * sequence(getattr(flows_limit[inflow, outflow], keyword_limit))[t]
        for (inflow, outflow) in flows_limit
        for p, t in om.TIMEINDEX
    )
    return limit_sum

def import_export_bilanz(om, keyword, keyword_limit, flows=None):
    flows_main = _check_and_set_flows(om, flows, keyword)
    limit_name = "integral_limit_" + keyword

    # Integral-Ausdruck für das Hauptkeyword
    setattr(
        om,
        limit_name,
        po.Expression(
            expr=sum(
                om.flow[inflow, outflow, p, t]
                * om.timeincrement[t]
                * sequence(getattr(flows_main[inflow, outflow], keyword))[t]
                for (inflow, outflow) in flows_main
                for p, t in om.TIMEINDEX
            )
        ),
    )

    # Limit berechnen (intern)
    limit = calculate_keyword_limit_sum(om, keyword_limit, flows)

    # Constraint mit dynamischer Schranke
    setattr(
        om,
        limit_name + "_constraint",
        po.Constraint(expr=(getattr(om, limit_name) <= limit)),
    )

    return om




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
    
#------------------------------------------------------------------------------
# Bilanziell erneuerbar
#------------------------------------------------------------------------------

def Bilanziell_erneuerbar(om, sim_data, model_name, factor):
    Sum_load = 0
    if model_name == 'BS_regionalization':
        region = ['north', 'middle', 'east', 'swest']
        for r in region:
           Sum_load += (sim_data['Loadprofiles']['electricity'][r].sum() + sim_data['Loadprofiles']['gas'][r].sum() + sim_data['Loadprofiles']['oil'][r].sum()+
                     sim_data['Loadprofiles']['fuel'][r].sum()+sim_data['Loadprofiles']['dist_heating'][r].sum()+sim_data['Loadprofiles']['H2'][r].sum())
    # elif model_name.endswith('utility_energy'):
    #     Sum_load += (sim_data['Loadprofiles_ne']['cooling_ghd']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['cooling_household']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['cooling_industry']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['electrical_ghd']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['electrical_household']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['electrical_industry']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['material_usage_industry']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['process_heating_ghd']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['process_heating_industry']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['space_heating_ghd']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['space_heating_household']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['space_heating_industry']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['mobility_goods']['demand_data']['total_value']+
    #                  sim_data['Loadprofiles_ne']['mobility_person']['demand_data']['total_value']
    #                  )
    else:
        Sum_load +=(sim_data['Loadprofiles']['electricity'].sum() + sim_data['Loadprofiles']['gas'].sum() + sim_data['Loadprofiles']['oil'].sum()+
                  sim_data['Loadprofiles']['fuel'].sum()+sim_data['Loadprofiles']['dist_heating'].sum()+sim_data['Loadprofiles']['H2'].sum())
    constraints.emission_limit(om, limit = -Sum_load*factor)
    
    
def _check_and_set_flows(om, flows, keyword):
    """Checks and sets flows if needed

    Parameters
    ----------
    om : oemof.solph.Model
        Model to which constraints are added.

    flows : dict
        Dictionary holding the flows that should be considered in constraint.
        Keys are (source, target) objects of the Flow. If no dictionary is
        given all flows containing the keyword attribute will be
        used.

    keyword : string
        attribute to consider

    Returns
    -------
    flows : dict
        the flows to be considered
    """
    if flows is None:
        flows = {}
        for i, o in om.flows:
            if hasattr(om.flows[i, o], keyword):
                flows[(i, o)] = om.flows[i, o]

    else:
        for i, o in flows:
            if not hasattr(flows[i, o], keyword):
                raise AttributeError(
                    (
                        "Flow with source: {0} and target: {1} "
                        "has no attribute {2}."
                    ).format(i.label, o.label, keyword)
                )

    return flows