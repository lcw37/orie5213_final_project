import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import numpy as np
from datetime import datetime, timedelta
import travel_times

def diff(first, second):
        second = set(second)
        return [item for item in first if item not in second]

def generate_start_times(num_schools):
    time_range = ["07:30:00", "08:00:00", "08:30:00", "09:00:00"]
    time_list = np.random.choice(time_range, num_schools)
    
    return time_list

def get_feasible_routes(num_students, num_schools, start_times, travel_time, coords, max_routes=10):
    print('Setting up mixed-integer program...')
    d = [0]
    P = list(range(1, 1 + num_students))
    S = list(range(num_students + 1, num_students + num_schools + 1))
    L = d + P + S
    O = list(range(num_students + num_schools + 1))

    school_earliest_dropoff_buffer = 30 # minutes lower bound on dropoff i.e. time window for dropoff [8:00 to 8:30am]
    school_latest_dropoff_buffer = 10 # minutes upper bound on dropoff i.e. time window for dropoff [8:00 to (8:30-10min)]
    student_loading_buffer = 2 # minutes

    school_start_times = np.ones(len(L)) * (60*60*12)
    for i in range(len(S)):
        time = datetime.strptime(start_times[i], "%H:%M:%S")
        seconds = time.hour * 3600 + time.minute * 60 + time.second
        school_start_times[i+len(P)+1] = seconds

    school_earliest_dropoff_times = school_start_times - (school_earliest_dropoff_buffer*60) 
    school_latest_dropoff_times = school_start_times - (school_latest_dropoff_buffer*60) 

    choices = np.random.choice(S, num_students)
    A = np.zeros((len(L), choices.max() + 1))
    A[np.arange(choices.size)+1, choices] = 1

    for j in (P+S):
        travel_time[:,j] = travel_time[:,j] + student_loading_buffer
    
    BigM = np.max(school_start_times) + np.max(travel_time)

    print('Building model...')
    m = gp.Model("bus_route")
    m.Params.OutputFlag = 0 
    m.Params.PoolSearchMode = 1
    m.Params.PoolSolutions = max_routes

    X = m.addVars(L, L, O, vtype=GRB.BINARY, name="X")

    Y = m.addVars(diff(L,d), vtype=GRB.INTEGER, name="Y")

    K = m.addVars(L, vtype=GRB.CONTINUOUS, name="K")

    m.setObjective(gp.quicksum(travel_time[i,j] * X[i,j,o] for i in L for j in L for o in O) - K[0]/100, GRB.MINIMIZE)

    m.addConstr(gp.quicksum(X[0,j,0] for j in L) == 1 , name="DepotFirst")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L for o in O) == 1 for j in diff(L,d)), name="OneIn")

    m.addConstrs((gp.quicksum(X[i,j,o] for j in L for o in O) <= 1 for i in L), name="OneOut")

    m.addConstrs((X[i,i,o] == 0 for i in L for o in O), name="NoSelf")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L for j in L) == 1 for o in O[:-1]), name="InOrder")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L) - gp.quicksum(X[j,k,o+1] for k in L) == 0 for j in L for o in O[:-2]), name="Continuity")

    m.addConstrs((gp.quicksum(o * X[i,j,o] for i in L for o in O) == Y[j] for j in diff(L,d)), name="AssignOrder")

    m.addConstrs((Y[i] * A[i,s] <= Y[s] for i in P for s in S), name="PickupOrder")

    m.addConstrs((K[i] + travel_time[i,j] - BigM * (1- gp.quicksum(X[i,j,o] for o in O)) <= K[j] for i in L for j in L), name="StartTimes")

    m.update()

    m.addConstrs((K[s] <= school_latest_dropoff_times[s] for s in S), name="StartTime")

    m.addConstrs((K[s] >= school_earliest_dropoff_times[s] for s in S), name="DropoffTime")

    m.addConstr(K[0] >= 60*60*6.5, name="Leave depot after 6:30am")

    print('Optimizing...')
    m.optimize()

    status = m.Status
    if status in [GRB.INF_OR_UNBD, GRB.INFEASIBLE, GRB.UNBOUNDED]:
        print("Model is either infeasible or unbounded.")
   
    route_solutions = []
    pickup_time_solutions = []
    nSolutions = min(m.SolCount, max_routes)
    for sol in range(nSolutions):
        m.setParam(GRB.Param.SolutionNumber, sol)
        values = m.Xn
        num_vars = num_students + num_schools
        ordering = list(map(lambda x: int(x), values[-(2*num_vars+1):-(num_vars+1)]))
        cumulative_times_of_arrival = list(map(lambda x: int(x), values[-(num_vars+1):]))

        #add depot
        route = [1] * (len(ordering)+1)
        route[0] = coords[0]
        node_order = [0] * (len(ordering)+1)
        for i in range(len(ordering)):
             route[ordering[i]+1] = coords[i+1]
             node_order[ordering[i]+1] = i+1

        route_solutions.append(route)
        
        sorted_arrivals = sorted(cumulative_times_of_arrival)
        time_strings = []
        
        for seconds in sorted_arrivals:
            time_delta = timedelta(seconds=seconds)
            time = (datetime(1900, 1, 1) + time_delta).time()
            time_string = time.strftime("%H:%M:%S")
            time_strings.append(time_string)
        
        pickup_time_solutions.append(time_strings)
        
    print('Optimization complete!')
    return route_solutions, pickup_time_solutions


if __name__ == "__main__":
    num_student_locations = 5
    num_schools = 2

    xmin, xmax = -73.961004, -73.906759
    ymin, ymax = 40.662075, 40.708213

    
    G = travel_times.generate_G(mode = 'bbox', location_data = (ymax, ymin, xmin, xmax))
    coords = travel_times.generate_random_coords(G, num_student_locations, num_schools, depot_coords=(40.7283, -73.94060))
    travel_time = travel_times.calculate_travel_times(G, num_student_locations, num_schools, coords)
    starting_times = generate_start_times(num_schools)
    routes, pickups = get_feasible_routes(num_student_locations, num_schools, starting_times, travel_time, coords)
    print(routes, pickups)