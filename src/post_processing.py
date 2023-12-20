import os
import sys
import time
import numpy as np
import pandas as pd

def AddRouteInformation(raw_routes,df,fields):

	routes=[]

	for raw_route in raw_routes:

		route={field:[] for field in fields}

		for stop in raw_route:

			row=df[df['ID']==int(stop)]

			for field in fields:

				route[field].append(str(row[field].values[0]))

		routes.append(route)

	return routes
