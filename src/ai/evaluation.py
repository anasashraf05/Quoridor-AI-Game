from src.core.pathfinder import Pathfinder


class Evaluation:
    PATH_WEIGHT = 10.0      # Distance to goal is the strongest signal
    WALL_WEIGHT = 0.5       # Walls in hand = future flexibility
    MOBILITY_WEIGHT = 0.2   # How many moves are available
    TRAPPED_PENALTY = 100000.0

    @staticmethod
    def evaluate_board(board, players, ai_player_id, human_player_id):
        """
        Evaluates from the AI's perspective.
        Positive  → AI is winning.
        Negative  → Human is winning.
        """
        ai_player    = next(p for p in players if p.player_id == ai_player_id)
        human_player = next(p for p in players if p.player_id == human_player_id)

        ai_pos    = ai_player.position
        human_pos = human_player.position

        ai_goal_row    = ai_player.goal_row
        human_goal_row = human_player.goal_row

        # Win / loss terminal checks
        if ai_pos[0] == ai_goal_row:
            return Evaluation.TRAPPED_PENALTY
        if human_pos[0] == human_goal_row:
            return -Evaluation.TRAPPED_PENALTY

        ai_dist    = Pathfinder.get_shortest_path_length(board, ai_pos, ai_goal_row)
        human_dist = Pathfinder.get_shortest_path_length(board, human_pos, human_goal_row)

        # Handle trapped states
        if ai_dist == float('inf') and human_dist == float('inf'):
            return 0.0
        if ai_dist == float('inf'):
            return -Evaluation.TRAPPED_PENALTY
        if human_dist == float('inf'):
            return Evaluation.TRAPPED_PENALTY

        # Primary: distance advantage (fewer steps = better)
        path_score = (human_dist - ai_dist) * Evaluation.PATH_WEIGHT

        # Secondary: wall count advantage
        ai_walls    = ai_player.walls_left
        human_walls = human_player.walls_left
        wall_score  = (ai_walls - human_walls) * Evaluation.WALL_WEIGHT

        # Tertiary: mobility (reachable squares in one step)
        ai_mobility    = len(Pathfinder.get_neighbors(board, ai_pos))
        human_mobility = len(Pathfinder.get_neighbors(board, human_pos))
        mobility_score = (ai_mobility - human_mobility) * Evaluation.MOBILITY_WEIGHT

        return path_score + wall_score + mobility_score