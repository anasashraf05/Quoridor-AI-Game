from src.ai.minimax import Minimax
from src.core.enums import DIFFICULTY


class AIPlayer:
    def __init__(self, player_id, start_position, goal_row, difficulty=DIFFICULTY.MEDIUM):
        """
        Sets up the AI player.
        difficulty controls how many plies deep Minimax searches:
            EASY   -> depth 1  (looks 1 move ahead)
            MEDIUM -> depth 2  (looks 2 moves ahead)
            HARD   -> depth 3  (looks 3 moves ahead)
        """
        self.player_id  = player_id
        self.position   = start_position
        self.walls_left = 10
        self.goal_row   = goal_row
        self.difficulty = difficulty

    def get_action(self, board):
        """
        Called by the GameController when it is the AI's turn.
        Returns an action dict:
            {"type": "move", "pos": (row, col)}
          OR
            {"type": "wall", "wall": <Wall object>}
        """
        depth_map = {
            DIFFICULTY.EASY:   1,
            DIFFICULTY.MEDIUM: 2,
            DIFFICULTY.HARD:   3,
        }
        depth = depth_map.get(self.difficulty, 2)
        return Minimax.get_best_action(board, self.player_id, depth)