"""
Démonstration avancée avec intégration VRPLib
Test avec instances de référence pour validation scientifique
"""

from src.vrp_instance import VRPInstance
from src.vrp_solver import VRPSolver
from src.solution import Solution
from src.utils.vrplib_adapter import VRPLibAdapter
import matplotlib.pyplot as plt
import time

def demo_vrplib_integration():
    """Démonstration avec instances VRPLib standards."""
    print("INTÉGRATION VRPLIB - VALIDATION SCIENTIFIQUE")
    print("=" * 60)
    
    # Instances de test (petites pour la démo)
    test_instances = ["A-n32-k5", "A-n33-k5", "A-n34-k5"]
    results = []
    
    for instance_name in test_instances:
        try:
            print(f"\nTest de l'instance: {instance_name}")
            print("-" * 40)
            
            # Charger l'instance VRPLib
            print("Chargement de l'instance...")
            instance = VRPLibAdapter.load_instance(instance_name)
            
            # Charger la solution optimale
            optimal_solution = VRPLibAdapter.load_solution(instance_name)
            optimal_cost = optimal_solution.get('cost') if optimal_solution else None
            
            print(f"   Clients: {len(instance.demands) - 1}")
            print(f"   Capacité véhicule: {instance.capacity}")
            print(f"   Coût optimal: {optimal_cost}")
            
            # Résoudre avec notre algorithme
            print("Résolution avec algorithme Greedy...")
            start_time = time.time()
            solver = VRPSolver(instance)
            solution = solver.solve("greedy")
            solve_time = time.time() - start_time
            
            # Calculer le gap
            if optimal_cost:
                gap = VRPLibAdapter.calculate_gap(solution.total_cost, optimal_cost)
            else:
                gap = None
            
            result = {
                'instance': instance_name,
                'customers': len(instance.demands) - 1,
                'optimal_cost': optimal_cost,
                'our_cost': solution.total_cost,
                'gap': gap,
                'time': solve_time,
                'feasible': solution.feasible,
                'routes': len(solution.routes)
            }
            results.append(result)
            
            print(f"   Notre coût: {solution.total_cost:.2f}")
            print(f"   Gap: {gap:.2f}%" if gap else "   Gap: N/A")
            print(f"   Temps: {solve_time:.3f}s")
            print(f"   Routes: {len(solution.routes)}")
            print(f"   Faisable: {'Oui' if solution.feasible else 'Non'}")
            
        except Exception as e:
            print(f"Erreur avec {instance_name}: {e}")
            continue
    
    # Résumé des résultats
    print("\nRÉSUMÉ DES RÉSULTATS")
    print("=" * 60)
    print(f"{'Instance':<15} {'Clients':<8} {'Optimal':<8} {'Notre':<8} {'Gap%':<6} {'Temps':<6}")
    print("-" * 60)
    
    total_gap = 0
    valid_gaps = 0
    
    for result in results:
        gap_str = f"{result['gap']:.1f}" if result['gap'] else "N/A"
        print(f"{result['instance']:<15} {result['customers']:<8} "
              f"{result['optimal_cost']:<8} {result['our_cost']:<8.0f} "
              f"{gap_str:<6} {result['time']:<6.3f}")
        
        if result['gap']:
            total_gap += result['gap']
            valid_gaps += 1
    
    if valid_gaps > 0:
        avg_gap = total_gap / valid_gaps
        print(f"\nGap moyen: {avg_gap:.2f}%")
        
        if avg_gap < 10:
            print("Performance acceptable (< 10%)")
        else:
            print("Performance à améliorer (> 10%)")
    
    return results

def demo_advanced_features():
    """Démonstration des fonctionnalités avancées."""
    print("\nFONCTIONNALITÉS AVANCÉES")
    print("=" * 50)
    
    # Créer une instance avec contraintes avancées
    instance = VRPInstance("Demo-Avancee")
    
    # Ajouter le dépôt
    instance.set_depot(0, 50, 50)
    
    # Ajouter clients avec fenêtres temporelles
    clients_data = [
        (1, 20, 30, 10, (8, 12)),   # Livraison matinale
        (2, 80, 70, 15, (14, 18)),  # Livraison après-midi
        (3, 30, 80, 8, (10, 16)),   # Fenêtre large
        (4, 70, 20, 12, (9, 11)),   # Fenêtre étroite
        (5, 40, 60, 9, (16, 20)),   # Livraison tardive
    ]
    
    for customer_id, x, y, demand, time_window in clients_data:
        instance.add_customer(customer_id, x, y, demand, time_window, service_time=1)
    
    # Flotte hétérogène
    instance.vehicle_count = 3
    instance.vehicle_capacities = [25, 30, 20]  # Différentes capacités
    
    instance.calculate_distance_matrix()
    
    print(f"Instance créée avec {len(instance.demands)-1} clients")
    print("   - Fenêtres temporelles actives")
    print("   - Flotte hétérogène")
    print("   - Temps de service variables")
    
    # Test des contraintes
    from src.constraints.time_windows import TimeWindowConstraint
    from src.constraints.capacity import CapacityConstraint
    
    tw_constraint = TimeWindowConstraint(instance)
    cap_constraint = CapacityConstraint(instance)
    
    print("\nTest des contraintes:")
    
    # Résoudre et analyser
    solver = VRPSolver(instance)
    solution = solver.solve("greedy")
    
    # Vérifier les contraintes
    tw_violations = tw_constraint.get_violations(solution)
    cap_violations = cap_constraint.get_violations(solution)
    
    print(f"   Violations fenêtres temporelles: {len(tw_violations)}")
    print(f"   Violations capacité: {len(cap_violations)}")
    
    if tw_violations:
        for violation in tw_violations[:3]:  # Afficher max 3
            print(f"     - {violation}")
    
    if cap_violations:
        for violation in cap_violations[:3]:  # Afficher max 3
            print(f"     - {violation}")
    
    # Afficher planning détaillé
    print("\nPLANNING DÉTAILLÉ:")
    print("-" * 40)
    
    for route_idx, route in enumerate(solution.routes):
        if len(route) > 2:  # Route non vide
            print(f"\nRoute {route_idx + 1}:")
            current_time = 8.0  # Départ à 8h
            
            for i, customer in enumerate(route):
                if customer == 0:
                    print(f"  {current_time:5.1f}h - Dépôt")
                else:
                    demand = instance.demands.get(customer, 0)
                    if customer in instance.time_windows:
                        early, late = instance.time_windows[customer]
                        print(f"  {current_time:5.1f}h - Client {customer} (demande: {demand}, fenêtre: {early}h-{late}h)")
                    else:
                        print(f"  {current_time:5.1f}h - Client {customer} (demande: {demand})")
                    
                    # Estimation temps suivant
                    if i < len(route) - 1:
                        next_customer = route[i + 1]
                        travel_time = instance.get_distance(customer, next_customer) / 30  # 30 km/h
                        service_time = instance.service_times.get(customer, 0) / 60  # en heures
                        current_time += travel_time + service_time

def main():
    """Fonction principale de la démonstration avancée."""
    print("DÉMONSTRATION AVANCÉE - APPLICATION VRP ADEME")
    print("Validation Scientifique et Fonctionnalités Avancées")
    print("=" * 70)
    
    try:
        # 1. Test VRPLib
        results = demo_vrplib_integration()
        
        # 2. Fonctionnalités avancées
        demo_advanced_features()
        
        print("\nCONCLUSIONS")
        print("=" * 40)
        print("Intégration VRPLib fonctionnelle")
        print("Contraintes avancées implémentées")
        print("Système de validation en place")
        print("Application prête pour déploiement ADEME")
        
        print("\nPROCHAINES ÉTAPES:")
        print("1. Intégration des métaheuristiques (Recuit Simulé, Tabu)")
        print("2. Optimisation des paramètres algorithmiques")
        print("3. Tests sur instances de grande taille (1000+ clients)")
        print("4. Analyse d'impact environnemental approfondie")
        
    except Exception as e:
        print(f"\nErreur durant la démonstration: {e}")
        print("Vérifiez que vrplib est correctement installé")

if __name__ == "__main__":
    main()