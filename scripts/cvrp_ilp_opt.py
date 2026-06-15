import math
import pulp
import sys
import time
import os
from scripts.utils import parse_vrp, save_results_to_csv

def solve_cvrp_ilp(filepath, time_limit=None, show_plot=True):
    nodes, explicit_matrix, ew_type, demands, Q, K, depot = parse_vrp(filepath)
    V = list(demands.keys())
    N = [i for i in V if i != depot] 
    
    def dist(i, j):
        if ew_type == 'EUC_2D':
            dx = nodes[i][0] - nodes[j][0]
            dy = nodes[i][1] - nodes[j][1]
            return round(math.sqrt(dx*dx + dy*dy))
        elif ew_type == 'EXPLICIT':
            if i == j: return 0
            return explicit_matrix[(i, j)]
        return 0
        
    print(f"Wczytano {len(N)} klientów, depot: {depot}, pojemność: {Q}, maks. ciężarówek: {K}")
        
    prob = pulp.LpProblem("CVRP_ILP_OPT", pulp.LpMinimize)
    
    x = pulp.LpVariable.dicts("x", ((i, j) for i in V for j in V if i != j), cat='Binary')
    u = pulp.LpVariable.dicts("u", N, lowBound=0, upBound=Q, cat='Continuous')
    
    for i in N:
        u[i].lowBound = demands[i]
        
    prob += pulp.lpSum(dist(i, j) * x[i, j] for i in V for j in V if i != j)
    
    for j in N:
        prob += pulp.lpSum(x[i, j] for i in V if i != j) == 1
        
    for i in N:
        prob += pulp.lpSum(x[i, j] for j in V if i != j) == 1
        
    prob += pulp.lpSum(x[depot, j] for j in N) <= K
    prob += pulp.lpSum(x[i, depot] for i in N) <= K
    
    min_vehicles = math.ceil(sum(demands[i] for i in N) / Q)
    prob += pulp.lpSum(x[depot, j] for j in N) >= min_vehicles
    prob += pulp.lpSum(x[i, depot] for i in N) >= min_vehicles
    
    for i in N:
        for j in N:
            if i != j:
                prob += u[j] - u[i] >= demands[j] - Q * (1 - x[i, j]) + (Q - demands[i] - demands[j]) * x[j, i]
                
    print("Uruchamianie solvera")
    start_time = time.time()
    
    if time_limit is not None:
        prob.solve(pulp.PULP_CBC_CMD(msg=False, logPath=f"cbc_solver_{os.getpid()}.log", timeLimit=time_limit, gapRel=0.05))
    else:
        prob.solve(pulp.PULP_CBC_CMD(msg=False, logPath=f"cbc_solver_{os.getpid()}.log", gapRel=0.05))
        
    end_time = time.time()
    duration = end_time - start_time
    
    hit_time_limit = False
    if time_limit is not None and duration >= time_limit * 0.99:
        hit_time_limit = True
        
    print(f"Czas wykonania: {duration:.2f} s")
    print(f"Status: {pulp.LpStatus[prob.status]}")
    
    cost = None
    routes = []
    
    if prob.status == pulp.LpStatusOptimal or prob.status == 1:
        cost = pulp.value(prob.objective)
        print(f"Minimal tour: {cost}")
        
        for j in N:
            if pulp.value(x[depot, j]) and pulp.value(x[depot, j]) > 0.5:
                route = [depot, j]
                curr = j
                while True:
                    next_node = None
                    for k in V:
                        if curr != k and pulp.value(x[curr, k]) and pulp.value(x[curr, k]) > 0.5:
                            next_node = k
                            break
                    if next_node is None or next_node == depot:
                        route.append(depot)
                        break
                    route.append(next_node)
                    curr = next_node
                routes.append(route)
        print(f"Routes: {routes}")
        
    save_results_to_csv(filepath, 'ILP_CBC_OPT', len(N), K, Q, duration, time_limit, hit_time_limit, pulp.LpStatus[prob.status], cost, routes)

    if show_plot and cost is not None:
        from scripts.plot_utils import plot_route_map
        plot_route_map(nodes, routes, depot, title=f"Trasa - Koszt: {cost}", demands=demands)