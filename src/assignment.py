import json
import math
import random
import numpy as np
import pandas as pd

from .utilities import FullFact

def Assign(items,buckets,seed=None):
    '''
    distribute items randomly among sets such that all sets are
    close to evenly represented
    '''

    rng=np.random.default_rng(seed)

    assignment={}

    item_bins=[[] for idx in range(len(buckets))]

    for item in items:

        bin_index=rng.integers(0,len(item_bins))

        item_bins[bin_index].append(item)

    for idx,bucket in enumerate(buckets):

        assignment[bucket]=np.array(item_bins[idx])

    return assignment


def assign_chargers_to_vehicles(vehicles, chargers):
    """
    Assign chargers to vehicles based on EV Network.

    Parameters:
    - vehicles (list): List of dictionaries representing vehicles.
    - chargers (pd.DataFrame): DataFrame containing charger information.

    Returns:
    - list: Updated list of vehicles with assigned chargers.
    """

    # Initialize 'chargers' key in each vehicle dictionary
    vehicles = [dict(item, **{'chargers': []}) for item in vehicles]

    # Shuffle chargers randomly
    chargers = chargers.sample(frac=1).reset_index(drop=True)

    # Split chargers into groups based on EV Network
    for _, ev_network_chargers in chargers.groupby('EV Network'):

        ev_network_chargers = ev_network_chargers['ID'].to_list()

        # Split list of chargers for each EV network into roughly equal chunks
        chunk_size = math.ceil(len(ev_network_chargers) / len(vehicles))

        chunked_chargers = [
            ev_network_chargers[x * chunk_size:x * chunk_size + chunk_size]
            for x in range(len(vehicles))
        ]

        # Assign charger chunks to vehicles
        for vehicle, chargers_chunk in zip(vehicles, chunked_chargers):
            vehicle['chargers'].extend(chargers_chunk)

    with open("vehicle_charger_assignment.json", "w") as final:
        json.dump(vehicles, final)

    return vehicles

if __name__ == "__main__":
    # Assuming you have some initial data for vehicles and chargers_df
    vehicles = [{'name': 'Vehicle 1',
                 'make': 'Chevrolet',
                 'model': 'Bolt'},
                 {'name': 'Vehicle 2',
                 'make': 'Tesla',
                 'model': 'Model 3'},
                 {'name': 'Vehicle 3',
                 'make': 'Ford',
                 'model': 'Lightening'},
                 {'name': 'Vehicle 4',
                 'make': 'Hyndai',
                 'model': 'IONIQ 5'}]

    ev_networks = ['Network A', 'Network B', 'Network A', 'Network B']
    chargers_df = pd.DataFrame({
        'ID': random.sample(range(100), 65),
        'EV Network': random.choices(ev_networks, k=65)
        # ... other charger information ...
    })

    # Call the assign_chargers_to_vehicles function
    assigned_vehicles = assign_chargers_to_vehicles(vehicles, chargers_df)

    print("Assigned Vehicles:")
    print(assigned_vehicles)