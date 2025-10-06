#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de validation finale pour l'application VRP ADEME
Version simplifiée qui teste les fonctionnalités principales
"""

import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_basic_functionality():
    """Test de base de l'application VRP."""
    print("TEST DE VALIDATION VRP ADEME")
    print("=" * 50)
    
    try:
        print("\n1. Test des dépendances critiques...")
        import numpy as np
        import matplotlib.pyplot as plt
        print("   OK - NumPy et Matplotlib")
        
        print("\n2. Test de l'instance VRP...")
        from vrp_instance import VRPInstance
        
        instance = VRPInstance("validation_test")
        instance.node_coords = {
            0: (0, 0),    # Dépôt
            1: (10, 10),  # Client 1
            2: (20, 5),   # Client 2
            3: (5, 15)    # Client 3
        }
        instance.demands = {0: 0, 1: 10, 2: 15, 3: 8}
        instance.set_fleet(2, 25)
        instance.calculate_distance_matrix()
        
        print(f"   OK - Instance créée avec {len(instance.node_coords)} nœuds")
        print(f"   OK - Matrice de distances calculée: {instance.distance_matrix.shape}")
        
        print("\n3. Test de la solution...")
        from solution import Solution
        
        # Créer une solution simple
        solution = Solution(instance)
        solution.add_route([0, 1, 2, 0])
        solution.add_route([0, 3, 0])
        solution.calculate_cost()
        
        print(f"   OK - Solution créée avec {len(solution.routes)} routes")
        print(f"   OK - Coût total: {solution.total_cost:.2f}")
        print(f"   OK - Faisabilité: {solution.feasible}")
        
        print("\n4. Test des algorithmes de base...")
        # Test direct des algorithmes sans imports relatifs
        from algorithms.construction_heuristics import GreedyConstruction
        
        greedy = GreedyConstruction()
        greedy_solution = greedy.solve(instance)
        
        print(f"   OK - Algorithme Greedy: coût {greedy_solution.total_cost:.2f}")
        
        # Test Savings
        from algorithms.construction_heuristics import SavingsAlgorithm
        
        savings = SavingsAlgorithm()
        savings_solution = savings.solve(instance)
        
        print(f"   OK - Algorithme Savings: coût {savings_solution.total_cost:.2f}")
        
        print("\n5. Test VRPLib Integration...")
        from utils.vrplib_adapter import VRPLibAdapter
        
        test_instance = VRPLibAdapter.load_instance("A-n32-k5")
        print(f"   OK - Instance VRPLib chargée: {len(test_instance.node_coords)} nœuds")
        
        # Test de calcul de gap
        gap = VRPLibAdapter.calculate_gap(500, 400)
        print(f"   OK - Calcul de gap: {gap:.2f}%")
        
        print("\n6. Test de visualisation...")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Dessiner les nœuds
        for node_id, (x, y) in instance.node_coords.items():
            if node_id == 0:
                ax.plot(x, y, 'rs', markersize=10, label='Dépôt')
            else:
                ax.plot(x, y, 'bo', markersize=8, label='Client' if node_id == 1 else "")
        
        # Dessiner les routes de la solution
        colors = ['red', 'blue', 'green', 'orange', 'purple']
        for i, route in enumerate(solution.routes):
            route_coords = [instance.node_coords[node] for node in route]
            xs, ys = zip(*route_coords)
            ax.plot(xs, ys, colors[i % len(colors)], linewidth=2, alpha=0.7)
        
        ax.set_title('Solution VRP - Test de Validation')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.savefig('test_validation_plot.png', dpi=100, bbox_inches='tight')
        plt.close()  # Fermer pour éviter l'affichage
        
        print("   OK - Graphique sauvegardé: test_validation_plot.png")
        
        print("\n" + "=" * 50)
        print("SUCCESS - VALIDATION COMPLETE")
        print("✓ Application VRP ADEME opérationnelle")
        print("✓ Tous les modules fonctionnent")
        print("✓ Algorithmes disponibles")
        print("✓ VRPLib intégré")
        print("✓ Visualisation active")
        
        print("\nDémonstrations disponibles:")
        print("  python demo_complete.py")
        print("  python demo_vrplib_simple.py")
        
        return True
        
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_functionality()
    print(f"\nRésultat: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)