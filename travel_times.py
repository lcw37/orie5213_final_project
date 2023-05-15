import taxicab as tc
import osmnx as ox
import numpy as np

xmin, xmax = -73.961004, -73.906759
ymin, ymax = 40.662075, 40.708213

def tc_length_and_time(G, orig, dest):
    # calculate taxicab shortest route
    taxi_route = None
    eps = 1e-4
    alt = True
    # I encountered a bug in the taxicab source code (tc.distance.shortestpath), this try-except loop works around it
    while taxi_route is None:
        try:
            taxi_route = tc.distance.shortest_path(G, orig, dest)
            route_length, interior_nodes, first_segment, last_segment = taxi_route
        except:
            if alt:
                orig = (orig[0] + eps, orig[1])
                alt = False
            else:
                orig = (orig[0], orig[1] + eps)
                alt = True
        
    # calculate travel length (in meters) and time (in seconds) of interior nodes
    interior_length = int(sum(ox.utils_graph.get_route_edge_attributes(G, interior_nodes, "length")))
    interior_time = int(sum(ox.utils_graph.get_route_edge_attributes(G, interior_nodes, "travel_time")))

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


def generate_random_coords(G, n_students, n_schools, depot_coords):
    # randomly sample student and school locations
    random_locs = ox.utils_geo.sample_points(G, n_students + n_schools)

    # convert GeoSeries to dict of IDs and coordinate tuples (y, x)
    # {depot, students..., schools...}
    coords = {}
    coords[0] = depot_coords
    for i, row in enumerate(random_locs):
        coords[i+1] = (row.y, row.x)
    return coords


def calculate_travel_times(n_students, n_schools, depot_coords=(ymin, xmin)):
    # generate OSMnx graph
    G = ox.graph_from_bbox(ymax, ymin, xmin, xmax, network_type="drive", simplify=True)
    # calculate travel times for each edge (in seconds)
    G = ox.add_edge_speeds(G)
    G = ox.add_edge_travel_times(G)
    
    # randomly generate student and school coordinates
    coords = generate_random_coords(G, n_students, n_schools, depot_coords)
    
    # initialize travel_times as array of zeros
    travel_times = np.zeros((len(coords), len(coords)))

    # calculate travel times (in seconds)
    for i in coords:
        for j in coords:
            if i != j:
                orig = coords[i]
                dest = coords[j]
                _, t, _ = tc_length_and_time(G, orig, dest)
                travel_times[i, j] = t
        # print(f'progress: {i+1} / {len(coords)}')
    
    return travel_times, coords

if __name__ == "__main__":
    print(calculate_travel_times(5,2))