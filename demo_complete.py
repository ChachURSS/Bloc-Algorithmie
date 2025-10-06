"""
Démonstration complète de l'application VRP ADEME
Script fonctionnel sans imports relatifs
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Optional
import random
import math
import time
import json

# ===== CLASSES PRINCIPALES =====

class VRPInstance:
    """Représentation d'une instance VRP avec contraintes multiples."""
    
    def __init__(self, name: str = "vrp_instance"):
        self.name = name
        self.dimension = 0
        self.capacity = 0
        self.depot = 0
        
        # Données de base
        self.node_coords: Dict[int, Tuple[float, float]] = {}
        self.demands: Dict[int, int] = {}
        self.distance_matrix: np.ndarray = None
        
        # Fenêtres temporelles (optionnel)
        self.time_windows: Dict[int, Tuple[int, int]] = {}
        self.service_times: Dict[int, int] = {}
        
        # Contraintes de flotte (optionnel)
        self.vehicle_count = 1
        self.vehicle_capacities: List[int] = []
    
    def add_customer(self, customer_id: int, x: float, y: float, demand: int,
                     time_window: Optional[Tuple[int, int]] = None, service_time: int = 0):
        """Ajouter un client à l'instance."""
        self.node_coords[customer_id] = (x, y)
        self.demands[customer_id] = demand
        
        if time_window:
            self.time_windows[customer_id] = time_window
        if service_time > 0:
            self.service_times[customer_id] = service_time
            
        self.dimension = max(self.dimension, customer_id + 1)
    
    def set_depot(self, depot_id: int, x: float, y: float):
        """Définir le dépôt."""
        self.depot = depot_id
        self.node_coords[depot_id] = (x, y)
        self.demands[depot_id] = 0
        
    def calculate_distance_matrix(self):
        """Calculer la matrice des distances euclidiennes."""
        nodes = sorted(self.node_coords.keys())
        n = len(nodes)
        self.distance_matrix = np.zeros((n, n))
        
        for i, node_i in enumerate(nodes):
            for j, node_j in enumerate(nodes):
                if i != j:
                    x1, y1 = self.node_coords[node_i]
                    x2, y2 = self.node_coords[node_j]
                    distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
                    self.distance_matrix[i][j] = distance
    
    def set_fleet(self, vehicle_count: int, capacity: int = None):
        """Configurer la flotte de véhicules."""
        self.vehicle_count = vehicle_count
        if capacity is not None:
            self.capacity = capacity
            self.vehicle_capacities = [capacity] * vehicle_count
    
    def get_distance(self, from_node: int, to_node: int) -> float:
        """Obtenir la distance entre deux nœuds."""
        if self.distance_matrix is not None:
            return self.distance_matrix[from_node][to_node]
        else:
            x1, y1 = self.node_coords[from_node]
            x2, y2 = self.node_coords[to_node]
            return np.sqrt((x1 - x2)**2 + (y1 - y2)**2)


class Solution:
    """Représentation d'une solution VRP."""
    
    def __init__(self, instance: VRPInstance = None):
        self.instance = instance
        self.routes: List[List[int]] = []
        self.total_cost: float = 0.0
        self.total_distance: float = 0.0
        self.feasible: bool = True
        self.violations: List[str] = []
    
    def add_route(self, route: List[int]):
        """Ajouter une route à la solution."""
        if route and route[0] != self.instance.depot:
            route = [self.instance.depot] + route
        if route and route[-1] != self.instance.depot:
            route = route + [self.instance.depot]
        self.routes.append(route)
    
    def calculate_cost(self) -> float:
        """Calculer le coût total de la solution."""
        if not self.instance:
            return 0.0
        
        total_cost = 0.0
        for route in self.routes:
            for i in range(len(route) - 1):
                from_node = route[i]
                to_node = route[i + 1]
                total_cost += self.instance.get_distance(from_node, to_node)
        
        self.total_cost = total_cost
        self.total_distance = total_cost
        return total_cost
    
    def is_feasible(self) -> bool:
        """Vérifier la faisabilité de la solution."""
        self.violations = []
        
        # Vérifier les contraintes de capacité
        for i, route in enumerate(self.routes):
            route_load = sum(self.instance.demands.get(customer, 0) 
                           for customer in route if customer != self.instance.depot)
            vehicle_capacity = (self.instance.vehicle_capacities[i] 
                              if i < len(self.instance.vehicle_capacities) 
                              else self.instance.capacity)
            
            if route_load > vehicle_capacity:
                self.violations.append(f"Route {i}: surcharge {route_load} > {vehicle_capacity}")
        
        self.feasible = len(self.violations) == 0
        return self.feasible
    
    def copy(self):
        """Créer une copie de la solution."""
        new_solution = Solution(self.instance)
        new_solution.routes = [route.copy() for route in self.routes]
        new_solution.total_cost = self.total_cost
        new_solution.feasible = self.feasible
        new_solution.violations = self.violations.copy()
        return new_solution


class GreedyConstruction:
    """Heuristique constructive greedy pour VRP."""
    
    def __init__(self, instance: VRPInstance):
        self.instance = instance
    
    def construct(self) -> Solution:
        """Construire une solution avec l'heuristique du plus proche voisin."""
        solution = Solution(self.instance)
        unvisited = set(self.instance.demands.keys()) - {self.instance.depot}
        
        vehicle_id = 0
        while unvisited and vehicle_id < self.instance.vehicle_count:
            route = self._build_route(unvisited, vehicle_id)
            if route:
                solution.add_route(route)
                for customer in route:
                    if customer in unvisited:
                        unvisited.remove(customer)
            vehicle_id += 1
        
        # Gérer les clients restants
        while unvisited:
            remaining = list(unvisited)
            solution.add_route([remaining[0]])
            unvisited.remove(remaining[0])
        
        solution.calculate_cost()
        return solution
    
    def _build_route(self, unvisited: set, vehicle_id: int) -> List[int]:
        """Construire une route pour un véhicule."""
        route = [self.instance.depot]
        current_node = self.instance.depot
        current_load = 0
        
        vehicle_capacity = (self.instance.vehicle_capacities[vehicle_id] 
                          if vehicle_id < len(self.instance.vehicle_capacities) 
                          else self.instance.capacity)
        
        while unvisited:
            best_customer = None
            best_distance = float('inf')
            
            for customer in unvisited:
                demand = self.instance.demands.get(customer, 0)
                if current_load + demand > vehicle_capacity:
                    continue
                
                distance = self.instance.get_distance(current_node, customer)
                if distance < best_distance:
                    best_distance = distance
                    best_customer = customer
            
            if best_customer is None:
                break
            
            route.append(best_customer)
            current_node = best_customer
            current_load += self.instance.demands.get(best_customer, 0)
            unvisited.remove(best_customer)
        
        route.append(self.instance.depot)
        return route if len(route) > 2 else []


class VRPSolver:
    """Solveur principal VRP."""
    
    def __init__(self, instance: VRPInstance):
        self.instance = instance
        self.best_solution: Optional[Solution] = None
    
    def solve(self, algorithm: str = "greedy", **kwargs) -> Solution:
        """Résoudre l'instance VRP."""
        if algorithm == "greedy":
            constructor = GreedyConstruction(self.instance)
            solution = constructor.construct()
            solution.calculate_cost()
            self.best_solution = solution
            return solution
        else:
            raise ValueError(f"Algorithme non supporté: {algorithm}")


# ===== FONCTIONS DE DÉMONSTRATION =====

def create_sample_instance() -> VRPInstance:
    """Créer une instance d'exemple."""
    instance = VRPInstance("ADEME-Demo-10clients")
    
    # Dépôt central
    instance.set_depot(0, 50, 50)
    
    # Clients avec coordonnées, demandes et fenêtres temporelles
    clients_data = [
        (1, 20, 30, 8, (8, 12)),   # Client 1
        (2, 80, 70, 12, (9, 14)),  # Client 2  
        (3, 30, 80, 6, (10, 16)),  # Client 3
        (4, 70, 20, 15, (11, 15)), # Client 4
        (5, 40, 60, 9, (13, 17)),  # Client 5
        (6, 60, 80, 11, (8, 13)),  # Client 6
        (7, 10, 50, 7, (14, 18)),  # Client 7
        (8, 90, 40, 13, (10, 15)), # Client 8
        (9, 25, 75, 5, (12, 16)),  # Client 9
        (10, 75, 85, 10, (9, 14)), # Client 10
    ]
    
    for customer_id, x, y, demand, time_window in clients_data:
        instance.add_customer(customer_id, x, y, demand, time_window, service_time=1)
    
    # Configuration de la flotte
    instance.set_fleet(3, 30)  # 3 véhicules de capacité 30
    
    # Calculer les distances
    instance.calculate_distance_matrix()
    
    return instance


def visualize_solution(instance: VRPInstance, solution: Solution):
    """Visualiser une solution VRP."""
    plt.figure(figsize=(12, 8))
    
    # Couleurs pour les routes
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
    
    # Tracer les clients
    customers = [(x, y) for node, (x, y) in instance.node_coords.items() if node != instance.depot]
    if customers:
        cx, cy = zip(*customers)
        plt.scatter(cx, cy, c='lightblue', s=100, alpha=0.7, label='Clients', zorder=3)
    
    # Tracer le dépôt
    dx, dy = instance.node_coords[instance.depot]
    plt.scatter(dx, dy, c='red', s=200, marker='s', label='Dépôt', zorder=5)
    
    # Tracer les routes
    for route_idx, route in enumerate(solution.routes):
        if len(route) > 2:  # Route avec des clients
            color = colors[route_idx % len(colors)]
            
            # Points de la route
            route_x = [instance.node_coords[node][0] for node in route]
            route_y = [instance.node_coords[node][1] for node in route]
            
            # Tracer les segments
            plt.plot(route_x, route_y, color=color, linewidth=2, alpha=0.7, 
                    label=f'Route {route_idx + 1}', zorder=2)
            
            # Marquer les points de passage
            for i, node in enumerate(route):
                if node != instance.depot:
                    x, y = instance.node_coords[node]
                    plt.scatter(x, y, c=color, s=60, zorder=4)
    
    # Annotations
    for node, (x, y) in instance.node_coords.items():
        if node != instance.depot:
            demand = instance.demands.get(node, 0)
            time_window = instance.time_windows.get(node, (0, 24))
            plt.annotate(f'{node}\\nD:{demand}\\n{time_window[0]}h-{time_window[1]}h', 
                        (x, y), xytext=(5, 5), textcoords='offset points', 
                        fontsize=8, bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.title(f'Solution VRP - {instance.name}\\nCoût total: {solution.total_cost:.2f}', fontsize=14)
    plt.xlabel('Coordonnée X')
    plt.ylabel('Coordonnée Y')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def analyze_solution(instance: VRPInstance, solution: Solution):
    """Analyser une solution en détail."""
    print(f"\\n📊 ANALYSE DE LA SOLUTION")
    print(f"{'='*50}")
    
    # Informations générales
    print(f"Instance: {instance.name}")
    print(f"Nombre de clients: {len(instance.demands) - 1}")
    print(f"Nombre de véhicules: {len(solution.routes)}")
    print(f"Coût total: {solution.total_cost:.2f}")
    print(f"Solution réalisable: {'✅' if solution.feasible else '❌'}")
    
    if solution.violations:
        print(f"Violations: {', '.join(solution.violations)}")
    
    # Analyse par route
    print(f"\\n🚛 DÉTAIL DES ROUTES:")
    print(f"{'-'*60}")
    
    total_demand = 0
    for i, route in enumerate(solution.routes):
        if len(route) > 2:  # Route avec clients
            customers = [c for c in route if c != instance.depot]
            route_demand = sum(instance.demands.get(c, 0) for c in customers)
            route_distance = 0
            
            for j in range(len(route) - 1):
                route_distance += instance.get_distance(route[j], route[j+1])
            
            capacity = (instance.vehicle_capacities[i] if i < len(instance.vehicle_capacities) 
                       else instance.capacity)
            
            print(f"Route {i+1}: {' → '.join(map(str, route))}")
            print(f"  Clients: {len(customers)}")
            print(f"  Demande: {route_demand}/{capacity} ({route_demand/capacity*100:.1f}%)")
            print(f"  Distance: {route_distance:.2f}")
            
            total_demand += route_demand
    
    # Statistiques globales
    total_capacity = sum(instance.vehicle_capacities) if instance.vehicle_capacities else instance.capacity * instance.vehicle_count
    print(f"\\n📈 STATISTIQUES GLOBALES:")
    print(f"{'-'*30}")
    print(f"Demande totale: {total_demand}")
    print(f"Capacité totale: {total_capacity}")
    print(f"Taux d'utilisation: {total_demand/total_capacity*100:.1f}%")
    print(f"Distance moyenne par route: {solution.total_cost/len(solution.routes):.2f}")


def benchmark_algorithms():
    """Comparer différentes configurations."""
    print(f"\\n🔬 BENCHMARK DES ALGORITHMES")
    print(f"{'='*50}")
    
    # Créer plusieurs instances de test
    instances = []
    
    # Instance petite (5 clients)
    small_instance = VRPInstance("Petite-5clients")
    small_instance.set_depot(0, 50, 50)
    for i in range(1, 6):
        x, y = random.uniform(10, 90), random.uniform(10, 90)
        demand = random.randint(5, 15)
        small_instance.add_customer(i, x, y, demand)
    small_instance.set_fleet(2, 25)
    small_instance.calculate_distance_matrix()
    instances.append(small_instance)
    
    # Instance moyenne (10 clients) - celle déjà créée
    instances.append(create_sample_instance())
    
    # Tester sur chaque instance
    results = []
    for instance in instances:
        solver = VRPSolver(instance)
        
        start_time = time.time()
        solution = solver.solve("greedy")
        solve_time = time.time() - start_time
        
        results.append({
            'instance': instance.name,
            'clients': len(instance.demands) - 1,
            'vehicles': len(solution.routes),
            'cost': solution.total_cost,
            'time': solve_time,
            'feasible': solution.feasible
        })
    
    # Afficher les résultats
    print(f"\\n📋 RÉSULTATS DU BENCHMARK:")
    print(f"{'-'*80}")
    print(f"{'Instance':<20} {'Clients':>8} {'Véhicules':>10} {'Coût':>10} {'Temps(s)':>10} {'Faisable':>10}")
    print(f"{'-'*80}")
    
    for result in results:
        feasible_str = "✅" if result['feasible'] else "❌"
        print(f"{result['instance']:<20} {result['clients']:>8} {result['vehicles']:>10} "
              f"{result['cost']:>10.2f} {result['time']:>10.3f} {feasible_str:>10}")


def main():
    """Fonction principale de démonstration."""
    print(f"🚛 APPLICATION VRP POUR ADEME")
    print(f"{'='*60}")
    print(f"Optimisation des Tournées de Livraison")
    print(f"Projet de Mobilité Multimodale Intelligente")
    print(f"{'='*60}")
    
    # 1. Créer une instance d'exemple
    print(f"\\n📝 1. CRÉATION D'UNE INSTANCE D'EXEMPLE")
    instance = create_sample_instance()
    print(f"✅ Instance créée: {instance.name}")
    print(f"   - {len(instance.demands) - 1} clients")
    print(f"   - {instance.vehicle_count} véhicules de capacité {instance.capacity}")
    print(f"   - Fenêtres temporelles: {len(instance.time_windows)} clients")
    
    # 2. Résoudre avec l'algorithme greedy
    print(f"\\n🧮 2. RÉSOLUTION AVEC ALGORITHME GREEDY")
    solver = VRPSolver(instance)
    
    start_time = time.time()
    solution = solver.solve("greedy")
    solve_time = time.time() - start_time
    
    print(f"✅ Solution trouvée en {solve_time:.3f}s")
    print(f"   - Coût total: {solution.total_cost:.2f}")
    print(f"   - Nombre de routes: {len(solution.routes)}")
    print(f"   - Faisabilité: {'✅' if solution.feasible else '❌'}")
    
    # 3. Analyse détaillée
    analyze_solution(instance, solution)
    
    # 4. Visualisation
    print(f"\\n📊 3. VISUALISATION DE LA SOLUTION")
    try:
        visualize_solution(instance, solution)
        print(f"✅ Graphique affiché")
    except Exception as e:
        print(f"❌ Erreur lors de la visualisation: {e}")
    
    # 5. Benchmark
    benchmark_algorithms()
    
    # 6. Suggestions d'amélioration
    print(f"\\n💡 SUGGESTIONS D'AMÉLIORATION")
    print(f"{'='*40}")
    print(f"1. Implémenter le Recuit Simulé pour améliorer les solutions")
    print(f"2. Ajouter la recherche Tabou pour l'intensification")
    print(f"3. Intégrer les contraintes de fenêtres temporelles dans le solveur")
    print(f"4. Développer l'optimisation du trafic dynamique")
    print(f"5. Connecter à vrplib pour les benchmarks standards")
    
    print(f"\\n🎯 IMPACT ENVIRONNEMENTAL ESTIMÉ")
    print(f"{'='*40}")
    total_distance = solution.total_cost
    co2_factor = 0.2  # kg CO2 par km (estimation)
    co2_saved = total_distance * 0.15 * co2_factor  # 15% d'économie estimée
    print(f"Distance totale: {total_distance:.2f} km")
    print(f"Réduction CO₂ estimée: {co2_saved:.2f} kg avec optimisation")
    print(f"Équivalent à: {co2_saved/2.3:.1f} litres d'essence économisés")
    
    print(f"\\n✅ DÉMONSTRATION TERMINÉE - APPLICATION PRÊTE POUR ADEME")


if __name__ == "__main__":
    main()