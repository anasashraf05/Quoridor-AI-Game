class Board:
    def __init__(self):
        """Initializes the 9x9 grid, empty wall list, and player locations."""
        pass

    def move_pawn(self, player_id, new_position):
        """Updates the position of a specific player's pawn."""
        pass

    def place_wall(self, wall):
        """Adds a Wall object to the board's list of placed walls."""
        pass

    def get_pawn_position(self, player_id):
        """Returns the current (x, y) coordinates of the requested player."""
        pass

    def get_all_walls(self):
        """Returns a list of all currently placed walls on the board."""
        pass

    def clone(self):
        """Creates a deep copy of the board state (super useful for the AI later)."""
        pass