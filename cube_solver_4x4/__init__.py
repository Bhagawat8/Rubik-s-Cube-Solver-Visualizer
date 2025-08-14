"""
4x4 Rubik's Cube Solver
Implements the reduction method: reduce 4x4 to 3x3, then solve using DCP algorithm.
"""

from .solver_4x4 import solve_4x4, verify_4x4
from .tools_4x4 import random_4x4_cube

__all__ = ['solve_4x4', 'verify_4x4', 'random_4x4_cube']

def solve(cube_state):
    """Main solve function for 4x4 cube"""
    return solve_4x4(cube_state)

def verify(cube_state):
    """Verify if 4x4 cube state is valid and solvable"""
    return verify_4x4(cube_state)