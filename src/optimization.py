import sys
import time
import numpy as np
import pandas as pd
import pickle as pkl
import matplotlib.pyplot as plt

from .utilities import IsIterable,FullFact

def ZoneNetTraffic(traffic,zones):

	zone_ratios=np.zeros(len(zones))

	for idx,zone in enumerate(zones):

		traffic_out=traffic[zone].sum()
		traffic_in=traffic[:,zone].sum()
		traffic_zone=traffic[zone][:,zone].sum()
		traffic_total=traffic_out+traffic_in

		zone_ratios[idx]=traffic_zone/traffic_total

	return zone_ratios

def ZoneRatio(traffic,zone):

	if zone:

		traffic_out=traffic[zone].sum()
		traffic_in=traffic[:,zone].sum()
		traffic_zone=traffic[zone][:,zone].sum()
		traffic_total=traffic_out+traffic_in

		return 1-traffic_zone/traffic_total

	else:

		return 1

def AcceptanceProbability(e,e_prime,temp):

	return min([1,np.exp(-(e_prime-e)/temp)])

def Acceptance(e,e_prime,temp):

	return AcceptanceProbability(e,e_prime,temp)>np.random.rand()

def RouteOptimization(route,steps=100):

	# #Pulling destination vertices from vertices
	# destination_vertices=[]
	# for route in routes:
	# 	destination_vertices.extend(route[1:-1])

	# Initializing temperature
	temperature=1

	#Getting initial route distance

	# Looping while there is still temperature
	k=0
	while temperature>0:

		# Randomly selecting swap vertices
		swap_vertices=np.random.choice(route[1:-1],replace=False)



		# Termination condition
		if k>=steps:
			break
		else:
			k+=1

def AnnealTraffic(traffic,steps=100):

	#Starting off with one single-vertex zone for each vertex
	zones=[[i] for i in range(traffic.shape[0])]
	zone_ratios=ZoneNetTraffic(traffic,zones)
	# print(zones,zone_ratios)

	temp=1

	while temp>0:

		idx_0=np.random.randint(0,len(zones))
		idx_1=np.random.randint(0,len(zones))
		if idx_0!=idx_1:

			zone_0=zones[idx_0]
			zone_1=zones[idx_1]

			swap_vertex=np.random.choice(zone_1)

			if np.any(traffic[swap_vertex][zone_0]):

				new_zone_0=zone_0[:]
				new_zone_1=zone_1[:]

				new_zone_0.append(swap_vertex)
				new_zone_1.remove(swap_vertex)

				# print(zone_0,zone_1)

				old_zone_ratio=(ZoneRatio(traffic,zone_0)+ZoneRatio(traffic,zone_1))
				new_zone_ratio=(ZoneRatio(traffic,new_zone_0)+ZoneRatio(traffic,new_zone_1))
				print(old_zone_ratio,new_zone_ratio)

				

				if Acceptance(old_zone_ratio,new_zone_ratio,temp):
					# print(AcceptanceProbability(zone_ratio,merged_zone_ratio,temp))
					# print(zone_0,zone_1)
					
					zones.remove(zone_0)
					zones.remove(zone_1)
					# print('a')
					zones.append(new_zone_0)
					if new_zone_1:
						zones.append(new_zone_1)
					# print('b')
					# print(zones,temp)


				# print(merged_zone_ratio)
				# print(zone_0,zone_1,merged_zone,merged_zone_ratio)

		temp-=1/steps
	print(zones)

	return zones

		


