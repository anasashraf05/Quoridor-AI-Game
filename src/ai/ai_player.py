import random
from src.core.enums import DIFFICULTY
from src.ai.minimax import Minimax


class AIPlayer:
    """
    Wraps the Minimax engine and exposes difficulty-based search depths.

    Easy   → depth 1  (looks 1 ply ahead, mostly greedy)
    Medium → depth 2  (looks 2 plies ahead)
    Hard   → depth 3  (looks 3 plies ahead, strong play)
    """

    DEPTH_MAP = {
        DIFFICULTY.EASY:   1,
        DIFFICULTY.MEDIUM: 2,
        DIFFICULTY.HARD:   3,
    }

    # On Easy, the AI makes a random move this fraction of the time
    EASY_RANDOM_CHANCE = 0.4

    def __init__(self, player_id, start_position, goal_row, difficulty=DIFFICULTY.MEDIUM):
        self.player_id    = player_id
        self.position     = start_position
        self.walls_left   = 10
        self.goal_row     = goal_row
        self.difficulty   = difficulty

    # ------------------------------------------------------------------ #
    #  Required by Player protocol
    # ------------------------------------------------------------------ #
    def has_walls_left(self):
        return self.walls_left > 0

    def use_wall(self):
        self.walls_left -= 1

    # ------------------------------------------------------------------ #
    #  Main interface called by GameController
    # ------------------------------------------------------------------ #
    def get_action(self, board, players):
        """
        Returns the best action for the current board state.
        Action format:
            {"type": "move", "pos": (row, col)}
            {"type": "wall", "wall": Wall}
        """
        depth = self.DEPTH_MAP.get(self.difficulty, 2)

        # Easy mode: sometimes play randomly to feel beatable
        if self.difficulty == DIFFICULTY.EASY and random.random() < self.EASY_RANDOM_CHANCE:
            actions = Minimax.get_all_legal_actions(board, players, self.player_id)
            move_actions = [a for a in actions if a["type"] == "move"]
            if move_actions:
                return random.choice(move_actions)

        human_player_id = next(p.player_id for p in players if p.player_id != self.player_id)

        return Minimax.get_best_action(
            board, players, self.player_id, human_player_id, depth
        )