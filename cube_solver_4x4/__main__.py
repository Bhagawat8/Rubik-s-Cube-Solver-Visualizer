"""
Command-line interface for 4x4 cube solver.
Allows running: python -m cube_solver_4x4
"""

from .solver_4x4 import solve_4x4
from .tools_4x4 import random_4x4_cube

if __name__ == "__main__":
    print("4x4 Rubik's Cube Solver")
    print("Generating random scramble...")
    
    scrambled_cube = random_4x4_cube()
    print("Solving...")
    
    try:
        solution = solve_4x4(scrambled_cube)
        print(f"Solution: {solution}")
        print(f"Move count: {len(solution.split())}")
    except Exception as e:
        print(f"Error: {e}")