from src.core.pathfinder import Pathfinder


class Evaluation:
    # Optimized weights for depth=2 minimax
    # Path distance is critical; mobility and walls support tactical decisions
    PATH_WEIGHT = 12.0      # Distance to goal (stronger for depth 2)
    WALL_WEIGHT = 1.0       # Wall advantage (better tuned for depth 2)
    MOBILITY_WEIGHT = 0.5   # Tactical flexibility in moves
    TRAPPED_PENALTY = 100000.0

    @staticmethod
    def evaluate_board(board, players, ai_player_id, human_player_id):
        """
        Evaluates from the AI's perspective for depth=2 minimax.
        Positive  → AI is winning.
        Negative  → Human is winning.
        
        At depth 2, we look 2 plies ahead (AI move + human response),
        so evaluation factors in both immediate advantage and position after opponent's best move.
        """
        ai_player    = next(p for p in players if p.player_id == ai_player_id)
        human_player = next(p for p in players if p.player_id == human_player_id)

        ai_pos    = ai_player.position
        human_pos = human_player.position

        ai_goal_row    = ai_player.goal_row
        human_goal_row = human_player.goal_row

        # Win / loss terminal checks (highest priority)
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
        # Bonus: if player is very close to goal (2-3 moves), boost urgency
        path_score = (human_dist - ai_dist) * Evaluation.PATH_WEIGHT
        
        # Endgame bonus: if AI is close to winning, heavily reward it
        if ai_dist <= 3:
            path_score += (3 - ai_dist) * 2.0  # Bonus for being very close
        # Defensive bonus: if opponent is close to winning, heavily penalize it
        if human_dist <= 3:
            path_score -= (3 - human_dist) * 2.0  # Penalty for opponent being close

        # Secondary: wall count advantage (more important at depth 2)
        ai_walls    = ai_player.walls_left
        human_walls = human_player.walls_left
        wall_score  = (ai_walls - human_walls) * Evaluation.WALL_WEIGHT

        # Tertiary: mobility (reachable squares in one step)
        # Tactical significance: more moves = more options to respond to threats
        ai_mobility    = len(Pathfinder.get_neighbors(board, ai_pos))
        human_mobility = len(Pathfinder.get_neighbors(board, human_pos))
        mobility_score = (ai_mobility - human_mobility) * Evaluation.MOBILITY_WEIGHT

        return path_score + wall_score + mobility_score