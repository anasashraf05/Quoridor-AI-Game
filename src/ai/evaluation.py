class Evaluator:
    @staticmethod
    def evaluate_board(board, ai_player_id, human_player_id):
        """
        Assigns a numerical score to a specific board layout.
        A positive score means the AI is winning. A negative score means the Human is winning.
        
        Standard Quoridor Strategy:
        AI Shortest Path = Pathfinder.get_shortest_path_length(board, ai_pos, ai_goal)
        Human Shortest Path = Pathfinder.get_shortest_path_length(board, human_pos, human_goal)
        
        Score = (Human Shortest Path) - (AI Shortest Path)
        """
        pass