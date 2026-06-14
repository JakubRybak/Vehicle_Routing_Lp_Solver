import math
import pulp
import sys
import time
import os
from scripts.utils import parse_vrp, save_results_to_csv
from scripts.cvrp_genetic import solve_cvrp_ga

def solve_cvrp_hybrid(filepath, ga_time_limit=60, ilp_time_limit=600, population_size=100, generations=500, seed=None):
    print("\n" + "="*50)
    print(f"URUCHAMIANIE MATEURYSTYKI (HYBRYDA GA + ILP)")
    print(f"Krok 1: Inicjalizacja Algorytmem Genetycznym ({ga_time_limit}s)")
    print("="*50)
    
    # Krok 1: Uruchomienie GA (które samo też zaraportuje swój własny wynik do CSV)
    ga_cost, ga_routes = solve_cvrp_ga(filepath, time_limit=ga_time_limit, population_size=population_size, generations=generations, seed=seed)
    
    print("\n" + "="*50)
    print(f"Krok 2: Uruchamianie solvera ILP CBC (Ciepły start z wyniku GA: {ga_cost})")
    print("="*50)
    
    # Krok 2: Uruchomienie ILP
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
        
    prob = pulp.LpProblem("CVRP_HYBRID", pulp.LpMinimize)
    
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
                
    # MAGIA MATEURYSTYKI: Wstrzykiwanie rozwiązania z Genetyka
    for i in V:
        for j in V:
            if i != j:
                x[i, j].setInitialValue(0)
                
    for route in ga_routes:
        # route ma format np. [1, 5, 12, 1] (z węzłami bazy na krańcach)
        for i in range(len(route) - 1):
            x[route[i], route[i+1]].setInitialValue(1)

    start_time = time.time()
    
    if ilp_time_limit is not None:
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=ilp_time_limit, gapRel=0.05, warmStart=True, keepFiles=True))
    else:
        prob.solve(pulp.PULP_CBC_CMD(msg=False, gapRel=0.05, warmStart=True, keepFiles=True))
        
    end_time = time.time()
    duration = end_time - start_time
    total_duration = duration + ga_time_limit # łączny czas eksperymentu
    
    hit_time_limit = False
    if ilp_time_limit is not None and duration >= ilp_time_limit * 0.99:
        hit_time_limit = True
        
    print(f"Czas wykonania fazy ILP: {duration:.2f} s")
    print(f"Status ILP: {pulp.LpStatus[prob.status]}")
    
    cost = None
    routes = []
    
    if prob.status == pulp.LpStatusOptimal or prob.status == 1:
        cost = pulp.value(prob.objective)
        print(f"Ostateczny koszt po korekcie ILP: {cost}")
        
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
        print(f"Trasy końcowe: {routes}")
        
    save_results_to_csv(filepath, 'HYBRID_GA_ILP', len(N), K, Q, total_duration, ilp_time_limit, hit_time_limit, pulp.LpStatus[prob.status], cost, routes)

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else r'..\data\E\E-n22-k4.vrp'
    solve_cvrp_hybrid(filepath)
