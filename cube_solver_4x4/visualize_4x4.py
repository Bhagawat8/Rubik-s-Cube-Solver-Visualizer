"""
4x4 Cube Visualization
Extends the 3x3 visualization to handle 4x4 cube display and animation.
"""

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from mpl_toolkits.mplot3d import Axes3D
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from .tools_4x4 import pretty_print_4x4, apply_moves_4x4

def visualize_4x4_2d(cube_state, move_sequence=None):
    """
    2D visualization of 4x4 cube using matplotlib.
    Shows cube net with all 96 stickers.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib required for visualization. Install with: pip install matplotlib")
        return
    
    fig, ax = plt.subplots(figsize=(12, 9))
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 12)
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Color mapping
    color_map = {
        'U': 'white', 'R': 'red', 'F': 'green',
        'D': 'yellow', 'L': 'orange', 'B': 'blue'
    }
    
    # Draw 4x4 net layout
    _draw_4x4_face(ax, cube_state[0:16], 4, 8, color_map)    # U face
    _draw_4x4_face(ax, cube_state[64:80], 0, 4, color_map)   # L face  
    _draw_4x4_face(ax, cube_state[32:48], 4, 4, color_map)   # F face
    _draw_4x4_face(ax, cube_state[16:32], 8, 4, color_map)   # R face
    _draw_4x4_face(ax, cube_state[80:96], 12, 4, color_map)  # B face
    _draw_4x4_face(ax, cube_state[48:64], 4, 0, color_map)   # D face
    
    plt.title("4x4 Rubik's Cube State", fontsize=16)
    plt.tight_layout()
    plt.show()

def _draw_4x4_face(ax, face_state, x_offset, y_offset, color_map):
    """Draw a single 4x4 face at specified position"""
    for i in range(4):
        for j in range(4):
            sticker_index = i * 4 + j
            color_char = face_state[sticker_index]
            color = color_map.get(color_char, 'gray')
            
            # Draw sticker as rectangle
            rect = patches.Rectangle(
                (x_offset + j, y_offset + (3-i)), 
                0.9, 0.9,
                linewidth=1, 
                edgecolor='black', 
                facecolor=color
            )
            ax.add_patch(rect)

def visualize_4x4_3d(cube_state, move_sequence=None):
    """
    3D visualization of 4x4 cube.
    Shows interactive 3D model with individual stickers.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib required for 3D visualization")
        return
    
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    
    # Generate 4x4 cube geometry
    _draw_4x4_cube_3d(ax, cube_state)
    
    # Set viewing parameters
    ax.set_xlim([-2.5, 2.5])
    ax.set_ylim([-2.5, 2.5]) 
    ax.set_zlim([-2.5, 2.5])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    plt.title("4x4 Rubik's Cube - 3D View")
    plt.show()

def _draw_4x4_cube_3d(ax, cube_state):
    """Draw 4x4 cube in 3D with individual stickers"""
    
    # Color mapping for 3D (using dark variants as requested)
    color_map = {
        'U': 'white', 'R': 'darkred', 'F': 'darkgreen', 
        'D': 'gold', 'L': 'darkorange', 'B': 'darkblue'
    }
    
    # Generate sticker positions for each face
    faces = [
        ('U', cube_state[0:16], [0, 0, 2]),      # Up face
        ('D', cube_state[48:64], [0, 0, -2]),    # Down face
        ('R', cube_state[16:32], [2, 0, 0]),     # Right face
        ('L', cube_state[64:80], [-2, 0, 0]),    # Left face
        ('F', cube_state[32:48], [0, 2, 0]),     # Front face
        ('B', cube_state[80:96], [0, -2, 0])     # Back face
    ]
    
    sticker_size = 0.4
    
    for face_name, face_state, face_center in faces:
        _draw_4x4_face_3d(ax, face_state, face_center, face_name, color_map, sticker_size)

def _draw_4x4_face_3d(ax, face_state, center, face_name, color_map, size):
    """Draw individual 4x4 face in 3D"""
    
    # Define face orientations
    if face_name in ['U', 'D']:
        # Horizontal faces
        directions = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]
    elif face_name in ['R', 'L']:
        # Side faces (YZ plane)
        directions = [(0, 1, 0), (0, 0, 1), (1, 0, 0)]
    else:  # F, B
        # Front/back faces (XZ plane)
        directions = [(1, 0, 0), (0, 0, 1), (0, 1, 0)]
    
    # Draw 4x4 grid of stickers
    for i in range(4):
        for j in range(4):
            sticker_index = i * 4 + j
            color_char = face_state[sticker_index]
            color = color_map.get(color_char, 'gray')
            
            # Calculate sticker position
            x_offset = (j - 1.5) * size * 1.1  
            y_offset = (1.5 - i) * size * 1.1
            
            # Create sticker vertices based on face orientation
            vertices = _create_sticker_vertices(center, directions, x_offset, y_offset, size)
            
            # Add sticker to plot
            poly = Poly3DCollection([vertices], alpha=0.9)
            poly.set_facecolor(color)
            poly.set_edgecolor('black')
            poly.set_linewidth(0.5)
            ax.add_collection3d(poly)

def _create_sticker_vertices(center, directions, x_offset, y_offset, size):
    """Create vertices for a single sticker square"""
    dx, dy, dz = directions
    
    # Base position
    base = np.array(center)
    
    # Local coordinate system
    local_x = np.array(dx) * x_offset
    local_y = np.array(dy) * y_offset
    
    # Sticker corners
    half_size = size / 2
    corners = [
        base + local_x - half_size * np.array(dx) + local_y - half_size * np.array(dy),
        base + local_x + half_size * np.array(dx) + local_y - half_size * np.array(dy),  
        base + local_x + half_size * np.array(dx) + local_y + half_size * np.array(dy),
        base + local_x - half_size * np.array(dx) + local_y + half_size * np.array(dy)
    ]
    
    return corners

def animate_4x4_solution(cube_state, move_sequence):
    """
    Animate the solution of a 4x4 cube.
    Shows each move step by step.
    """
    if not MATPLOTLIB_AVAILABLE:
        print("Matplotlib required for animation")
        return
        
    moves = move_sequence.split()
    states = [cube_state]
    
    # Generate intermediate states
    current_state = cube_state
    for move in moves:
        current_state = apply_moves_4x4(current_state, move)
        states.append(current_state)
    
    # Create animation
    fig = plt.figure(figsize=(12, 8))
    
    def update_frame(frame_num):
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_xlim(0, 16)
        ax.set_ylim(0, 12)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Color mapping
        color_map = {
            'U': 'white', 'R': 'red', 'F': 'green',
            'D': 'yellow', 'L': 'orange', 'B': 'blue'
        }
        
        # Draw current state
        state = states[frame_num]
        _draw_4x4_face(ax, state[0:16], 4, 8, color_map)    # U face
        _draw_4x4_face(ax, state[64:80], 0, 4, color_map)   # L face
        _draw_4x4_face(ax, state[32:48], 4, 4, color_map)   # F face
        _draw_4x4_face(ax, state[16:32], 8, 4, color_map)   # R face
        _draw_4x4_face(ax, state[80:96], 12, 4, color_map)  # B face
        _draw_4x4_face(ax, state[48:64], 4, 0, color_map)   # D face
        
        # Show current move
        if frame_num > 0:
            move = moves[frame_num - 1]
            ax.text(8, 11, f"Move {frame_num}: {move}", 
                   ha='center', va='center', fontsize=14, fontweight='bold')
        
        ax.set_title(f"4x4 Cube Solution - Step {frame_num}/{len(states)-1}", fontsize=16)
    
    # Manual frame stepping (for simplicity)
    for i in range(len(states)):
        update_frame(i)
        plt.pause(1.0)  # 1 second per move
    
    plt.show()

def show_4x4_steps_console(cube_state, move_sequence):
    """
    Show 4x4 solution steps in console (text-based).
    Alternative when matplotlib is not available.
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