import math
import pulp
import sys
import time
import os
from scripts.utils import parse_vrp, save_results_to_csv

def solve_cvrp_lp(filepath, time_limit=None, show_plot=True):
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
        
    prob = pulp.LpProblem("CVRP_LP", pulp.LpMinimize)
    
    x = pulp.LpVariable.dicts("x", ((i, j) for i in V for j in V if i != j), lowBound = 0, upBound = 1, cat='Continuous')
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
    
    for i in N:
        for j in N:
            if i != j:
                prob += u[j] - u[i] >= demands[j] - Q * (1 - x[i, j])
                
    print("Uruchamianie solvera")
    start_time = time.time()
    if time_limit is not None:
        prob.solve(pulp.PULP_CBC_CMD(msg=False, logPath=f"cbc_solver_{os.getpid()}.log", timeLimit=time_limit))
    else:
        prob.solve(pulp.PULP_CBC_CMD(msg=False, logPath=f"cbc_solver_{os.getpid()}.log"))
    end_time = time.time()
    duration = end_time - start_time
    
    hit_time_limit = False
    if time_limit is not None and duration >= time_limit * 0.99:
        hit_time_limit = True
        
    print(f"Czas wykonania: {duration:.2f} s")
    print(f"Status: {pulp.LpStatus[prob.status]}")
    
    cost = None
    routes = []
    
    if prob.status == pulp.LpStatusOptimal:
        cost = pulp.value(prob.objective)
        print(f"Minimal tour: {cost}")
        
        edges = []
        for i in N:
            for j in N:
                if i != j:
                    val = pulp.value(x[i,j])
                    if val is not None and val > 0:
                        edges.append((val, i, j))
        edges.sort(key=lambda item: item[0], reverse=True)

        route_of = {i: i for i in N}            
        route_nodes = {i: [i] for i in N}        
        route_loads = {i: demands[i] for i in N}

        for val, i, j in edges:
            r_i = route_of[i]
            r_j = route_of[j]
            
            if r_i == r_j:
                continue
                
            if route_nodes[r_i][-1] == i and route_nodes[r_j][0] == j:
                if route_loads[r_i] + route_loads[r_j] <= Q:
                    route_nodes[r_i].extend(route_nodes[r_j])
                    route_loads[r_i] += route_loads[r_j]
                    for node in route_nodes[r_j]:
                        route_of[node] = r_i
                    del route_nodes[r_j]
                    del route_loads[r_j]

        active_routes = list(route_nodes.keys())
        
        if len(active_routes) > K:
            print(f"Przekroczony limit pojazdów. Mamy {len(active_routes)} fragmentów. Limit to {K}. Dopychanie geometryczne.")
            fallback_edges = []
            for r1 in active_routes:
                for r2 in active_routes:
                    if r1 != r2:
                        end_r1 = route_nodes[r1][-1]
                        start_r2 = route_nodes[r2][0]
                        fallback_edges.append((dist(end_r1, start_r2), r1, r2))
                        
            fallback_edges.sort(key=lambda x: x[0])
            
            for distance, r1, r2 in fallback_edges:
                if len(active_routes) <= K:
                    print("Otrzymano wymagane ograniczenie na liczbę pojazdów.")
                    break
                if r1 in route_nodes and r2 in route_nodes:
                    if route_loads[r1] + route_loads[r2] <= Q:
                        route_nodes[r1].extend(route_nodes[r2])
                        route_loads[r1] += route_loads[r2]
                        for node in route_nodes[r2]:
                            route_of[node] = r1
                        del route_nodes[r2]
                        del route_loads[r2]
                        active_routes.remove(r2)
                        
            if len(active_routes) > K:
                print("Uwaga! Po połączeniu tras nadal nie spełniamy ograniczenia liczby pojazdów.")

        for r_id in active_routes:
            routes.append([depot] + route_nodes[r_id] + [depot])


    save_results_to_csv(filepath, 'LP_CBC_GREEDY', len(N), K, Q, duration, time_limit, hit_time_limit, pulp.LpStatus[prob.status], cost, routes)
    
    if show_plot and cost is not None:
        from scripts.plot_utils import plot_route_map
        plot_route_map(nodes, routes, depot, title=f"LP GREEDY - Koszt: {cost}", demands=demands)