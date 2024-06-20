# -*- coding: utf-8 -*-
"""
Created on Fri Mar 15 16:50:12 2024

@author: treinhardt01
"""

from graphviz import Digraph
from oemof import solph, network
import logging
import os 


def draw_energy_system(energy_system=None, filepath="network", img_format=None, legend=False):
    """Draw the energy system with Graphviz.
    
    Parameters
    ----------
    energy_system: `oemof.solph.network.EnergySystem`
        The oemof energy stystem
        
    filepath: str
        path, where the rendered result shall be saved, if an extension is provided, the format will be 
        automatically adapted except if the `img_format` argument is provided
        Default: "network"
        
    img_format: str
        extension of one of the available image formats of graphviz (e.g "png", "svg", "pdf" ...)
        Default: "pdf"

    legend: bool
        specify, whether a legend will be added to the graph or not
        Default: False

    Returns
    -------
    None: render the generated dot graph in the filepath
    """
    
    file_name, file_ext = os.path.splitext(filepath)
    
    if img_format is None:
        if file_ext != "":
            img_format = file_ext.replace(".", "")
        else:
            img_format = "pdf"
    
    # Creates the Directed-Graph
    dot = Digraph(filename=file_name, format=img_format)
    
    if legend is True:
        dot.node("Bus", shape='rectangle', fontsize="10")
        dot.node("Sink", shape='trapezium', fontsize="10", color="red")
        dot.node("Source", shape='invtrapezium', fontsize="10", color="blue")
        dot.node("Transformer", shape='rectangle', fontsize="10", color="yellow")
        dot.node("Storage", shape='rectangle', style='dashed', fontsize="10", color="green")
    
    busses = []
    # draw a node for each of the network's component. The shape depends on the component's type
    for nd in energy_system.nodes:
        if isinstance(nd, solph.Bus) or isinstance(nd, network.Node):
            dot.node(nd.label, shape='rectangle', fontsize="15", fixedsize='shape', width='2.1', height='0.6')
            # keep the bus reference for drawing edges later
            busses.append(nd)
        if isinstance(nd, solph.components.Sink):
            dot.node(nd.label, shape='trapezium', fontsize="15", color="red")
        if isinstance(nd, solph.components.Source):
            dot.node(nd.label, shape='invtrapezium', fontsize="15", color="blue")
        if isinstance(nd, solph.components.Converter):
            dot.node(nd.label, shape='rectangle', fontsize="15", color="yellow")
        if isinstance(nd, solph.components.GenericStorage):
            dot.node(nd.label, shape='rectangle', style='dashed', fontsize="15", color="green")

    # draw the edges between the nodes based on each bus inputs/outputs        
    for bus in busses:
        for component in bus.inputs:
            #draw an arrow from the component to the bus
            dot.edge(component.label, bus.label)
        for component in bus.outputs:
            #draw an arrow from the bus to the component
            dot.edge(bus.label, component.label)

    dot.view()