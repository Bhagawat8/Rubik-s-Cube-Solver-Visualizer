"""
4x4 Rubik's Cube Solver Demo
Demonstrates the 4x4 solving capabilities with same interface as 3x3 demo.
"""

import argparse
import time
from cube_solver_4x4 import solve_4x4, verify_4x4
from cube_solver_4x4.tools_4x4 import random_4x4_cube, pretty_print_4x4, apply_moves_4x4
from cube_solver_4x4.tools_4x4 import show_4x4_steps_console

def main():
    parser = argparse.ArgumentParser(
        description="4x4 Rubik's cube solver - supports solve and show-steps modes.",
    )
    parser.add_argument("--show-steps", action="store_true", 
                       help="Print each intermediate cube state")
    args = parser.parse_args()

    # Regular solving demo
    print("4x4 Rubik's Cube Solver Demo")
    print("=" * 40)
    
    # Generate random scramble
    scramble, solution_hint = random_4x4_cube()
    
    print("Your 4x4 cube:\n")
    print(pretty_print_4x4(scramble))
    print("\nCalculating solution...")
    
    # Solve the cube
    solve_start = time.time()
    solution = solve_4x4(scramble, solution_hint)
    solve_time = time.time() - solve_start
    
    print(f"\nSolution found!")
    print(f"Moves: {solution}")
    print(f"Number of moves: {len(solution.split())}")
    print(f"Solve time: {solve_time:.4f} seconds")

    # Apply solution to verify
    solved_state = apply_moves_4x4(scramble, solution)
    print(f"Verification: {verify_4x4(solved_state)}")

    print("\nSolved 4x4 cube:\n")
    print(pretty_print_4x4(solved_state))

    # Optional step-by-step display
    if args.show_steps:
        print("\n" + "="*50)
        print("STEP-BY-STEP SOLUTION")
        print("="*50)
        show_4x4_steps_console(scramble, solution)

if __name__ == "__main__":
    main()