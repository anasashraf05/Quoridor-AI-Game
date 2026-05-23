# =============================================================================
# game_screen.py
# The main game screen — owns the pygame window, the game loop, and all state
# needed to display the game.
#
# Talks to the backend through GameController.
# Calls renderer.py to draw everything.
# Calls input_handler.py to interpret mouse/keyboard events.
# Does NOT contain any game logic itself.
# =============================================================================

import pygame
import time

from src.ui.constants import *
from src.ui import renderer
from src.ui.input_handler import InputHandler
from src.ai.ai_player import AIPlayer
from src.core.enums import GameMode, Orientation, DIFFICULTY
from src.controller.game_controller import GameController


# ---------------------------------------------------------------------------
# UI Adapter — bridges GameController's ui.method() calls into GameScreen
# ---------------------------------------------------------------------------

class _UIAdapter:
    """
    GameController calls methods on self.ui such as:
        self.ui.move_pawn(player_id, pos)
        self.ui.place_wall_visually(row, col, orientation)
        self.ui.update_turn_label(player_id)
        self.ui.update_wall_counts(players)
        self.ui.show_winner(player_id)
    We intercept all of those here so the controller needs no changes.
    """

    def __init__(self, screen: "GameScreen"):
        self._screen = screen

    def move_pawn(self, player_id: int, pos: tuple):
        self._screen._on_pawn_moved(player_id, pos)

    def place_wall_visually(self, row, col, orientation):
        self._screen._on_wall_placed(row, col, orientation)

    def update_turn_label(self, player_id: int):
        # GameScreen reads the turn directly from the controller — nothing to store
        pass

    def update_wall_counts(self, players):
        # GameScreen reads wall counts directly from the controller — nothing to store
        pass

    def update_walls_left_display(self):
        # Pygame renders wall counts directly from controller state
        pass

    def reset_board_visuals(self):
        # Pygame redraw logic is managed by the game loop and controller state
        self._screen._refresh_valid_moves()

    def clear_highlights(self):
        self._screen._valid_moves = []

    def highlight_square(self, row: int, col: int):
        self._screen._valid_moves.append((row, col))

    def show_invalid_wall_feedback(self, row, col, orientation):
        self._screen._show_invalid_wall_preview(row, col, orientation)

    def schedule_ai(self):
        self._screen._schedule_ai()

    def show_winner(self, player_id: int):
        self._screen._on_winner(player_id)


# ---------------------------------------------------------------------------
# GameScreen
# ---------------------------------------------------------------------------

class GameScreen:
    """Owns the pygame window. Call .run() to start the game loop."""

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Quoridor")
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        self.clock  = pygame.time.Clock()

        self.input  = InputHandler()
        self.controller: GameController | None = None

        # UI state
        self.mode_selecting = True
        self.winner: int | None = None
        self.message       = "Select a game mode to begin."
        self.message_type  = "info"
        self.game_mode     = GameMode.PVP

        # Valid moves cache (list of (row, col)) for the current player
        self._valid_moves: list = []

        # Wall ownership map  { id(wall_obj): player_id }  for colour coding
        self._wall_owner: dict = {}

        # Invalid wall preview state
        self._invalid_wall_preview = None
        self._invalid_wall_until   = 0

        # AI turn scheduling
        self._ai_pending = False
        self._ai_time    = 0
        self.difficulty  = DIFFICULTY.MEDIUM

        # Mode selection state
        self.mode_menu = "main"
        self._main_mode_buttons = self._make_main_mode_buttons()
        self._ai_mode_buttons   = self._make_ai_difficulty_buttons()
        self._game_buttons      = self._make_game_buttons_v2()

    # -------------------------
    # Game loop
    # -------------------------

    def run(self):
        """Blocking call — runs until the window is closed."""
        running = True
        while running:
            self.clock.tick(60)

            # Schedule AI turn after a short delay so the board redraws first
            if self._ai_pending and not self.mode_selecting:
                if time.time() * 1000 >= self._ai_time:
                    self._ai_pending = False
                    # AI runs in a background thread (inside execute_ai_turn)
                    # so we just need to trigger it
                    if self.controller:
                        self.controller.execute_ai_turn()

            active_buttons = self._active_mode_buttons() if self.mode_selecting else self._game_buttons
            for event in pygame.event.get():
                action = self.input.process(event, self.mode_selecting, active_buttons)
                if action:
                    result = self._handle_action(action, active_buttons)
                    if result == "quit":
                        running = False

            self._draw()
            pygame.display.flip()

        pygame.quit()

    # -------------------------
    # Action dispatch
    # -------------------------

    def _handle_action(self, action: dict, active_buttons: list):
        t = action["type"]

        if t == "quit":
            return "quit"

        if t == "reset":
            self._start_game(self.game_mode, self.difficulty if self.game_mode == GameMode.PVE else DIFFICULTY.MEDIUM)
            return

        if t == "btn_click":
            idx = action.get("index", 0)
            btn = active_buttons[idx] if 0 <= idx < len(active_buttons) else None
            if btn is None:
                return

            if self.mode_selecting:
                if btn.get("_action") == "choose_ai":
                    self.mode_menu = "ai"
                    self._set_message("Choose AI difficulty:", "info")
                    return
                if btn.get("_action") == "load_saved":
                    self._load_saved_game()
                    return
                if btn.get("_action") == "back_to_main":
                    self.mode_menu = "main"
                    self._set_message("Select a game mode to begin.", "info")
                    return
                if btn.get("mode") == GameMode.PVP:
                    self._start_game(GameMode.PVP, DIFFICULTY.MEDIUM)
                    return
                if btn.get("mode") == GameMode.PVE:
                    difficulty = btn.get("difficulty", DIFFICULTY.MEDIUM)
                    self._start_game(GameMode.PVE, difficulty)
                    return

            if btn.get("_action") == "undo":
                if self.controller:
                    self.controller.undo()
                    self._set_message("Undo performed.", "info")
                return
            if btn.get("_action") == "redo":
                if self.controller:
                    self.controller.redo()
                    self._set_message("Redo performed.", "info")
                return
            if btn.get("_action") == "reset":
                self._start_game(self.game_mode, self.difficulty if self.game_mode == GameMode.PVE else DIFFICULTY.MEDIUM)
                return
            if btn.get("_action") == "save":
                self._save_game()
                return
            if btn.get("_action") == "back":
                self._return_to_menu()
                return

        if t == "mode_pvp":
            self._start_game(GameMode.PVP, DIFFICULTY.MEDIUM)
            return

        if t == "mode_pve":
            self._start_game(GameMode.PVE, DIFFICULTY.MEDIUM)
            return

        if t == "undo":
            if self.controller:
                self.controller.undo()
                self._set_message("Undo performed.", "info")
            return

        if t == "redo":
            if self.controller:
                self.controller.redo()
                self._set_message("Redo performed.", "info")
            return

        # In-game actions only
        if self.controller is None or self.winner or self.mode_selecting:
            return

        if t == "move":
            self._try_pawn_move(action["pos"])

        elif t == "wall":
            self._try_wall_place(action["row"], action["col"], action["orientation"])

    # -------------------------
    # Game start / reset
    # -------------------------

    def _start_game(self, mode: GameMode, difficulty: DIFFICULTY = DIFFICULTY.MEDIUM):
        self.game_mode      = mode
        self.difficulty     = difficulty
        self.mode_selecting = False
        self.winner         = None
        self._wall_owner    = {}
        self._ai_pending    = False
        self._valid_moves   = []

        self.controller = GameController(mode=mode, ai_difficulty=difficulty)
        self.controller.ui = _UIAdapter(self)
        self.controller.start_game()

        self._refresh_valid_moves()
        if mode == GameMode.PVP:
            label = "Human vs Human"
        else:
            label = f"Human vs AI ({difficulty.name.title()})"
        self._set_message(f"{label} — Player 1 goes first!", "ok")

    # -------------------------
    # Pawn move
    # -------------------------

    def _try_pawn_move(self, pos: tuple):
        if self.controller is None:
            return
        before = self.controller.current_player_index
        self.controller.handle_pawn_move_attempt(pos)
        after  = self.controller.current_player_index

        if before == after and not self.winner:
            self._set_message("Invalid move! Try again.", "error")

    # -------------------------
    # Wall placement
    # -------------------------

    def _try_wall_place(self, row: int, col: int, orientation: Orientation):
        if self.controller is None:
            return
        cur = self.controller.players[self.controller.current_player_index]
        if not cur.has_walls_left():
            self._set_message("No walls left!", "error")
            return

        before = self.controller.current_player_index
        self.controller.handle_wall_placement_attempt(row, col, orientation)
        after  = self.controller.current_player_index

        if before == after and not self.winner:
            self._set_message("Invalid wall placement!", "error")

    # -------------------------
    # Controller callbacks (called via _UIAdapter)
    # -------------------------

    def _on_pawn_moved(self, player_id: int, pos: tuple):
        """Called after a successful pawn move."""
        if self.winner or self.controller is None:
            return
        cur_idx = self.controller.current_player_index
        next_pid = self.controller.players[cur_idx].player_id
        self._set_message(f"Player {player_id} moved. Player {next_pid}'s turn.", "ok")
        self._refresh_valid_moves()

        # Schedule AI turn if needed
        if self.game_mode == GameMode.PVE and next_pid == 2:
            self._schedule_ai()

    def _on_wall_placed(self, row, col, orientation):
        """Called after a successful wall placement."""
        if self.winner or self.controller is None:
            return
        # Record wall ownership for colour coding
        walls = self.controller.board.get_all_walls()
        if walls:
            cur_pid = self.controller.players[self.controller.current_player_index].player_id
            self._wall_owner[id(walls[-1])] = cur_pid

        cur_idx = self.controller.current_player_index
        next_pid = self.controller.players[cur_idx].player_id
        self._set_message(f"Wall placed. Player {next_pid}'s turn.", "info")
        self._refresh_valid_moves()

        if self.game_mode == GameMode.PVE and next_pid == 2:
            self._schedule_ai()

    def _on_winner(self, player_id: int):
        """Called when a player wins."""
        self.winner = player_id
        self._valid_moves = []
        self._set_message(f"Player {player_id} wins! Press R to restart.", "ok")

    # -------------------------
    # AI scheduling
    # -------------------------

    def _schedule_ai(self):
        """Schedules the AI move after a short visual delay."""
        self._ai_pending = True
        self._ai_time    = time.time() * 1000 + AI_THINK_MS
        self._set_message("AI is thinking…", "info")

    # -------------------------
    # Helpers
    # -------------------------

    def _refresh_valid_moves(self):
        """Rebuilds the valid-move highlight list for the current player."""
        if self.controller is None or self.winner:
            self._valid_moves = []
            return

        from src.core.rules import Rules
        cur   = self.controller.players[self.controller.current_player_index]
        board = self.controller.board
        moves = []
        r, c  = cur.position

        for dr in range(-2, 3):
            for dc in range(-2, 3):
                tp = (r + dr, c + dc)
                if tp == cur.position:
                    continue
                if Rules.is_valid_pawn_move(board, cur.position, tp):
                    moves.append(tp)

        self._valid_moves = moves

    def _show_invalid_wall_preview(self, row: int, col: int, orientation: Orientation):
        self._invalid_wall_preview = (row, col, orientation)
        self._invalid_wall_until = time.time() * 1000 + 450

    def _set_message(self, text: str, mtype: str = "info"):
        self.message      = text
        self.message_type = mtype

    # -------------------------
    # Drawing
    # -------------------------

    def _draw(self):
        self.screen.fill(C_BG)

        if self.mode_selecting:
            subtitle = "Choose AI difficulty" if self.mode_menu == "ai" else "Select Game Mode"
            renderer.draw_mode_screen(self.screen, self._active_mode_buttons(), subtitle)
            return

        renderer.draw_board(
            self.screen,
            valid_moves=self._valid_moves,
            selected_pos=None,
        )

        hover_wall = self.input.get_hover_wall() if not self.winner else None
        if self._invalid_wall_preview and time.time() * 1000 <= self._invalid_wall_until:
            hover_wall = self._invalid_wall_preview
            hover_invalid = True
        else:
            hover_invalid = False
            if self.controller and hover_wall is not None:
                hover_invalid = not self.controller.is_valid_wall_placement_preview(
                    hover_wall[0], hover_wall[1], hover_wall[2]
                )

        renderer.draw_walls(
            self.screen,
            walls=self.controller.board.get_all_walls() if self.controller else [],
            player_id_map=self._wall_owner,
            hover_wall=hover_wall,
            hover_invalid=hover_invalid,
        )

        if self.controller:
            positions = {p.player_id: p.position for p in self.controller.players}
            renderer.draw_pawns(self.screen, positions)

        walls_left = {}
        cur_player = 1
        if self.controller:
            walls_left = {p.player_id: p.walls_left for p in self.controller.players}
            cur_player = self.controller.players[self.controller.current_player_index].player_id

        if self.game_mode == GameMode.PVP:
            mode_label = "Human vs Human"
        else:
            mode_label = f"Human vs AI ({self.difficulty.name.title()})"

        renderer.draw_sidebar(self.screen, {
            "current_player":  cur_player,
            "walls_left":      walls_left,
            "message":         self.message,
            "message_type":    self.message_type,
            "game_mode_label": mode_label,
            "winner":          self.winner,
        })

        for btn in self._game_buttons:
            col = C_BTN_HOVER if btn["hovered"] else C_BTN_NORMAL
            pygame.draw.rect(self.screen, col, btn["rect"], border_radius=6)
            pygame.draw.rect(self.screen, C_BTN_TEXT, btn["rect"], 2, border_radius=6)
            lbl = pygame.font.SysFont("segoeui", FONT_SMALL_SIZE, bold=True).render(
                btn["label"], True, C_BTN_TEXT)
            self.screen.blit(lbl, lbl.get_rect(center=btn["rect"].center))

        if self.winner:
            renderer.draw_winner_overlay(self.screen, self.winner)

    # -------------------------
    # Button factories
    # -------------------------

    def _active_mode_buttons(self) -> list:
        return self._ai_mode_buttons if self.mode_menu == "ai" else self._main_mode_buttons

    def _load_saved_game(self):
        self.controller = GameController()
        self.controller.ui = _UIAdapter(self)
        if not self.controller.load_game():
            self._set_message("No saved game found.", "error")
            self.controller = None
            self.controller = None
            return
        self.game_mode = self.controller.game_mode
        self.difficulty = self.controller.ai_difficulty
        self.mode_selecting = False
        self.winner = None
        self._wall_owner = {}
        self._refresh_valid_moves()
        if (self.game_mode == GameMode.PVE and
                isinstance(self.controller.players[self.controller.current_player_index], AIPlayer)):
            self._schedule_ai()
        self._set_message("Saved game loaded. Continue playing.", "ok")

    def _save_game(self):
        if not self.controller:
            self._set_message("Nothing to save yet.", "error")
            return
        self.controller.save_game()
        self._set_message("Game saved.", "ok")

    def _return_to_menu(self):
        self.mode_selecting = True
        self.mode_menu = "main"
        self.controller = None
        self.winner = None
        self._wall_owner = {}
        self._valid_moves = []
        self._set_message("Select a game mode to begin.", "info")

    def _make_main_mode_buttons(self) -> list:
        cx = WINDOW_W // 2
        cy = WINDOW_H // 2
        w, h = 280, 48
        return [
            {"label": "Human vs Human", "rect": pygame.Rect(cx - w // 2, cy - 94, w, h), "hovered": False,
             "mode": GameMode.PVP, "difficulty": DIFFICULTY.MEDIUM},
            {"label": "Human vs AI", "rect": pygame.Rect(cx - w // 2, cy - 30, w, h), "hovered": False,
             "_action": "choose_ai"},
            {"label": "Load Saved Game", "rect": pygame.Rect(cx - w // 2, cy + 34, w, h), "hovered": False,
             "_action": "load_saved"},
        ]

    def _make_ai_difficulty_buttons(self) -> list:
        cx = WINDOW_W // 2
        cy = WINDOW_H // 2
        w, h = 280, 48
        return [
            {"label": "Easy", "rect": pygame.Rect(cx - w // 2, cy - 94, w, h), "hovered": False,
             "mode": GameMode.PVE, "difficulty": DIFFICULTY.EASY},
            {"label": "Medium", "rect": pygame.Rect(cx - w // 2, cy - 30, w, h), "hovered": False,
             "mode": GameMode.PVE, "difficulty": DIFFICULTY.MEDIUM},
            {"label": "Hard", "rect": pygame.Rect(cx - w // 2, cy + 34, w, h), "hovered": False,
             "mode": GameMode.PVE, "difficulty": DIFFICULTY.HARD},
            {"label": "← Back", "rect": pygame.Rect(cx - w // 2, cy + 98, w, h), "hovered": False,
             "_action": "back_to_main"},
        ]

    def _make_game_buttons_v2(self) -> list:
        sx = BOARD_PX + BOARD_OFFSET_X + 20
        sy = BOARD_OFFSET_Y + BOARD_PX - 180
        return [
            {"label": "↶  Undo (Z)", "rect": pygame.Rect(sx, sy, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "undo"},
            {"label": "↷  Redo (Y)", "rect": pygame.Rect(sx, sy + 44, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "redo"},
            {"label": "💾  Save", "rect": pygame.Rect(sx, sy + 88, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "save"},
            {"label": "↺  Reset  (R)", "rect": pygame.Rect(sx, sy + 132, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "reset"},
            {"label": "←  Back", "rect": pygame.Rect(sx, sy + 176, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "back"},
        ]

    def _make_game_buttons(self) -> list:
        sx = BOARD_PX + BOARD_OFFSET_X + 20
        sy = BOARD_OFFSET_Y + BOARD_PX - 100
        return [
            {"label": "💾  Save", "rect": pygame.Rect(sx, sy, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "save"},
            {"label": "↺  Reset  (R)", "rect": pygame.Rect(sx, sy + 44, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "reset"},
            {"label": "←  Back", "rect": pygame.Rect(sx, sy + 88, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "back"},
        ]