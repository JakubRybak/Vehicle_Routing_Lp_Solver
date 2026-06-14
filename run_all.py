import os
from cvrp_ilp import solve_cvrp_ilp

def run_experiments():
    instances = [
        os.path.join('data', 'E', 'E-n22-k4.vrp'),
        os.path.join('data', 'E', 'E-n23-k3.vrp'),
        os.path.join('data', 'E', 'E-n30-k3.vrp'),
        os.path.join('data', 'E', 'E-n33-k4.vrp')
    ]
    
    for inst in instances:
        if os.path.exists(inst):
            print(f"--- Uruchamianie dla: {inst} ---")
            try:
                solve_cvrp_ilp(inst)
            except Exception as e:
                print(f"Błąd podczas analizy {inst}: {e}")
        else:
            print(f"Plik {inst} nie istnieje!")
            
if __name__ == '__main__':
    run_experiments()
