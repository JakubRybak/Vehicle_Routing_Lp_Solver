import os
import re
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

def save_results_to_csv(filepath, algorithm_name, nodes_count, vehicles_count, capacity, 
                        duration, time_limit, hit_time_limit, status, cost, routes):
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
            'Algorithm': algorithm_name,
            'Nodes': nodes_count,
            'Vehicles': vehicles_count,
            'Capacity': capacity,
            'Time_s': round(duration, 2),
            'TimeLimit': time_limit if time_limit is not None else 'None',
            'HitTimeLimit': hit_time_limit,
            'Status': status,
            'Cost': cost,
            'Routes': str(routes)
        })
    print(f"Zapisano statystyki eksperymentu do {results_file}")
