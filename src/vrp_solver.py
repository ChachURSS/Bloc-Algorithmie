"""
VRP Solver using Simulated Annealing
Main solver class implementing metaheuristic optimization for Vehicle Routing Problem.
"""

import random
import math
import time
from typing import List, Tuple, Optional, Dict, Any
import copy

from .vrp_instance import VRPInstance
from .solution import Solution
from .algorithms.simulated_annealing import SimulatedAnnealing
from .algorithms.tabu_search import TabuSearch
from .algorithms.construction_heuristics import GreedyConstruction, SavingsAlgorithm


class VRPSolver:
    """
    Main VRP solver implementing multiple metaheuristic algorithms.
    """
    
    def __init__(self, instance: VRPInstance):
        self.instance = instance
        self.best_solution: Optional[Solution] = None
        self.algorithm_stats: Dict[str, Any] = {}
        
    def solve(self, algorithm: str = "simulated_annealing", **kwargs) -> Solution:
        """
        Solve the VRP instance using the specified algorithm.
        
        Args:
            algorithm: Algorithm to use ('simulated_annealing', 'tabu_search', 'greedy')
            **kwargs: Algorithm-specific parameters
            
        Returns:
            Best solution found
        """
        start_time = time.time()
        
        # Create initial solution
        if algorithm in ["simulated_annealing", "tabu_search"]:
            initial_solution = self._create_initial_solution(kwargs.get('construction', 'greedy'))
        else:
            initial_solution = None
        
        # Run selected algorithm
        if algorithm == "simulated_annealing":
            solution = self._solve_simulated_annealing(initial_solution, **kwargs)
        elif algorithm == "tabu_search":
            solution = self._solve_tabu_search(initial_solution, **kwargs)
        elif algorithm == "greedy":
            solution = self._solve_greedy(**kwargs)
        elif algorithm == "savings":
            solution = self._solve_savings(**kwargs)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        # Record statistics
        solve_time = time.time() - start_time
        self.algorithm_stats = {
            'algorithm': algorithm,
            'solve_time': solve_time,
            'final_cost': solution.total_cost,
            'feasible': solution.feasible,
            'violations': len(solution.violations)
        }
        
        self.best_solution = solution
        return solution
    
    def _create_initial_solution(self, method: str = "greedy") -> Solution:
        """Create initial solution using construction heuristic."""
        if method == "greedy":
            constructor = GreedyConstruction(self.instance)
        elif method == "savings":
            constructor = SavingsAlgorithm(self.instance)
        else:
            constructor = GreedyConstruction(self.instance)
        
        return constructor.construct()
    
    def _solve_simulated_annealing(self, initial_solution: Solution, **kwargs) -> Solution:
        """Solve using Simulated Annealing."""
        sa = SimulatedAnnealing(
            instance=self.instance,
            initial_temp=kwargs.get('initial_temp', 1000.0),
            final_temp=kwargs.get('final_temp', 1.0),
            cooling_rate=kwargs.get('cooling_rate', 0.95),
            max_iterations=kwargs.get('max_iterations', 10000),
            max_iterations_per_temp=kwargs.get('max_iterations_per_temp', 100)
        )
        
        solution = sa.solve(initial_solution)
        self.algorithm_stats.update(sa.get_stats())
        return solution
    
    def _solve_tabu_search(self, initial_solution: Solution, **kwargs) -> Solution:
        """Solve using Tabu Search."""
        ts = TabuSearch(
            instance=self.instance,
            tabu_tenure=kwargs.get('tabu_tenure', 20),
            max_iterations=kwargs.get('max_iterations', 1000),
            max_no_improvement=kwargs.get('max_no_improvement', 200)
        )
        
        solution = ts.solve(initial_solution)
        self.algorithm_stats.update(ts.get_stats())
        return solution
    
    def _solve_greedy(self, **kwargs) -> Solution:
        """Solve using Greedy Construction."""
        constructor = GreedyConstruction(self.instance)
        solution = constructor.construct()
        solution.calculate_cost()
        return solution
    
    def _solve_savings(self, **kwargs) -> Solution:
        """Solve using Savings Algorithm."""
        constructor = SavingsAlgorithm(self.instance)
        solution = constructor.construct()
        solution.calculate_cost()
        return solution
    
    def get_stats(self) -> Dict[str, Any]:
        """Get solving statistics."""
        return self.algorithm_stats.copy()
    
    def benchmark_algorithms(self, algorithms: List[str] = None, 
                           runs_per_algorithm: int = 5) -> Dict[str, List[float]]:
        """
        Benchmark multiple algorithms on the instance.
        
        Args:
            algorithms: List of algorithms to test
            runs_per_algorithm: Number of runs per algorithm
            
        Returns:
            Dictionary with costs for each algorithm
        """
        if algorithms is None:
            algorithms = ["greedy", "savings", "simulated_annealing", "tabu_search"]
        
        results = {}
        
        for algorithm in algorithms:
            costs = []
            times = []
            
            for run in range(runs_per_algorithm):
                start_time = time.time()
                solution = self.solve(algorithm)
                solve_time = time.time() - start_time
                
                costs.append(solution.total_cost)
                times.append(solve_time)
            
            results[algorithm] = {
                'costs': costs,
                'times': times,
                'avg_cost': sum(costs) / len(costs),
                'min_cost': min(costs),
                'avg_time': sum(times) / len(times)
            }
        
        return results