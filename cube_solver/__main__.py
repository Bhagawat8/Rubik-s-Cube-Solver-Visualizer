import sys
from . import solve

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m cube_solver <54-char facelet string>")
        sys.exit(1)
    facelets = "".join(sys.argv[1:]).strip()
    print(solve(facelets)) 