import os
import sys
import time
import numpy as np
import pandas as pd

def AddRouteInformation(graph,raw_routes,fields):

	routes=[]

	for raw_route in raw_routes:

		route={field:[] for field in fields}

		for stop in raw_route:

			for field in fields:

				route[field].append(graph._node[stop][field])

		routes.append(route)

	return routes
