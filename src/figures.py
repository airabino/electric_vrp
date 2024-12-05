import os
import sys
import time
import matplotlib
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.collections import LineCollection

default_prop_cycle = matplotlib.rcParamsDefault['axes.prop_cycle'].by_key()['color'].copy()

class Colormap():

    color_schemes = {
        'day_night': ["#e6df44", "#f0810f", "#063852", "#011a27"],
        'beach_house': ["#d5c9b1", "#e05858", "#bfdccf", "#5f968e"],
        'autumn': ["#db9501", "#c05805", "#6e6702", "#2e2300"],
        'ocean': ["#003b46", "#07575b", "#66a5ad", "#c4dfe6"],
        'forest': ["#7d4427", "#a2c523", "#486b00", "#2e4600"],
        'aqua': ["#004d47", "#128277", "#52958b", "#b9c4c9"],
        'field': ["#5a5f37", "#fffae1", "#524a3a", "#919636"],
        'misty': ["#04202c", "#304040", "#5b7065", "#c9d1c8"],
        'greens': ["#265c00", "#68a225", "#b3de81", "#fdffff"],
        'citroen': ["#b38540", "#563e20", "#7e7b15", "#ebdf00"],
        'blues': ["#1e1f26", "#283655",  "#4d648d", "#d0e1f9"],
        'dusk': ["#363237", "#2d4262", "#73605b", "#d09683"],
        'ice': ["#1995ad", "#a1d6e2", "#bcbabe", "#f1f1f2"],
        'csu': ["#1e4d2b", "#c8c372"],
        'ucd': ['#022851', '#ffbf00'],
        'incose': ["#f2606b", "#ffdf79", "#c6e2b1", "#509bcf"],
        'sae': ["#01a0e9", "#005195", "#cacac8", "#9a9b9d", "#616265"],
        'trb': ["#82212a", "#999999", "#181818"],
        'default_prop_cycle': default_prop_cycle,
    }

    def __init__(self, colors = 'viridis'):

        self.build(colors)

    def __call__(self, values):

        return self.colors(values)

    def build(self, colors):

        self.norm = matplotlib.colors.Normalize(0, 1)

        if type(colors) == str:

            if colors in self.color_schemes.keys():

                colors_list = self.color_schemes[colors]

                self.cmap = LinearSegmentedColormap.from_list(
                    'custom', colors_list, N = 256)

            else:

                self.cmap = matplotlib.cm.get_cmap(colors)

        else:

            self.cmap = LinearSegmentedColormap.from_list(
                'custom', colors, N = 256)

    def colors(self, values):

        values = np.asarray(values).astype(float)

        values[values == np.inf] = np.nan
        values[values == -np.inf] = np.nan

        vmin = np.nanmin(values)
        vmax = np.nanmax(values)

        if vmin == vmax:

            values_norm = values

        else:

            values_norm = (
                (values - vmin) / (vmax - vmin)
                )

        self.norm = matplotlib.colors.Normalize(vmin, vmax)

        return self.cmap(values_norm)

def plot_edges(graph, ax, **kwargs):

    _node = graph._node
    _adj = graph._adj

    cmap = kwargs.get('cmap', Colormap('viridis'))
    field = kwargs.get('field', None)
    selection = kwargs.get('selection', None)
    colorbar = kwargs.get('colorbar', None)
    kw = kwargs.get('plot', {})

    if selection is None:

        selection = [(s, t) for s, adj in graph._adj.items() for t in adj.keys()]

    lines = []
    values = []

    for edge in selection:

        source, target = edge

        lines.append(np.array([
            [_node[source]['x'], _node[source]['y']],
            [_node[target]['x'], _node[target]['y']]
            ]))

        values.append(_adj[source][target].get(field, np.nan))

    if field is not None:

        kw['color'] = cmap(values)

    edges_plot = LineCollection(lines, **kw)

    ax.add_collection(edges_plot)

    if colorbar is not None:

        plot_colorbar(cmap, ax, **colorbar)

    return edges_plot

def plot_nodes(graph, ax, **kwargs):

    cmap = kwargs.get('cmap', Colormap('viridis'))
    field = kwargs.get('field', None)
    selection = kwargs.get('selection', None)
    colorbar = kwargs.get('colorbar', None)
    kw = kwargs.get('plot', {})

    if selection == []:

        return None

    if selection is None:

        selection = [s for s in graph.nodes]

    nodes = [graph._node[s] for s in selection]

    coords = np.array([[node['x'], node['y']] for node in nodes])

    values = np.array([v.get(field, np.nan) for v in nodes])

    indices = np.argsort(values)

    values = values[indices]
    coords = coords[indices]

    if field is not None:

        kw['color'] = cmap(values)

    nodes_plot = ax.scatter(
        coords[:, 0], coords[:, 1], **kw
        )

    if colorbar is not None:

        plot_colorbar(cmap, ax, **colorbar)
    
    return nodes_plot

def plot_colorbar(cmap, ax, **kwargs):

    sm = matplotlib.cm.ScalarMappable(cmap = cmap.cmap, norm = cmap.norm)    
    sm.set_array([])

    colorbar = plt.colorbar(sm, ax = ax, **kwargs)

    return colorbar

def plot_graph(graph, ax, **kwargs):

    edges = kwargs.get('edges', None)
    nodes = kwargs.get('nodes', None)

    if edges is not None:

        edges_plot = plot_edges(graph, ax, **edges)

    else:

        edges_plot = None

    if nodes is not None:
       
        nodes_plot = plot_nodes(graph, ax, **nodes)

    else:

        nodes_plot = None


    return nodes_plot, edges_plot