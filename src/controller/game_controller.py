from src.core.enums import GameMode
from src.core.board import Board
from src.core.player import Player
from src.core.rules import Rules
from src.core.wall import Wall
from src.ai.ai_player import AIPlayer
from src.core.enums import DIFFICULTY


class GameController:
    def __init__(self, mode=GameMode.PVP):
        """
        Initializes the game controller.
        mode: GameMode.PVP (Human vs Human) or GameMode.PVE (Human vs AI)
        """
        self.board                 = None
        self.players               = []
        self.current_player_index  = 0
        self.game_mode             = mode
        self.ai_player             = None
        self.ui                    = None

    def start_game(self):
        """
        Resets the board, places pawns in starting positions, and creates the AI
        player if running in PvE mode.
        """
        self.board = Board()

        # Player 1 starts at row 1 (top), goal is row 9 (bottom)
        # Player 2 starts at row 9 (bottom), goal is row 1 (top)
        self.players = [
            Player(player_id=1, start_pos=(1, 5), goal_row=9),
            Player(player_id=2, start_pos=(9, 5), goal_row=1),
        ]

        self.board.move_pawn(1, (1, 5))
        self.board.move_pawn(2, (9, 5))
        self.current_player_index = 0

        # Create AI for Player 2 in PvE mode
        if self.game_mode == GameMode.PVE:
            self.ai_player = AIPlayer(
                player_id=2,
                start_position=(9, 5),
                goal_row=1,
                difficulty=DIFFICULTY.MEDIUM,
            )

    # ------------------------------------------------------------------
    # Pawn move
    # ------------------------------------------------------------------

    def handle_pawn_move_attempt(self, target_pos):
        """
        Called by the UI when a human clicks a square to move their pawn.
        Validates the move, updates the board, checks for a winner, then ends the turn.
        """
        current_player = self.players[self.current_player_index]

        if Rules.is_valid_pawn_move(self.board, current_player.position, target_pos):
            # Update game state
            current_player.position = target_pos
            self.board.move_pawn(current_player.player_id, target_pos)

            # Update UI visuals
            self.ui.move_pawn(current_player.player_id, target_pos)

            # Check for winner before switching turns
            if Rules.is_winner(current_player):
                self.ui.show_winner(current_player.player_id)
                return

            self.end_turn()
        else:
            print(f"ILLEGAL MOVE: {current_player.player_id} cannot move to {target_pos}")

    # ------------------------------------------------------------------
    # Wall placement
    # ------------------------------------------------------------------

    def handle_wall_placement_attempt(self, x, y, orientation):
        """
        Called by the UI when a human attempts to place a wall.
        Validates the placement, updates the board, deducts a wall, then ends the turn.
        """
        current_player = self.players[self.current_player_index]

        if not current_player.has_walls_left():
            print(f"Player {current_player.player_id} has no walls left!")
            return

        new_wall = Wall(x, y, orientation)

        if Rules.is_valid_wall_placement(self.board, new_wall):
            self.board.place_wall(new_wall)
            current_player.use_wall()
            self.ui.place_wall_visually(new_wall.row, new_wall.col, orientation)
            self.end_turn()
        else:
            print(f"ILLEGAL WALL: Player {current_player.player_id} at ({x},{y}) {orientation}")

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    def end_turn(self):
        """
        Switches to the next player.
        If the next player is the AI (PvE mode), triggers the AI move.
        """
        self.current_player_index = 1 if self.current_player_index == 0 else 0
        current = self.players[self.current_player_index]

        # Tell the UI to update the turn label and wall counts
        self.ui.update_turn_label(current.player_id)
        self.ui.update_wall_counts(self.players)

        # Trigger AI if it is now the AI's turn
        if self.game_mode == GameMode.PVE and current.player_id == 2:
            self.execute_ai_turn()

    def execute_ai_turn(self):
        """
        Asks the AIPlayer for its best action, then executes it automatically.
        Runs in a background thread so the UI stays responsive while the AI thinks.
        """
        import threading

        def run():
            action = self.ai_player.get_action(self.board)
            if action is None:
                print("AI has no valid action — skipping turn.")
                return
            if action["type"] == "move":
                self.handle_pawn_move_attempt(action["pos"])
            else:
                w = action["wall"]
                self.handle_wall_placement_attempt(w.row, w.col, w.orientation)

        threading.Thread(target=run, daemon=True).start()