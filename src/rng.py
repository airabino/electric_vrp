import time
import numpy as np

from scipy.special import factorial

class MultiNormalSample():

    def __init__(self, loc = [0], scale = [1], weight = [1], seed = None):

        self.loc = loc
        self.scale = scale
        self.weight = weight
        self.rng = np.random.default_rng(seed)

        self.n = len(loc)
        self.bins = np.cumsum(weight)

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

        return vals

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

        self.rng = kwargs.get('rng', np.random.default_rng())
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