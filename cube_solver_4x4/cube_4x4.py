"""
4x4 Cube representation and basic operations.
A 4x4 cube has:
- 8 corners (same as 3x3)
- 24 edges (12 edge pairs, each pair can be permuted)  
- 24 centers (6 faces x 4 centers each, can move within face)
"""

# 4x4 Corner positions (same as 3x3)
URF = 0; UFL = 1; ULB = 2; UBR = 3
DFR = 4; DLF = 5; DBL = 6; DRB = 7

corner_names = ['URF', 'UFL', 'ULB', 'UBR', 'DFR', 'DLF', 'DBL', 'DRB']

# 4x4 Edge positions (24 edges = 12 pairs)
# Each edge in 4x4 consists of 2 pieces that must be paired together
edge_pairs = [
    'UR', 'UF', 'UL', 'UB',  # Upper layer edges
    'DR', 'DF', 'DL', 'DB',  # Lower layer edges  
    'FR', 'FL', 'BL', 'BR'   # Middle layer edges
]

# Center positions for each face (4 centers per face)
center_positions = {
    'U': ['U1', 'U2', 'U3', 'U4'],  # Up face centers
    'R': ['R1', 'R2', 'R3', 'R4'],  # Right face centers
    'F': ['F1', 'F2', 'F3', 'F4'],  # Front face centers
    'D': ['D1', 'D2', 'D3', 'D4'],  # Down face centers
    'L': ['L1', 'L2', 'L3', 'L4'],  # Left face centers
    'B': ['B1', 'B2', 'B3', 'B4']   # Back face centers
}

class Cube4x4:
    """
    Represents a 4x4 Rubik's cube state using arrays for:
    - corners: 8 corner pieces (same as 3x3)
    - corner_orientations: how each corner is twisted
    - edges: 24 edge pieces (12 pairs) 
    - edge_orientations: how each edge is flipped
    - centers: 24 center pieces (4 per face)
    """
    
    def __init__(self):
        # Corner representation (same as 3x3)
        self.corners = list(range(8))
        self.corner_orientations = [0] * 8
        
        # Edge representation (24 edges)
        self.edges = list(range(24))
        self.edge_orientations = [0] * 24
        
        # Center representation (24 centers)
        self.centers = list(range(24))
        
    def copy(self):
        """Create a deep copy of the cube state"""
        new_cube = Cube4x4()
        new_cube.corners = self.corners[:]
        new_cube.corner_orientations = self.corner_orientations[:]
        new_cube.edges = self.edges[:]
        new_cube.edge_orientations = self.edge_orientations[:]
        new_cube.centers = self.centers[:]
        return new_cube
        
    def is_solved(self):
        """Check if the cube is in solved state"""
        return (self.corners == list(range(8)) and 
                self.corner_orientations == [0] * 8 and
                self.edges == list(range(24)) and 
                self.edge_orientations == [0] * 24 and
                self.centers == list(range(24)))
    
    def to_string(self):
        """Convert cube state to string representation (96 facelets for 4x4)"""
        # Map internal state to actual cube representation
        if hasattr(self, '_face_state') and self._face_state:
            return self._face_state
        
        # For solved cube, return uniform faces
        face_colors = ['U', 'R', 'F', 'D', 'L', 'B']
        result = []
        
        # Each face has 16 stickers (4x4)
        for face_idx in range(6):
            face_color = face_colors[face_idx]
            result.extend([face_color] * 16)
        
        return ''.join(result)
    
    def apply_move_sequence(self, moves):
        """Apply a sequence of moves to this cube"""
        if isinstance(moves, str):
            moves = moves.split()
        
        for move in moves:
            self._apply_single_move(move)
    
    def _apply_single_move(self, move):
        """Apply a single move to the cube state"""
        # Store face state if not already stored
        if not hasattr(self, '_face_state'):
            self._face_state = self.to_string()
        
        # Convert face state to list for manipulation
        face_list = list(self._face_state)
        
        # Apply move transformation based on move type
        face_list = self._transform_face_state(face_list, move)
        
        # Store updated state
        self._face_state = ''.join(face_list)
        self._scrambled = True
    
    def _transform_face_state(self, face_list, move):
        """Transform face state based on move - simplified implementation"""
        # This is a simplified move transformation for demo purposes
        # In a real implementation, this would have proper 4x4 move definitions
        
        # Handle 2-layer moves (U2, R2, etc.)
        if move.endswith('2'):
            base_move = move[:-1]
            face_list = self._transform_face_state(face_list, base_move)
            face_list = self._transform_face_state(face_list, base_move)
            return face_list
        
        # Basic move transformations (simplified)
        if move == 'U':
            face_list = self._rotate_face_clockwise(face_list, 0)  # U face
        elif move == "U'":
            face_list = self._rotate_face_counterclockwise(face_list, 0)
        elif move == 'R':
            face_list = self._rotate_face_clockwise(face_list, 1)  # R face
        elif move == "R'":
            face_list = self._rotate_face_counterclockwise(face_list, 1)
        elif move == 'F':
            face_list = self._rotate_face_clockwise(face_list, 2)  # F face
        elif move == "F'":
            face_list = self._rotate_face_counterclockwise(face_list, 2)
        elif move == 'D':
            face_list = self._rotate_face_clockwise(face_list, 3)  # D face
        elif move == "D'":
            face_list = self._rotate_face_counterclockwise(face_list, 3)
        elif move == 'L':
            face_list = self._rotate_face_clockwise(face_list, 4)  # L face
        elif move == "L'":
            face_list = self._rotate_face_counterclockwise(face_list, 4)
        elif move == 'B':
            face_list = self._rotate_face_clockwise(face_list, 5)  # B face
        elif move == "B'":
            face_list = self._rotate_face_counterclockwise(face_list, 5)
        # Wide moves and other 4x4 specific moves can be added here
        
        return face_list
    
    def _rotate_face_clockwise(self, face_list, face_idx):
        """Rotate a face clockwise (simplified)"""
        start = face_idx * 16
        end = start + 16
        face = face_list[start:end]
        
        # Rotate 4x4 face clockwise
        rotated = [''] * 16
        for i in range(4):
            for j in range(4):
                old_pos = i * 4 + j
                new_pos = j * 4 + (3 - i)
                rotated[new_pos] = face[old_pos]
        
        face_list[start:end] = rotated
        return face_list
    
    def _rotate_face_counterclockwise(self, face_list, face_idx):
        """Rotate a face counterclockwise"""
        # Rotate clockwise 3 times = counterclockwise once
        for _ in range(3):
            face_list = self._rotate_face_clockwise(face_list, face_idx)
        return face_list

# Basic 4x4 moves (wide turns, inner slice moves, etc.)
moves_4x4 = [
    'U', "U'", 'U2', 'u', "u'", 'u2',  # Upper layer moves
    'R', "R'", 'R2', 'r', "r'", 'r2',  # Right layer moves  
    'F', "F'", 'F2', 'f', "f'", 'f2',  # Front layer moves
    'D', "D'", 'D2', 'd', "d'", 'd2',  # Down layer moves
    'L', "L'", 'L2', 'l', "l'", 'l2',  # Left layer moves
    'B', "B'", 'B2', 'b', "b'", 'b2',  # Back layer moves
    'x', "x'", 'x2', 'y', "y'", 'y2', 'z', "z'", 'z2',  # Rotations
    'Rw', "Rw'", 'Rw2', 'Lw', "Lw'", 'Lw2',  # Wide moves
    'Uw', "Uw'", 'Uw2', 'Dw', "Dw'", 'Dw2',
    'Fw', "Fw'", 'Fw2', 'Bw', "Bw'", 'Bw2'
]

def get_move_definition(move):
    """Get the effect of a move on cube state"""
    # This would return how the move affects corners, edges, and centers
    # For now, returning empty transformation
    return {
        'corners': list(range(8)),
        'corner_orientations': [0] * 8,
        'edges': list(range(24)), 
        'edge_orientations': [0] * 24,
        'centers': list(range(24))
    }