import math 
import random 
import time 
import sys 
import os 
from scripts .utils import parse_vrp ,save_results_to_csv 

def solve_cvrp_ga (filepath ,generations =500 ,population_size =100 ,mutation_rate =0.2 ,tournament_size =3 ,time_limit =60 ,seed =None ,save_csv =True ,show_plot =True ):
    nodes ,explicit_matrix ,ew_type ,demands ,Q ,K_limit ,depot =parse_vrp (filepath )
    V =list (demands .keys ())
    N =[i for i in V if i !=depot ]

    def dist (i ,j ):
        if ew_type =='EUC_2D':
            dx =nodes [i ][0 ]-nodes [j ][0 ]
            dy =nodes [i ][1 ]-nodes [j ][1 ]
            return round (math .sqrt (dx *dx +dy *dy ))
        elif ew_type =='EXPLICIT':
            if i ==j :return 0 
            return explicit_matrix [(i ,j )]
        return 0 

    print(f"Wczytano {len(N)} klientów, depot: {depot}, pojemność: {Q}, maks. ciężarówek: {K_limit}")
    print (f"Parametry GA: Populacja={population_size }, Pokolenia={generations }, Limit czasu={time_limit }s")
    print("Uruchamianie algorytmu genetycznego")
    if seed is not None :
        random .seed (seed )


    def evaluate (individual ):
        routes =[]
        current_route =[]
        current_load =0 
        total_cost =0 
        current_node =depot 

        for customer in individual :
            demand =demands [customer ]
            if current_load +demand >Q :

                total_cost +=dist (current_node ,depot )
                routes .append (current_route )
                current_route =[]
                current_load =0 
                current_node =depot 


            total_cost +=dist (current_node ,customer )
            current_route .append (customer )
            current_load +=demand 
            current_node =customer 


        if current_route :
            total_cost +=dist (current_node ,depot )
            routes .append (current_route )

        return total_cost ,routes 


    population =[random .sample (N ,len (N ))for _ in range (population_size )]

    best_cost =float ('inf')
    best_routes =[]

    start_time =time .time ()
    hit_time_limit =False 
    
    progress_history = []


    for gen in range (generations ):

        if time .time ()-start_time >=time_limit :
            print (f"Przerwano: Osiągnięto limit czasu {time_limit }s (Pokolenie: {gen })")
            hit_time_limit =True 
            break 


        scored_population =[]
        for ind in population :
            cost ,r =evaluate (ind )
            scored_population .append ((cost ,ind ,r ))
            if cost <best_cost :
                best_cost =cost 
                best_routes =r 


        scored_population .sort (key =lambda x :x [0 ])
        new_population =[scored_population [0 ][1 ]]


        while len (new_population )<population_size :

            parents =[]
            for _ in range (2 ):
                tournament =random .sample (scored_population ,tournament_size )
                tournament .sort (key =lambda x :x [0 ])
                parents .append (tournament [0 ][1 ])

            p1 ,p2 =parents 


            size =len (p1 )
            a ,b =sorted (random .sample (range (size ),2 ))
            child =[None ]*size 
            child [a :b +1 ]=p1 [a :b +1 ]

            p2_filtered =[x for x in p2 if x not in child [a :b +1 ]]
            idx =0 
            for i in range (size ):
                if child [i ]is None :
                    child [i ]=p2_filtered [idx ]
                    idx +=1 


            if random .random ()<mutation_rate :
                a ,b =sorted (random .sample (range (size ),2 ))
                child [a :b +1 ]=reversed (child [a :b +1 ])

            new_population .append (child )

        population =new_population 
        
        current_time = time.time() - start_time
        progress_history.append((current_time, best_cost))

    end_time =time .time ()
    duration =end_time -start_time 

    print(f"Czas wykonania: {duration:.2f} s")
    print(f"Minimal tour: {best_cost}")


    formatted_routes =[]
    for r in best_routes :
        formatted_routes .append ([depot ]+r +[depot ])
        
    print(f"Routes: {formatted_routes}")
        
    try:
        with open("ga_solver.csv", "w", encoding='utf-8') as f:
            f.write("Time,BestCost\n")
            for t, c in progress_history:
                f.write(f"{t},{c}\n")
    except Exception as e:
        print(f"Nie udało się zapisać logu GA: {e}")

    status ='Feasible'if not hit_time_limit else 'Time Limit'
    if save_csv :
        save_results_to_csv (filepath ,'GA_CVRP',len (N ),len (best_routes ),Q ,duration ,time_limit ,hit_time_limit ,status ,best_cost ,formatted_routes )
        
    if show_plot:
        from scripts.plot_utils import plot_route_map
        plot_route_map(nodes, formatted_routes, depot, title=f"Genetyk - Koszt: {best_cost}")

    return best_cost ,formatted_routes 

if __name__ =='__main__':

    filepath =sys .argv [1 ]if len (sys .argv )>1 else r'..\data\E\E-n22-k4.vrp'
    solve_cvrp_ga (filepath ,save_csv =True )
