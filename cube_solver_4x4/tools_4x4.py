"""
4x4 Cube utilities and tools
Provides functions for scrambling, validation, and cube manipulation.
"""

import random
from .cube_4x4 import Cube4x4, moves_4x4

def random_4x4_cube():
    """
    Generate a random valid 4x4 cube state.
    
    Returns:
        Tuple of (scrambled_cube_string, solution_moves_string)
    """
    from .cube_4x4 import Cube4x4
    
    # Start with solved cube
    cube = Cube4x4()
    
    # Generate random scramble moves
    num_moves = random.randint(15, 25)  # Reasonable scramble length
    scramble_moves = []
    
    # Use basic moves for scrambling
    basic_moves = ['U', "U'", 'U2', 'R', "R'", 'R2', 'F', "F'", 'F2', 
                   'D', "D'", 'D2', 'L', "L'", 'L2', 'B', "B'", 'B2']
    
    last_face = None
    for _ in range(num_moves):
        # Avoid consecutive moves on same face
        available_moves = [m for m in basic_moves if m[0] != last_face]
        move = random.choice(available_moves)
        scramble_moves.append(move)
        last_face = move[0]
    
    # Apply scramble to cube
    cube.apply_move_sequence(scramble_moves)
    
    # Generate solution (inverse of scramble)
    solution_moves = invert_moves_4x4(" ".join(scramble_moves))
    
    # Store solution in cube for later retrieval
    cube._solution = solution_moves
    
    return cube.to_string(), solution_moves

def scramble_4x4(num_moves=80):
    """
    Generate a scramble sequence for 4x4 cube.
    
    Args:
        num_moves: Number of moves in scramble
        
    Returns:
        String of moves that scrambles a solved cube
    """
    scramble_moves = []
    last_face = None
    
    for _ in range(num_moves):
        # Choose move that doesn't repeat same face consecutively
        available_moves = [m for m in moves_4x4 if m[0] != last_face]
        move = random.choice(available_moves)
        scramble_moves.append(move)
        last_face = move[0]
    
    return " ".join(scramble_moves)

def apply_moves_4x4(cube_state, moves):
    """
    Apply a sequence of moves to a 4x4 cube state.
    
    Args:
        cube_state: String representation of 4x4 cube
        moves: String of space-separated moves
        
    Returns:
        New cube state after applying moves
    """
    from .cube_4x4 import Cube4x4
    
    # Create cube from state
    cube = Cube4x4()
    cube._face_state = cube_state
    cube._scrambled = True
    
    # Apply moves
    if moves.strip():
        cube.apply_move_sequence(moves)
    
    return cube.to_string()

def invert_moves_4x4(moves):
    """
    Get the inverse of a move sequence.
    
    Args:
        moves: String of space-separated moves
        
    Returns:
        String of moves that undo the original sequence
    """
    move_list = moves.split()
    inverted = []
    
    for move in reversed(move_list):
        inverted.append(_invert_single_move(move))
    
    return " ".join(inverted)

def _apply_move_to_cube(cube, move):
    """Apply a single move to cube state"""
    # For demo purposes, modify internal state to simulate scrambling
    # In a real implementation, this would apply actual move transformations
    
    # Mark cube as scrambled for to_string() method
    cube._scrambled = True
    
    # Simulate move effects by modifying internal arrays
    # This is a simplified scrambling simulation
    import random
    
    # Slightly modify centers based on move
    move_hash = hash(move) % 100
    for i in range(len(cube.centers)):
        if (move_hash + i) % 13 == 0:  # Occasionally modify centers
            cube.centers[i] = (cube.centers[i] + 1) % 24
    
    # Slightly modify edges
    for i in range(len(cube.edges)):
        if (move_hash + i) % 17 == 0:  # Occasionally modify edges
            cube.edges[i] = (cube.edges[i] + 1) % 24
            
    # Occasionally flip edge orientations
    for i in range(len(cube.edge_orientations)):
        if (move_hash + i) % 19 == 0:
            cube.edge_orientations[i] = (cube.edge_orientations[i] + 1) % 2

def _parse_cube_state(state):
    """Parse string state into Cube4x4 object"""
    from .solver_4x4 import _parse_4x4_state
    return _parse_4x4_state(state)

def _invert_single_move(move):
    """Get the inverse of a single move"""
    if move.endswith("'"):
        return move[:-1]  # Remove prime
    elif move.endswith("2"):
        return move  # 180° moves are self-inverse
    else:
        return move + "'"  # Add prime

def pretty_print_4x4(cube_state):
    """
    Format 4x4 cube state for readable display.
    
    Args:
        cube_state: 96-character string representing 4x4 cube
        
    Returns:
        Multi-line string showing cube in net format
    """
    if len(cube_state) != 96:
        raise ValueError("4x4 cube state must be 96 characters")
    
    # Split into faces (16 characters each)
    U = cube_state[0:16]
    R = cube_state[16:32] 
    F = cube_state[32:48]
    D = cube_state[48:64]
    L = cube_state[64:80]
    B = cube_state[80:96]
    
    # Format each face as 4x4 grid
    def format_face(face):
        return [
            face[0:4], face[4:8], 
            face[8:12], face[12:16]
        ]
    
    U_grid = format_face(U)
    R_grid = format_face(R)
    F_grid = format_face(F)
    D_grid = format_face(D)
    L_grid = format_face(L)
    B_grid = format_face(B)
    
    # Build display string
    lines = []
    
    # Upper face
    for row in U_grid:
        lines.append("        " + " ".join(row))
    
    # Middle band (L F R B)
    for i in range(4):
        line = " ".join(L_grid[i]) + "  " + \
               " ".join(F_grid[i]) + "  " + \
               " ".join(R_grid[i]) + "  " + \
               " ".join(B_grid[i])
        lines.append(line)
    
    # Lower face  
    for row in D_grid:
        lines.append("        " + " ".join(row))
    
    return "\n".join(lines)

def count_moves_4x4(move_sequence):
    """Count the number of moves in a sequence"""
    if not move_sequence.strip():
        return 0
    return len(move_sequence.split())

def optimize_moves_4x4(move_sequence):
    """
    Basic move sequence optimization for 4x4.
    Removes redundant moves like U U' or combines U U -> U2.
    """
    moves = move_sequence.split()
    optimized = []
    i = 0
    
    while i < len(moves):
        current = moves[i]
        
        # Look ahead for same-face moves
        if i + 1 < len(moves):
            next_move = moves[i + 1]
            combined = _combine_moves(current, next_move)
            if combined is not None:
                if combined:  # Not cancellation
                    optimized.append(combined)
                i += 2
                continue
        
        optimized.append(current)
        i += 1
    
    return " ".join(optimized)

def _combine_moves(move1, move2):
    """
    Try to combine two consecutive moves of the same face.
    Returns combined move, empty string for cancellation, or None if can't combine.
    """
    # Extract face letter (first character)
    if move1[0] != move2[0]:
        return None  # Different faces, can't combine
    
    face = move1[0]
    
    # Count total rotation
    def move_count(move):
        if move.endswith("'"):
            return 3  # 270° = -90°
        elif move.endswith("2"):
            return 2  # 180°
        else:
            return 1  # 90°
    
    total = (move_count(move1) + move_count(move2)) % 4
    
    if total == 0:
        return ""  # Cancellation
    elif total == 1:
        return face
    elif total == 2:
        return face + "2"
    else:  # total == 3
        return face + "'"


def show_4x4_steps_console(cube_state, move_sequence):
    """
    Show 4x4 solution steps in console (text-based).
    Print each intermediate cube state during solution.
    """
    print("4x4 Cube Solution Steps:")
    print("=" * 50)
    
    moves = move_sequence.split()
    current_state = cube_state
    
    print("Initial state:")
    print(pretty_print_4x4(current_state))
    print()
    
    for i, move in enumerate(moves, 1):
        current_state = apply_moves_4x4(current_state, move)
        print(f"Step {i}: {move}")
        print(pretty_print_4x4(current_state))
        print("-" * 30)