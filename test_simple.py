#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test de validation rapide pour l'application VRP ADEME
"""

import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Test de validation principal."""
    print("VALIDATION VRP ADEME - Test Rapide")
    print("=" * 40)
    
    try:
        print("\n1. Test des dépendances...")
        import numpy as np
        import matplotlib.pyplot as plt
        print("   OK - Dépendances principales")
        
        print("\n2. Test de l'instance...")
        from vrp_instance import VRPInstance
        
        instance = VRPInstance("test")
        instance.node_coords = {0: (0, 0), 1: (10, 10), 2: (20, 0)}
        instance.demands = {0: 0, 1: 10, 2: 15}
        instance.set_fleet(2, 20)
        instance.calculate_distance_matrix()
        print("   OK - Instance VRP créée")
        
        print("\n3. Test du solveur...")
        from vrp_solver import VRPSolver
        
        solver = VRPSolver(instance)
        solution = solver.solve("greedy")
        
        print(f"   OK - Solution: coût {solution.total_cost:.2f}")
        print(f"   OK - Faisable: {solution.feasible}")
        print(f"   OK - Routes: {len(solution.routes)}")
        
        print("\n4. Test VRPLib...")
        from utils.vrplib_adapter import VRPLibAdapter
        
        vrp_instance = VRPLibAdapter.load_instance("A-n32-k5")
        print(f"   OK - Instance VRPLib: {len(vrp_instance.node_coords)} nœuds")
        
        print("\n" + "=" * 40)
        print("SUCCESS - APPLICATION VRP ADEME VALIDÉE")
        print("\nDémonstrations:")
        print("  python demo_complete.py")
        print("  python demo_vrplib_simple.py")
        
        return True
        
    except Exception as e:
        print(f"\nERREUR: {e}")
        print("Vérifiez l'installation avec: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)