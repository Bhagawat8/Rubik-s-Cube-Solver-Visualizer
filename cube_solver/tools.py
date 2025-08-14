import random
from builtins import range

try:
    from .facecube import FaceCube
    from .cubiecube import CubieCube
    from .coordcube import CoordCube
    from .color import colors
except ImportError:
    from facecube import FaceCube
    from cubiecube import CubieCube
    from coordcube import CoordCube
    from color import colors


def verify(s):
    """
    Check if the cube definition string s represents a solvable cube.

    @param s is the cube definition string , see {@link Facelet}
    @return 0: Cube is solvable<br>
            -1: There is not exactly one facelet of each colour<br>
            -2: Not all 12 edges exist exactly once<br>
            -3: Flip error: One edge has to be flipped<br>
            -4: Not all 8 corners exist exactly once<br>
            -5: Twist error: One corner has to be twisted<br>
            -6: Parity error: Two corners or two edges have to be exchanged
    """
    count = [0] * 6     # new int[6]
    try:
        for i in range(54):
            assert s[i] in colors
            count[colors[s[i]]] += 1
    except:
        return -1

    for i in range(6):
        if count[i] != 9:
            return -1

    fc = FaceCube(s)
    cc = fc.toCubieCube()

    return cc.verify()


def randomCube():
    """
    Generates a random cube.
    @return A random cube in the string representation. Each cube of the cube space has the same probability.
    """
    cc = CubieCube()
    cc.setFlip(random.randint(0, CoordCube.N_FLIP - 1))
    cc.setTwist(random.randint(0, CoordCube.N_TWIST - 1))
    while True:
        cc.setURFtoDLB(random.randint(0, CoordCube.N_URFtoDLB - 1))
        cc.setURtoBR(random.randint(0, CoordCube.N_URtoBR - 1))

        if (cc.edgeParity() ^ cc.cornerParity()) == 0:
            break
    fc = cc.toFaceCube()
    return fc.to_String()


def randomLastLayerCube():
    """
    Generates a cube with a random last layer.
    @return A cube with a random last layer and otherwise solved facelets in the string representation.
    """
    cc = CubieCube()
    cc.setFlip(random.choice([0, 24, 40, 48, 72, 80, 96, 120]))
    cc.setTwist(random.randint(0, 26))
    while True:
        perms = [0, 624, 3744, 3840, 4344, 4440, 26064, 26160, 26664, 26760,
                 27360, 27984, 30384, 30480, 30984, 31080, 31680, 32304, 35304,
                 35400, 36000, 36624, 39744, 39840]
        cc.setURFtoDLB(random.choice(perms))
        cc.setURtoBR(random.choice(perms))

        if (cc.edgeParity() ^ cc.cornerParity()) == 0:
            break
    fc = cc.toFaceCube()
    return fc.to_String()


def analyze_solution(moves_str: str) -> dict:
    """
    Analyze a solution string and return statistics.
    
    Args:
        moves_str: Space-separated move sequence (e.g., "R U R' U'")
        
    Returns:
        Dictionary with analysis results
    """
    if not moves_str.strip():
        return {"error": "Empty solution"}
    
    moves = moves_str.strip().split()
    analysis = {
        "total_moves": len(moves),
        "face_counts": {"U": 0, "R": 0, "F": 0, "D": 0, "L": 0, "B": 0},
        "quarter_turns": 0,
        "half_turns": 0,
        "counter_turns": 0,
        "efficiency_score": 0,
        "move_pattern": []
    }
    
    for move in moves:
        face = move[0]
        if face in analysis["face_counts"]:
            analysis["face_counts"][face] += 1
        
        # Count turn types
        if len(move) == 1:
            analysis["quarter_turns"] += 1
            analysis["move_pattern"].append("90°")
        elif move.endswith("2"):
            analysis["half_turns"] += 1
            analysis["move_pattern"].append("180°")
        elif move.endswith("'"):
            analysis["counter_turns"] += 1
            analysis["move_pattern"].append("270°")
    
    # Calculate efficiency score (lower is better)
    # Penalty for excessive moves, bonus for balanced face usage
    total_moves = analysis["total_moves"]
    face_variance = sum((count - total_moves/6)**2 for count in analysis["face_counts"].values())
    analysis["efficiency_score"] = total_moves + (face_variance / 10)
    
    # Add move density analysis
    analysis["quarter_turn_ratio"] = analysis["quarter_turns"] / total_moves
    analysis["half_turn_ratio"] = analysis["half_turns"] / total_moves
    
    return analysis


def compare_solutions(solutions: list) -> dict:
    """
    Compare multiple solutions and rank them by quality.
    
    Args:
        solutions: List of solution strings
        
    Returns:
        Dictionary with comparison results
    """
    if not solutions:
        return {"error": "No solutions provided"}
    
    analyses = []
    for i, sol in enumerate(solutions):
        analysis = analyze_solution(sol)
        analysis["solution_index"] = i
        analysis["solution"] = sol
        analyses.append(analysis)
    
    # Sort by efficiency score (lower is better)
    analyses.sort(key=lambda x: x.get("efficiency_score", float('inf')))
    
    return {
        "best_solution": analyses[0],
        "all_analyses": analyses,
        "summary": {
            "shortest": min(a["total_moves"] for a in analyses),
            "longest": max(a["total_moves"] for a in analyses),
            "average": sum(a["total_moves"] for a in analyses) / len(analyses)
        }
    }
