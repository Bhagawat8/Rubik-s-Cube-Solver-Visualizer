
from __future__ import annotations

from .bitcube import BitPackedCubieCube
from .cubiecube import moveCube  # 6 basic quarter-turn CubieCubes
from .search import Search
ax_to_s = Search.ax_to_s
po_to_s = Search.po_to_s

from .coordcube import CoordCube

__all__ = ["MOVE_DELTA", "fast_cnk", "fast_factorial", "optimized_coordinate_calc"]

MOVE_DELTA: list[BitPackedCubieCube] = []  # len == 18

# Pre-computed binomial coefficients for faster Cnk calculations
_CNK_TABLE = {}

def _precompute_cnk(max_n=12):
    """Pre-compute all binomial coefficients C(n,k) up to max_n for O(1) lookup"""
    global _CNK_TABLE
    for n in range(max_n + 1):
        _CNK_TABLE[n] = {}
        for k in range(n + 1):
            if k == 0 or k == n:
                _CNK_TABLE[n][k] = 1
            elif k > n // 2:
                _CNK_TABLE[n][k] = _CNK_TABLE[n][n - k]
            else:
                result = 1
                for i in range(k):
                    result = result * (n - i) // (i + 1)
                _CNK_TABLE[n][k] = result

def fast_cnk(n, k):
    """O(1) binomial coefficient lookup - much faster than computing each time"""
    if k > n or k < 0:
        return 0
    return _CNK_TABLE.get(n, {}).get(k, 0)

# Pre-computed factorial table for permutation calculations
_FACTORIAL = [1, 1, 2, 6, 24, 120, 720, 5040, 40320, 362880, 3628800, 39916800, 479001600]

def fast_factorial(n):
    """O(1) factorial lookup for n <= 12"""
    return _FACTORIAL[n] if n < len(_FACTORIAL) else None

# Optimized coordinate calculation using bit manipulation
def optimized_coordinate_calc(flip_coord, twist_coord, slice_coord):
    """Optimized coordinate calculation using bit operations"""
    # Use bit shifting instead of multiplication where possible
    return (flip_coord << 10) + (twist_coord << 5) + slice_coord

# Pre-compute CNK table on module load
_precompute_cnk(12)

for axis in range(6):
    # quarter-turn (90° clockwise)
    cc90 = moveCube[axis]

    # half-turn – create a copy so original isn't modified
    cc180 = cc90.__class__(cp=cc90.cp.copy(), co=cc90.co.copy(),
                           ep=cc90.ep.copy(), eo=cc90.eo.copy())
    cc180.multiply(cc90)

    # three-quarter turn (270° CW == -90°)
    cc270 = cc180.__class__(cp=cc180.cp.copy(), co=cc180.co.copy(),
                            ep=cc180.ep.copy(), eo=cc180.eo.copy())
    cc270.multiply(cc90)

    for c in (cc90, cc180, cc270):
        MOVE_DELTA.append(BitPackedCubieCube.from_cubiecube(c))

# Small pattern database for phase2 (up to depth 5)
PHASE2_PATTERN_DB = {}

def build_phase2_pattern_db():
    """Pre-compute short solutions for common phase2 states"""
    global PHASE2_PATTERN_DB
    # Use simple int hash for state: (urf << 18) | (frbr << 9) | (par << 8) | urdf
    def state_hash(urf, frbr, par, urdf):
        return (urf << 18) | (frbr << 9) | (par << 8) | urdf
    
    def apply_phase2_move(state, mv):
        urf = (state >> 18) & 0x3FFF  # adjust masks
        frbr = (state >> 9) & 0x1FF
        par = (state >> 8) & 1
        urdf = state & 0xFF
        new_urf = CoordCube.URFtoDLF_Move[urf][mv]
        new_frbr = CoordCube.FRtoBR_Move[frbr][mv]
        new_par = CoordCube.parityMove[par][mv]
        new_urdf = CoordCube.URtoDF_Move[urdf][mv]
        return state_hash(new_urf, new_frbr, new_par, new_urdf)
    
    # In build function, use state_hash(0,0,0,0) as start
    queue = [(state_hash(0,0,0,0), [])]
    max_depth = 4  # Limit pattern database depth
    visited = set()
    # Limit to 10000 entries
    while queue and len(PHASE2_PATTERN_DB) < 10000:
        state, moves = queue.pop(0)
        if len(moves) > max_depth:
            continue
        PHASE2_PATTERN_DB[state] = ' '.join(moves)
        
        for mv in [0,1,2,9,10,11,3,4,5,6,7,8,12,13,14,15,16,17]:  
            if mv % 3 == 0: continue  
            new_state = apply_phase2_move(state, mv)  
            if new_state not in visited:
                visited.add(new_state)
                queue.append((new_state, moves + [ax_to_s[mv//3] + po_to_s[(mv%3)+1]]))

# Call on module load
build_phase2_pattern_db()
