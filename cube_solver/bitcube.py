"""Bit-packed cube representation.
Stores an entire Rubik's-cube state in three small Python ``int`` s.
Layout (little-endian bits):
pc   : 16 bits  – corner permutation Lehmer code (0 … 8!-1  < 2¹⁶)
pe   : 29 bits  – edge   permutation Lehmer code (0 … 12!-1 < 2²⁹)
orie : 23 bits
    upper 11 bits – corner twist base-3 integer (3⁷ < 2¹¹)
    lower 12 bits – edge flips (one bit per edge)
Total = 68 bits  ≈ 12 bytes including Python object header.
"""
from __future__ import annotations

from typing import List

# factorial table for Lehmer code ↔ integer conversion
_factorial: List[int] = [1]
for i in range(1, 13):
    _factorial.append(_factorial[-1] * i)


def perm_to_int(p: List[int]) -> int:
    """Permutation → Lehmer-code integer rank."""
    n = len(p)
    code = 0
    used = [False] * n
    for i in range(n):
        smaller = sum(1 for x in range(p[i]) if not used[x])
        code += smaller * _factorial[n - 1 - i]
        used[p[i]] = True
    return code


def int_to_perm(code: int, n: int) -> List[int]:
    """Lehmer-code integer → permutation list."""
    elems = list(range(n))
    perm: List[int] = []
    for i in range(n - 1, -1, -1):
        fact = _factorial[i]
        idx, code = divmod(code, fact)
        perm.append(elems.pop(idx))
    perm.reverse()
    return perm

class BitPackedCubieCube:
    """Compact cubie-level cube using three integers."""

    __slots__ = ("pc", "pe", "orie")

    #  construction
    def __init__(self, pc: int = 0, pe: int = 0, orie: int = 0):
        self.pc = pc  # corner permutation code  (<= 40319)
        self.pe = pe  # edge   permutation code  (<= 479001599)
        self.orie = orie  # 23-bit orientation field

    # conversion helpers
    @staticmethod
    def from_cubiecube(cc: "CubieCube") -> "BitPackedCubieCube":  # type: ignore
        """Pack existing *CubieCube* into compact form."""
        from .edge import edge_values
        pc = perm_to_int(cc.cp)
        pe = perm_to_int(cc.ep)
        # corners – base-3 integer of the first 7 twists
        coro = 0
        for i in range(7):
            coro = coro * 3 + cc.co[i]
        # edges – 12 bits (bit 0 = edge 11)
        eoro = 0
        for idx in reversed(edge_values):
            eoro = (eoro << 1) | (cc.eo[idx] & 1)
        orie = (coro << 12) | eoro
        return BitPackedCubieCube(pc, pe, orie)

    
    def to_cubiecube(self) -> "CubieCube":  # type: ignore
        """Decode into classic *CubieCube* (for compatibility)."""
        # delayed import to avoid cycles
        from .cubiecube import CubieCube
        from .edge import edge_values
        cp = int_to_perm(self.pc, 8)
        ep = int_to_perm(self.pe, 12)
        eoro = self.orie & 0xFFF
        coro = self.orie >> 12
        # edge flips list (edge0 is UR) – reverse of packing
        eo = [(eoro >> i) & 1 for i in range(12)][::-1]
        co = [0] * 8
        tmp = coro
        for i in range(6, -1, -1):
            tmp, rem = divmod(tmp, 3)
            co[i] = rem
        co[7] = (-sum(co) % 3)
        return CubieCube(cp=cp, co=co, ep=ep, eo=eo)


    # orientation decoding/encoding helpers (private)

    def _decode_orientations(self):
        """Return (co list[8], eo list[12])."""
        eoro = self.orie & 0xFFF
        coro = self.orie >> 12
        eo = [(eoro >> i) & 1 for i in range(12)][::-1]
        co = [0] * 8
        tmp = coro
        for i in range(6, -1, -1):
            tmp, rem = divmod(tmp, 3)
            co[i] = rem
        co[7] = (-sum(co) % 3)
        return co, eo

    @staticmethod
    def _encode_orientations(co: List[int], eo: List[int]) -> int:
        coro = 0
        for i in range(7):
            coro = coro * 3 + co[i]
        eoro = 0
        for bit in reversed(eo):
            eoro = (eoro << 1) | (bit & 1)
        return (coro << 12) | eoro


    def multiply_fallback(self, move_cc: "CubieCube") -> None:  # type: ignore
        """Slow but simple multiply via classic class (reference impl)."""
        cc = self.to_cubiecube()
        cc.multiply(move_cc)
        packed = BitPackedCubieCube.from_cubiecube(cc)
        self.pc, self.pe, self.orie = packed.pc, packed.pe, packed.orie


    # fast native multiply using pre-packed move deltas

    def multiply_native(self, axis: int, power: int = 1) -> None:
        from .bit_tables import MOVE_DELTA  # local import to avoid cycles
        from .edge import edge_values
        from .corner import corner_values
        delta = MOVE_DELTA[axis * 3 + (power % 3) - 1]
        # Permutation composition in array form
        perm_c = int_to_perm(self.pc, 8)
        perm_e = int_to_perm(self.pe, 12)
        d_perm_c = int_to_perm(delta.pc, 8)
        d_perm_e = int_to_perm(delta.pe, 12)
        new_perm_c = [perm_c[d_perm_c[i]] for i in range(8)]
        new_perm_e = [perm_e[d_perm_e[i]] for i in range(12)]
        new_pc = perm_to_int(new_perm_c)
        new_pe = perm_to_int(new_perm_e)
        # Orientations
        co, eo = self._decode_orientations()
        d_co, d_eo = delta._decode_orientations()
        new_co = [0] * 8
        for i in range(8):
            new_co[i] = (d_co[i] + co[d_perm_c[i]]) % 3
        new_co[7] = (-sum(new_co[0:7]) % 3)
        new_eo = [0] * 12
        for i in range(12):
            new_eo[i] = (d_eo[i] ^ eo[d_perm_e[i]])  # mod2 via XOR
        new_orie = BitPackedCubieCube._encode_orientations(new_co, new_eo)
        self.pc, self.pe, self.orie = new_pc, new_pe, new_orie

    def __repr__(self): 
        return (
            f"<BitPackedCubieCube pc={self.pc} pe={self.pe} "
            f"orie=0x{self.orie:X}>"
        )
