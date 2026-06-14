import math
import re
import pulp
import sys
import time
import os
import csv

def parse_vrp(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    capacity_match = re.search(r'CAPACITY\s*:\s*(\d+)', content)
    capacity = int(capacity_match.group(1)) if capacity_match else 0
    
    k_match = re.search(r'No of trucks:\s*(\d+)', content)
    if k_match:
        K = int(k_match.group(1))
    else:
        k_match = re.search(r'NAME\s*:.*-k(\d+)', content)
        K = int(k_match.group(1)) if k_match else 1
        
    ew_type_match = re.search(r'EDGE_WEIGHT_TYPE\s*:\s*(\w+)', content)
    ew_type = ew_type_match.group(1) if ew_type_match else 'EUC_2D'
    
    nodes = {}
    if ew_type == 'EUC_2D':
        node_coord_section = re.search(r'NODE_COORD_SECTION(.*?)(DEMAND_SECTION|EOF)', content, re.DOTALL)
        if node_coord_section:
            for line in node_coord_section.group(1).strip().split('\n'):
                parts = line.split()
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    
    explicit_matrix = {}
    if ew_type == 'EXPLICIT':
        ew_section = re.search(r'EDGE_WEIGHT_SECTION(.*?)(DEMAND_SECTION|EOF)', content, re.DOTALL)
        if ew_section:
            nums = [int(x) for x in ew_section.group(1).split()]
            dim_match = re.search(r'DIMENSION\s*:\s*(\d+)', content)
            dimension = int(dim_match.group(1))
            idx = 0
            for i in range(2, dimension + 1):
                for j in range(1, i):
                    val = nums[idx]
                    explicit_matrix[(i, j)] = val
                    explicit_matrix[(j, i)] = val
                    idx += 1
                
    demands = {}
    demand_section = re.search(r'DEMAND_SECTION(.*?)(DEPOT_SECTION|EDGE_WEIGHT_SECTION|EOF)', content, re.DOTALL)
    if demand_section:
        for line in demand_section.group(1).strip().split('\n'):
            parts = line.split()
            if len(parts) >= 2:
                demands[int(parts[0])] = int(parts[1])
                
    depot_section = re.search(r'DEPOT_SECTION(.*?)(EOF|$)', content, re.DOTALL)
    depot = 0
    if depot_section:
        parts = depot_section.group(1).strip().split()
        if len(parts) > 0:
            depot = int(parts[0])
                
    return nodes, explicit_matrix, ew_type, demands, capacity, K, depot

def solve_cvrp_ilp(filepath, time_limit=None):
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
    
    # --- Optymalizacja 2: Jeszcze lepsze domykanie ram zmiennej u ---
    for i in N:
        u[i].lowBound = demands[i]
        
    prob += pulp.lpSum(dist(i, j) * x[i, j] for i in V for j in V if i != j)
    
    for j in N:
        prob += pulp.lpSum(x[i, j] for i in V if i != j) == 1
        
    for i in N:
        prob += pulp.lpSum(x[i, j] for j in V if i != j) == 1
        
    prob += pulp.lpSum(x[depot, j] for j in N) <= K
    prob += pulp.lpSum(x[i, depot] for i in N) <= K
    
    # --- Optymalizacja 1: Valid Inequalities (Ważne nierówności) ---
    # Musi wyruszyć w trasę przynajmniej tyle ciężarówek, by fizycznie unieść ładunek
    min_vehicles = math.ceil(sum(demands[i] for i in N) / Q)
    prob += pulp.lpSum(x[depot, j] for j in N) >= min_vehicles
    prob += pulp.lpSum(x[i, depot] for i in N) >= min_vehicles
    
    # --- Optymalizacja 2b: Ulepszone ograniczenia MTZ (Zacieśnienie Desrochers i Laporte) ---
    for i in N:
        for j in N:
            if i != j:
                # Rozszerzenie oryginalnego MTZ, które dużo szybciej odrzuca niemożliwe pętle 
                prob += u[j] - u[i] >= demands[j] - Q * (1 - x[i, j]) + (Q - demands[i] - demands[j]) * x[j, i]
                
    print("Uruchamianie zoptymalizowanego solvera CBC (z ustawioną luką optymalności na 5%)...")
    start_time = time.time()
    
    # --- Optymalizacja 3: GapRel (5% tolerancji odległości od teoretycznego ideału) ---
    if time_limit is not None:
        prob.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=time_limit, gapRel=0.05))
    else:
        prob.solve(pulp.PULP_CBC_CMD(msg=False, gapRel=0.05))
        
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
        
    # Zapisywanie do CSV z innym tagiem algorytmu, by odróżnić od czystego ILP
    os.makedirs('results', exist_ok=True)
    dataset_name = os.path.basename(filepath)
    results_file = os.path.join('results', 'experiments.csv')
    file_exists = os.path.isfile(results_file)
    
    with open(results_file, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Dataset', 'Algorithm', 'Nodes', 'Vehicles', 'Capacity', 'Time_s', 'TimeLimit', 'HitTimeLimit', 'Status', 'Cost', 'Routes']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
            
        writer.writerow({
            'Dataset': dataset_name,
            'Algorithm': 'ILP_CBC_OPT',
            'Nodes': len(N),
            'Vehicles': K,
            'Capacity': Q,
            'Time_s': round(duration, 2),
            'TimeLimit': time_limit if time_limit is not None else 'None',
            'HitTimeLimit': hit_time_limit,
            'Status': pulp.LpStatus[prob.status],
            'Cost': cost,
            'Routes': str(routes)
        })
    print(f"Zapisano statystyki eksperymentu do {results_file}")

if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else r'data\E\E-n22-k4.vrp'
    solve_cvrp_ilp(filepath)
