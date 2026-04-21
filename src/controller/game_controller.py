from src.core.enums import GameMode
from src.core.player import Player

class GameController:
    def __init__(self, mode = GameMode.PVP):
        """
        Initializes the entire game state.
        mode: "PvP" (Human vs Human) or "PvE" (Human vs AI) [cite: 37, 38]
        """
        # Here you will instantiate your Board, Players, and AI
        self.board = None  
        self.players = []
        self.current_player_index = 0
        self.game_mode = mode
        
        # You will attach your UI window here later so the controller can talk to it
        self.ui = None 

    def start_game(self):
        """
        Resets the board, places pawns in starting positions, and tells the UI to draw.
        """
        # Create Player 1 (top row, middle column) and Player 2 (bottom row, middle column)
        self.players = [
            Player(player_id=1, start_pos=(0, 4), goal_row=8),
            Player(player_id=2, start_pos=(8, 4), goal_row=0)
        ]
        self.current_player_index = 0  # Player 1 goes first

    def handle_pawn_move_attempt(self, target_pos):
        """
        Called by the UI when a human clicks a square to move their pawn.
        1. Checks Rules.is_valid_pawn_move().
        2. If valid, updates Board.
        3. Checks Rules.is_winner()[cite: 12].
        4. If no winner, calls self.end_turn().
        """
        # TODO:
        current_player = self.players[self.current_player_index]
        # if self.Rules.is_valid_pawn_move():
        current_player.position = target_pos
        print(f"Player {current_player.player_id} moved to {target_pos}")

        # 3. Tell the UI to move the visual circle
        self.ui.move_pawn(current_player.player_id, target_pos)

        # 4. End the turn (Switch between 0 and 1)
        self.current_player_index = 1 if self.current_player_index == 0 else 0
        
        # 5. Optional: Update the UI turn label
        self.ui.turnLabel.setText(f"Player {self.current_player_index + 1}'s Turn")

    def handle_wall_placement_attempt(self, x, y, orientation):
        """
        Called by the UI when a human attempts to place a wall.
        1. Checks Rules.is_valid_wall_placement()[cite: 22].
        2. Checks Pathfinder.path_exists() to ensure no one is trapped[cite: 23, 24, 34].
        3. If valid, updates Board, deducts a wall from the player, and calls self.end_turn().
        """
        print("WALLL1!")
        pass

    def end_turn(self):
        """
        Switches current_player_index to the next player.
        If the new player is an AI (in PvE mode), it triggers the AI to calculate its move.
        Finally, tells the UI to update the visuals and turn indicators[cite: 41].
        """
        pass

    def execute_ai_turn(self):
        """
        Asks the AIPlayer for its best move, then automatically executes it 
        (either moving a pawn or placing a wall) and ends the turn.
        """
        pass