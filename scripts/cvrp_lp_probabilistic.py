import math
import pulp
import sys
import time
import os
import random
from scripts.utils import parse_vrp, save_results_to_csv

def solve_cvrp_lp_probabilistic(filepath, num_iterations=100, time_limit=None, show_plot=True):
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
    
    best_heuristic_cost = float('inf')
    best_final_routes = []
    
    if prob.status == pulp.LpStatusOptimal:
        lp_lower_bound = pulp.value(prob.objective)
        print(f"Teoretyczne minimum (ułamkowe LP): {lp_lower_bound:.2f}")
        
        lp_probs = {}
        for i in V:
            for j in V:
                if i != j:
                    val = pulp.value(x[i, j])
                    lp_probs[(i, j)] = max(0.0, val if val is not None else 0.0)

        print(f"Rozpoczynam zrandomizowane budowanie tras ({num_iterations} iteracji)...")
        
        for iteration in range(num_iterations):
            unvisited = set(N)
            routes_tmp = []
            
            while unvisited:
                route = [depot]
                curr = depot
                current_load = 0
                
                while True:
                    valid_neighbors = []
                    weights = []
                    
                    for k in unvisited:
                        if current_load + demands[k] <= Q:
                            valid_neighbors.append(k)
                            weights.append(lp_probs[(curr, k)])
                            
                    if not valid_neighbors:
                        break
                        
                    sum_weights = sum(weights)
                    best_next = None
                    
                    if sum_weights > 1e-5:
                        best_next = random.choices(valid_neighbors, weights=weights, k=1)[0]
                    else:
                        best_next = min(valid_neighbors, key=lambda node: dist(curr, node))
                        
                    route.append(best_next)
                    current_load += demands[best_next]
                    unvisited.remove(best_next)
                    curr = best_next
                    
                route.append(depot)
                routes_tmp.append(route)
                
            current_cost = sum(dist(r[i], r[i+1]) for r in routes_tmp for i in range(len(r)-1))
        
            if current_cost < best_heuristic_cost and len(routes_tmp) <= K:
                best_heuristic_cost = current_cost
                best_final_routes = routes_tmp
                
        if not best_final_routes and num_iterations > 0:
            print("Uwaga: Żadna wylosowana trasa nie spełniła rygorystycznego limitu K pojazdów. Używam ostatniej próby.")
            best_final_routes = routes_tmp
            best_heuristic_cost = current_cost
            
        print(f"Najlepszy koszt znaleziony metodą probabilistyczną: {best_heuristic_cost}")
        print(f"Zbudowano pojazdów: {len(best_final_routes)}")

    save_results_to_csv(filepath, 'LP_PROBABILISTIC', len(N), K, Q, duration, time_limit, hit_time_limit, pulp.LpStatus[prob.status], best_heuristic_cost, best_final_routes)
    
    if show_plot and best_heuristic_cost != float('inf'):
        from scripts.plot_utils import plot_route_map
        plot_route_map(nodes, best_final_routes, depot, title=f"LP PROBABILISTIC - Koszt: {best_heuristic_cost}", demands=demands)

    return best_final_routes, best_heuristic_cost