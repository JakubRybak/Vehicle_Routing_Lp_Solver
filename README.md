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
  Wersja eksperymentalna rozbudowana o **Heurystyczny "Ciepły Start" (Warm Start)**. Algorytm wewnątrz skryptu przed odpaleniem solvera uruchamia heurystykę konstrukcyjną w celu wyznaczenia wstępnej, legalnej trasy. Trasy te są następnie wstrzykiwane w formie predefiniowanych zmiennych $x_{ij}$ bezpośrednio do solvera CBC. Umożliwia to zminimalizowanie czasu wczesnych faz przeszukiwania (czas potrzebny na wyznaczenie heurystycznej trasy i jej konwersję wlicza się całkowicie w proces wstępny przed odliczeniem twardego `time_limit`).

* **`cvrp_genetic.py`**
  Zaawansowana, naturalna implementacja **Algorytmu Genetycznego (GA)** do rozwiązywania problemu CVRP bez narzucania niszczących kar (Death Penalty) za przekroczenie limitu pojazdów. Algorytm posiada mechanizm *Elity Dopuszczalnej* – hodowla i krzyżowanie w pętli pokoleń odbywają się całkowicie w oparciu o czysty fizyczny koszt trasy (aby nie utracić różnorodności biologicznej), podczas gdy prezentowany na zewnątrz wynik oraz interaktywne wykresy z biegu wyodrębniają stale śledzonego, najsilniejszego dotąd znalezionego i w 100% legalnego osobnika.

* **`cvrp_hybrid.py`**
  Standardowy model Hybrydowy (Mat-heurystyka). W kroku pierwszym odpala Algorytm Genetyczny (`cvrp_genetic.py`) celem znalezienia świetnego i legalnego punktu startowego. W kroku drugim odpala klasyczny model solvera ILP na pełnym grafie miast, stosując wynikową trasę z GA jako Warm Start, minimalizując tym błądzenia po ułamkowych przestrzeniach matematycznych.

* **`cvrp_hybrid_candidate.py`**
  Najbardziej zoptymalizowana wersja Hybrydy w projekcie, wykorzystująca architekturę **Candidate Graph** (Zredukowanego Grafu Kandydatów). Zamiast uruchamiać skomplikowany model ILP dla tysięcy połączeń (co w CBC skutkuje uderzeniem w limity czasowe), drastycznie zmniejsza liczbę zmiennych w modelu matematycznym, zezwalając solverowi wyłącznie na wybór krawędzi spośród:
  1. Złotych krawędzi wyewoluowanych przez Top 10% populacji końcowej Algorytmu Genetycznego (zarówno dopuszczalnej, jak i niedopuszczalnej).
  2. Krawędzi łączących klientów z ich 5-cioma najbliższymi sąsiadami (k-NN) w celu zabezpieczenia grafu przed utratą perspektywy globalnego optimum.
  
  Dzięki temu hybrydowemu filtrowaniu i nałożonym cięciom, czas pracy solvera maleje drastycznie, umożliwiając mu udowodnienie lokalnych lub globalnych minimów w ułamkach sekund.

### Pliki pomocnicze

* **`plot_utils.py`**
  Moduł wizualizujący – poza rysowaniem map z układami tras, posiada na pokładzie parser logów wyciągający dynamiczny postęp spadania funkcji celu z historii solvera CBC (`cbc_solver.log`) oraz Algorytmu Genetycznego (`ga_solver.csv`). Dodatkowo wrysowuje referencyjną linię z docelowym `optimum_cost` na tło wykresów zbiegania się, demaskując utknięcia w minimach lokalnych.

* **`utils.py`**
  Skrypt techniczny, do którego wydzielono powtarzalne mechanizmy w celu zachowania czystości głównych algorytmów:
  * `parse_vrp` - odpowiada za parsowanie (wczytywanie i interpretację) plików `.vrp` oraz ekstrakcję koordynatów, dystansów i macierzy popytu.
  * `save_results_to_csv` - ustandaryzowana "drukarka", dodająca do pliku analitycznego parametry uruchomienia solvera, czas wykonania i wyliczone trasy.

### Katalogi ze zbiorami i raportami

* **`data/`**
  Katalog przechowujący instancje problemów CVRP ze zróżnicowaną liczbą węzłów (od 7 do 33 klientów) podzielone na grupy A i E.

* **`results/`**
  Katalog docelowy gromadzący raporty z naszych eksperymentów. Znajduje się tam plik `experiments.csv` – zestawienie, pokazujące zachowanie poszczególnych wariantów modelu (ILP_CBC, ILP_CBC_OPT, ILP_CBC_WARM) na testowanych zbiorach danych wraz ze zmierzonymi czasami działania i kosztami.
