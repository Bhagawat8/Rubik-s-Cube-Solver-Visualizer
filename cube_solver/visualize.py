from __future__ import annotations

"""cube_solver.visualize – helper utilities for showing a Rubik\'s-cube
solution path in text, 2-D and 3-D.

The heavy lifting (solving the cube) is implemented in other modules of this
package.  This module focuses purely on *presentation* and therefore contains
no solving logic of its own.

Public helpers
--------------
states_from_moves(scramble, moves) -> list[str]
    Generate the sequence of facelet strings from scramble → solved cube.

show_intermediate_states(states)
    Print each state as a coloured ASCII net to the terminal.

visualize_2d(states)
    Interactive 2-D net view with slider + animation (matplotlib required).

visualize_3d(states)
    Enhanced 3-D cube animation with smooth rotation transitions (plotly required).

"""

import plotly.io as pio # type: ignore

# Configure Plotly renderer for VS Code compatibility
def _configure_plotly_renderer():
    """Configure Plotly renderer based on environment."""
    import os
    import sys
    
    # Detect Jupyter notebook environment
    try:
        from IPython import get_ipython # type: ignore
        if get_ipython() is not None and get_ipython().__class__.__name__ == 'ZMQInteractiveShell':
            pio.renderers.default = "notebook"
            return
    except ImportError:
        pass
    
    # Detect VS Code environment
    if ('VSCODE_PID' in os.environ or 
        ('TERM_PROGRAM' in os.environ and os.environ.get('TERM_PROGRAM') == 'vscode') or
        'VSCODE_CWD' in os.environ):
        # VS Code detected - use VS Code renderer if available
        available_renderers = list(pio.renderers.keys())
        if 'vscode' in available_renderers:
            pio.renderers.default = "vscode"
        elif 'plotly_mimetype+notebook' in available_renderers:
            pio.renderers.default = "plotly_mimetype+notebook"
        else:
            pio.renderers.default = "browser"
    else:
        # Default to browser for other environments
        pio.renderers.default = "browser"

_configure_plotly_renderer()

from typing import List

try:
    from .facecube import FaceCube
    from .cubiecube import CubieCube, moveCube
except ImportError:
    from facecube import FaceCube
    from cubiecube import CubieCube, moveCube

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
_move_axis = {"U": 0, "R": 1, "F": 2, "D": 3, "L": 4, "B": 5}

_face_colour = {
    "U": "white",
    "R": "red",
    "F": "green",
    "D": "yellow",
    "L": "orange",
    "B": "blue",
}

# Dark variant for 3-D view
_face_colour_dark = {
    "U": "#f5f5f5",   # white
    "R": "#8b0000",   # dark red
    "F": "#006400",   # dark green
    "D": "#ff69b4",   # pink
    "L": "#ff8c00",   # dark orange
    "B": "#00008b",   # dark blue
}


# Human-readable net (identical to pretty() in demo.py, duplicated here to
# avoid a circular import dependency.)

def _pretty(facelets: str) -> str:  # noqa: D401 – (simple function)
    """Return cube in human-readable net form (string)."""

    def blk(t: str):
        return [t[0:3], t[3:6], t[6:9]]

    U, R, F, D, L, B = map(
        blk,
        (
            facelets[0:9],
            facelets[9:18],
            facelets[18:27],
            facelets[27:36],
            facelets[36:45],
            facelets[45:54],
        ),
    )
    out = []
    for r in U:
        out.append(" " * 7 + " ".join(r))
    for i in range(3):
        out.append(
            " ".join(L[i])
            + "  "
            + " ".join(F[i])
            + "  "
            + " ".join(R[i])
            + "  "
            + " ".join(B[i])
        )
    for r in D:
        out.append(" " * 7 + " ".join(r))
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def states_from_moves(scramble: str, moves: str) -> List[str]:
    """Return list of facelet strings for each step from *scramble* to solved.

    The returned list *includes* the initial scramble as first element and the
    final solved cube as last element.
    """

    # start from scramble as CubieCube for efficient mutation
    cc = FaceCube(scramble).toCubieCube()
    states = [scramble]

    for token in moves.split():
        axis = _move_axis[token[0]]
        power = 1  # default 90° clockwise
        if len(token) == 2 and token[1] == "2":
            power = 2
        elif len(token) == 2 and token[1] == "'":
            power = 3
        # perform move(s)
        for _ in range(power):
            cc.multiply(moveCube[axis])
        states.append(cc.toFaceCube().to_String())

    return states


def show_intermediate_states(states: List[str]) -> None:
    """Pretty-print each state to the console."""

    for idx, s in enumerate(states):
        print(f"\nStep {idx}:\n")
        print(_pretty(s))
        print("-" * 50)


# ---------------------------------------------------------------------------
# Matplotlib-based visualisation helpers
# ---------------------------------------------------------------------------

def _ensure_matplotlib():
    """Import matplotlib lazily and return (plt, patches, widgets)."""

    import importlib

    plt = importlib.import_module("matplotlib.pyplot")
    patches = importlib.import_module("matplotlib.patches")
    widgets = importlib.import_module("matplotlib.widgets")
    return plt, patches, widgets


# ---- 2-D net ----------------------------------------------------------------

def visualize_2d(states: List[str]) -> None:
    """Interactive 2-D net visualisation using matplotlib.

    A small slider beneath the figure lets users scrub through individual
    states.  A *Play* button animates the solution automatically.
    """

    plt, patches, widgets = _ensure_matplotlib()

    fig, ax = plt.subplots(figsize=(6, 6))
    plt.subplots_adjust(bottom=0.25)  # room for slider/buttons
    ax.set_aspect("equal")
    ax.set_axis_off()

    # sticker rectangles for reuse so we can just update their face-colours
    rects = []

    def _draw_net(facelets: str):
        # helper to (re)draw the entire net and return list of rectangles
        ax.cla()
        ax.set_aspect("equal")
        ax.set_axis_off()
        rects_local = []

        def _add_rect(x, y, color):
            r = patches.Rectangle(
                (x, y),
                1,
                1,
                facecolor=color,
                edgecolor="black",
                linewidth=0.5,
            )
            ax.add_patch(r)
            rects_local.append(r)

        # mapping identical to pretty() output positions
        # grid coords: cols 0-3, rows 0-2 (higher y means upper in plot)
        # each face is 3×3
        faces = [
            ("U", 1, 2),  # col offset, row offset
            ("L", 0, 1),
            ("F", 1, 1),
            ("R", 2, 1),
            ("B", 3, 1),
            ("D", 1, 0),
        ]

        idx = 0
        for name, col_off, row_off in faces:
            for row in range(3):
                for col in range(3):
                    color_key = facelets[idx]
                    idx += 1
                    _add_rect(col_off * 3 + col, row_off * 3 + (2 - row), _face_colour[color_key])

        ax.set_xlim(0, 12)
        ax.set_ylim(0, 9)
        ax.invert_yaxis()
        return rects_local

    # initial draw
    rects = _draw_net(states[0])

    # --- slider & buttons ----------------------------------------------------
    ax_slider = plt.axes([0.15, 0.1, 0.7, 0.03])
    slider = widgets.Slider(
        ax=ax_slider,
        label="Step",
        valmin=0,
        valmax=len(states) - 1,
        valinit=0,
        valstep=1,
    )

    # play button
    ax_btn = plt.axes([0.88, 0.05, 0.08, 0.08])
    btn = widgets.Button(ax_btn, label="▶")

    def _update(val):
        step = int(slider.val)
        facelets = states[step]
        idx = 0
        for r in rects:
            color_key = facelets[idx]
            r.set_facecolor(_face_colour[color_key])
            idx += 1
        fig.canvas.draw_idle()

    slider.on_changed(_update)

    # simple play/animate implementation
    _playing = {"on": False}
    _timer = {"instance": None}

    def _toggle_play(event):
        _playing["on"] = not _playing["on"]
        btn.label.set_text("❚❚" if _playing["on"] else "▶")
        if _playing["on"]:
            _next_frame()
        else:
            # Stop the timer when paused
            if _timer["instance"]:
                _timer["instance"].stop()
                _timer["instance"] = None

    def _next_frame():
        if not _playing["on"]:
            return
        current = int(slider.val)
        next_step = (current + 1) % len(states)
        slider.set_val(next_step)
        
        # Stop previous timer if exists
        if _timer["instance"]:
            _timer["instance"].stop()
        
        # Create new timer for next frame
        _timer["instance"] = fig.canvas.new_timer(interval=400)
        _timer["instance"].add_callback(_next_frame)
        _timer["instance"].start()

    btn.on_clicked(_toggle_play)

    plt.show()


# ---- 3-D cube --------------------------------------------------------------

def visualize_3d(states: List[str], gif_path: str | None = None) -> None:
    """Enhanced 3-D cube animation with smooth rotation transitions.
    
    Shows actual cube piece rotations between moves using Plotly for 
    interactive 3D visualization with animation controls.
    """
    
    try:
        import plotly.graph_objects as go # type: ignore
        import numpy as np # type: ignore
        print("Starting enhanced 3D visualization with Plotly...")
    except ImportError:
        print("Enhanced 3D visualization requires plotly and numpy.")
        print("Install with: pip install plotly numpy")
        print("Falling back to basic matplotlib 3D...")
        _visualize_3d_matplotlib(states)
        return
    
    # Extract moves from states
    print(f"Processing {len(states)} cube states...")
    moves = _extract_moves_from_states(states)
    print(f"Extracted {len(moves)} valid moves: {' '.join(moves[:10])}{'...' if len(moves) > 10 else ''}")
    
    # Create Plotly 3D figure with enhanced animation
    fig = go.Figure()
    
    # Generate all animation frames
    print("Generating solid cube animation frames...")
    all_frames = []
    
    # Add frames for each state + intermediate rotation frames
    for i in range(len(states)):
        # Add main state frame
        frame_data = _create_plotly_cube_frame(states[i], f"State {i}")
        all_frames.append(frame_data)
        
        # Add intermediate rotation frames if not the last state
        if i < len(moves):
            move = moves[i]
            next_state = states[i + 1]
            
            # Create 6 intermediate frames for smooth rotation
            for step in range(1, 7):
                progress = step / 7.0
                interp_frame = _create_interpolated_frame(states[i], next_state, move, progress, f"Rotate {i}.{step}")
                all_frames.append(interp_frame)
    
    print(f"Generated {len(all_frames)} total animation frames")
    
    # Set initial frame
    if all_frames:
        for trace in all_frames[0]['data']:
            fig.add_trace(trace)
    
    # Create frames for animation
    frames = []
    for i, frame_data in enumerate(all_frames):
        frame = go.Frame(
            data=frame_data['data'],
            name=str(i)
        )
        frames.append(frame)
    
    fig.frames = frames
    
    # Configure layout with animation controls
    fig.update_layout(
        title=dict(
            text="🧩 Solid Rubik's Cube 3D Animation",
            x=0.5,
            font=dict(size=20)
        ),
        scene=dict(
            xaxis=dict(range=[-1.6, 1.6], showticklabels=False, showgrid=False, zeroline=False, showbackground=False),
            yaxis=dict(range=[-1.6, 1.6], showticklabels=False, showgrid=False, zeroline=False, showbackground=False),
            zaxis=dict(range=[-1.6, 1.6], showticklabels=False, showgrid=False, zeroline=False, showbackground=False),
            camera=dict(
                eye=dict(x=2.0, y=2.0, z=2.0),
                center=dict(x=0, y=0, z=0)
            ),
            aspectmode='cube',
            bgcolor='rgba(245,245,245,1)'
        ),
        updatemenus=[{
            'type': 'buttons',
            'showactive': False,
            'y': 0.05,
            'x': 0.05,
            'xanchor': 'left',
            'yanchor': 'bottom',
            'buttons': [
                {
                    'label': '▶️ Play Animation',
                    'method': 'animate',
                    'args': [None, {
                        'frame': {'duration': 300, 'redraw': True},
                        'mode': 'immediate',
                        'fromcurrent': True,
                        'transition': {'duration': 150}
                    }]
                },
                {
                    'label': '⏸️ Pause',
                    'method': 'animate',
                    'args': [[None], {
                        'frame': {'duration': 0, 'redraw': False},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }]
                },
                {
                    'label': '💾 Save',
                    'method': 'skip',
                    'args': []
                },
                {
                    'label': '⏮️ Reset',
                    'method': 'animate',
                    'args': [['0'], {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 0}
                    }]
                }
            ]
        }],
        sliders=[{
            'active': 0,
            'currentvalue': {'prefix': 'Step: '},
            'pad': {'t': 50},
            'steps': [
                {
                    'label': f'{i}',
                    'method': 'animate',
                    'args': [[str(i)], {
                        'frame': {'duration': 0, 'redraw': True},
                        'mode': 'immediate',
                        'transition': {'duration': 100}
                    }]
                } for i in range(len(all_frames))
            ],
            'x': 0.05,
            'y': 0.02,
            'len': 0.9
        }],
        width=900,
        height=700,
        margin=dict(l=20, r=20, t=80, b=100)
    )
    
    print("Launching solid 3D cube visualization...")
    print("Features:")
    
    # Optional GIF export ---------------------------------------------------
    if gif_path:
        try:
            from plotly.io import to_image # type: ignore
            import imageio.v2 as imageio # type: ignore
            print(f"Exporting animation to GIF → {gif_path} (this may take a while)…")
            frames_png = []
            for f in frames:
                fig.update(data=f.data)
                img_bytes = to_image(fig, format="png", width=800, height=800, scale=2)
                frames_png.append(imageio.imread(img_bytes))
            imageio.mimsave(gif_path, frames_png, duration=0.3)
            print("GIF saved successfully.")
        except Exception as ex:
            print("[warn] Could not export GIF:", ex)
            print("Ensure 'kaleido' and 'imageio' are installed (pip install kaleido imageio).")
    # Show the figure with appropriate renderer and error handling
    print("- Interactive 3D visualization with animation controls")
    print("- Play/Pause buttons and frame scrubbing slider")
    print("- Smooth rotation animations between moves")
    print("- VS Code compatible display")
    
    try:
        # Auto-detect best renderer for current environment
        import os
        current_renderer = pio.renderers.default
        
        # Check for VS Code environment with multiple detection methods
        is_vscode = ('VSCODE_PID' in os.environ or 
                    ('TERM_PROGRAM' in os.environ and os.environ.get('TERM_PROGRAM') == 'vscode') or
                    'VSCODE_CWD' in os.environ)
        
        if is_vscode:
            # VS Code (or code-server) often fails with the "vscode" renderer ➜ generate a temp HTML file
            # and open it with the system browser for a guaranteed result.
            import tempfile, pathlib, webbrowser
            html_path = pathlib.Path(tempfile.gettempdir()) / "cube_visualization.html"
            fig.write_html(str(html_path), auto_open=False)
            webbrowser.open_new_tab(html_path.as_uri())
            print(f"\n✅ 3D visualization saved to and opened from: {html_path}")
        else:
            # Any other environment – rely on Plotly's default renderer behaviour
            fig.show()
            print("\n✅ 3D visualization launched!")

            
    except Exception as e:
        print(f"\n❌ Visualization error: {e}")
        print("Falling back to HTML export...")
        try:
            html_path = "cube_visualization.html"
            fig.write_html(html_path)
            print(f"📁 Visualization saved as '{html_path}'")
            print("   Open this file in your browser to view the 3D animation.")
        except Exception as html_err:
            print(f"❌ HTML export also failed: {html_err}")
            print("Consider installing/updating plotly: pip install --upgrade plotly")


def _visualize_3d_matplotlib(states: List[str]) -> None:
    """Fallback matplotlib 3D visualization (original implementation)."""
    
    plt, patches, widgets = _ensure_matplotlib()
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection # type: ignore

    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_box_aspect([1, 1, 1])

    # helper generating squares for one state
    def _generate_faces(facelets: str):
        # coordinates based on cube of size 3 centred at origin, sticker size 1
        squares = []  # list[(verts, colour)]
        idx = 0

        def _quad(p1, p2, p3, p4):
            return [p1, p2, p3, p4]

        # mapping for 6 faces
        # U (z = +1.5)
        for row in range(3):
            for col in range(3):
                x0 = -1.5 + col
                y0 = 1.5 - row - 1
                squares.append((
                    _quad(
                        (x0, y0, 1.5),
                        (x0 + 1, y0, 1.5),
                        (x0 + 1, y0 + 1, 1.5),
                        (x0, y0 + 1, 1.5),
                    ),
                    _face_colour[facelets[idx]],
                ))
                idx += 1
        # R (x = +1.5)
        for row in range(3):
            for col in range(3):
                y0 = 1.5 - row - 1
                z0 = 1.5 - col - 1
                squares.append((
                    _quad(
                        (1.5, y0, z0),
                        (1.5, y0, z0 + 1),
                        (1.5, y0 + 1, z0 + 1),
                        (1.5, y0 + 1, z0),
                    ),
                    _face_colour[facelets[idx]],
                ))
                idx += 1
        # F (y = +1.5)
        for row in range(3):
            for col in range(3):
                x0 = -1.5 + col
                z0 = 1.5 - row - 1
                squares.append((
                    _quad(
                        (x0, 1.5, z0),
                        (x0 + 1, 1.5, z0),
                        (x0 + 1, 1.5, z0 + 1),
                        (x0, 1.5, z0 + 1),
                    ),
                    _face_colour[facelets[idx]],
                ))
                idx += 1
        # D (z = -1.5)
        for row in range(3):
            for col in range(3):
                x0 = -1.5 + col
                y0 = -1.5 + row
                squares.append((
                    _quad(
                        (x0, y0, -1.5),
                        (x0 + 1, y0, -1.5),
                        (x0 + 1, y0 + 1, -1.5),
                        (x0, y0 + 1, -1.5),
                    ),
                    _face_colour[facelets[idx]],
                ))
                idx += 1
        # L (x = -1.5)
        for row in range(3):
            for col in range(3):
                y0 = -1.5 + row
                z0 = 1.5 - col - 1
                squares.append((
                    _quad(
                        (-1.5, y0, z0),
                        (-1.5, y0, z0 + 1),
                        (-1.5, y0 + 1, z0 + 1),
                        (-1.5, y0 + 1, z0),
                    ),
                    _face_colour[facelets[idx]],
                ))
                idx += 1
        # B (y = -1.5)
        for row in range(3):
            for col in range(3):
                x0 = 1.5 - col - 1
                z0 = 1.5 - row - 1
                squares.append((
                    _quad(
                        (x0, -1.5, z0),
                        (x0 + 1, -1.5, z0),
                        (x0 + 1, -1.5, z0 + 1),
                        (x0, -1.5, z0 + 1),
                    ),
                    _face_colour[facelets[idx]],
                ))
                idx += 1

        return squares

    # initial state
    first_faces = _generate_faces(states[0])
    coll = Poly3DCollection([verts for verts, _ in first_faces])
    coll.set_facecolor([colour for _, colour in first_faces])
    coll.set_edgecolor("black")
    ax.add_collection3d(coll)

    ax.set_xlim(-2, 2)
    ax.set_ylim(-2, 2)
    ax.set_zlim(-2, 2)
    ax.set_axis_off()

    # slider
    _, _, widgets = _ensure_matplotlib()
    ax_slider = plt.axes([0.15, 0.05, 0.7, 0.03])
    slider = widgets.Slider(
        ax=ax_slider,
        label="Step",
        valmin=0,
        valmax=len(states) - 1,
        valinit=0,
        valstep=1,
    )

    def _update(val):
        step = int(slider.val)
        squares = _generate_faces(states[step])
        coll.set_verts([verts for verts, _ in squares])
        coll.set_facecolor([colour for _, colour in squares])
        fig.canvas.draw_idle()

    slider.on_changed(_update)

    plt.show()


# ---- Enhanced 3D animation helper functions --------------------------------

def _extract_moves_from_states(states: List[str]) -> List[str]:
    """Extract the sequence of moves by analyzing state transitions."""
    moves = []
    
    # Get the solution moves from the solver
    # This ensures we only use valid Rubik's cube moves
    try:
        from .search import Search
        # We need to get the actual moves that were used to solve
        # For now, we'll use a simplified approach that only allows valid moves
        moves = _get_valid_moves_from_solver(states)
    except ImportError:
        # Fallback: analyze state transitions
        for i in range(len(states) - 1):
            current_state = states[i]
            next_state = states[i + 1]
            move = _find_move_between_states(current_state, next_state)
            if move:
                moves.append(move)
    
    return moves


def _get_valid_moves_from_solver(states: List[str]) -> List[str]:
    """Get the valid moves that were used by the solver."""
    
    # Since we don't have direct access to the solver's move sequence,
    # we'll reconstruct it by analyzing the state transitions
    # and ensuring only valid Rubik's cube moves are used
    
    moves = []
    valid_moves = ["U", "U'", "U2", "R", "R'", "R2", "F", "F'", "F2", 
                   "D", "D'", "D2", "L", "L'", "L2", "B", "B'", "B2"]
    
    for i in range(len(states) - 1):
        current_state = states[i]
        next_state = states[i + 1]
        
        # Find which valid move transforms current_state to next_state
        found_move = None
        for move in valid_moves:
            if _apply_move_to_state(current_state, move) == next_state:
                found_move = move
                break
        
        if found_move:
            moves.append(found_move)
        else:
            # If no valid move found, skip this transition
            # This ensures we only use valid moves
            continue
    
    return moves


def _apply_move_to_state(state: str, move: str) -> str:
    """Apply a valid Rubik's cube move to a state and return the new state."""
    
    # Convert state to CubieCube
    cc = FaceCube(state).toCubieCube()
    
    # Parse the move
    axis = _move_axis[move[0]]
    power = 1
    if len(move) == 2:
        if move[1] == "2":
            power = 2
        elif move[1] == "'":
            power = 3
    
    # Apply the move using the standard move cubes
    for _ in range(power):
        cc.multiply(moveCube[axis])
    
    # Convert back to facelet string
    return cc.toFaceCube().to_String()


def _find_move_between_states(state1: str, state2: str) -> str:
    """Find the move that transforms state1 into state2."""
    
    # Convert states to CubieCube for analysis
    cc1 = FaceCube(state1).toCubieCube()
    cc2 = FaceCube(state2).toCubieCube()
    
    # Test all possible moves to find the one that matches
    move_names = ["U", "U'", "U2", "R", "R'", "R2", "F", "F'", "F2", 
                  "D", "D'", "D2", "L", "L'", "L2", "B", "B'", "B2"]
    
    for move_name in move_names:
        # Apply move to state1 and see if it matches state2
        test_cc = CubieCube(cp=cc1.cp.copy(), co=cc1.co.copy(), 
                           ep=cc1.ep.copy(), eo=cc1.eo.copy())
        
        axis = _move_axis[move_name[0]]
        power = 1
        if len(move_name) == 2:
            if move_name[1] == "2":
                power = 2
            elif move_name[1] == "'":
                power = 3
        
        # Apply the move
        for _ in range(power):
            test_cc.multiply(moveCube[axis])
        
        # Check if this matches state2
        if (_arrays_equal(test_cc.cp, cc2.cp) and _arrays_equal(test_cc.co, cc2.co) and 
            _arrays_equal(test_cc.ep, cc2.ep) and _arrays_equal(test_cc.eo, cc2.eo)):
            return move_name
    
    return ""  # No move found


def _arrays_equal(arr1, arr2):
    """Check if two arrays are equal."""
    if len(arr1) != len(arr2):
        return False
    return all(a == b for a, b in zip(arr1, arr2))


def _generate_animation_frames(states: List[str], moves: List[str]):
    """Generate smooth animation frames showing rotation transitions."""
    
    import numpy as np # type: ignore
    
    animation_frames = []
    rotation_steps = 10  # Number of intermediate frames per move
    
    for i, state in enumerate(states):
        # Add current state frame
        frame_data = _create_plotly_cube_frame(state, f"State {i}")
        animation_frames.append(frame_data)
        
        # Add rotation transition frames if not the last state
        if i < len(moves):
            move = moves[i]
            next_state = states[i + 1]
            
            # Generate intermediate rotation frames
            for step in range(1, rotation_steps):
                progress = step / rotation_steps
                interpolated_frame = _create_rotation_frame(state, next_state, move, progress)
                animation_frames.append(interpolated_frame)
    
    return animation_frames


def _create_plotly_cube_frame(state: str, frame_name: str):
    """Create a Plotly frame showing the cube in a specific state."""
    
    try:
        import plotly.graph_objects as go # type: ignore
        import numpy as np # type: ignore
    except ImportError:
        return {'data': []}
    
    traces = []
    
    # Create individual cube pieces
    cube_pieces = _create_simple_cube_pieces(state)
    
    for piece in cube_pieces:
        trace = go.Mesh3d(
            x=piece['x'],
            y=piece['y'], 
            z=piece['z'],
            i=piece['i'],
            j=piece['j'],
            k=piece['k'],
            facecolor=piece['color'],
            opacity=1.0,
            flatshading=True,
            lighting=dict(ambient=0.3, diffuse=0.7, specular=0.2, roughness=0.8, fresnel=0.1),
            showscale=False,
            hoverinfo='skip'
        )
        traces.append(trace)
    
    return {'data': traces}


def _create_interpolated_frame(state1: str, state2: str, move: str, progress: float, frame_name: str):
    """Create an interpolated frame showing rotation between two states."""
    
    # Create a smooth interpolation between states
    # This shows the actual rotation of pieces during the move
    
    try:
        import plotly.graph_objects as go # type: ignore
        import numpy as np # type: ignore
    except ImportError:
        return {'data': []}
    
    traces = []
    
    # Get the pieces that should rotate for this move
    rotating_pieces, static_pieces = _get_rotating_pieces_for_move(state1, move)
    
    # Add static pieces (unchanged)
    for piece in static_pieces:
        trace = go.Mesh3d(
            x=piece['x'],
            y=piece['y'],
            z=piece['z'],
            i=piece['i'],
            j=piece['j'],
            k=piece['k'],
            facecolor=piece['color'],
            opacity=1.0,
            flatshading=True,
            lighting=dict(ambient=0.3, diffuse=0.7, specular=0.2, roughness=0.8, fresnel=0.1),
            showscale=False,
            hoverinfo='skip'
        )
        traces.append(trace)
    
    # Add rotating pieces with interpolated positions
    for piece in rotating_pieces:
        rotated_piece = _interpolate_piece_rotation(piece, move, progress)
        trace = go.Mesh3d(
            x=rotated_piece['x'],
            y=rotated_piece['y'],
            z=rotated_piece['z'],
            i=piece['i'],
            j=piece['j'],
            k=piece['k'],
            facecolor=piece['color'],
            opacity=1.0,
            flatshading=True,
            lighting=dict(ambient=0.3, diffuse=0.7, specular=0.2, roughness=0.8, fresnel=0.1),
            showscale=False,
            hoverinfo='skip'
        )
        traces.append(trace)
    
    return {'data': traces}


def _get_rotating_pieces_for_move(state: str, move: str):
    """Determine which pieces rotate for a given move."""
    
    # Get all pieces
    all_pieces = _create_simple_cube_pieces(state)
    
    # Determine which pieces should rotate based on the move
    rotating_pieces = []
    static_pieces = []
    
    move_face = move[0]  # U, R, F, D, L, B
    
    for piece in all_pieces:
        # Check if this piece is on the face being rotated
        if _piece_on_face(piece, move_face):
            rotating_pieces.append(piece)
        else:
            static_pieces.append(piece)
    
    return rotating_pieces, static_pieces


def _piece_on_face(piece, face):
    """Check if a piece is on the specified face."""
    
    # Get the center position of the piece
    x_center = sum(piece['x']) / len(piece['x'])
    y_center = sum(piece['y']) / len(piece['y'])
    z_center = sum(piece['z']) / len(piece['z'])
    
    # Check if piece is on the face being rotated
    if face == 'U' and abs(z_center - 1) < 0.1:
        return True
    elif face == 'D' and abs(z_center + 1) < 0.1:
        return True
    elif face == 'R' and abs(x_center - 1) < 0.1:
        return True
    elif face == 'L' and abs(x_center + 1) < 0.1:
        return True
    elif face == 'F' and abs(y_center - 1) < 0.1:
        return True
    elif face == 'B' and abs(y_center + 1) < 0.1:
        return True
    
    return False


def _interpolate_piece_rotation(piece, move, progress):
    """Interpolate piece rotation for smooth animation."""
    
    import numpy as np # type: ignore
    
    # Get rotation matrix for the move
    rotation_matrix = _get_rotation_matrix_for_move(move, progress)
    
    # Apply rotation to piece vertices
    vertices = []
    for i in range(len(piece['x'])):
        vertex = np.array([piece['x'][i], piece['y'][i], piece['z'][i]])
        rotated_vertex = rotation_matrix @ vertex
        vertices.append(rotated_vertex)
    
    # Extract coordinates
    x_coords = [v[0] for v in vertices]
    y_coords = [v[1] for v in vertices]
    z_coords = [v[2] for v in vertices]
    
    return {
        'x': x_coords,
        'y': y_coords,
        'z': z_coords
    }


import math

def _ease_in_out(t: float) -> float:
    """Sine-based ease-in-out for smooth interpolation (0‒1)."""
    return 0.5 * (1 - math.cos(math.pi * t))


def _get_rotation_matrix_for_move(move, progress):
    """Get rotation matrix for a specific move and progress."""
    
    import numpy as np # type: ignore
    
    # Define rotation angles for each move
    angle_map = {
        'U': (0, 0, 90), 'U\'': (0, 0, -90), 'U2': (0, 0, 180),
        'D': (0, 0, -90), 'D\'': (0, 0, 90), 'D2': (0, 0, -180),
        'R': (90, 0, 0), 'R\'': (-90, 0, 0), 'R2': (180, 0, 0),
        'L': (-90, 0, 0), 'L\'': (90, 0, 0), 'L2': (-180, 0, 0),
        'F': (0, 90, 0), 'F\'': (0, -90, 0), 'F2': (0, 180, 0),
        'B': (0, -90, 0), 'B\'': (0, 90, 0), 'B2': (0, -180, 0),
    }
    
    if move not in angle_map:
        return np.eye(3)
    
    angles = angle_map[move]
    # Apply easing for smoother motion
    eased = _ease_in_out(progress)
    # Scale by eased progress
    angles = tuple(angle * eased * np.pi / 180 for angle in angles)
    
    # Create rotation matrix
    cos_x, sin_x = np.cos(angles[0]), np.sin(angles[0])
    cos_y, sin_y = np.cos(angles[1]), np.sin(angles[1])
    cos_z, sin_z = np.cos(angles[2]), np.sin(angles[2])
    
    Rx = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]])
    Ry = np.array([[cos_y, 0, sin_y], [0, 1, 0], [-sin_y, 0, cos_y]])
    Rz = np.array([[cos_z, -sin_z, 0], [sin_z, cos_z, 0], [0, 0, 1]])
    
    return Rz @ Ry @ Rx


def _create_simple_cube_pieces(state: str):
    """Create a solid 3x3x3 cube structure with proper piece connections."""
    
    pieces = []
    
    # Define the 27 positions in a 3x3x3 cube (including center pieces)
    # Each position is (x, y, z) where x,y,z are in [-1, 0, 1]
    cube_positions = []
    for x in [-1, 0, 1]:
        for y in [-1, 0, 1]:
            for z in [-1, 0, 1]:
                cube_positions.append((x, y, z))
    
    # Create solid cube pieces at each position
    for pos in cube_positions:
        x, y, z = pos
        piece = _create_solid_cube_piece(x, y, z, state)
        pieces.append(piece)
    
    return pieces


def _create_solid_cube_piece(x, y, z, state):
    """Create a solid cube piece with proper face colors based on position."""
    
    # Map cube position to facelet indices in the state string
    # This mapping follows the standard facelet ordering: U, R, F, D, L, B
    facelet_map = _get_facelet_map_for_position(x, y, z)
    
    # Get colors for visible faces of this piece
    colors = {}
    for face, idx in facelet_map.items():
        if idx < len(state):
            colors[face] = _face_colour_dark[state[idx]]
    
    # Create the piece with proper colors
    piece = _create_colored_cube_piece(x, y, z, 0.98, colors)  # 0.98 for minimal gaps
    return piece


def _get_facelet_map_for_position(x, y, z):
    """Map a cube position to the facelet indices that should be visible."""
    
    facelet_map = {}
    
    # U face (z = 1) - indices 0-8
    if z == 1:
        facelet_map['U'] = (1-y) * 3 + (x+1)
    
    # D face (z = -1) - indices 27-35
    if z == -1:
        facelet_map['D'] = 27 + (y+1) * 3 + (x+1)
    
    # R face (x = 1) - indices 9-17
    if x == 1:
        facelet_map['R'] = 9 + (1-y) * 3 + (1-z)
    
    # L face (x = -1) - indices 36-44
    if x == -1:
        facelet_map['L'] = 36 + (y+1) * 3 + (1-z)
    
    # F face (y = 1) - indices 18-26
    if y == 1:
        facelet_map['F'] = 18 + (x+1) * 3 + (1-z)
    
    # B face (y = -1) - indices 45-53
    if y == -1:
        facelet_map['B'] = 45 + (1-x) * 3 + (1-z)
    
    return facelet_map


def _create_colored_cube_piece(x, y, z, size, face_colors):
    """Create a cube piece with different colors for each visible face."""
    
    # Define cube vertices
    s = size / 2
    vertices = [
        [x-s, y-s, z-s], [x+s, y-s, z-s], [x+s, y+s, z-s], [x-s, y+s, z-s],  # bottom
        [x-s, y-s, z+s], [x+s, y-s, z+s], [x+s, y+s, z+s], [x-s, y+s, z+s]   # top
    ]
    
    # Define cube faces as triangles with specific colors
    faces = []
    face_colors_list = []
    
    # Bottom face (z = z-s)
    if 'D' in face_colors:
        faces.extend([[0,1,2], [0,2,3]])
        face_colors_list.extend([face_colors['D'], face_colors['D']])
    else:
        faces.extend([[0,1,2], [0,2,3]])
        face_colors_list.extend(['#333333', '#333333'])
    
    # Top face (z = z+s)
    if 'U' in face_colors:
        faces.extend([[4,7,6], [4,6,5]])
        face_colors_list.extend([face_colors['U'], face_colors['U']])
    else:
        faces.extend([[4,7,6], [4,6,5]])
        face_colors_list.extend(['#333333', '#333333'])
    
    # Front face (y = y+s)
    if 'F' in face_colors:
        faces.extend([[0,4,5], [0,5,1]])
        face_colors_list.extend([face_colors['F'], face_colors['F']])
    else:
        faces.extend([[0,4,5], [0,5,1]])
        face_colors_list.extend(['#333333', '#333333'])
    
    # Back face (y = y-s)
    if 'B' in face_colors:
        faces.extend([[2,6,7], [2,7,3]])
        face_colors_list.extend([face_colors['B'], face_colors['B']])
    else:
        faces.extend([[2,6,7], [2,7,3]])
        face_colors_list.extend(['#333333', '#333333'])
    
    # Left face (x = x-s)
    if 'L' in face_colors:
        faces.extend([[0,3,7], [0,7,4]])
        face_colors_list.extend([face_colors['L'], face_colors['L']])
    else:
        faces.extend([[0,3,7], [0,7,4]])
        face_colors_list.extend(['#333333', '#333333'])
    
    # Right face (x = x+s)
    if 'R' in face_colors:
        faces.extend([[1,5,6], [1,6,2]])
        face_colors_list.extend([face_colors['R'], face_colors['R']])
    else:
        faces.extend([[1,5,6], [1,6,2]])
        face_colors_list.extend(['#333333', '#333333'])
    
    x_coords = [v[0] for v in vertices]
    y_coords = [v[1] for v in vertices]
    z_coords = [v[2] for v in vertices]
    
    i_coords = [f[0] for f in faces]
    j_coords = [f[1] for f in faces]
    k_coords = [f[2] for f in faces]
    
    return {
        'x': x_coords,
        'y': y_coords,
        'z': z_coords,
        'i': i_coords,
        'j': j_coords,
        'k': k_coords,
        'color': face_colors_list
    }


def _create_single_cube_piece(x, y, z, size, color):
    """Create a single small cube piece."""
    
    # Define cube vertices
    s = size / 2
    vertices = [
        [x-s, y-s, z-s], [x+s, y-s, z-s], [x+s, y+s, z-s], [x-s, y+s, z-s],  # bottom
        [x-s, y-s, z+s], [x+s, y-s, z+s], [x+s, y+s, z+s], [x-s, y+s, z+s]   # top
    ]
    
    # Define cube faces as triangles
    faces = [
        [0,1,2], [0,2,3],  # bottom
        [4,7,6], [4,6,5],  # top
        [0,4,5], [0,5,1],  # front
        [2,6,7], [2,7,3],  # back
        [0,3,7], [0,7,4],  # left
        [1,5,6], [1,6,2]   # right
    ]
    
    x_coords = [v[0] for v in vertices]
    y_coords = [v[1] for v in vertices]
    z_coords = [v[2] for v in vertices]
    
    i_coords = [f[0] for f in faces]
    j_coords = [f[1] for f in faces]
    k_coords = [f[2] for f in faces]
    
    return {
        'x': x_coords,
        'y': y_coords,
        'z': z_coords,
        'i': i_coords,
        'j': j_coords,
        'k': k_coords,
        'color': color
    }


def _create_rotation_frame(state1: str, state2: str, move: str, progress: float):
    """Create intermediate rotation frame between two states."""
    
    try:
        import plotly.graph_objects as go # type: ignore
        import numpy as np # type: ignore
    except ImportError:
        return {'data': []}
    
    traces = []
    
    # Get pieces that should rotate for this move
    rotating_pieces, static_pieces = _get_move_pieces(state1, move)
    
    # Create rotation matrix for the move
    rotation_matrix = _get_rotation_matrix(move, progress)
    
    # Add static pieces (unchanged)
    for piece in static_pieces:
        trace = go.Mesh3d(
            x=piece['x'],
            y=piece['y'],
            z=piece['z'],
            i=piece['i'],
            j=piece['j'],
            k=piece['k'],
            facecolor=piece['colors'],
            showscale=False,
            lighting=dict(ambient=0.7, diffuse=0.9, specular=0.1),
            lightposition=dict(x=100, y=200, z=300)
        )
        traces.append(trace)
    
    # Add rotating pieces with interpolated positions
    for piece in rotating_pieces:
        # Apply rotation to piece coordinates
        rotated_coords = _apply_rotation_to_piece(piece, rotation_matrix)
        
        trace = go.Mesh3d(
            x=rotated_coords['x'],
            y=rotated_coords['y'],
            z=rotated_coords['z'],
            i=piece['i'],
            j=piece['j'],
            k=piece['k'],
            facecolor=piece['colors'],
            showscale=False,
            lighting=dict(ambient=0.7, diffuse=0.9, specular=0.1),
            lightposition=dict(x=100, y=200, z=300)
        )
        traces.append(trace)
    
    return {'data': traces}


def _generate_cube_pieces(state: str):
    """Generate 3D mesh data for all cube pieces."""
    
    pieces = []
    idx = 0
    
    # Define cube structure - each piece as a small cube
    cube_size = 0.45  # Slightly smaller than 0.5 to show gaps between pieces
    
    # U face pieces (top)
    for row in range(3):
        for col in range(3):
            x_center = -1 + col
            y_center = 1 - row
            z_center = 1.5
            
            piece = _create_cube_piece(x_center, y_center, z_center, cube_size, 
                                     _face_colour[state[idx]])
            pieces.append(piece)
            idx += 1
    
    # R face pieces (right)
    for row in range(3):
        for col in range(3):
            x_center = 1.5
            y_center = 1 - row
            z_center = 1 - col
            
            piece = _create_cube_piece(x_center, y_center, z_center, cube_size,
                                     _face_colour[state[idx]])
            pieces.append(piece)
            idx += 1
    
    # F face pieces (front)
    for row in range(3):
        for col in range(3):
            x_center = -1 + col
            y_center = 1.5
            z_center = 1 - row
            
            piece = _create_cube_piece(x_center, y_center, z_center, cube_size,
                                     _face_colour[state[idx]])
            pieces.append(piece)
            idx += 1
    
    # D face pieces (bottom)
    for row in range(3):
        for col in range(3):
            x_center = -1 + col
            y_center = -1 + row
            z_center = -1.5
            
            piece = _create_cube_piece(x_center, y_center, z_center, cube_size,
                                     _face_colour[state[idx]])
            pieces.append(piece)
            idx += 1
    
    # L face pieces (left)
    for row in range(3):
        for col in range(3):
            x_center = -1.5
            y_center = -1 + row
            z_center = 1 - col
            
            piece = _create_cube_piece(x_center, y_center, z_center, cube_size,
                                     _face_colour[state[idx]])
            pieces.append(piece)
            idx += 1
    
    # B face pieces (back)
    for row in range(3):
        for col in range(3):
            x_center = 1 - col
            y_center = -1.5
            z_center = 1 - row
            
            piece = _create_cube_piece(x_center, y_center, z_center, cube_size,
                                     _face_colour[state[idx]])
            pieces.append(piece)
            idx += 1
    
    return pieces


def _create_cube_piece(x, y, z, size, color):
    """Create a small cube piece with given center and color."""
    
    # Define vertices of a cube
    vertices = [
        [x-size/2, y-size/2, z-size/2],  # 0
        [x+size/2, y-size/2, z-size/2],  # 1
        [x+size/2, y+size/2, z-size/2],  # 2
        [x-size/2, y+size/2, z-size/2],  # 3
        [x-size/2, y-size/2, z+size/2],  # 4
        [x+size/2, y-size/2, z+size/2],  # 5
        [x+size/2, y+size/2, z+size/2],  # 6
        [x-size/2, y+size/2, z+size/2],  # 7
    ]
    
    # Define faces (triangles)
    faces = [
        # Bottom face
        [0, 1, 2], [0, 2, 3],
        # Top face  
        [4, 7, 6], [4, 6, 5],
        # Front face
        [0, 4, 5], [0, 5, 1],
        # Back face
        [2, 6, 7], [2, 7, 3],
        # Left face
        [0, 3, 7], [0, 7, 4],
        # Right face
        [1, 5, 6], [1, 6, 2],
    ]
    
    x_coords = [v[0] for v in vertices]
    y_coords = [v[1] for v in vertices]
    z_coords = [v[2] for v in vertices]
    
    i_coords = [f[0] for f in faces]
    j_coords = [f[1] for f in faces]
    k_coords = [f[2] for f in faces]
    
    # Create color array for all faces
    colors = [color] * len(faces)
    
    return {
        'x': x_coords,
        'y': y_coords,
        'z': z_coords,
        'i': i_coords,
        'j': j_coords,
        'k': k_coords,
        'colors': colors
    }


def _get_move_pieces(state: str, move: str):
    """Determine which pieces rotate for a given move."""
    
    # For now, return simplified logic - would need more complex cube analysis
    # to determine exact piece movements
    all_pieces = _generate_cube_pieces(state)
    
    # Simple approximation - return half as rotating, half as static
    mid = len(all_pieces) // 2
    rotating_pieces = all_pieces[:mid]
    static_pieces = all_pieces[mid:]
    
    return rotating_pieces, static_pieces


def _get_rotation_matrix(move: str, progress: float):
    """Get rotation matrix for a move at given progress (0.0 to 1.0)."""
    
    import numpy as np # type: ignore
    
    # Define rotation angles for each move
    angle_map = {
        'U': (0, 0, 90), 'U\'': (0, 0, -90), 'U2': (0, 0, 180),
        'D': (0, 0, -90), 'D\'': (0, 0, 90), 'D2': (0, 0, -180),
        'R': (90, 0, 0), 'R\'': (-90, 0, 0), 'R2': (180, 0, 0),
        'L': (-90, 0, 0), 'L\'': (90, 0, 0), 'L2': (-180, 0, 0),
        'F': (0, 90, 0), 'F\'': (0, -90, 0), 'F2': (0, 180, 0),
        'B': (0, -90, 0), 'B\'': (0, 90, 0), 'B2': (0, -180, 0),
    }
    
    if move not in angle_map:
        return np.eye(3)
    
    angles = angle_map[move]
    # Apply easing for smoother motion
    eased = _ease_in_out(progress)
    # Scale by eased progress
    angles = tuple(angle * eased * np.pi / 180 for angle in angles)
    
    # Create rotation matrix (simplified - would need proper 3D rotation)
    cos_x, sin_x = np.cos(angles[0]), np.sin(angles[0])
    cos_y, sin_y = np.cos(angles[1]), np.sin(angles[1])
    cos_z, sin_z = np.cos(angles[2]), np.sin(angles[2])
    
    Rx = np.array([[1, 0, 0], [0, cos_x, -sin_x], [0, sin_x, cos_x]])
    Ry = np.array([[cos_y, 0, sin_y], [0, 1, 0], [-sin_y, 0, cos_y]])
    Rz = np.array([[cos_z, -sin_z, 0], [sin_z, cos_z, 0], [0, 0, 1]])
    
    return Rz @ Ry @ Rx


def _apply_rotation_to_piece(piece, rotation_matrix):
    """Apply rotation matrix to piece coordinates."""
    
    import numpy as np # type: ignore
    
    # Get coordinates
    coords = np.array([piece['x'], piece['y'], piece['z']])
    
    # Apply rotation
    rotated_coords = rotation_matrix @ coords
    
    return {
        'x': rotated_coords[0].tolist(),
        'y': rotated_coords[1].tolist(),
        'z': rotated_coords[2].tolist()
    }


def _add_cube_pieces_to_figure(fig, state: str, frame_id: int):
    """Add cube pieces as traces to Plotly figure."""
    
    pieces = _generate_cube_pieces(state)
    
    for piece in pieces:
        try:
            import plotly.graph_objects as go # type: ignore
            
            trace = go.Mesh3d(
                x=piece['x'],
                y=piece['y'],
                z=piece['z'],
                i=piece['i'],
                j=piece['j'],
                k=piece['k'],
                facecolor=piece['colors'],
                showscale=False,
                lighting=dict(ambient=0.7, diffuse=0.9, specular=0.1),
                lightposition=dict(x=100, y=200, z=300)
            )
            fig.add_trace(trace)
        except ImportError:
            pass