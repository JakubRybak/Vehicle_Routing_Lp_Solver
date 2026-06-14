# Capacitated Vehicle Routing Problem (CVRP) - Solvery ILP

Ten projekt zawiera implementację oraz optymalizację algorytmów rozwiązujących problem wyznaczania tras pojazdów z ograniczeniem pojemności (CVRP) przy użyciu programowania całkowitoliczbowego (ILP) w bibliotece PuLP z darmowym solverem CBC.

## Struktura plików

W głównym katalogu projektu znajdują się następujące kluczowe pliki:

### Pliki główne (Modele i Algorytmy)

* **`cvrp_ilp.py`**
  Podstawowa, klasyczna implementacja modelu matematycznego ILP. Używa sformułowania przepływowego oraz standardowych ograniczeń **MTZ (Miller-Tucker-Zemlin)** do eliminacji podtras i wymuszania pojemności. Jest to wariant bazowy, w którym kompilator matematyczny poszukuje optymalnego rozwiązania bez żadnych dodatkowych podpowiedzi ze strony programisty.
  
  **Zmienne decyzyjne:**
  * $x_{ij} \in \{0, 1\}$ – zmienna binarna; przyjmuje 1, jeśli ciężarówka przemieszcza się bezpośrednio z węzła $i$ do $j$.
  * $u_i \ge 0$ – ciągła zmienna pomocnicza, pełniąca rolę skumulowanego "licznika wydanych paczek" w pojeździe po obsłużeniu klienta $i$.

  **Funkcja celu:** (Minimalizacja całkowitego dystansu)
  
  $$
  \min \sum_{i \in V} \sum_{j \in V, j \neq i} c_{ij} x_{ij}
  $$

  **Podstawowe ograniczenia:**
  * Wjazd i wyjazd od każdego klienta dokładnie jeden raz:
  
    $$
    \sum_{i \in V} x_{ij} = 1, \quad \sum_{j \in V} x_{ji} = 1 \quad \text{dla wszystkich } j \in N
    $$
    
  * Ograniczenie floty ($K$) w bazie (węzeł 0):
  
    $$
    \sum_{j \in N} x_{0j} \le K, \quad \sum_{i \in N} x_{i0} \le K
    $$
    
  * **Klasyczne MTZ (eliminacja podtras i pilnowanie pojemności Q):**
  
    $$
    u_j - u_i \ge q_j - Q(1 - x_{ij})
    $$
    
    Gdzie $Q$ to pojemność auta, a $q_j$ to zapotrzebowanie (demand) klienta $j$.

* **`cvrp_ilp_opt.py`**
  Znacznie zoptymalizowana wersja modelu ILP. Zostały w niej dodane matematyczne modyfikacje, które drastycznie ułatwiają solverowi odcinanie błędnych gałęzi w drzewie poszukiwań. **Wprowadzono tu następujące optymalizacje:**
  
  1. **Ważne Nierówności (Valid Inequalities):** Model na sztywno oblicza minimalną, fizycznie wymaganą liczbę ciężarówek (całkowity popyt wszystkich klientów podzielony przez pojemność auta) i wymusza taką minimalną liczbę wyjazdów oraz powrotów z bazy. Zapobiega to marnowaniu czasu na testowanie tras ze zbyt małą liczbą pojazdów.
  
     $$
     \sum_{j \in N} x_{0j} \ge \left\lceil \frac{\sum_{i \in N} q_i}{Q} \right\rceil
     $$
     
  2. **Zacieśnione granice MTZ (Formuła Desrochers'a i Laporte'a):** Klasyczne ograniczenie MTZ zostało rozszerzone o bardzo restrykcyjny składnik uwzględniający przepływ w przeciwnym kierunku. Skutkuje to dużo szybszym odrzucaniem matematycznie niemożliwych układów węzłów podczas fazy pre-solve.
  
     $$
     u_j - u_i \ge q_j - Q(1 - x_{ij}) + (Q - q_i - q_j)x_{ji}
     $$
     
  3. **Luka Optymalności (Optimality Gap = 5%):** Dodano parametr do solvera `gapRel=0.05`, który wymusza przerwanie poszukiwań i zwrot wyniku w momencie, w którym bieżące rozwiązanie jest udowodnione jako nie gorsze niż 5% od matematycznego absolutu. Skraca to czas działania na trudnych instancjach z godzin do zaledwie minut lub sekund.

* **`cvrp_ilp_warm.py`**
  Wersja eksperymentalna rozbudowana o **Heurystyczny "Ciepły Start" (Warm Start)**. Algorytm wewnątrz skryptu przed odpaleniem solvera uruchamia prostą heurystykę konstrukcyjną typu *Nearest Neighbor* (Najbliższy Sąsiad). Heurystyka ta "zachłannie" buduje wstępne, w pełni legalne trasy. Trasy te są następnie wstrzykiwane w formie predefiniowanych zmiennych $x_{ij}$ bezpośrednio do solvera CBC. Solver odbiera te jedynki jako silne rozwiązanie początkowe, co pozwala mu pominąć setki tysięcy pierwszych węzłów i natychmiast rozpocząć odcinanie słabych kombinacji.

### Pliki pomocnicze

* **`utils.py`**
  Skrypt techniczny, do którego wydzielono powtarzalne mechanizmy w celu zachowania czystości głównych algorytmów:
  * `parse_vrp` - odpowiada za parsowanie (wczytywanie i interpretację) plików `.vrp` oraz ekstrakcję koordynatów, dystansów i macierzy popytu.
  * `save_results_to_csv` - ustandaryzowana "drukarka", dodająca do pliku analitycznego parametry uruchomienia solvera, czas wykonania i wyliczone trasy.

### Katalogi ze zbiorami i raportami

* **`data/`**
  Katalog przechowujący instancje problemów CVRP ze zróżnicowaną liczbą węzłów (od 7 do 33 klientów) podzielone na grupy A i E.

* **`results/`**
  Katalog docelowy gromadzący raporty z naszych eksperymentów. Znajduje się tam plik `experiments.csv` – zestawienie, pokazujące zachowanie poszczególnych wariantów modelu (ILP_CBC, ILP_CBC_OPT, ILP_CBC_WARM) na testowanych zbiorach danych wraz ze zmierzonymi czasami działania i kosztami.
