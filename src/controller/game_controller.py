from src.core.enums import GameMode
from src.core.board import Board
from src.core.player import Player
from src.core.rules import Rules
from src.core.wall import Wall

class GameController:
    def __init__(self, mode = GameMode.PVP):
        """
        Initializes the entire game state.
        mode: "PvP" (Human vs Human) or "PvE" (Human vs AI)
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
        # 1. Create the physical board
        self.board = Board()
        
        # 2. Create Player 1 (top row, middle column) and Player 2 (bottom row, middle column)
        self.players = [
            Player(player_id=1, start_pos=(1, 5), goal_row=9),
            Player(player_id=2, start_pos=(9, 5), goal_row=1)
        ]
        
        # 3. Tell the board where the players are starting
        self.board.move_pawn(1, (1, 5))
        self.board.move_pawn(2, (9, 5))
        
        self.current_player_index = 0
        

    def handle_pawn_move_attempt(self, target_pos):
        """
        Called by the UI when a human clicks a square to move their pawn.
        1. Checks Rules.is_valid_pawn_move().
        2. If valid, updates Board.
        3. Checks Rules.is_winner()[cite: 12].
        4. If no winner, calls self.end_turn().
        """
        current_player = self.players[self.current_player_index]
        
        # 1. THE REFEREE CHECK: Pass the board, the start, and the target!
        if Rules.is_valid_pawn_move(self.board, current_player.position, target_pos):
            
            # 2. If valid, update the core rules and board
            current_player.position = target_pos
            self.board.move_pawn(current_player.player_id, target_pos)
            print(f"Player {current_player.player_id} legally moved to {target_pos}")
            
            # 3. Update the UI
            self.ui.move_pawn(current_player.player_id, target_pos)

            # 4. End the turn
            self.current_player_index = 1 if self.current_player_index == 0 else 0  # use end_turn method
            self.ui.turnLabel.setText(f"Player {self.current_player_index + 1}'s Turn")
            
        else:
            print(f"ILLEGAL MOVE: Blocked by rules!")

    def handle_wall_placement_attempt(self, x, y, orientation):
        """
        Called by the UI when a human attempts to place a wall.
        1. Checks if current player has walls left.
        2. Checks Rules.is_valid_wall_placement().
        3. If valid, updates Board, deducts a wall from the player, and calls self.end_turn().
        """
        current_player = self.players[self.current_player_index]
        # 1. Make sure they actually have walls left!
        if not current_player.has_walls_left():
            print(f"Player {current_player.player_id} is out of walls!")
            return
        
        new_wall = Wall(x, y, orientation)
        
        if(Rules.is_valid_wall_placement(self.board, new_wall)):
            self.board.place_wall(new_wall)
            current_player.use_wall()
            print(f"Player {current_player.player_id} legally placed wall at ({new_wall.row, new_wall.col})")
            self.ui.place_wall_visually(new_wall.row, new_wall.col, orientation)
            # 5. End the turn
            self.current_player_index = 1 if self.current_player_index == 0 else 0      # use end_turn method
            self.ui.turnLabel.setText(f"Player {self.current_player_index + 1}'s Turn")
        else:
            print("ILLEGAL WALL ATTEMPT: Blocked by rules")
        

    def end_turn(self):
        """
        Switches current_player_index to the next player.
        If the new player is an AI (in PvE mode), it triggers the AI to calculate its move.
        Finally, tells the UI to update the visuals and turn indicators.
        """
        pass

    def execute_ai_turn(self):
        """
        Asks the AIPlayer for its best move, then automatically executes it 
        (either moving a pawn or placing a wall) and ends the turn.
        """
        pass