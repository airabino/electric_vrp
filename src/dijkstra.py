'''
Module for Dijkstra routing

Code is based on (is an edited version of):
NetworkX shortest_paths.weighted._dijkstra_multisource

Edits are to allow for native tracking of multiple shortest path simultaneously.
For example, one could get a shortest path weighted by 'distance' but also
want to know path 'time', this edited code allows for this to be done efficiently.
'''
from heapq import heappop, heappush
from itertools import count

def Dijkstra(
    graph,
    sources,
    fields,
    log_paths=False,
    cutoff=None,
    target=None,
    ):
    """Uses Dijkstra's algorithm to find shortest weighted paths

    Code is based on (is an edited version of):
    NetworkX shortest_paths.weighted._dijkstra_multisource

    Edits are to allow for native tracking of multiple shortest path simultaneously.

    Parameters
    ----------
    graph : NetworkX graph

    sources : non-empty iterable of nodes
        Starting nodes for paths. If this is just an iterable containing
        a single node, then all paths computed by this function will
        start from that node. If there are two or more nodes in this
        iterable, the computed paths may begin from any one of the start
        nodes.

    weight: edge field or list of edge fields
        If one edge field is provided shortest path will be computed for
        that field and that field will be included in the distance output.
        If a list of edge fields is provided then shortest paths will be 
        computed for the first field in the list but all fields will be
        included in the distance output.

    paths: Boolean
        Boolean whether or not to compute paths dictionary. If False None
        is returned for the paths output.

    target : node label, optional
        Ending node for path. Search is halted when target is found.

    cutoff : integer or float, optional
        Length (sum of edge weights) at which the search is stopped.
        If cutoff is provided, only return paths with summed weight <= cutoff.

    Returns
    -------
    distance : dictionary
        A mapping from node to shortest distance to that node from one
        of the source nodes.

    paths : dictionary
        Dictionary containing ordered lists of nodes passed on shortest
        path between the origin node and other nodes.
    """

    if log_paths:
        paths = {source: [source] for source in sources}
    else:
        paths = None

    if not hasattr(fields, '__iter__'):
        fields=[fields]

    n_fields=len(fields)

    graph_succ = graph._adj
    # For speed-up (and works for both directed and undirected graphs)

    dist = {}  # dictionary of final distances
    seen = {}

    # fringe is heapq with 3-tuples (distance,c,node)
    # use the count c to avoid comparing nodes (may not be able to)

    c = count()
    fringe = []

    for source in sources:

        seen[source] = 0
        heappush(fringe, ([0,]*n_fields, next(c), source))

    while fringe:

        (d, _, v) = heappop(fringe)

        if v in dist:

            continue  # already searched this node.

        dist[v] = d

        if v == target:

            break

        for u, e in graph_succ[v].items():

            # cost = weight(v, u, e)
            cost = [e.get(field, 1) for field in fields]

            if cost[0] is None:

                continue

            vu_dist = [dist[v][idx] + cost[idx] for idx in range(n_fields)]

            if cutoff is not None:

                if vu_dist[0] > cutoff:

                    continue

            if u in dist:

                u_dist = dist[u]

                if vu_dist[0] < u_dist[0]:

                    raise ValueError("Contradictory paths found:", "negative weights?")

            elif u not in seen or vu_dist[0] < seen[u]:

                seen[u] = vu_dist[0]

                heappush(fringe, (vu_dist, next(c), u))

                if paths is not None:

                    paths[u] = paths[v] + [u]

    return dist,paths