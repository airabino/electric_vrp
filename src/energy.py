import time
import numpy as np
import networkx as nx

from .progress_bar import ProgressBar

class Vehicle():

	def __init__(self, **kwargs):

		self.capacity = kwargs.get('capacity', 80 * 3.6e6)
		self.speeds = kwargs.get('speeds', [13.4, 25.3, 31.3])
		self.consumptions = kwargs.get('consumptions', [338, 515, 423])

	def energy(self, distance, speed):

		return np.interp(speed, self.speeds, self.consumptions) * distance

	def update_graph(self, graph):

		# edges = {e: 0 for e in list(graph.edges)}

		# for key, value in edges.items():

		# 	source, target = termini

		# 	edge = graph._adj[source][target]

		# 	if edge['time'] == 0:

		# 		continue

		# 	speed = edge['distance'] / edge['time']

		# 	edges[termini] = self.energy(edge['distance'], speed)

		for source, _adj in graph._adj.items():
			for target, edge in _adj.items():

				speed = 0 if edge['time'] == 0 else edge['distance'] / edge['time']

				edge['energy'] = self.energy(edge['distance'], speed)

		return graph