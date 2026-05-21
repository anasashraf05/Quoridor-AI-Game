from src.core.pathfinder import Pathfinder


class Evaluator:
    @staticmethod
    def evaluate_board(board, ai_player_id, human_player_id):
        """
        Assigns a numerical score to a board layout.
        Positive = AI is winning. Negative = Human is winning.

        Strategy:
            Score = (Human's shortest path to goal) - (AI's shortest path to goal)

        A higher score means the AI is closer to winning relative to the human.
        """
        ai_pos    = board.get_pawn_position(ai_player_id)
        human_pos = board.get_pawn_position(human_player_id)

        # AI is always player 2, goal row = 1
        # Human is always player 1, goal row = 9
        ai_dist    = Pathfinder.get_shortest_path_length(board, ai_pos, 1)
        human_dist = Pathfinder.get_shortest_path_length(board, human_pos, 9)

        return human_dist - ai_dist