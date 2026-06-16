# Capacitated Vehicle Routing Problem - Solvery ILP

Ten projekt zawiera implementację oraz optymalizację algorytmów rozwiązujących problem wyznaczania tras pojazdów z ograniczeniem pojemności przy użyciu programowania całkowitoliczbowego w bibliotece PuLP.

## Struktura plików

W głównym katalogu projektu znajdują się następujące kluczowe pliki:

### Pliki główne i Algorytmy

* **`cvrp_ilp.py`**
  Podstawowa, klasyczna implementacja modelu matematycznego ILP. Używa sformułowania przepływowego oraz standardowych ograniczeń do eliminacji podtras i wymuszania pojemności.
  **Zmienne decyzyjne:**
  * $x_{ij} \in \{0, 1\}$ – zmienna binarna; przyjmuje 1, jeśli ciężarówka przemieszcza się bezpośrednio z węzła $i$ do $j$.
  * $u_i \ge 0$ – ciągła zmienna pomocnicza, pełniąca rolę skumulowanego "licznika wydanych paczek" w pojeździe po obsłużeniu klienta $i$.

  **Funkcja celu:** Minimalizacja całkowitego dystansu
  
  $$
  \min \sum_{i \in V} \sum_{j \in V, j \neq i} c_{ij} x_{ij}
  $$

  **Podstawowe ograniczenia:**
  * Wjazd i wyjazd od każdego klienta dokładnie jeden raz:
  
    $$
    \sum_{i \in V} x_{ij} = 1, \quad \sum_{j \in V} x_{ji} = 1 \quad \text{dla wszystkich } j \in N
    $$
    
  * Ograniczenie floty $K$ w bazie, to znaczy w węźle 0:
  
    $$
    \sum_{j \in N} x_{0j} \le K, \quad \sum_{i \in N} x_{i0} \le K
    $$
    
  * **Klasyczne ograniczenia eliminacji podtras i pilnowania pojemności Q:**
  
    $$
    u_j - u_i \ge q_j - Q(1 - x_{ij})
    $$
    
    Gdzie $Q$ to pojemność auta, a $q_j$ to zapotrzebowanie klienta $j$.

* **`cvrp_ilp_opt.py`**
  Znacznie zoptymalizowana wersja modelu ILP. Zostały w niej dodane matematyczne modyfikacje, które drastycznie ułatwiają solverowi odcinanie błędnych gałęzi w drzewie poszukiwań. **Wprowadzono tu następujące optymalizacje:**
  
  1. **Ważne Nierówności:** Model na sztywno oblicza minimalną, fizycznie wymaganą liczbę ciężarówek na podstawie całkowitego popytu wszystkich klientów podzielonego przez pojemność auta i wymusza taką minimalną liczbę wyjazdów oraz powrotów z bazy. Zapobiega to marnowaniu czasu na testowanie tras ze zbyt małą liczbą pojazdów.
  
     $$
     \sum_{j \in N} x_{0j} \ge \left\lceil \frac{\sum_{i \in N} q_i}{Q} \right\rceil
     $$
     
  2. **Zacieśnione granice pojemności:** Klasyczne ograniczenie wymuszające ciągłość trasy zostało rozszerzone o bardzo restrykcyjny składnik uwzględniający przepływ w przeciwnym kierunku. Skutkuje to dużo szybszym odrzucaniem matematycznie niemożliwych układów węzłów.
  
     $$
     u_j - u_i \ge q_j - Q(1 - x_{ij}) + (Q - q_i - q_j)x_{ji}
     $$
     
  3. **Luka Optymalności 5 procent:** Dodano parametr do solvera gapRel=0.05, który wymusza przerwanie poszukiwań i zwrot wyniku w momencie, w którym bieżące rozwiązanie jest udowodnione jako nie gorsze niż 5 procent od matematycznego absolutu. Skraca to czas działania na trudnych instancjach.

* **`cvrp_ilp_warm.py`**
  Wersja eksperymentalna rozbudowana o Heurystyczny Warm Start algorytmu Nearest Neighbor. Algorytm wewnątrz skryptu przed odpaleniem solvera uruchamia heurystykę konstrukcyjną w celu wyznaczenia wstępnej, legalnej trasy. Trasy te są następnie wstrzykiwane w formie predefiniowanych zmiennych $x_{ij}$ bezpośrednio do solvera CBC. Umożliwia to zminimalizowanie czasu wczesnych faz przeszukiwania a czas potrzebny na wyznaczenie heurystycznej trasy i jej konwersję wlicza się całkowicie w proces wstępny przed odliczeniem twardego time_limit.

* **`cvrp_genetic.py`**
  Implementacja Algorytmu Genetycznego do rozwiązywania problemu CVRP. Algorytm na drodze ewolucji krzyżuje i mutuje trasy w oparciu o ich całkowity koszt dystansu. Posiada wbudowany mechanizm Elity Dopuszczalnej, który stale śledzi populację i wyodrębnia z niej na zewnątrz najlepsze rozwiązanie mieszczące się w rygorystycznym limicie ciężarówek.

* **`cvrp_hybrid.py`**
  Model Hybrydowy. W kroku pierwszym odpala Algorytm Genetyczny celem znalezienia świetnego i legalnego punktu startowego. W kroku drugim odpala klasyczny model solvera ILP na pełnym grafie miast, stosując wynikową trasę jako Warm Start, minimalizując tym błądzenia po ułamkowych przestrzeniach matematycznych.

* **`cvrp_hybrid_candidate.py`**
  Inna wersja Hybrydy w projekcie, wykorzystująca architekturę Zredukowanego Grafu Kandydatów. Zamiast uruchamiać skomplikowany model ILP dla tysięcy połączeń drastycznie zmniejsza liczbę zmiennych w modelu matematycznym, zezwalając solverowi wyłącznie na wybór krawędzi spośród:
  1. Krawędzi wyewoluowanych przez Top 10 procent populacji końcowej Algorytmu Genetycznego.
  2. Krawędzi łączących klientów z ich pięcioma najbliższymi sąsiadami w celu zabezpieczenia grafu przed utratą perspektywy globalnego optimum.
  
  Dzięki temu hybrydowemu filtrowaniu i nałożonym cięciom, czas pracy solvera maleje, umożliwiając mu udowodnienie lokalnych lub globalnych minimów.
