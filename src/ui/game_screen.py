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
from src.core.enums import GameMode, Orientation
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

        # AI turn scheduling
        self._ai_pending = False
        self._ai_time    = 0

        # Buttons
        self._buttons      = self._make_mode_buttons()
        self._game_buttons = self._make_game_buttons()

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

            active_buttons = self._buttons if self.mode_selecting else self._game_buttons
            for event in pygame.event.get():
                action = self.input.process(event, self.mode_selecting, active_buttons)
                if action:
                    result = self._handle_action(action)
                    if result == "quit":
                        running = False

            self._draw()
            pygame.display.flip()

        pygame.quit()

    # -------------------------
    # Action dispatch
    # -------------------------

    def _handle_action(self, action: dict):
        t = action["type"]

        if t == "quit":
            return "quit"

        if t == "reset":
            self._start_game(self.game_mode)
            return

        # Mode-selection buttons
        if t == "btn_click" and self.mode_selecting:
            idx = action.get("index", 0)
            self._start_game(GameMode.PVP if idx == 0 else GameMode.PVE)
            return

        if t == "mode_pvp":
            self._start_game(GameMode.PVP)
            return

        if t == "mode_pve":
            self._start_game(GameMode.PVE)
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

    def _start_game(self, mode: GameMode):
        self.game_mode      = mode
        self.mode_selecting = False
        self.winner         = None
        self._wall_owner    = {}
        self._ai_pending    = False
        self._valid_moves   = []

        self.controller = GameController(mode=mode)
        self.controller.ui = _UIAdapter(self)
        self.controller.start_game()

        self._refresh_valid_moves()
        label = "Human vs Human" if mode == GameMode.PVP else "Human vs AI"
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
        if self.winner:
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
        if self.winner:
            return
        # Record wall ownership for colour coding
        walls = self.controller.board.get_all_walls()
        if walls:
            prev_idx = 0 if self.controller.current_player_index == 1 else 1
            prev_pid = self.controller.players[prev_idx].player_id
            self._wall_owner[id(walls[-1])] = prev_pid

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

    def _set_message(self, text: str, mtype: str = "info"):
        self.message      = text
        self.message_type = mtype

    # -------------------------
    # Drawing
    # -------------------------

    def _draw(self):
        self.screen.fill(C_BG)

        if self.mode_selecting:
            renderer.draw_mode_screen(self.screen, self._buttons)
            return

        renderer.draw_board(
            self.screen,
            valid_moves=self._valid_moves,
            selected_pos=None,
        )

        hover_wall = self.input.get_hover_wall() if not self.winner else None
        renderer.draw_walls(
            self.screen,
            walls=self.controller.board.get_all_walls() if self.controller else [],
            player_id_map=self._wall_owner,
            hover_wall=hover_wall,
        )

        if self.controller:
            positions = {p.player_id: p.position for p in self.controller.players}
            renderer.draw_pawns(self.screen, positions)

        walls_left = {}
        cur_player = 1
        if self.controller:
            walls_left = {p.player_id: p.walls_left for p in self.controller.players}
            cur_player = self.controller.players[self.controller.current_player_index].player_id

        mode_label = "Human vs Human" if self.game_mode == GameMode.PVP else "Human vs AI"
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

    def _make_mode_buttons(self) -> list:
        cx = WINDOW_W // 2
        cy = WINDOW_H // 2
        w, h = 240, 48
        return [
            {"label": "Human  vs  Human", "rect": pygame.Rect(cx - w // 2, cy - 10, w, h), "hovered": False},
            {"label": "Human  vs  AI",    "rect": pygame.Rect(cx - w // 2, cy + 54, w, h), "hovered": False},
        ]

    def _make_game_buttons(self) -> list:
        sx = BOARD_PX + BOARD_OFFSET_X + 20
        sy = BOARD_OFFSET_Y + BOARD_PX - 44
        return [
            {"label": "↺  Reset  (R)", "rect": pygame.Rect(sx, sy, SIDEBAR_W - 30, 34),
             "hovered": False, "_action": "reset"},
        ]