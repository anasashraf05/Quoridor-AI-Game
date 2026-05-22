import copy
import json
import os

from src.core.enums import GameMode, DIFFICULTY
from src.core.board import Board
from src.core.player import Player
from src.core.rules import Rules
from src.core.wall import Wall
from src.ai.ai_player import AIPlayer
from src.core.enums import Orientation


SAVE_FILE = "quoridor_save.json"


class GameController:
    def __init__(self, mode=GameMode.PVP, ai_difficulty=DIFFICULTY.MEDIUM):
        self.board                = None
        self.players              = []
        self.current_player_index = 0
        self.game_mode            = mode
        self.ai_difficulty        = ai_difficulty
        self.ui                   = None
        self.game_over            = False

        # Undo / Redo stacks — each entry is a deep snapshot
        self._undo_stack = []
        self._redo_stack = []

    # ------------------------------------------------------------------ #
    #  Game lifecycle
    # ------------------------------------------------------------------ #

    def start_game(self):
        self.board = Board()
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.game_over            = False
        self.current_player_index = 0

        if self.game_mode == GameMode.PVP:
            self.players = [
                Player(player_id=1, start_pos=(1, 5), goal_row=9),
                Player(player_id=2, start_pos=(9, 5), goal_row=1),
            ]
        else:  # PvE
            self.players = [
                Player(player_id=1, start_pos=(1, 5), goal_row=9),
                AIPlayer(player_id=2, start_position=(9, 5), goal_row=1,
                         difficulty=self.ai_difficulty),
            ]

        self.board.move_pawn(1, (1, 5))
        self.board.move_pawn(2, (9, 5))

        if self.ui:
            self.ui.update_walls_left_display()
            if hasattr(self.ui, "update_turn_label"):
                self.ui.update_turn_label(1)

        self.update_move_highlights()

    def reset_game(self):
        """Restart safely — wired to the Restart button."""
        if not self.ui:
            return

        if hasattr(self.ui, "revert_timer"):
            self.ui.revert_timer.stop()
        if hasattr(self.ui, "_revert_invalid_wall"):
            self.ui._revert_invalid_wall()

        if hasattr(self.ui, "reset_board_visuals"):
            self.ui.reset_board_visuals()

        # Reset logic
        self.start_game()

    # ------------------------------------------------------------------ #
    #  Snapshot helpers (undo / redo)
    # ------------------------------------------------------------------ #

    def _snapshot(self):
        return {
            "board":   copy.deepcopy(self.board),
            "players": copy.deepcopy(self.players),
            "index":   self.current_player_index,
        }

    def _restore(self, snapshot):
        self.board                = snapshot["board"]
        self.players              = snapshot["players"]
        self.current_player_index = snapshot["index"]
        self.game_over            = False

    def undo(self):
        if not self._undo_stack:
            return
        self._redo_stack.append(self._snapshot())
        self._restore(self._undo_stack.pop())
        self._refresh_ui_after_state_change()

    def redo(self):
        if not self._redo_stack:
            return
        self._undo_stack.append(self._snapshot())
        self._restore(self._redo_stack.pop())
        self._refresh_ui_after_state_change()

    def _refresh_ui_after_state_change(self):
        if not self.ui:
            return
        self.ui.reset_board_visuals()
        for w in self.board.walls:
            self.ui.place_wall_visually(w.row, w.col, w.orientation)
        for p in self.players:
            self.ui.move_pawn(p.player_id, p.position)
        self.ui.update_walls_left_display()
        if hasattr(self.ui, "update_turn_label"):
            self.ui.update_turn_label(self.current_player_index + 1)
        self.update_move_highlights()

    # ------------------------------------------------------------------ #
    #  Save / Load
    # ------------------------------------------------------------------ #

    def save_game(self):
        state = {
            "current_player_index": self.current_player_index,
            "game_mode": self.game_mode.value,
            "ai_difficulty": self.ai_difficulty.name,
            "players": [
                {
                    "player_id":  p.player_id,
                    "position":   list(p.position),
                    "walls_left": p.walls_left,
                    "goal_row":   p.goal_row,
                    "is_ai":      isinstance(p, AIPlayer),
                }
                for p in self.players
            ],
            "walls": [
                {
                    "row": w.row,
                    "col": w.col,
                    "orientation": w.orientation.name,
                }
                for w in self.board.walls
            ],
        }
        with open(SAVE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        print(f"Game saved to {SAVE_FILE}")

    def load_game(self):
        if not os.path.exists(SAVE_FILE):
            print("No save file found.")
            return False

        with open(SAVE_FILE, "r") as f:
            state = json.load(f)

        self.board   = Board()
        self.players = []

        for pd in state["players"]:
            pos = tuple(pd["position"])
            if pd["is_ai"]:
                p = AIPlayer(player_id=pd["player_id"], start_position=pos,
                             goal_row=pd["goal_row"], difficulty=self.ai_difficulty)
            else:
                p = Player(player_id=pd["player_id"], start_pos=pos,
                           goal_row=pd["goal_row"])
            p.walls_left = pd["walls_left"]
            self.players.append(p)
            self.board.move_pawn(p.player_id, pos)

        for wd in state["walls"]:
            orient = (Orientation.HORIZONTAL
                      if "HORIZ" in wd["orientation"].upper()
                      else Orientation.VERTICAL)
            self.board.place_wall(Wall(wd["row"], wd["col"], orient))

        self.current_player_index = state["current_player_index"]
        self.game_mode            = GameMode(state.get("game_mode", self.game_mode.value))
        self.ai_difficulty        = DIFFICULTY[state.get("ai_difficulty", self.ai_difficulty.name)]
        self.game_over            = False
        self._undo_stack.clear()
        self._redo_stack.clear()

        self._refresh_ui_after_state_change()
        print("Game loaded.")
        return True

    # ------------------------------------------------------------------ #
    #  Move handling
    # ------------------------------------------------------------------ #

    def handle_pawn_move_attempt(self, target_pos):
        if self.game_over:
            return
        current_player = self.players[self.current_player_index]
        if isinstance(current_player, AIPlayer):
            return   # ignore clicks on the AI's turn

        if Rules.is_valid_pawn_move(self.board, current_player.position, target_pos):
            self._undo_stack.append(self._snapshot())
            self._redo_stack.clear()

            current_player.position = target_pos
            self.board.move_pawn(current_player.player_id, target_pos)
            self.ui.move_pawn(current_player.player_id, target_pos)

            if Rules.is_winner(current_player):
                self.game_over = True
                self.ui.show_winner(current_player.player_id)
                self.ui.clear_highlights()
                return

            self.end_turn()
        else:
            print("ILLEGAL MOVE")

    def handle_wall_placement_attempt(self, x, y, orientation):
        if self.game_over:
            return
        current_player = self.players[self.current_player_index]
        if isinstance(current_player, AIPlayer):
            return

        if not current_player.has_walls_left():
            print("No walls left!")
            return

        new_wall = Wall(x, y, orientation)
        if Rules.is_valid_wall_placement(self.board, new_wall):
            self._undo_stack.append(self._snapshot())
            self._redo_stack.clear()

            self.board.place_wall(new_wall)
            current_player.use_wall()
            self.ui.update_walls_left_display()
            self.ui.place_wall_visually(new_wall.row, new_wall.col, orientation)
            self.end_turn()
        else:
            print("ILLEGAL WALL")
            if self.ui:
                self.ui.show_invalid_wall_feedback(x, y, orientation)

    # ------------------------------------------------------------------ #
    #  Turn management
    # ------------------------------------------------------------------ #

    def end_turn(self):
        if self.game_over:
            return
        self.current_player_index = 1 - self.current_player_index
        if self.ui and hasattr(self.ui, "update_turn_label"):
            self.ui.update_turn_label(self.current_player_index + 1)
        self.update_move_highlights()

        if self.game_mode == GameMode.PVE and self.current_player_index == 1 and hasattr(self.ui, "schedule_ai"):
            self.ui.schedule_ai()

    def update_move_highlights(self):
        if not self.ui:
            return
        self.ui.clear_highlights()
        curr = self.players[self.current_player_index]
        # Skip highlighting while it's the AI's turn
        if isinstance(curr, AIPlayer):
            return
        for r_off in range(-2, 3):
            for c_off in range(-2, 3):
                target = (curr.position[0] + r_off, curr.position[1] + c_off)
                if Rules.is_valid_pawn_move(self.board, curr.position, target):
                    self.ui.highlight_square(target[0], target[1])

    def is_valid_wall_placement_preview(self, x, y, orientation):
        if self.game_over:
            return False
        current_player = self.players[self.current_player_index]
        if not current_player.has_walls_left():
            return False
        return Rules.is_valid_wall_placement(self.board, Wall(x, y, orientation))

    # ------------------------------------------------------------------ #
    #  AI turn
    # ------------------------------------------------------------------ #

    def execute_ai_turn(self):
        if self.game_over:
            return
        ai_player = self.players[self.current_player_index]
        if not isinstance(ai_player, AIPlayer):
            return

        action = ai_player.get_action(self.board, self.players)
        if action is None:
            return

        self._undo_stack.append(self._snapshot())
        self._redo_stack.clear()

        if action["type"] == "move":
            ai_player.position = action["pos"]
            self.board.move_pawn(ai_player.player_id, action["pos"])
            self.ui.move_pawn(ai_player.player_id, action["pos"])

            if Rules.is_winner(ai_player):
                self.game_over = True
                self.ui.show_winner(ai_player.player_id)
                self.ui.clear_highlights()
                return

        elif action["type"] == "wall":
            w = action["wall"]
            self.board.place_wall(w)
            ai_player.use_wall()
            self.ui.update_walls_left_display()
            self.ui.place_wall_visually(w.row, w.col, w.orientation)

        self.end_turn()