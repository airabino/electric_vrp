import time
import numpy as np

from scipy.special import factorial

class MultiNormalSample():

    def __init__(self, **kwargs):

        self.loc = kwargs.get('loc', [0])
        self.scale = kwargs.get('scale', [1])
        self.weight = kwargs.get('weight', [1])
        self.clip = kwargs.get('clip', [-np.inf, np.inf])
        self.rng = np.random.default_rng(kwargs.get('seed', None))

        self.n = len(self.loc)
        self.bins = np.cumsum(self.weight)

    def random(self, size = (1, )):
        # t0 = time.time()

        rn = self.rng.random(size)
        # print(time.time() - t0)

        distribution_idx = np.digitize(rn, self.bins)
        # print(time.time() - t0)

        vals = np.zeros(size)

        for idx in range(self.n):
            add = distribution_idx == idx

            vals += self.rng.normal(self.loc[idx], self.scale[idx], size) * add
        # print(time.time() - t0)

        return np.clip(vals, *self.clip)

def queuing_time(l, m, c):

    rho = l / (c * m)

    k = np.arange(0, c, 1)

    p_0 = 1 / (
        sum([(c * rho) ** k / factorial(k) for k in k]) +
        (c * rho) ** c / (factorial(c) * (1 - rho))
    )

    l_q = (p_0 * (l / m) ** c * rho) / (factorial(c) * (1 - rho))

    w_q = l_q / l

    return w_q

def arrival_frequency(node, rng, size):

    if node['rural']:

        return 1 / (rng.random(size = size) * 10800 + 1800)

    else:

        return 1 / (rng.random(size = size) * 3600 + 600)

def service_frequency(node, rng, size):

    n_ac = np.nanmax([1, node['n_ac']])
    n_dc = np.nanmax([0, node['n_dc']])

    c = max([n_ac + n_dc, 1])

    # print('a', n_ac, n_dc, c)

    m_ac = m_ac = 1 / (np.clip(rng.normal(37.8, 14.8, size = size), 1, 100) / 12.1 * 3600)
    m_dc = m_ac = 1 / (np.clip(rng.normal(37.8, 14.8, size = size), 1, 100) / 80 * 3600)

    return (n_ac * m_ac + n_dc * m_dc) / c, c

def test_time(node, rng, size):

    n_ac = np.nanmax([0, node['n_ac']])
    n_dc = np.nanmax([0, node['n_dc']])

    time_per_test = rng.triangular(240, 480, 720, size = size)

    return (n_ac + n_dc) * time_per_test

class Charger_Time():

    def __init__(self, **kwargs):

        self.rng = np.random.default_rng(kwargs.get('seed', None))
        self.size = kwargs.get('size', (1, ))

        self.arrival = lambda n: arrival_frequency(n, self.rng, self.size)
        self.service = lambda n: service_frequency(n, self.rng, self.size)
        self.test = lambda n: test_time(n, self.rng, self.size)

    def assign(self, node):

        l = self.arrival(node)
        m, c = self.service(node)

        # print(l, m, c)

        node['queue_time'] = queuing_time(l, m, c)

        node['test_time'] = self.test(node)

        node['time'] = node['queue_time'] + node['test_time']

def assign_link_parameters(graph, parameters):

    # mns = MultiNormalSample(
    #     **parameters['link_traffic'],
    #     seed = parameters['rng_seed']
    #     )

    shape = parameters['n_samples']
    rng = np.random.default_rng(parameters['rng_seed'])

    for source, links in graph._adj.items():
        for target, link in links.items():

            # mult = 1 / mns.random(shape)
            k_0 = parameters['link_speed_multiplier'][0]
            k_1 = parameters['link_speed_multiplier'][1] - k_0
            mult = rng.random(shape) * k_1 + k_0

            link['time'] = link['time'] / mult
            link['length'] = link['length'] * np.ones(shape)
            link['price'] = (link['length'] * parameters['efficiency'] / 
                3.6e6 * parameters['energy_price'])

    return graph

def assign_node_parameters(graph, parameters):

    size = parameters['n_samples']
    seed = parameters['rng_seed']

    charger_time = Charger_Time(size = size, seed = seed)

    for node in graph._node.values():

        charger_time.assign(node)
        node['length'] = np.zeros(size)
        node['price'] = np.zeros(size)

        # node['time_dl'] = np.zeros(size)

    return graph

def assign_node_parameters_null(graph, parameters):

    size = parameters['n_samples']
    seed = parameters['rng_seed']

    charger_time = Charger_Time(size = size, seed = seed)

    for node in graph._node.values():

        # charger_time.assign(node)
        node['time'] = np.zeros(size)
        node['length'] = np.zeros(size)
        node['price'] = np.zeros(size)

        # node['time_dl'] = np.zeros(size)

    return graph