import re 
import matplotlib .pyplot as plt 
import os 

def plot_cbc_log (log_filepath="cbc_solver.log", optimum_cost=None):
    times =[]
    upper_bounds =[]
    lower_bounds =[]

    pattern = re.compile(r"([0-9\.eE\+\-]+)\s+best solution.*?best possible\s+([0-9\.eE\+\-]+).*?\(([0-9\.]+)\s+seconds\)")
    
    if not os.path.exists(log_filepath):
        print(f"Błąd: Nie znaleziono pliku '{log_filepath}'. Uruchom najpierw solver ILP, aby wygenerował log!")
        return
        
    with open(log_filepath, 'r') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                ub = float(match.group(1))
                lb = float(match.group(2))
                t = float(match.group(3))
                
                if ub >= 1e49:
                    upper_bounds.append(None)
                else:
                    upper_bounds.append(ub)
                    
                lower_bounds.append(lb)
                times.append(t)
                
    if not times:
        print ("Nie znaleziono odpowiednich danych w logu. Solver mógł rozwiązać problem tak szybko (np. w pierwszej sekundzie), że nie musiał logować postępu udowadniania.")
        return 

    plt .figure (figsize =(10 ,6 ))
    plt .plot (times ,upper_bounds ,label ='Najlepsza znaleziona trasa',color ='red',marker ='o',linewidth =2 )
    plt .plot (times ,lower_bounds ,label ='Optimum teoryczne',color ='green',marker ='x',linewidth =2 )

    if optimum_cost is not None:
        plt.axhline(y=optimum_cost, color='black', linestyle='--', linewidth=2, label='Globalne Optimum')

    plt.title('Postęp Solvera CBC - Zbieganie się Optimum')
    plt.xlabel('Czas (sekundy)')
    plt.ylabel('Dystans')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_route_map(nodes, routes, depot, title="Trasy CVRP", demands=None):
    if not nodes:
        return
        
    plt.figure(figsize=(10, 8))
    
    x_coords = [coords[0] for n, coords in nodes.items() if n != depot]
    y_coords = [coords[1] for n, coords in nodes.items() if n != depot]
    
    if demands:
        client_demands = [demands[n] for n in nodes.keys() if n != depot]
        if client_demands:
            min_d = min(client_demands)
            max_d = max(client_demands)
            if min_d == max_d:
                sizes = [50 for _ in client_demands]
            else:
                sizes = [30 + 270 * ((d - min_d) / (max_d - min_d)) for d in client_demands]
        else:
            sizes = 30
    else:
        sizes = 30
        
    plt.scatter(x_coords, y_coords, c='blue', s=sizes, label='Klienci', zorder=2)
    
    if depot in nodes:
        plt.scatter([nodes[depot][0]], [nodes[depot][1]], c='red', marker='s', s=100, label='Baza (Depot)', zorder=3)
        
    cmap = plt.cm.get_cmap('tab10', max(10, len(routes)))
    
    for i, route in enumerate(routes):
        rx = [nodes[n][0] for n in route]
        ry = [nodes[n][1] for n in route]
        plt.plot(rx, ry, marker='o', linestyle='-', color=cmap(i % 10), linewidth=2, zorder=1, label=f'Trasa {i+1}')
        
    plt.title(title)
    plt.xlabel('Oś X')
    plt.ylabel('Oś Y')
    
    if len(routes) <= 10:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()

def plot_ga_log(log_filepath="ga_solver.csv", optimum_cost=None):
    if not os.path.exists(log_filepath):
        return
        
    times = []
    costs = []
    try:
        with open(log_filepath, 'r', encoding='utf-8') as f:
            next(f)
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    times.append(float(parts[0]))
                    costs.append(float(parts[1]))
    except Exception as e:
        print(f"Błąd podczas odczytu logu GA: {e}")
        return
        
    if not times:
        return
        
    plt.figure(figsize=(10, 6))
    plt.plot(times, costs, label='Najlepszy osobnik w populacji', color='purple', linewidth=2)
    
    if optimum_cost is not None:
        plt.axhline(y=optimum_cost, color='black', linestyle='--', linewidth=2, label='Globalne Optimum')
        
    plt.title('Postęp Algorytmu Genetycznego')
    plt.xlabel('Czas (sekundy)')
    plt.ylabel('Dystans')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

def plot_hybrid_log(ga_filepath="ga_solver.csv", cbc_filepath="cbc_solver.log", optimum_cost=None):
    if not os.path.exists(ga_filepath) or not os.path.exists(cbc_filepath):
        return
        
    ga_times, ga_costs = [], []
    try:
        with open(ga_filepath, 'r', encoding='utf-8') as f:
            next(f)
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    ga_times.append(float(parts[0]))
                    ga_costs.append(float(parts[1]))
    except Exception:
        pass
        
    cbc_times, cbc_ub, cbc_lb = [], [], []
    pattern = re.compile(r"([0-9\.eE\+\-]+)\s+best solution.*?best possible\s+([0-9\.eE\+\-]+).*?\(([0-9\.]+)\s+seconds\)")
    try:
        with open(cbc_filepath, 'r') as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    ub = float(match.group(1))
                    lb = float(match.group(2))
                    t = float(match.group(3))
                    if ub >= 1e49:
                        cbc_ub.append(None)
                    else:
                        cbc_ub.append(ub)
                    cbc_lb.append(lb)
                    cbc_times.append(t)
    except Exception:
        pass
        
    if not ga_times or not cbc_times:
        print("Nie zebrano wystarczających logów do rysowania złączonego wykresu.")
        return
        
    ga_end_time = ga_times[-1]
    shifted_cbc_times = [t + ga_end_time for t in cbc_times]
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(ga_times, ga_costs, label='Faza 1: Najlepszy osobnik w Populacji', color='purple', linewidth=2)
    plt.plot(shifted_cbc_times, cbc_ub, label='Faza 2: Najlepsza znaleziona trasa', color='red', marker='o', linewidth=2)
    plt.plot(shifted_cbc_times, cbc_lb, label='Faza 2: Optimum teoryczne', color='green', marker='x', linewidth=2)
    
    plt.axvline(x=ga_end_time, color='orange', linestyle=':', linewidth=2, label='Przełączenie solverów')
    
    if optimum_cost is not None:
        plt.axhline(y=optimum_cost, color='black', linestyle='--', linewidth=2, label='Globalne Optimum')
        
    plt.title('Postęp Hybrydowy (Genetyk + ILP) w czasie')
    plt.xlabel('Całkowity Czas (sekundy)')
    plt.ylabel('Dystans')
    
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
