from src.core.enums import Orientation
from src.core.wall import Wall


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
        """Returns the current (row, col) coordinates of the requested player."""
        return self.pawn_positions[player_id]

    def get_all_walls(self):
        """Returns a list of all currently placed walls on the board."""
        return self.walls

    def has_wall_between(self, pos1, pos2):
        """
        Checks if a placed wall physically blocks the path between pos1 and pos2.
        pos1 and pos2 are tuples like (row, col).
        """
        attempted_edge_1 = (pos1, pos2)
        attempted_edge_2 = (pos2, pos1)

        for wall in self.walls:
            blocked_edges = wall.get_blocked_edges()
            if attempted_edge_1 in blocked_edges or attempted_edge_2 in blocked_edges:
                return True

        return False

    def is_diagonal_path_blocked(self, opponent_pos, diagonal_target):
        """
        Checks if a diagonal jump from opponent_pos to diagonal_target is blocked.
        """
        opp_r, opp_c = opponent_pos
        tgt_r, tgt_c = diagonal_target

        corner1 = (opp_r, tgt_c)
        corner2 = (tgt_r, opp_c)

        return (self.has_wall_between(opponent_pos, corner1) or
                self.has_wall_between(opponent_pos, corner2))

    def clone(self):
        """Creates a deep copy of the board state for use by the AI."""
        new_board = Board()
        new_board.pawn_positions = dict(self.pawn_positions)
        # Wall objects are never mutated after placement, so a shallow copy is safe
        new_board.walls = list(self.walls)
        return new_board