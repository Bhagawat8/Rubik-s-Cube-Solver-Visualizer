import argparse
import time
from cube_solver import solve, verify
from cube_solver.tools import randomCube
from cube_solver.facecube import FaceCube
from cube_solver.cubiecube import CubieCube, moveCube
from cube_solver.visualize import (
    states_from_moves,
    show_intermediate_states,
    visualize_2d,
    visualize_3d,
)

# map single-letter move to index 0..5
move_axis = {"U": 0, "R": 1, "F": 2, "D": 3, "L": 4, "B": 5}


def apply_moves(facelets: str, moves: str) -> str:
    """Return facelet string obtained by applying moves to facelets."""
    cc = FaceCube(facelets).toCubieCube()
    for token in moves.split():
        axis = move_axis[token[0]]
        power = 1  # default 90° clockwise
        if len(token) == 2 and token[1] == "2":
            power = 2
        elif len(token) == 2 and token[1] == "'":
            power = 3
        for _ in range(power):
            cc.multiply(moveCube[axis])
    return cc.toFaceCube().to_String()


def pretty(s: str) -> str:
    blk = lambda t: [t[0:3], t[3:6], t[6:9]]
    U, R, F, D, L, B = map(blk, (s[0:9], s[9:18], s[18:27],
                                  s[27:36], s[36:45], s[45:54]))
    out = []
    for r in U: out.append(" " * 7 + " ".join(r))
    for i in range(3):
        out.append(" ".join(L[i]) + "  " +
                   " ".join(F[i]) + "  " +
                   " ".join(R[i]) + "  " +
                   " ".join(B[i]))
    for r in D: out.append(" " * 7 + " ".join(r))
    return "\n".join(out)


def main():

    parser = argparse.ArgumentParser(
        description="Rubik cube solver with optional visualisation.",
    )
    parser.add_argument("--show-steps", action="store_true", help="Print each intermediate cube state")
    parser.add_argument("--visualize", action="store_true", help="Show 2-D net animation of the solution path")
    parser.add_argument("--visualize3d", action="store_true", help="Show 3-D cube animation of the solution path")
    parser.add_argument("--save-gif", metavar="PATH", help="Render 3-D animation to GIF at given path", default=None)
    parser.add_argument("--test", action="store_true", help="Benchmark average solving time over 10 random scrambles")
    args = parser.parse_args()

    # Benchmark mode – solve 10 random scrambles and report statistics.
    if args.test:
        samples = 10
        times = []
        for i in range(samples):
            scramble = randomCube()
            start_t = time.time()
            _ = solve(scramble)
            times.append(time.time() - start_t)
            print(f"Run {i+1:2d}/{samples}: {times[-1]:.4f}s")
        avg_time = sum(times) / samples
        best = min(times)
        worst = max(times)
        print("\nBenchmark summary ({} samples):".format(samples))
        print(f"  Average : {avg_time:.4f} s")
        print(f"  Fastest : {best:.4f} s")
        print(f"  Slowest : {worst:.4f} s")
        return

    scramble = randomCube()
    
    print("Your cube:\n")
    print(pretty(scramble))
    print("\nCalculating…")
    
    solve_start = time.time()
    solution = solve(scramble)
    solve_time = time.time() - solve_start
    
    print("Your solution :")
    print(solution)
    print("Number of moves:", len(solution.split()))
    print(f"Solve time: {solve_time:.4f} seconds")

    solved_facelets = apply_moves(scramble, solution)
    assert verify(solved_facelets) == 0  # cube is solved

    # produce list of intermediate states once so we can reuse for all options
    states = states_from_moves(scramble, solution)

    print("\nSolved cube:\n")
    print(pretty(solved_facelets))

    # optional visualisations
    if args.show_steps:
        show_intermediate_states(states)

    if args.visualize:
        visualize_2d(states)

    if args.visualize3d or args.save_gif:
        visualize_3d(states, gif_path=args.save_gif)







if __name__ == "__main__":
    main()