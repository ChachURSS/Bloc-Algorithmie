#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test d'installation pour l'application VRP ADEME
Vérifie que toutes les dépendances et modules sont correctement installés
"""

import sys
import os

# Ajouter le dossier src au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_dependencies():
    """Teste les dépendances Python requises."""
    print("Test des dépendances...")
    
    required_packages = [
        'numpy', 'matplotlib', 'scipy', 'pandas', 
        'seaborn', 'plotly', 'networkx', 'vrplib'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   OK {package}")
        except ImportError:
            print(f"   ERREUR {package} - NON INSTALLE")
            missing_packages.append(package)
    
    return len(missing_packages) == 0

def test_core_imports():
    """Teste les imports des modules principaux."""
    print("\nTest des imports principaux...")
    
    try:
        from vrp_instance import VRPInstance
        print("   OK VRPInstance importe")
    except Exception as e:
        print(f"   ERREUR VRPInstance: {e}")
        return False
        
    try:
        from vrp_solver import VRPSolver
        print("   OK VRPSolver importe")
    except Exception as e:
        print(f"   ERREUR VRPSolver: {e}")
        return False
        
    try:
        from solution import Solution
        print("   OK Solution importe")
    except Exception as e:
        print(f"   ERREUR Solution: {e}")
        return False
    
    return True

def test_algorithms():
    """Teste les imports des algorithmes."""
    print("\nTest des algorithmes...")
    
    try:
        from algorithms.construction_heuristics import GreedyConstruction, SavingsAlgorithm
        print("   OK Heuristiques constructives")
    except Exception as e:
        print(f"   ERREUR heuristiques: {e}")
        return False
        
    try:
        from algorithms.simulated_annealing import SimulatedAnnealing
        print("   OK Recuit simule")
    except Exception as e:
        print(f"   ERREUR recuit simule: {e}")
        return False
        
    try:
        from algorithms.tabu_search import TabuSearch
        print("   OK Recherche tabou")
    except Exception as e:
        print(f"   ERREUR recherche tabou: {e}")
        return False
    
    return True

def test_constraints():
    """Teste les imports des contraintes."""
    print("\nTest des contraintes...")
    
    try:
        from constraints.time_windows import TimeWindowConstraint
        print("   OK Fenetres temporelles")
    except Exception as e:
        print(f"   ERREUR fenetres temporelles: {e}")
        return False
    
    return True

def test_functionality():
    """Teste la fonctionnalité de base."""
    print("\nTest de l'application VRP...")
    
    try:
        from vrp_instance import VRPInstance
        from vrp_solver import VRPSolver
        
        # Créer une instance simple
        instance = VRPInstance("test_install")
        instance.node_coords = {0: (0, 0), 1: (10, 10), 2: (20, 0)}
        instance.demands = {0: 0, 1: 10, 2: 15}
        instance.set_fleet(2, 20)
        instance.calculate_distance_matrix()
        
        print(f"   OK Instance creee: {len(instance.node_coords)} noeuds")
        
        # Tester le solveur
        solver = VRPSolver(instance)
        solution = solver.solve("greedy")
        
        print(f"   OK Solution trouvee: cout {solution.total_cost:.2f}")
        print(f"   OK Faisabilite: {solution.feasible}")
        
        return True
        
    except Exception as e:
        print(f"   ERREUR lors du test: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("TEST D'INSTALLATION - APPLICATION VRP ADEME")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test des dépendances
    if not test_dependencies():
        all_tests_passed = False
    
    # Test des imports
    if not test_core_imports():
        all_tests_passed = False
    
    if not test_algorithms():
        all_tests_passed = False
    
    if not test_constraints():
        all_tests_passed = False
    
    # Test de fonctionnalité
    if not test_functionality():
        all_tests_passed = False
    
    # Résultat final
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("SUCCES - TOUS LES TESTS PASSES")
        print("L'application VRP ADEME est prete a l'utilisation !")
        print("\nProchaines etapes:")
        print("   - Executez: python demo_complete.py")
        print("   - Consultez: notebooks/01_modelisation.ipynb")
        print("   - Benchmark: python demo_vrplib_simple.py")
    else:
        print("ERREUR - CERTAINS TESTS ONT ECHOUE")
        print("Verifiez les dependances avec: pip install -r requirements.txt")
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)