import math

def get_turn(prev, curr, nxt):
    a1 = math.atan2(curr[1]-prev[1], curr[0]-prev[0])
    a2 = math.atan2(nxt[1]-curr[1], nxt[0]-curr[0])
    diff = math.degrees(a2 - a1)

    if -30 < diff < 30:
        return "Go straight"
    elif diff > 30:
        return "Turn right"
    else:
        return "Turn left"

def distance(p1, p2):
    """
    Calculate Euclidean distance between two (x, y) points
    """
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)