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
        attempted_edge_1 = (pos1, pos2)
        attempted_edge_2 = (pos2, pos1)

        for wall in self.walls:
            blocked_edges = wall.get_blocked_edges()
            # If the player's path matches the wall's blocked path, stop them!
            if attempted_edge_1 in blocked_edges or attempted_edge_2 in blocked_edges:
                return True
            
        # If we check every wall and none of them block the path, the way is clear!
        return False
    
    def is_diagonal_path_blocked(self, opponent_pos, diagonal_target):
        """
        Checks if a diagonal jump from opponent_pos to diagonal_target is blocked.
        A diagonal jump is blocked
        """
        opp_r, opp_c = opponent_pos
        tgt_r, tgt_c = diagonal_target
    
        corner1 = (opp_r, tgt_c)  # 2 horizontal adjacent pawns
        corner2 = (tgt_r, opp_c)  # 2 vertical adjacent pawns
    
        # If either edge has a wall, the diagonal path is blocked
        return (self.has_wall_between(opponent_pos, corner1) or 
            self.has_wall_between(opponent_pos, corner2))
    
    # TODO:
    def clone(self):
        """Creates a deep copy of the board state (super useful for the AI later).""" 
        pass