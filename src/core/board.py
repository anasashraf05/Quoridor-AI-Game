from src.core.enums import Orientation

class Board:
    def __init__(self):
        """Initializes the 9x9 grid, empty wall list, and player locations."""
        self.grid_size = 9
        self.walls = []
        self.pawn_positions = {}

    def move_pawn(self, player_id, new_position):
        """Updates the position of a specific player's pawn."""
        self.pawn_positions[player_id] = new_position

    def place_wall(self, wall):
        """Adds a Wall object to the board's list of placed walls."""
        self.walls.append(wall)

    def get_pawn_position(self, player_id):
        """Returns the current (x, y) coordinates of the requested player."""
        return self.pawn_positions[player_id]

    def get_all_walls(self):
        """Returns a list of all currently placed walls on the board."""
        return self.walls
    
    # TODO: NOT TESTED YET
    def has_wall_between(self, pos1, pos2):
        """
        Checks if a placed wall physically blocks the path between pos1 and pos2.
        pos1 and pos2 are tuples like (row, col).
        """
        r1, c1 = pos1
        r2, c2 = pos2

        for wall in self.walls:
            # Check for HORIZONTAL walls blocking a vertical move
            if wall.orientation == Orientation.HORIZONTAL:
                # A horizontal wall at (row, col) blocks (row, col) to (row+1, col) 
                # AND it blocks (row, col+1) to (row+1, col+1) because it spans two squares!
                if (r1 == wall.row and r2 == wall.row + 1) or (r2 == wall.row and r1 == wall.row + 1):
                    if c1 == wall.col or c1 == wall.col + 1:
                        if c1 == c2: # Ensure it's actually a straight vertical move
                            return True

            # Check for VERTICAL walls blocking a horizontal move
            elif wall.orientation == Orientation.VERTICAL:
                # A vertical wall at (row, col) blocks (row, col) to (row, col+1)
                # AND it blocks (row+1, col) to (row+1, col+1)
                if (c1 == wall.col and c2 == wall.col + 1) or (c2 == wall.col and c1 == wall.col + 1):
                    if r1 == wall.row or r1 == wall.row + 1:
                        if r1 == r2: # Ensure it's actually a straight horizontal move
                            return True

        # If we check every wall and none of them block the path, the way is clear!
        return False
    
    # TODO:
    def clone(self):
        """Creates a deep copy of the board state (super useful for the AI later)."""
        pass