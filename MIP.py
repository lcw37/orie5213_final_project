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

    choices = np.random.choice(S, num_students)
    A = np.zeros((len(L), choices.max() + 1))
    A[np.arange(choices.size)+1, choices] = 1

    school_start_times = np.ones(len(L)) * 200000

    print('Building model...')
    m = gp.Model("bus_route")
    m.Params.OutputFlag = 0 
    m.Params.PoolSearchMode = 1
    m.Params.PoolSolutions = max_routes

    X = m.addVars(L, L, O, vtype=GRB.BINARY, name="X")

    Y = m.addVars(diff(L,d), vtype=GRB.INTEGER, name="Y")

    # K = m.addVars(L, vtype=GRB.CONTINUOUS, name="K")

    m.setObjective(gp.quicksum(travel_time[i,j] * X[i,j,o] for i in L for j in L for o in O), GRB.MINIMIZE)

    m.addConstr(gp.quicksum(X[0,j,0] for j in L) == 1 , name="DepotFirst")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L for o in O) == 1 for j in diff(L,d)), name="OneIn")

    m.addConstrs((gp.quicksum(X[i,j,o] for j in L for o in O) <= 1 for i in L), name="OneOut")

    m.addConstrs((X[i,i,o] == 0 for i in L for o in O), name="NoSelf")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L for j in L) == 1 for o in O[:-1]), name="InOrder")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L) - gp.quicksum(X[j,k,o+1] for k in L) == 0 for j in L for o in O[:-2]), name="Continuity")

    m.addConstrs((gp.quicksum(o * X[i,j,o] for i in L for o in O) == Y[j] for j in diff(L,d)), name="AssignOrder")

    m.addConstrs((Y[i] * A[i,s] <= Y[s] for i in P for s in S), name="PickupOrder")

    # m.addConstrs((gp.quicksum(travel_time[i,j] * X[i,j,o] for i in L for j in L for o in O[:Y[s]]) <= T[s] for s in S), name="StartTimes")
    
    # m.addConstrs((gp.quicksum(travel_time[i,j] * X[i,j,o] for i in L for j in L for o in O[:t]) == K[t] for t in L), name="Yas")


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
        ordering = list(map(lambda x: int(x), values[-num_vars:]))

        #add depot
        route = [1] * (len(ordering)+1)
        route[0] = coords[0]
        node_order = [0] * (len(ordering)+1)
        for i in range(len(ordering)):
             route[ordering[i]+1] = coords[i+1]
             node_order[ordering[i]+1] = i+1

        route_solutions.append(route)
        
        pickup_times = list()

        school_dropoff_buffer = 5 # minutes
        student_loading_buffer = 2 # minutes
        
        current_time = datetime.strptime(start_times[node_order[-1]-num_students-1], "%H:%M:%S") - timedelta(minutes=school_dropoff_buffer)
        pickup_times.append(current_time.strftime("%H:%M:%S"))

        for k in range(len(node_order)-1):
            current_time -= timedelta(seconds=(travel_time[node_order[-(k+1)], node_order[-(k)]] + student_loading_buffer))
            pickup_times.append(current_time.strftime("%H:%M:%S"))

        pickup_time_solutions.append(pickup_times[::-1])
        
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
    