from src.core.enums import DIFFICULTY
class AIPlayer:
    def __init__(self, player_id, start_position, goal_row, difficulty = DIFFICULTY.MEDIUM):
        """
        Sets up the AI player. 
        Bonus feature: You can pass in different difficulty levels here!
        """
        self.player_id = player_id
        self.position = start_position
        self.walls_left = 10
        self.goal_row = goal_row
        self.difficulty = difficulty 

    def get_action(self, board):
        """
        The main method called by the GameController when it's the AI's turn.
        Depending on self.difficulty, it asks the Minimax algorithm for the best move.
        Returns a dictionary or tuple representing the chosen action 
        (e.g., {"type": "move", "pos": (4, 5)} OR {"type": "wall", "wall": Wall_Object}).
        """
        pass