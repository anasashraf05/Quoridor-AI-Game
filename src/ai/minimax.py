from src.core.rules import Rules
from src.core.wall import Wall
from src.core.enums import Orientation
from src.ai.evaluation import Evaluator


class Minimax:
    @staticmethod
    def get_all_legal_actions(board, player_id):
        """
        Generates every legal action for the given player:
        - All valid pawn moves (orthogonal, straight jumps, diagonal jumps)
        - All valid wall placements (if the player has walls left — checked by caller)
        """
        actions = []
        pos = board.get_pawn_position(player_id)

        # All candidate pawn move offsets (orthogonal steps, straight jumps, diagonal jumps)
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1),
                       (-2, 0), (2, 0), (0, -2), (0, 2),
                       (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            target = (pos[0] + dr, pos[1] + dc)
            if Rules.is_valid_pawn_move(board, pos, target):
                actions.append({"type": "move", "pos": target})

        # All candidate wall placements (anchor rows/cols 1–8)
        for r in range(1, 9):
            for c in range(1, 9):
                for orientation in [Orientation.HORIZONTAL, Orientation.VERTICAL]:
                    wall = Wall(r, c, orientation)
                    if Rules.is_valid_wall_placement(board, wall):
                        actions.append({"type": "wall", "wall": wall})

        return actions

    @staticmethod
    def minimax(board, depth, alpha, beta, is_maximizing, ai_id, human_id):
        """
        Recursive Minimax with Alpha-Beta pruning.

        depth          -- how many plies left to search
        alpha          -- best score the maximiser can guarantee so far
        beta           -- best score the minimiser can guarantee so far
        is_maximizing  -- True when it is the AI's turn
        """
        # Terminal checks — build lightweight proxy objects for is_winner
        ai_proxy    = _PlayerProxy(board.get_pawn_position(ai_id),    1)
        human_proxy = _PlayerProxy(board.get_pawn_position(human_id), 9)

        if Rules.is_winner(ai_proxy):
            return 1000 + depth   # win sooner = better
        if Rules.is_winner(human_proxy):
            return -1000 - depth  # lose later = better

        if depth == 0:
            return Evaluator.evaluate_board(board, ai_id, human_id)

        current_id = ai_id if is_maximizing else human_id
        actions    = Minimax.get_all_legal_actions(board, current_id)

        if not actions:
            # No moves available — evaluate as-is
            return Evaluator.evaluate_board(board, ai_id, human_id)

        if is_maximizing:
            best = float('-inf')
            for action in actions:
                clone = board.clone()
                if action["type"] == "move":
                    clone.move_pawn(current_id, action["pos"])
                else:
                    clone.walls.append(action["wall"])
                score = Minimax.minimax(clone, depth - 1, alpha, beta, False, ai_id, human_id)
                best  = max(best, score)
                alpha = max(alpha, best)
                if beta <= alpha:
                    break   # prune
            return best
        else:
            best = float('inf')
            for action in actions:
                clone = board.clone()
                if action["type"] == "move":
                    clone.move_pawn(current_id, action["pos"])
                else:
                    clone.walls.append(action["wall"])
                score = Minimax.minimax(clone, depth - 1, alpha, beta, True, ai_id, human_id)
                best  = min(best, score)
                beta  = min(beta, best)
                if beta <= alpha:
                    break   # prune
            return best

    @staticmethod
    def get_best_action(board, ai_player_id, depth):
        """
        Entry point: searches all legal actions to depth plies and returns
        the action dict with the highest minimax score.
        """
        human_id   = 1 if ai_player_id == 2 else 2
        best_score = float('-inf')
        best_action = None

        for action in Minimax.get_all_legal_actions(board, ai_player_id):
            clone = board.clone()
            if action["type"] == "move":
                clone.move_pawn(ai_player_id, action["pos"])
            else:
                clone.walls.append(action["wall"])

            score = Minimax.minimax(
                clone, depth - 1,
                float('-inf'), float('inf'),
                False, ai_player_id, human_id
            )
            if score > best_score:
                best_score  = score
                best_action = action

        return best_action


# ---------------------------------------------------------------------------
# Tiny helper so we can call Rules.is_winner() without a real Player object
# ---------------------------------------------------------------------------
class _PlayerProxy:
    def __init__(self, position, goal_row):
        self.position = position
        self.goal_row = goal_row