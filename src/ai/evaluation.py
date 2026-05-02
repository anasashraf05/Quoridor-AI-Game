from src.core.pathfinder import Pathfinder  

class Evaluator:
    PATH_WEIGHT = 1.0
    WALL_WEIGHT = 0.5
    MOBILITY_WEIGHT = 0.2
    TRAPPED_PENALTY = 10000.0

    @staticmethod
    def evaluate_board(board, ai_player_id, human_player_id):
        """
        Evaluates the current board state from the AI's perspective.
        Positive score = AI is winning. Negative score = Human is winning.
        """
        # 1. Get current positions and goals
        ai_pos = board.position(ai_player_id)
        human_pos = board.position(human_player_id)
        
        ai_goal_row = board.goal_row(ai_player_id)   
        human_goal_row = board.goal_row(human_player_id) 

        # 2. Calculate shortest paths using Pathfinder
        ai_dist = Pathfinder.get_shortest_path_length(board, ai_pos, ai_goal_row)
        human_dist = Pathfinder.get_shortest_path_length(board, human_pos, human_goal_row)

        # 3. Handle trapped states (paths blocked completely) and this should not happen as if there no path exist the wall placement should be invalid but just in case we will give it a score
        if ai_dist == float('inf') and human_dist == float('inf'):
            return 0.0  # Both trapped (draw/deadlock)
        if ai_dist == float('inf'):
            return -Evaluator.TRAPPED_PENALTY  # AI trapped this means massive loss
        if human_dist == float('inf'):
            return Evaluator.TRAPPED_PENALTY   # Human trapped this means massive win

        # 4. Primary heuristic: Race distance difference
        # If human_dist > ai_dist, AI is closer so positive score
        path_score = (human_dist - ai_dist) * Evaluator.PATH_WEIGHT

        # 5. Secondary heuristic: Wall advantage
        # More walls = better ability to block or create alternate routes
        ai_walls = board.walls_left(ai_player_id)
        human_walls = board.walls_left(human_player_id)
        wall_score = (ai_walls - human_walls) * Evaluator.WALL_WEIGHT

        # 6. Tertiary heuristic: Mobility / Central control
        # More valid moves = less likely to be cornered, more flexibility
        ai_mobility = len(Pathfinder.get_neighbors(board, ai_pos))
        human_mobility = len(Pathfinder.get_neighbors(board, human_pos))
        mobility_score = (ai_mobility - human_mobility) * Evaluator.MOBILITY_WEIGHT

        # 7. Combine scores
        return path_score + wall_score + mobility_score