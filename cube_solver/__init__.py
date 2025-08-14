"""cube_solver – Pure-Python engine powering the *Dual-Coordinate Pivot* (DCP)
solver used by *CubeSolver-X*.

"""

from .search import Search
from .tools import verify  # basic structural checker

__all__ = ["solve", "verify"]


def solve(facelets: str, max_depth: int = 24, timeOut: int = 1000) -> str:
    """Solve a scramble given as 54-character facelet string.

    The string must list the cube stickers in the canonical URF... order.
    Return value is a space-separated sequence of face turns.  Raises
    ValueError if the cube is invalid or the depth bound is exceeded.
    
    Args:
        facelets: 54-character cube state string
        max_depth: Maximum number of moves to attempt  
        timeOut: Time limit in milliseconds
    """
    # quick structural validation
    err = verify(facelets)
    if err != 0:
        raise ValueError(f"Cube definition invalid, verify() error code {err}")

    # Use enhanced search with optimizations
    search_instance = Search()
    result = search_instance.solution(facelets, max_depth, timeOut, False).strip()
    if result.startswith("Error"):
        raise ValueError(result)
    return result
