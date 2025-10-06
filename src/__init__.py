"""
VRP Solver Package
Vehicle Routing Problem optimization with advanced constraints for ADEME project.
"""

__version__ = "1.0.0"
__author__ = "CesiCDP Team"
__email__ = "team@cesicip.com"

from .vrp_solver import VRPSolver
from .vrp_instance import VRPInstance
from .solution import Solution

__all__ = ['VRPSolver', 'VRPInstance', 'Solution']