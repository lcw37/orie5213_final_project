import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import numpy as np
import travel_times

def diff(first, second):
        second = set(second)
        return [item for item in first if item not in second]

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

    # T = start_times
    T = np.ones(len(S)) * 2000

    # x_indices = np.arange(len(O)).reshape(len(O), 1)
    # y_indices = np.arange(len(O)).reshape(1, len(O))
    # travel_time = x_indices * y_indices + 2


    print('Building model...')
    m = gp.Model("bus_route")
    m.Params.OutputFlag = 0 
    #m.Params.PoolSolutions = 10
    #m.Params.PoolSearchMode = 2

    X = m.addVars(L, L, O, vtype=GRB.BINARY, name="X")

    Y = m.addVars(diff(L,d), vtype=GRB.INTEGER, name="Y")

    m.addConstr(gp.quicksum(X[0,j,0] for j in L) == 1 , name="DepotFirst")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L for o in O) == 1 for j in diff(L,d)), name="OneIn")

    m.addConstrs((gp.quicksum(X[i,j,o] for j in L for o in O) <= 1 for i in L), name="OneOut")

    m.addConstrs((X[i,i,o] == 0 for i in L for o in O), name="NoSelf")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L for j in L) == 1 for o in O[:-1]), name="InOrder")

    m.addConstrs((gp.quicksum(X[i,j,o] for i in L) - gp.quicksum(X[j,k,o+1] for k in L) == 0 for j in L for o in O[:-2]), name="Continuity")

    m.addConstrs((gp.quicksum(o * X[i,j,o] for i in L for o in O) == Y[j] for j in diff(L,d)), name="AssignOrder")

    m.addConstrs((Y[i] * A[i,s] <= Y[s] for i in P for s in S), name="PickupOrder")

    # m.addConstrs((gp.quicksum(travel_time[i,j] * X[i,j,o] for i in L for j in L for o in O[:Y[s]]) <= T[s] for s in S), name="StartTimes")

    m.setObjective(gp.quicksum(travel_time[i,j] * X[i,j,o] for i in L for j in L for o in O), GRB.MINIMIZE)

    print('Optimizing...')
    m.optimize()

    status = m.Status
    if status in [GRB.INF_OR_UNBD, GRB.INFEASIBLE, GRB.UNBOUNDED]:
        print("Model is either infeasible or unbounded.")
    # print(coords)

    solutions = []
    nSolutions = min(m.SolCount, max_routes)
    for sol in range(nSolutions):
        m.setParam(GRB.Param.SolutionNumber, sol)
        values = m.Xn
        num_vars = num_students + num_schools
        ordering = list(map(lambda x: int(x), values[-num_vars:]))

        #add depot
        route = [1] * (len(ordering)+1)
        route[0] = coords[0]
        
        for i in range(len(ordering)):
             route[ordering[i]+1] = coords[i+1]

        solutions.append(route)
    print('Optimization complete!')
    return solutions#, G


if __name__ == "__main__":
    print(get_feasible_routes(5, 1, None))

    