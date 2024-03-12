import time
import numpy as np

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

# def MMC_Queue():

# 	def __init__(self, arrival_frequency)


# def expected_queuing_time(l = 1 / 600, m = 1 / (45 * 60), c = 1):

# 	rho = l / (c * m)

# 	k = np.arange(0, c, 1)

# 	p_0 = 1 / (
# 		((c * rho) ** k / factorial(k)).sum() + (c * rho) ** c / (factorial(c) * (1 - rho))
# 	)

# 	l_q = (p_0 * (l / m) ** c * rho) / (factorial(c) * (1 - rho))

# 	w_q = l_q / l

# 	return w_q, l_q, p_0


