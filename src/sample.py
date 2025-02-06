import time
import numpy as np
import pandas as pd
import networkx as nx

import pyomo.environ as pyomo

from sklearn import tree
from heapq import heappop, heappush
from itertools import count

from .utilities import cprint
from .adjacency import node_assignment
from .graph import cypher, subgraph

class Optimization():

    def __init__(self, graph, counts, **kwargs):

        self.graph = graph
        self.counts = counts

        self.verbose = kwargs.get('verbose', True)

        self.handles = []

        t0 = time.time()
        self.build()
        cprint(f'Problem Built: {time.time() - t0}', self.verbose)

    def solve(self, tee = False, **kwargs):

        #Generating the solver object
        solver = pyomo.SolverFactory(**kwargs)

        # Building and solving as a linear problem
        t0 = time.time()
        self.result = solver.solve(self.model, tee = tee)
        cprint(f'Problem Solved: {time.time() - t0}', self.verbose)

        # Making solution dictionary
        t0 = time.time()
        self.collect_results()
        cprint(f'Results Collected: {time.time() - t0}', self.verbose)

    def collect_results(self):

        self.results = {}
        self.assignment = {}

        for handle in self.handles:

            value = list(getattr(self.model, handle).extract_values().values())[0]

            self.results[handle] = value

            if value > 0:

                parts = handle.split(':')

                if parts[-1] == 'assignment':

                    self.assignment[int(parts[0])] = int(parts[1])

    def build(self):

        self.model = pyomo.ConcreteModel()

        sum_cost = 0

        group_counts = {k: 0 for k in self.counts.keys()}

        for source, node in self.graph._node.items():

            assignment_sum = 0

            for depot, cost in node['depot_costs'].items():

                # print(depot, cost)

                handle = f"{source}:{depot}::assignment"
                variable = pyomo.Var(domain = pyomo.Binary)
                setattr(self.model, handle, variable)
                self.handles.append(handle)

                assignment_sum += getattr(self.model, handle)

                sum_cost += getattr(self.model, handle) * cost

                if node['group'] is not None:

                    group_counts[node['group']] += getattr(self.model, handle)

            handle = f"{source}::node_sum"
            constraint = pyomo.Constraint(expr = (0, assignment_sum, 1))
            setattr(self.model, handle, constraint)

        for group, count in group_counts.items():

            if not isinstance(count, (int, float)):

                handle = f"{group}::group_sum"
                constraint = pyomo.Constraint(expr = count == self.counts[group])
                setattr(self.model, handle, constraint)

        self.model.objective = pyomo.Objective(expr = sum_cost, sense = pyomo.minimize)

def subgraphs(graph, assignment):

    depots = np.unique(list(assignment.values()))

    subgraphs = {}

    for depot in depots:

        nodes = [depot] + [k for k, v in assignment.items() if v == depot]

        subgraphs[depot] = subgraph(graph, nodes)

    return subgraphs

def dijkstra(graph, origins, objective = 'objective'):

    nodes = graph._node
    edges = graph._adj

    costs = {} # dictionary of objective values for paths
    paths = {}

    c = count() # use the count c to avoid comparing nodes (may not be able to)
    heap = [] # heap is heapq with 3-tuples (cost, c, node)

    for origin in origins:
        
        costs[origin] = 0
        paths[origin] = [origin]

        heappush(heap, (0, next(c), origin))

    while heap: # Iterating while there are accessible unseen nodes

        # Popping the lowest cost unseen node from the heap
        cost, _, source = heappop(heap)

        for target, edge in edges[source].items():

            # Updating states for edge traversal
            cost_target = cost + edge.get(objective, 1)

            # Updating the weighted cost for the path
            savings = cost_target < costs.get(target, np.inf)

            if savings:
               
                costs[target] = cost_target
                paths[target] = paths[source] + [target]

                heappush(heap, (cost_target, next(c), target))

    return costs, paths

def station_costs(graph, atlas, depots, objective = 'objective'):

    graph_to_atlas, atlas_to_graph = node_assignment(atlas, graph)

    encode, decode = cypher(graph)

    # depots_atlas = [graph_to_atlas[d] for d in depots]

    for _, node in graph._node.items():

        node['depot_costs'] = {d: np.inf for d in depots}

    for idx, depot in enumerate(depots):

        costs, _ = dijkstra(atlas, [graph_to_atlas[depot]], objective = objective)

        for atlas_node, cost in costs.items():

            for graph_node in atlas_to_graph.get(atlas_node, []):

                graph._node[graph_node]['depot_costs'][depot] = cost

    return graph

def load_groups(file):
    
    groups = pd.read_csv(file)

    counts = {idx: g for idx, g in enumerate(groups['Count'].to_numpy())}

    mapping = {
        'GreaterRegion': 'region',
        'EV Network Clean': 'network',
        'DAC/LIC': 'dac_lic',
        'rural': 'rural',
        'DCFC': 'dcfc',
    }

    groups = groups[list(mapping.keys())]
    groups = groups.rename(mapping, axis = 1)

    return groups, counts

def assign_groups(graph, groups):

    unique_values = {}

    groups = groups.copy()

    for key in groups.keys():

        u, ui = np.unique(groups[key], return_inverse = True)

        unique_values[key] = {uv: idx for idx, uv in enumerate(u)}
        groups[key] = ui

    x = groups.to_numpy()
    y = groups.index.to_numpy()

    clf = tree.DecisionTreeClassifier()
    clf = clf.fit(x, y)

    for source, node in graph._node.items():

        if node['network'] == 'Depot':

            # print('s')
            node['group' ] = None

        else:

            try:

                node_vals = [[]]

                for key, val in unique_values.items():

                    node_vals[0].append(val[node[key]])

                node['group'] = clf.predict(node_vals)[0]

            except:

                node['group'] = None

    return graph

def adjust_counts(graph, counts):

    totals = {k: 0 for k in counts.keys()}

    for source, node in graph._node.items():

        if node['group'] is not None:

            totals[node['group']] += 1

    adjusted_counts = {k: min([totals[k], counts[k]]) for k in totals.keys()}

    return adjusted_counts