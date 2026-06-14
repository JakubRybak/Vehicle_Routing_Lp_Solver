import re 
import matplotlib .pyplot as plt 
import os 

def plot_cbc_log (log_filepath ="cbc_solver.log", optimum_cost=None):
    times =[]
    upper_bounds =[]
    lower_bounds =[]



    pattern =re .compile (r"([0-9\.]+)\s+best solution.*?best possible\s+([0-9\.]+).*?\(([0-9\.]+)\s+seconds\)")

    if not os .path .exists (log_filepath ):
        print (f"Błąd: Nie znaleziono pliku '{log_filepath }'. Uruchom najpierw solver ILP, aby wygenerował log!")
        return 

    with open (log_filepath ,'r')as f :
        for line in f :
            match =pattern .search (line )
            if match :
                ub =float (match .group (1 ))
                lb =float (match .group (2 ))
                t =float (match .group (3 ))

                upper_bounds .append (ub )
                lower_bounds .append (lb )
                times .append (t )

    first_valid_ub = next((x for x in upper_bounds if x != 50.0), None)
    if first_valid_ub is not None:
        upper_bounds = [first_valid_ub if x == 50.0 else x for x in upper_bounds]

    if not times :
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

def plot_route_map(nodes, routes, depot, title="Trasy CVRP"):
    if not nodes:
        print("Nie mogę narysować mapy, instancja nie zawiera współrzędnych klientów (NODE_COORD_SECTION).")
        return
        
    plt.figure(figsize=(10, 8))
    
    x_coords = [coords[0] for n, coords in nodes.items() if n != depot]
    y_coords = [coords[1] for n, coords in nodes.items() if n != depot]
    plt.scatter(x_coords, y_coords, c='blue', s=30, label='Klienci', zorder=2)
    
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
