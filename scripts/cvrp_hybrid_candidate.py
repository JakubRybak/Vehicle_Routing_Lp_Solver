import math 
import pulp 
import sys 
import time 
import os 
from scripts .utils import parse_vrp ,save_results_to_csv 
from scripts .cvrp_genetic import solve_cvrp_ga 

def solve_cvrp_hybrid_candidate (filepath ,ga_time_limit =60 ,ilp_time_limit =600 ,population_size =100 ,generations =500 ,mutation_rate =0.2 ,tournament_size =3 ,seed =None ,show_plot =True ,nearest_neighbors_k =5 ):
    print ("Krok 1: Inicjalizacja Algorytmem Genetycznym")

    ga_cost ,ga_routes, ga_population =solve_cvrp_ga (filepath ,time_limit =ga_time_limit ,population_size =population_size ,generations =generations ,mutation_rate =mutation_rate ,tournament_size =tournament_size ,seed =seed ,save_csv =False ,show_plot =False ,return_population =True )

    print ("")
    print (f"Krok 2: Uruchamianie solvera ILP z filtrowaniem krawędzi")

    nodes ,explicit_matrix ,ew_type ,demands ,Q ,K ,depot =parse_vrp (filepath )
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

    allowed_edges =set ()
    for route in ga_routes:
        for i in range (len (route )-1 ):
            u =route [i ]
            v =route [i +1 ]
            allowed_edges .add ((u ,v ))
            allowed_edges .add ((v ,u ))

    num_to_keep =max (1 ,int (len (ga_population )*0.1 ))
    top_individuals =ga_population [:num_to_keep ]
    for cost ,ind ,routes_list in top_individuals :
        for route in routes_list :
            full_route =[depot ]+route +[depot ]
            for i in range (len (full_route )-1 ):
                u =full_route [i ]
                v =full_route [i +1 ]
                allowed_edges .add ((u ,v ))
                allowed_edges .add ((v ,u ))

    for i in V:
        neighbors =sorted ([j for j in V if j !=i ],key =lambda j :dist (i ,j ))
        for j in neighbors [:nearest_neighbors_k ]:
            allowed_edges .add ((i ,j ))
            allowed_edges .add ((j ,i ))

    for i in N:
        allowed_edges .add ((depot ,i ))
        allowed_edges .add ((i ,depot ))

    prob =pulp .LpProblem ("CVRP_HYBRID_CANDIDATE",pulp .LpMinimize )

    x =pulp .LpVariable .dicts ("x",allowed_edges ,cat ='Binary')
    u =pulp .LpVariable .dicts ("u",N ,lowBound =0 ,upBound =Q ,cat ='Continuous')

    for i in N :
        u [i ].lowBound =demands [i ]

    prob +=pulp .lpSum (dist (i ,j )*x [i ,j ]for (i ,j )in allowed_edges )

    for j in N :
        prob +=pulp .lpSum (x [i ,j ]for i in V if (i ,j )in allowed_edges )==1 

    for i in N :
        prob +=pulp .lpSum (x [i ,j ]for j in V if (i ,j )in allowed_edges )==1 

    prob +=pulp .lpSum (x [depot ,j ]for j in N if (depot ,j )in allowed_edges )<=K 
    prob +=pulp .lpSum (x [i ,depot ]for i in N if (i ,depot )in allowed_edges )<=K 

    min_vehicles =math .ceil (sum (demands [i ]for i in N )/Q )
    prob +=pulp .lpSum (x [depot ,j ]for j in N if (depot ,j )in allowed_edges )>=min_vehicles 
    prob +=pulp .lpSum (x [i ,depot ]for i in N if (i ,depot )in allowed_edges )>=min_vehicles 

    for i in N :
        for j in N :
            if i !=j :
                if (i ,j )in allowed_edges :
                    x_ji =x [j ,i ]if (j ,i )in allowed_edges else 0 
                    prob +=u [j ]-u [i ]>=demands [j ]-Q *(1 -x [i ,j ])+(Q -demands [i ]-demands [j ])*x_ji 

    for (i ,j )in allowed_edges :
        x [i ,j ].setInitialValue (0 )

    for route in ga_routes :
        for i in range (len (route )-1 ):
            if (route [i ],route [i +1 ])in allowed_edges :
                x [route [i ],route [i +1 ]].setInitialValue (1 )

    start_time =time .time ()

    if ilp_time_limit is not None :
        prob .solve (pulp .PULP_CBC_CMD (msg =False ,logPath =f"cbc_solver_{os.getpid()}.log" ,timeLimit =ilp_time_limit ,gapRel =0.05 ,warmStart =True ,keepFiles =True ))
    else :
        prob .solve (pulp .PULP_CBC_CMD (msg =False ,logPath =f"cbc_solver_{os.getpid()}.log" ,gapRel =0.05 ,warmStart =True ,keepFiles =True ))

    end_time =time .time ()
    duration =end_time -start_time 
    total_duration =duration +ga_time_limit 

    hit_time_limit =False 
    if ilp_time_limit is not None and duration >=ilp_time_limit *0.99 :
        hit_time_limit =True 

    print (f"Czas wykonania: {duration :.2f} s")
    print (f"Status: {pulp .LpStatus [prob .status ]}")

    cost =None 
    routes =[]

    if prob .status ==pulp .LpStatusOptimal or prob .status ==1 :
        cost =pulp .value (prob .objective )
        print (f"Minimal tour: {cost }")

        for j in N :
            x_depot_j =x [depot ,j ]if (depot ,j )in allowed_edges else None 
            if x_depot_j is not None and pulp .value (x_depot_j )and pulp .value (x_depot_j )>0.5 :
                route =[depot ,j ]
                curr =j 
                while True :
                    next_node =None 
                    for k in V :
                        if curr !=k :
                            x_curr_k =x [curr ,k ]if (curr ,k )in allowed_edges else None 
                            if x_curr_k is not None and pulp .value (x_curr_k )and pulp .value (x_curr_k )>0.5 :
                                next_node =k 
                                break 
                    if next_node is None or next_node ==depot :
                        route .append (depot )
                        break 
                    route .append (next_node )
                    curr =next_node 
                routes .append (route )
        print (f"Routes: {routes }")

    save_results_to_csv (filepath ,'HYBRID_GA_ILP_CANDIDATE',len (N ),K ,Q ,total_duration ,ilp_time_limit ,hit_time_limit ,pulp .LpStatus [prob .status ],cost ,routes )
    
    if show_plot and cost is not None :
        from scripts.plot_utils import plot_route_map
        plot_route_map (nodes ,routes ,depot ,title =f"Trasa - Koszt: {cost}",demands =demands )
