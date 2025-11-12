#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRPLib Adapter - Intégration avec la bibliothèque VRPLib
"""

import os
import sys
from typing import Optional, Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from vrp_instance import VRPInstance

class VRPLibAdapter:
    """Adaptateur pour l'intégration avec VRPLib."""
    
    @staticmethod
    def load_instance(instance_name: str) -> VRPInstance:
        """Charge une instance VRPLib (version synthétique pour la démonstration)."""
        try:
            # Pour cette démonstration, nous créons des instances synthétiques
            # car les vraies instances VRPLib nécessitent des fichiers spécifiques
            
            # Normaliser le nom pour éviter les problèmes de casse
            instance_name_lower = instance_name.lower()
            
            if instance_name.startswith("A-n32"):
                return VRPLibAdapter._create_synthetic_instance(31, 5, "A-n32-k5")
            elif instance_name.startswith("A-n33"):
                return VRPLibAdapter._create_synthetic_instance(32, 5, "A-n33-k5")
            elif instance_name.startswith("A-n34"):
                return VRPLibAdapter._create_synthetic_instance(33, 5, "A-n34-k5")
            elif instance_name.startswith("A-n36"):
                return VRPLibAdapter._create_synthetic_instance(35, 5, "A-n36-k5")
            elif instance_name.startswith("A-n37"):
                return VRPLibAdapter._create_synthetic_instance(36, 5, "A-n37-k5")
            elif instance_name_lower.startswith("x-n101"):
                return VRPLibAdapter._create_synthetic_instance(100, 25, "X-n101-k25")
            else:
                # Instance par défaut
                print(f"WARNING: Instance {instance_name} non reconnue, utilisation de l'instance par défaut (20 clients)")
                return VRPLibAdapter._create_synthetic_instance(20, 3, instance_name)
                
        except Exception as e:
            raise Exception(f"Failed to load instance {instance_name}: {e}")
    
    @staticmethod
    def _create_synthetic_instance(num_customers: int, num_vehicles: int, name: str) -> VRPInstance:
        """Crée une instance synthétique basée sur les caractéristiques VRPLib."""
        import random
        
        # Seed basé sur le nom pour la reproductibilité
        seed = hash(name) % 2**32
        random.seed(seed)
        
        # Créer l'instance
        instance = VRPInstance(name)
        
        # Configurer les paramètres de base
        instance.dimension = num_customers + 1  # +1 pour le dépôt
        instance.depot = 0
        
        # Générer des coordonnées aléatoires (dépôt + clients)
        instance.node_coords[0] = (50, 50)  # Dépôt au centre
        for i in range(1, num_customers + 1):
            # Distribution plus réaliste autour du dépôt
            angle = random.uniform(0, 2 * 3.14159)
            radius = random.uniform(10, 40)
            x = 50 + radius * random.uniform(-1, 1)
            y = 50 + radius * random.uniform(-1, 1)
            # Garder dans les limites
            x = max(5, min(95, x))
            y = max(5, min(95, y))
            instance.node_coords[i] = (x, y)
        
        # Générer des demandes réalistes
        instance.demands[0] = 0  # Dépôt a demande 0
        total_demand = 0
        for i in range(1, num_customers + 1):
            # Demandes variées mais réalistes
            demand = random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20])
            instance.demands[i] = demand
            total_demand += demand
        
        # Capacité des véhicules calculée pour être réaliste
        vehicle_capacity = max(30, (total_demand // num_vehicles) + random.randint(5, 15))
        instance.set_fleet(num_vehicles, vehicle_capacity)
        
        # Calculer la matrice des distances
        instance.calculate_distance_matrix()
        
        return instance
    
    @staticmethod
    def load_solution(instance_name: str) -> Optional[Dict[str, Any]]:
        """Charge la solution optimale connue pour une instance."""
        
        # Coûts optimaux connus pour les instances VRPLib classiques
        optimal_costs = {
            "A-n32-k5": 784,
            "A-n33-k5": 661,
            "A-n34-k5": 778,
            "A-n36-k5": 799,
            "A-n37-k5": 669,
            "A-n38-k5": 730,
            "A-n39-k5": 822,
            "A-n45-k6": 944,
            "A-n48-k7": 1073,
            "A-n54-k7": 1167,
            "X-n101-k25": 27591  # Instance de 100 clients
        }
        
        if instance_name in optimal_costs:
            return {
                'cost': optimal_costs[instance_name],
                'instance': instance_name,
                'source': 'VRPLib'
            }
        else:
            # Estimation pour instances inconnues
            print(f"WARNING: Coût optimal non trouvé pour {instance_name}")
            print(f"Clés disponibles: {list(optimal_costs.keys())}")
            return None
    
    @staticmethod
    def calculate_gap(solution_cost: float, optimal_cost: Optional[float]) -> Optional[float]:
        """Calcule le gap entre la solution et l'optimum."""
        if optimal_cost is None or optimal_cost <= 0:
            return None
        
        gap = ((solution_cost - optimal_cost) / optimal_cost) * 100
        return gap  # Peut être négatif si meilleur que l'optimal (rare mais possible)
    
    @staticmethod
    def benchmark_instance(instance_name: str, algorithm: str = "greedy", num_runs: int = 5) -> Dict[str, Any]:
        """
        Effectue un benchmark complet sur une instance.
        
        Args:
            instance_name: Nom de l'instance VRPLib
            algorithm: Algorithme à utiliser
            num_runs: Nombre d'exécutions pour les statistiques
            
        Returns:
            Dictionnaire avec les résultats du benchmark
        """
        from vrp_solver import VRPSolver
        import time
        
        try:
            # Charger l'instance et la solution optimale
            instance = VRPLibAdapter.load_instance(instance_name)
            optimal_solution = VRPLibAdapter.load_solution(instance_name)
            optimal_cost = optimal_solution.get('cost') if optimal_solution else None
            
            # Exécuter plusieurs runs
            results = []
            for run in range(num_runs):
                start_time = time.time()
                
                solver = VRPSolver(instance)
                solution = solver.solve(algorithm)
                
                solve_time = time.time() - start_time
                gap = VRPLibAdapter.calculate_gap(solution.total_cost, optimal_cost)
                
                results.append({
                    'run': run + 1,
                    'cost': solution.total_cost,
                    'gap': gap,
                    'time': solve_time,
                    'feasible': solution.feasible,
                    'num_routes': len(solution.routes)
                })
            
            # Calculer les statistiques
            costs = [r['cost'] for r in results]
            times = [r['time'] for r in results]
            gaps = [r['gap'] for r in results if r['gap'] is not None]
            
            benchmark_result = {
                'instance': instance_name,
                'algorithm': algorithm,
                'num_customers': len(instance.node_coords) - 1,  # -1 pour exclure le dépôt
                'num_vehicles': instance.vehicle_count,
                'vehicle_capacity': instance.capacity,
                'optimal_cost': optimal_cost,
                'runs': num_runs,
                'avg_cost': sum(costs) / len(costs),
                'min_cost': min(costs),
                'max_cost': max(costs),
                'std_cost': (sum((c - sum(costs)/len(costs))**2 for c in costs) / len(costs)) ** 0.5,
                'avg_time': sum(times) / len(times),
                'min_time': min(times),
                'max_time': max(times),
                'avg_gap': sum(gaps) / len(gaps) if gaps else None,
                'min_gap': min(gaps) if gaps else None,
                'feasible_rate': sum(1 for r in results if r['feasible']) / len(results),
                'detailed_results': results
            }
            
            return benchmark_result
            
        except Exception as e:
            return {
                'instance': instance_name,
                'error': str(e),
                'success': False
            }
    
    @staticmethod
    def export_solution(solution, instance_name: str, filename: Optional[str] = None) -> str:
        """Exporte une solution au format VRPLib."""
        if filename is None:
            filename = f"{instance_name}_solution.txt"
        
        with open(filename, 'w') as f:
            f.write(f"Instance: {instance_name}\n")
            f.write(f"Cost: {solution.total_cost:.2f}\n")
            f.write(f"Vehicles used: {len(solution.routes)}\n")
            f.write(f"Feasible: {solution.feasible}\n\n")
            
            for i, route in enumerate(solution.routes):
                f.write(f"Route {i+1}: {' -> '.join(map(str, route))}\n")
        
        return filename

# Fonctions utilitaires pour compatibilité
def load_vrplib_instance(instance_name: str) -> VRPInstance:
    """Fonction utilitaire pour charger une instance VRPLib."""
    return VRPLibAdapter.load_instance(instance_name)

def calculate_gap(solution_cost: float, optimal_cost: float) -> float:
    """Fonction utilitaire pour calculer le gap."""
    return VRPLibAdapter.calculate_gap(solution_cost, optimal_cost)