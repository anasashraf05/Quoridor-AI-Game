import copy
from src.core.rules import Rules
from src.core.wall import Wall
from src.core.enums import Orientation


class Minimax:
    """
    Minimax with Alpha-Beta pruning for Quoridor AI.
    Scores are from the AI's perspective: higher = better for AI.
    """

    # Cap wall placements we consider per turn to keep search tractable
    MAX_WALLS_PER_NODE = 10

    @staticmethod
    def get_best_action(board, players, ai_player_id, human_player_id, depth):
        """
        Entry point. Returns the best action dict:
          {"type": "move", "pos": (r, c)}
          {"type": "wall", "wall": Wall}
        """
        best_score = float('-inf')
        best_action = None
        alpha = float('-inf')
        beta = float('inf')

        actions = Minimax.get_all_legal_actions(board, players, ai_player_id)

        for action in actions:
            new_board, new_players = Minimax._apply_action(board, players, action, ai_player_id)
            score = Minimax._minimax(
                new_board, new_players, depth - 1, alpha, beta,
                False, ai_player_id, human_player_id
            )
            if score > best_score:
                best_score = score
                best_action = action
            alpha = max(alpha, best_score)

        return best_action

    @staticmethod
    def _minimax(board, players, depth, alpha, beta, is_maximizing, ai_player_id, human_player_id):
        from src.ai.evaluation import Evaluation as Evaluator

        # Terminal / depth check
        ai_player = next(p for p in players if p.player_id == ai_player_id)
        human_player = next(p for p in players if p.player_id == human_player_id)

        if ai_player.position[0] == ai_player.goal_row:
            return Evaluator.TRAPPED_PENALTY  # AI won
        if human_player.position[0] == human_player.goal_row:
            return -Evaluator.TRAPPED_PENALTY  # Human won
        if depth == 0:
            return Evaluator.evaluate_board(board, players, ai_player_id, human_player_id)

        current_player_id = ai_player_id if is_maximizing else human_player_id
        actions = Minimax.get_all_legal_actions(board, players, current_player_id)

        if not actions:
            return Evaluator.evaluate_board(board, players, ai_player_id, human_player_id)

        if is_maximizing:
            max_eval = float('-inf')
            for action in actions:
                new_board, new_players = Minimax._apply_action(board, players, action, current_player_id)
                score = Minimax._minimax(new_board, new_players, depth - 1, alpha, beta,
                                         False, ai_player_id, human_player_id)
                max_eval = max(max_eval, score)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for action in actions:
                new_board, new_players = Minimax._apply_action(board, players, action, current_player_id)
                score = Minimax._minimax(new_board, new_players, depth - 1, alpha, beta,
                                         True, ai_player_id, human_player_id)
                min_eval = min(min_eval, score)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_eval

    @staticmethod
    def _apply_action(board, players, action, player_id):
        """Returns a deep-copied (board, players) with the action applied."""
        new_board = copy.deepcopy(board)
        new_players = copy.deepcopy(players)
        player = next(p for p in new_players if p.player_id == player_id)

        if action["type"] == "move":
            player.position = action["pos"]
            new_board.move_pawn(player_id, action["pos"])
        elif action["type"] == "wall":
            w = action["wall"]
            new_board.place_wall(w)
            player.use_wall()

        return new_board, new_players

    @staticmethod
    def get_all_legal_actions(board, players, player_id):
        """
        Returns all legal pawn moves + a pruned set of wall placements.
        Wall placements are sorted by heuristic value and capped to avoid explosion.
        """
        player = next(p for p in players if p.player_id == player_id)
        actions = []

        # --- Pawn moves ---
        r, c = player.position
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                target = (r + dr, c + dc)
                if Rules.is_valid_pawn_move(board, player.position, target):
                    actions.append({"type": "move", "pos": target})

        # --- Wall placements (only if player has walls) ---
        if player.walls_left > 0:
            wall_actions = []
            for row in range(1, 9):
                for col in range(1, 9):
                    for orient in (Orientation.HORIZONTAL, Orientation.VERTICAL):
                        w = Wall(row, col, orient)
                        if Rules.is_valid_wall_placement(board, w):
                            wall_actions.append({"type": "wall", "wall": w})

            # Heuristic sort: prioritise walls near the human player (more impactful)
            human_player = next(p for p in players if p.player_id != player_id)
            hr, hc = human_player.position

            def wall_priority(wa):
                w = wa["wall"]
                return abs(w.row - hr) + abs(w.col - hc)

            wall_actions.sort(key=wall_priority)
            actions.extend(wall_actions[:Minimax.MAX_WALLS_PER_NODE])

        return actions