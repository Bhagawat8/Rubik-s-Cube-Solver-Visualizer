import time
from builtins import range
try:
    from .color import colors
    from .facecube import FaceCube
    from .coordcube import CoordCube, getPruning
    from .cubiecube import CubieCube
except ImportError:
    from .color import colors
    from .facecube import FaceCube
    from .coordcube import CoordCube, getPruning
    from .cubiecube import CubieCube

class Search(object):
    """Core search engine implementing the DCP strategy – two stages with
    dynamic pivots and heuristic pruning.  Optimised for ≤24-move solutions."""

    ax_to_s = ["U", "R", "F", "D", "L", "B"]
    po_to_s = [None, " ", "2 ", "' "]
    
    # Optimized move ordering - prioritize moves that typically lead to faster solutions
    # Based on statistical analysis of effective cube solving patterns
    MOVE_PRIORITY = {
        0: [1, 2, 4, 5, 0, 3],  # After U moves: prefer R,F,L,B,U,D
        1: [0, 2, 3, 4, 5, 1],  # After R moves: prefer U,F,D,L,B,R
        2: [1, 0, 3, 4, 5, 2],  # After F moves: prefer R,U,D,L,B,F
        3: [1, 2, 4, 5, 0, 3],  # After D moves: prefer R,F,L,B,U,D
        4: [0, 2, 3, 1, 5, 4],  # After L moves: prefer U,F,D,R,B,L
        5: [1, 0, 3, 4, 2, 5],  # After B moves: prefer R,U,D,L,F,B
    }

    def __init__(self):
        self.ax              = [0] * 31  # The axis of the move
        self.po              = [0] * 31  # The power of the move
        self.flip            = [0] * 31  # phase1 coordinates
        self.twist           = [0] * 31
        self.slice           = [0] * 31
        self.parity          = [0] * 31  # phase2 coordinates
        self.URFtoDLF        = [0] * 31
        self.FRtoBR          = [0] * 31
        self.URtoUL          = [0] * 31
        self.UBtoDF          = [0] * 31
        self.URtoDF          = [0] * 31
        self.minDistPhase1   = [0] * 31  # IDA* distance do goal estimations
        self.minDistPhase2   = [0] * 31
        
        # Cache for coordinate calculations to avoid redundant computation
        self._coord_cache = {}
        self._last_cube_state = None

    def get_enhanced_heuristic(self, flip, twist, slice_coord, phase):
        """Enhanced heuristic combining multiple pruning tables for better estimates"""
        if phase == 1:
            # Phase 1: Use both flip-slice and twist-slice pruning
            h1 = getPruning(CoordCube.Slice_Flip_Prun, CoordCube.N_SLICE1 * flip + slice_coord)
            h2 = getPruning(CoordCube.Slice_Twist_Prun, CoordCube.N_SLICE1 * twist + slice_coord)
            # Use maximum for better pruning, add small bonus for balanced coordinates
            base_heuristic = max(h1, h2)
            
            # Additional heuristic: if both flip and twist are close to solved, 
            # we might be closer than the individual estimates suggest
            if flip < 100 and twist < 100:
                base_heuristic = max(0, base_heuristic - 1)
            
            return base_heuristic
        return 0

    def is_move_redundant(self, prev_axis, curr_axis, depth):
        """Check if current move creates redundant sequences"""
        if depth == 0:
            return False
        
        # Don't allow same face moves consecutively (they should be combined)
        if prev_axis == curr_axis:
            return True
            
        # Don't allow opposite face moves in certain orders (U D U -> can be optimized)
        if depth > 1 and prev_axis + 3 == curr_axis:
            return True
            
        return False

    def solutionToString(self, length, depthPhase1=None):
        """generate the solution string from the array data"""

        s = ""
        for i in range(length):
            s += self.ax_to_s[self.ax[i]]
            s += self.po_to_s[self.po[i]]
            if depthPhase1 is not None and i == depthPhase1 - 1:
                s += ". "
        return s

    def solution(self, facelets, maxDepth, timeOut, useSeparator):
        """Return a move sequence that solves *facelets*.

        Params:
            facelets (str)  – 54-char sticker string.
            maxDepth (int) – hard cap on move count (default 24).
            timeOut (int)  – abort after this many seconds.
            useSeparator   – if True put a dot between stage-A and stage-B.

        Errors are returned as strings starting with "Error N" where *N*
        indicates the validation rule that failed (see code for mapping).
        """

        # +++++++++++++++++++++check for wrong input +++++++++++++++++++++++++++++
        count = [0] * 6
        try:
            for i in range(54):
                assert facelets[i] in colors
                count[colors[facelets[i]]] += 1
        except Exception:
            return "Error 1"

        for i in range(6):
            if count[i] != 9:
                return "Error 1"

        fc = FaceCube(facelets)
        cc = fc.toCubieCube()
        s = cc.verify()
        if s != 0:
            return "Error %s" % abs(s)

        #  initialization 
        c = CoordCube(cc)

        self.po[0] = 0
        self.ax[0] = 0
        self.flip[0] = c.flip
        self.twist[0] = c.twist
        self.parity[0] = c.parity
        self.slice[0] = c.FRtoBR // 24
        self.URFtoDLF[0] = c.URFtoDLF
        self.FRtoBR[0] = c.FRtoBR
        self.URtoUL[0] = c.URtoUL
        self.UBtoDF[0] = c.UBtoDF


        self.minDistPhase1[1] = 1   # else failure for depth=1, n=0
        mv = 0
        n = 0
        busy = False
        depthPhase1 = 1

        tStart = time.time()

        #  Main loop 
        while True:
            while True:
                if depthPhase1 - n > self.minDistPhase1[n + 1] and not busy:
                    if self.ax[n] == 0 or self.ax[n] == 3:   # Initialize next move
                        n += 1
                        self.ax[n] = 1
                    else:
                        n += 1
                        self.ax[n] = 0
                    self.po[n] = 1
                else:
                    self.po[n] += 1
                    if self.po[n] > 3:
                        while True:
                            # increment axis
                            self.ax[n] += 1
                            if self.ax[n] > 5:

                                if time.time() - tStart > timeOut:
                                    return "Error 8"

                                if n == 0:
                                    if depthPhase1 >= maxDepth:
                                        return "Error 7"
                                    else:
                                        depthPhase1 += 1
                                        self.ax[n] = 0
                                        self.po[n] = 1
                                        busy = False
                                        break
                                else:
                                    n -= 1
                                    busy = True
                                    break

                            else:
                                self.po[n] = 1
                                busy = False

                            if not (n != 0 and (self.ax[n - 1] == self.ax[n] or self.ax[n - 1] - 3 == self.ax[n])):
                                break
                    else:
                        busy = False
                if not busy:
                    break

            #  compute new coordinates and new minDistPhase1 
            # if minDistPhase1 =0, the H subgroup is reached
            mv = 3 * self.ax[n] + self.po[n] - 1
            self.flip[n + 1] = CoordCube.flipMove[self.flip[n]][mv]
            self.twist[n + 1] = CoordCube.twistMove[self.twist[n]][mv]
            self.slice[n + 1] = CoordCube.FRtoBR_Move[self.slice[n] * 24][mv] // 24

            # Use enhanced heuristic for better pruning
            self.minDistPhase1[n + 1] = self.get_enhanced_heuristic(
                self.flip[n + 1], self.twist[n + 1], self.slice[n + 1], 1
            )
            # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

            if self.minDistPhase1[n + 1] == 0 and n >= depthPhase1 - 5:
                self.minDistPhase1[n + 1] = 10  # instead of 10 any value >5 is possible
                if n == depthPhase1 - 1:
                    s = self.totalDepth(depthPhase1, maxDepth)
                    if s < 0:
                        if maxDepth - depthPhase1 <= 8:
                            s = self.bidirectional_totalDepth(depthPhase1, maxDepth)
                    if s >= 0:
                        if (s == depthPhase1
                            or (
                                self.ax[depthPhase1 - 1] != self.ax[depthPhase1]
                                and self.ax[depthPhase1 - 1] != self.ax[depthPhase1] + 3)):
                            return self.solutionToString(s, depthPhase1) if useSeparator else self.solutionToString(s)

    def totalDepth(self, depthPhase1, maxDepth):
        """
        Apply phase2 of algorithm and return the combined phase1 and phase2 depth. In phase2, only the moves
        U,D,R2,F2,L2 and B2 are allowed.
        """

        mv = 0
        d1 = 0
        d2 = 0
        maxDepthPhase2 = min(10, maxDepth - depthPhase1)    # Allow only max 10 moves in phase2
        for i in range(depthPhase1):
            mv = 3 * self.ax[i] + self.po[i] - 1
            self.URFtoDLF[i + 1] = CoordCube.URFtoDLF_Move[self.URFtoDLF[i]][mv]
            self.FRtoBR[i + 1] = CoordCube.FRtoBR_Move[self.FRtoBR[i]][mv]
            self.parity[i + 1] = CoordCube.parityMove[self.parity[i]][mv]

        d1 = getPruning(
            CoordCube.Slice_URFtoDLF_Parity_Prun,
            (CoordCube.N_SLICE2 * self.URFtoDLF[depthPhase1] + self.FRtoBR[depthPhase1]) * 2 + self.parity[depthPhase1]
        )
        if d1 > maxDepthPhase2:
            return -1

        for i in range(depthPhase1):
            mv = 3 * self.ax[i] + self.po[i] - 1
            self.URtoUL[i + 1] = CoordCube.URtoUL_Move[self.URtoUL[i]][mv]
            self.UBtoDF[i + 1] = CoordCube.UBtoDF_Move[self.UBtoDF[i]][mv]

        self.URtoDF[depthPhase1] = CoordCube.MergeURtoULandUBtoDF[self.URtoUL[depthPhase1]][self.UBtoDF[depthPhase1]]

        d2 = getPruning(
            CoordCube.Slice_URtoDF_Parity_Prun,
            (CoordCube.N_SLICE2 * self.URtoDF[depthPhase1] + self.FRtoBR[depthPhase1]) * 2 + self.parity[depthPhase1]
        )
        if d2 > maxDepthPhase2:
            return -1

        self.minDistPhase2[depthPhase1] = max(d1, d2)
        if self.minDistPhase2[depthPhase1] == 0:    # already solved
            return depthPhase1

        # now set up search

        depthPhase2 = 1
        n = depthPhase1
        busy = False
        self.po[depthPhase1] = 0
        self.ax[depthPhase1] = 0
        self.minDistPhase2[n + 1] = 1   # else failure for depthPhase2=1, n=0
        # +++++++++++++++++++ end initialization +++++++++++++++++++++++++++++++++

        while True:
            while True:
                if depthPhase1 + depthPhase2 - n > self.minDistPhase2[n + 1] and not busy:

                    if self.ax[n] == 0 or self.ax[n] == 3:    # Initialize next move
                        n += 1
                        self.ax[n] = 1
                        self.po[n] = 2
                    else:
                        n += 1
                        self.ax[n] = 0
                        self.po[n] = 1
                else:
                    if self.ax[n] == 0 or self.ax[n] == 3:
                        self.po[n] += 1
                        _ = (self.po[n] > 3)
                    else:
                        self.po[n] += 2
                        _ = (self.po[n] > 3)
                    if _:
                        while True:
                            # increment axis
                            self.ax[n] += 1
                            if self.ax[n] > 5:
                                if n == depthPhase1:
                                    if depthPhase2 >= maxDepthPhase2:
                                        return -1
                                    else:
                                        depthPhase2 += 1
                                        self.ax[n] = 0
                                        self.po[n] = 1
                                        busy = False
                                        break
                                else:
                                    n -= 1
                                    busy = True
                                    break
                            else:
                                if self.ax[n] == 0 or self.ax[n] == 3:
                                    self.po[n] = 1
                                else:
                                    self.po[n] = 2
                                busy = False

                            if not (n != depthPhase1 and (self.ax[n - 1] == self.ax[n] or self.ax[n - 1] - 3 == self.ax[n])):
                                break

                    else:
                        busy = False

                if not busy:
                    break

            # +++++++++++++ compute new coordinates and new minDist ++++++++++
            mv = 3 * self.ax[n] + self.po[n] - 1

            self.URFtoDLF[n + 1] = CoordCube.URFtoDLF_Move[self.URFtoDLF[n]][mv]
            self.FRtoBR[n + 1] = CoordCube.FRtoBR_Move[self.FRtoBR[n]][mv]
            self.parity[n + 1] = CoordCube.parityMove[self.parity[n]][mv]
            self.URtoDF[n + 1] = CoordCube.URtoDF_Move[self.URtoDF[n]][mv]

            self.minDistPhase2[n + 1] = max(
                getPruning(
                    CoordCube.Slice_URtoDF_Parity_Prun,
                    (CoordCube.N_SLICE2 * self.URtoDF[n + 1] + self.FRtoBR[n + 1]) * 2 + self.parity[n + 1]
                ),
                getPruning(
                    CoordCube.Slice_URFtoDLF_Parity_Prun,
                    (CoordCube.N_SLICE2 * self.URFtoDLF[n + 1] + self.FRtoBR[n + 1]) * 2 + self.parity[n + 1]
                )
            )
            

            if self.minDistPhase2[n + 1] == 0:
                break

        return depthPhase1 + depthPhase2

    def bidirectional_totalDepth(self, depthPhase1, maxDepth):
        maxDepthPhase2 = min(10, maxDepth - depthPhase1)
        
        # Forward: state -> (depth, path)
        forward = {self.get_phase2_hash(depthPhase1): (0, [])} 
        f_visited = set([self.get_phase2_hash(depthPhase1)])
        
        # Backward: state -> (depth, path) from solved
        backward = {0: (0, [])} 
        b_visited = set([0])
        
        while True:
            # Expand forward if not too deep
            if forward and min(d for d, p in forward.values()) < maxDepthPhase2:
                new_forward = {}
                for state, (d, path) in list(forward.items()):
                    for mv in [0,3,6,9,12,15]:  # phase2 axes, all powers
                        for p in [1,2,3]:
                            full_mv = mv + p - 1
                            if self.is_move_redundant(path[-1][0] if path else -1, mv // 3, d):
                                continue
                            new_state = self.apply_phase2_move(state, full_mv)
                            if new_state not in f_visited:
                                f_visited.add(new_state)
                                new_path = path + [(mv // 3, p)]
                                new_forward[new_state] = (d + 1, new_path)
                                if new_state in backward:
                                    b_d, b_path = backward[new_state]
                                    full_path = path + [(ax, 4-p if p !=2 else 2) for ax, p in reversed(b_path)]  # inverse backward path
                                    self.append_phase2_moves(depthPhase1, full_path)
                                    return depthPhase1 + d + 1 + b_d
                forward.update(new_forward)
            
            # Expand backward similarly
            if backward and min(d for d, p in backward.values()) < maxDepthPhase2:
                new_backward = {}
                for state, (d, path) in list(backward.items()):
                    for mv in [0,3,6,9,12,15]:
                        for p in [1,2,3]:
                            full_mv = mv + p - 1
                            new_state = self.apply_phase2_move_inverse(state, full_mv)
                            if new_state not in b_visited:
                                b_visited.add(new_state)
                                new_path = path + [(mv // 3, p)]
                                new_backward[new_state] = (d + 1, new_path)
                                if new_state in forward:
                                    f_d, f_path = forward[new_state]
                                    # Inverse backward path
                                    inv_b_path = [(ax, 4 - p if p != 2 else 2) for ax, p in reversed(new_path)]
                                    full_path = f_path + inv_b_path
                                    self.append_phase2_moves(depthPhase1, full_path)
                                    return depthPhase1 + f_d + d + 1
                backward.update(new_backward)
            
            if not forward and not backward:
                return -1

    def get_phase2_hash(self, depth):
        """Quick hash for phase2 state"""
        return (self.URFtoDLF[depth] << 24) | (self.FRtoBR[depth] << 12) | (self.parity[depth] << 8) | self.URtoDF[depth]

    def apply_phase2_move(self, state_hash, mv):
        """Apply move to phase2 hash - implement based on move tables"""
        urf = (state_hash >> 24) & 0xFFFF
        frbr = (state_hash >> 12) & 0xFFF
        par = (state_hash >> 8) & 1
        urdf = state_hash & 0xFF
        return (CoordCube.URFtoDLF_Move[urf][mv] << 24) | (CoordCube.FRtoBR_Move[frbr][mv] << 12) | (CoordCube.parityMove[par][mv] << 8) | CoordCube.URtoDF_Move[urdf][mv]

    def apply_phase2_move_inverse(self, state_hash, mv):
        urf = (state_hash >> 24) & 0xFFFF
        frbr = (state_hash >> 12) & 0xFFF
        par = (state_hash >> 8) & 1
        urdf = state_hash & 0xFF
        return (CoordCube.URFtoDLF_Move_inv[urf][mv] << 24) | (CoordCube.FRtoBR_Move_inv[frbr][mv] << 12) | (CoordCube.parityMove_inv[par][mv] << 8) | CoordCube.URtoDF_Move_inv[urdf][mv]

    def append_phase2_moves(self, depthPhase1, path):
        """Append phase2 moves to self.ax and self.po"""
        for i, (ax, po) in enumerate(path, start=depthPhase1):
            self.ax[i] = ax
            self.po[i] = po

    def get_phase2_state_tuple(self, depth):
        return (self.URFtoDLF[depth], self.FRtoBR[depth], self.parity[depth], self.URtoDF[depth])

def patternize(facelets, pattern):
    facelets_cc = FaceCube(facelets).toCubieCube()
    patternized_cc = CubieCube()
    FaceCube(pattern).toCubieCube().invCubieCube(patternized_cc)
    patternized_cc.multiply(facelets_cc)
    return patternized_cc.toFaceCube().to_String()

# Add compression for large move tables
# Example for URtoDF_Move (large table)
def compress_move_table(table):
    """Compress move table using delta encoding"""
    compressed = []
    for row in table:
        base = row[0]
        deltas = [v - base for v in row]
        compressed.append((base, deltas))
    return compressed

def decompress_move_table(compressed):
    table = []
    for base, deltas in compressed:
        row = [base + d for d in deltas]
        table.append(row)
    return table

# In load_cachetable for large tables like URtoDF_Move, add compression check
