import os
import sys
import time
import matplotlib
import numpy as np
import numpy.random as rand
import matplotlib.pyplot as plt

from matplotlib.colors import LinearSegmentedColormap

default_prop_cycle = matplotlib.rcParamsDefault['axes.prop_cycle'].by_key()['color'].copy()

colormaps={
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


def colormap(colors):

	if type(colors) == str:

		if colors in colormaps.keys():

			colormap_out = LinearSegmentedColormap.from_list(
				'custom', colormaps[colors], N = 256)

		else:

			colormap_out = matplotlib.cm.get_cmap(colors)

	else:

		colormap_out = LinearSegmentedColormap.from_list(
			'custom', colors, N = 256)

	return colormap_out

def add_node_field(graph, field, values):

	for idx, key in enumerate(graph._node.keys()):

		graph._node[key][field] = values[idx]

	return graph

def plot_routes(graph, routes, ax = None, **kwargs):

	return_fig = False

	if ax is None:

		fig, ax = plt.subplots(**kwargs.get('figure', {}))
		return_fig = True

	for route in routes:

		x = [graph._node[n]['x'] for n in route['nodes']]
		y = [graph._node[n]['y'] for n in route['nodes']]

		ax.plot(x, y, **kwargs['line'])

	if return_fig:

		return fig

def plot_graph(graph, ax = None, **kwargs):

	cmap = kwargs.get('cmap', colormap('viridis'))
	node_field = kwargs.get('node_field', None)
	link_field = kwargs.get('link_field', None)
	show_links = kwargs.get('show_links', True)
	show_colorbar = kwargs.get('show_colorbar', False)
	
	

	coords = np.array([[node['x'], node['y']] for node in graph._node.values()])

	if node_field is not None:

		values = np.array([v[node_field] for v in graph._node.values()])

		kwargs['scatter']['color'] = cmap(values / np.nanmax(values))
		# print(values)

	ax.scatter(
		coords[:, 0], coords[:, 1], **kwargs.get('scatter', {})
		)

	if show_links:

		dx = []
		dy = []

		if link_field is not None:
			
			values = []

			for source in graph._adj.keys():

				for target in graph._adj[source].keys():

					dx.append([graph._node[source]['x'], graph._node[target]['x']])
					dy.append([graph._node[source]['y'], graph._node[target]['y']])

					values.append(graph._adj[source][target][link_field])

			values_norm = (
				(values - np.nanmin(values)) / (np.nanmax(values) - np.nanmin(values))
				)

			for idx in range(len(dx)):

				ax.plot(
					dx[idx],
					dy[idx],
					color = cmap(values_norm[idx]),
					**kwargs.get('plot', {})
					)

		else:

			for source in graph._adj.keys():

				for target in graph._adj[source].keys():

					dx.append([graph._node[source]['x'], graph._node[target]['x']])
					dy.append([graph._node[source]['y'], graph._node[target]['y']])

			ax.plot(np.array(dx).T, np.array(dy).T, **kwargs.get('plot', {}))

	ax.set(**kwargs.get('axes', {}))

	if show_colorbar or kwargs.get('colorbar', {}):

		norm = matplotlib.colors.Normalize(
			vmin = np.nanmin(values),
			vmax = np.nanmax(values)
			) 

		sm = matplotlib.cm.ScalarMappable(cmap = cmap, norm = norm)    
		sm.set_array([])

		plt.colorbar(sm, ax = ax, **kwargs.get('colorbar', {}))