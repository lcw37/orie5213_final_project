import taxicab as tc
import osmnx as ox
import numpy as np


xmin, xmax = -73.961004, -73.906759
ymin, ymax = 40.662075, 40.708213


def generate_G(mode, location_data):
    # if given a bbox:
    if mode == 'bbox':
        ymax, ymin, xmin, xmax = location_data # location_data is a 4-tuple of xy values if 'bbox'
        G = ox.graph_from_bbox(ymax, ymin, xmin, xmax, network_type="drive", simplify=True)
    # if given a location name:
    if mode == 'name':
        location, distance = location_data # location_data is a (location name, distance) tuple if 'location'
        G = ox.graph_from_address(location, dist=distance, network_type='drive')
        
    # calculate travel times for each edge (in seconds)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    return G


def tc_length_and_time(G, orig, dest):
    """Calculate the shortest taxicab route between two points and return the length and time it takes to travel it.

    Parameters:
    -----------
    G : networkx.MultiDiGraph
        The road network to compute the route on.
    orig : tuple
        A tuple (latitude, longitude) representing the origin point.
    dest : tuple
        A tuple (latitude, longitude) representing the destination point.

    Returns:
    --------
    tuple of (float, float, list)
        A tuple of the form (route_length, route_time, taxi_route), where route_length is the length (in meters) of the
        entire route, route_time is the time (in seconds) it takes to travel the entire route, and taxi_route is a list of
        nodes representing the taxicab route taken (excluding the origin point but including the destination point).
    """
    # calculate taxicab shortest route
    taxi_route = None
    eps = 1e-4
    count = 0
    _orig, _dest = orig, dest
    max_tries = 20
    # I encountered a bug in the taxicab source code (tc.distance.shortestpath), this try-except loop works around it
    # repeatedly add eps to x-coord or y-coord (alternating) until a solution is found
    while taxi_route is None:
        try:
            taxi_route = tc.distance.shortest_path(G, _orig, _dest)
            route_length, interior_nodes, first_segment, last_segment = taxi_route
        except:
            if count == int(max_tries / 2): # reverse direction of search after 30 tries
                eps = -1e-4
                _orig = orig
            if count == max_tries: # stop search after 60 tries
                return None
            
            if count % 2 == 0:
                _orig = (_orig[0] + eps, _orig[1])
            else:
                _orig = (_orig[0], _orig[1] + eps)
            count += 1
        
    # calculate travel length (in meters) and time (in seconds) of interior nodes
    interior_length = int(sum(ox.utils_graph.get_route_edge_attributes(G, interior_nodes, "length")))
    interior_time = int(sum(ox.utils_graph.get_route_edge_attributes(G, interior_nodes, "travel_time")))

    # estimate average travel speed along the tail segments
    tails = [first_segment, last_segment]
    speeds = []
    for s in tails:
        if s != []:
            # get the "tail" of the segment, tail is the non-node end, tail end is always the last item in the coords list
            sx, sy = s.coords[-1]
            # get edges nearest to tail segments, use edge length (m) and edge travel time (s) to estimate average travel speed in m/s (need to manually calculate)
            nearest_edge = ox.nearest_edges(G, sx, sy)
            nearest_edge = G.edges[nearest_edge]
            total_len, total_time = nearest_edge['length'], nearest_edge['travel_time']
            speed = total_len / total_time
            speeds.append(speed)
    avg_tail_speed = np.mean(speeds)

    # get total length of tail segments (cannot directly access the length in meters of each separate tail segment)
    total_tail_len = route_length - interior_length
    # use the tail segments' partial lengths and the average speeds to estimate travel time along the tail segments
    tail_time = total_tail_len / avg_tail_speed

    # total route travel time is the sum of the interior node travel time and tail segment (estimated) travel time
    route_time = interior_time + tail_time

    return route_length, route_time, taxi_route


def generate_random_coords(G, n_students, n_schools, depot_coords=(ymin, xmin)):
    """Generate random coordinates for students and schools, and return a dictionary mapping their IDs to coordinates.

    Parameters:
    -----------
    G : networkx.MultiDiGraph
        The road network to sample the points from.
    n_students : int
        The number of student locations to generate.
    n_schools : int
        The number of school locations to generate.
    depot_coords : tuple, optional
        A tuple (latitude, longitude) representing the depot location. Default is (ymin, xmin).

    Returns:
    --------
    dict
        A dictionary mapping the IDs of the student and school locations to their respective coordinate tuples, of the form
        {depot, students..., schools...}.
    """
    # randomly sample student and school locations
    random_locs = ox.utils_geo.sample_points(G, n_students + n_schools)

    # convert GeoSeries to dict of IDs and coordinate tuples (y, x)
    # {depot, students..., schools...}
    coords = {}
    coords[0] = depot_coords
    for i, row in enumerate(random_locs):
        coords[i+1] = (row.y, row.x)
    return coords


def calculate_travel_times(G, n_students, n_schools, coords):
    """Calculate the travel times between all student and school locations.

    Parameters:
    -----------
    n_students : int
        The number of student locations to generate.
    n_schools : int
        The number of school locations to generate.
    depot_coords : tuple, optional
        A tuple (latitude, longitude) representing the depot location. Default is (ymin, xmin).

    Returns:
    --------
    numpy.ndarray
        An n+1 x n+1 numpy array representing the travel times (in seconds) between all locations, where n = n_students + n_schools.
        The first row and column of the array represent the depot location, and the remaining rows and columns represent the student
        and school locations, respectively.
    """ 
    
    # initialize travel_times as array of zeros
    travel_times = np.zeros((len(coords), len(coords)))

    # calculate travel times (in seconds)
    print('Calculating travel times...')
    for i in coords:
        for j in coords:
            if i != j:
                orig = coords[i]
                dest = coords[j]
                result = tc_length_and_time(G, orig, dest)
                if result is not None:   
                    _, t, _ = result
                    travel_times[i, j] = t
                else:
                    travel_times[i, j] = 1000000 # set to arbitrarily large number if no travel time is found?
        print(f'\tprogress: {i+1} / {len(coords)}')
    
    return travel_times


def generate_random_load_times(n_students, n_schools):
    """Generate random load times for students and schools, and return a dictionary mapping their IDs to their respective load times.

    Parameters:
    -----------
    n_students : int
        The number of students to generate load times for.
    n_schools : int
        The number of schools to generate load times for.

    Returns:
    --------
    dict
        A dictionary mapping the IDs of the student and school locations to their respective load times (in seconds).
        The load time for the depot location is always 0.
    """
    load_times = {}
    load_times[0] = 0 # depot load time is 0
    
    # draw student and school load times from exponential distributions, add 1 min
    student_load_times = np.random.exponential(scale=1, size=n_students) + 1
    school_offload_times = np.random.exponential(scale=3, size=n_schools) + 1
    
    # add load times to location-loadtime mapping (convert to seconds)
    for i in range(n_students):
        load_times[i+1] = student_load_times[i] * 60
    for i in range(n_schools):
        load_times[i+n_students+1] = school_offload_times[i] * 60
        
    return load_times


if __name__ == "__main__":
    # print(calculate_travel_times(5,2))
    print(generate_random_load_times(5,2))
