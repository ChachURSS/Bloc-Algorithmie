#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstration VRPLib Integration - Version Simple
Application VRP pour ADEME avec benchmarking VRPLib

Equipe CesiCDP - Octobre 2025
"""

import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))

import time
from src.vrp_instance import VRPInstance
from src.vrp_solver import VRPSolver
from src.utils.vrplib_adapter import VRPLibAdapter

def demo_vrplib_simple():
    """Demo simplifiee de l'integration VRPLib."""
    
    print("=== DEMO VRPLIB INTEGRATION ===")
    print("Application VRP pour ADEME")
    print("Equipe CesiCDP - Octobre 2025")
    print()
    
    # Test instances (taille croissante)
    test_instances = ["A-n32-k5", "A-n33-k5", "A-n34-k5"]
    algorithms = ["greedy", "savings"]
    
    print("BENCHMARK SUR INSTANCES VRPLIB")
    print("=" * 50)
    
    all_results = []
    
    for instance_name in test_instances:
        try:
            print(f"\nInstance: {instance_name}")
            
            # Charger l'instance
            instance = VRPLibAdapter.load_instance(instance_name)
            print(f"Clients: {len(instance.node_coords) - 1}")  # -1 pour exclure le dépôt
            print(f"Vehicules: {instance.vehicle_count}")
            print(f"Capacite: {instance.capacity}")
            
            # Charger la solution optimale si disponible
            optimal_solution = VRPLibAdapter.load_solution(instance_name)
            optimal_cost = optimal_solution.get('cost') if optimal_solution else None
            if optimal_cost:
                print(f"Cout optimal: {optimal_cost}")
            
            # Tester chaque algorithme
            for algorithm in algorithms:
                print(f"\n  Algorithme: {algorithm}")
                
                start_time = time.time()
                solver = VRPSolver(instance)
                solution = solver.solve(algorithm)
                solve_time = time.time() - start_time
                
                # Calculer le gap si on a l'optimal
                gap = VRPLibAdapter.calculate_gap(solution.total_cost, optimal_cost) if optimal_cost else None
                
                print(f"   Cout: {solution.total_cost:.2f}")
                if gap is not None:
                    print(f"   Gap: {gap:.2f}%")
                print(f"   Temps: {solve_time:.3f}s")
                print(f"   Routes: {len(solution.routes)}")
                print(f"   Faisable: {'Oui' if solution.feasible else 'Non'}")
                
                # Stocker pour analyse
                result = {
                    'instance': instance_name,
                    'algorithm': algorithm,
                    'cost': solution.total_cost,
                    'gap': gap,
                    'time': solve_time,
                    'feasible': solution.feasible,
                    'num_routes': len(solution.routes)
                }
                all_results.append(result)
                
                # Afficher detail des routes si petite instance
                if len(instance.node_coords) <= 10:
                    print("   Detail routes:")
                    for i, route in enumerate(solution.routes):
                        print(f"     Route {i+1}: {route}")
        
        except Exception as e:
            print(f"   ERREUR: {e}")
            continue
    
    # Analyse globale
    print(f"\n\nANALYSE GLOBALE")
    print("=" * 30)
    
    if all_results:
        valid_results = [r for r in all_results if r['gap'] is not None]
        
        if valid_results:
            avg_gap = sum(r['gap'] for r in valid_results) / len(valid_results)
            min_gap = min(r['gap'] for r in valid_results)
            max_gap = max(r['gap'] for r in valid_results)
            
            print(f"Gap moyen: {avg_gap:.2f}%")
            print(f"Meilleur gap: {min_gap:.2f}%")
            print(f"Pire gap: {max_gap:.2f}%")
        
        avg_time = sum(r['time'] for r in all_results) / len(all_results)
        feasible_rate = sum(1 for r in all_results if r['feasible']) / len(all_results)
        
        print(f"Temps moyen: {avg_time:.3f}s")
        print(f"Taux faisabilite: {feasible_rate:.0%}")
        
        # Comparaison des algorithmes
        print(f"\nComparaison algorithmes:")
        for algo in algorithms:
            algo_results = [r for r in all_results if r['algorithm'] == algo]
            if algo_results:
                avg_cost = sum(r['cost'] for r in algo_results) / len(algo_results)
                avg_time_algo = sum(r['time'] for r in algo_results) / len(algo_results)
                print(f"  {algo}: cout={avg_cost:.2f}, temps={avg_time_algo:.3f}s")
    
    print(f"\nBENCHMARK TERMINE")
    print(f"Instances testees: {len(test_instances)}")
    print(f"Resultats obtenus: {len(all_results)}")
    
    return all_results

if __name__ == "__main__":
    results = demo_vrplib_simple()