# =============================================================================
# input_handler.py
# Translates raw Pygame mouse/keyboard events into high-level game actions.
# The GameScreen uses this to stay clean — it never does its own hit-testing.
# =============================================================================

import pygame
from src.ui.constants import *
from src.core.enums import Orientation


# ---------------------------------------------------------------------------
# Hit-test helpers
# ---------------------------------------------------------------------------

def pixel_to_cell(mx: int, my: int):
    """
    Given a mouse position (mx, my), returns the 1-based (row, col) of the
    cell under the cursor, or None if the cursor is not over a cell.
    """
    bx = mx - BOARD_OFFSET_X
    by = my - BOARD_OFFSET_Y

    if bx < 0 or by < 0:
        return None

    step = CELL_SIZE + GAP_SIZE

    # Which tile column/row are we in?
    tile_col = bx // step
    tile_row = by // step

    # Offset within that tile
    ox = bx % step
    oy = by % step

    # Only valid if we're inside the cell portion (not the gap)
    if ox < CELL_SIZE and oy < CELL_SIZE:
        col = tile_col + 1   # 1-based
        row = tile_row + 1
        if 1 <= row <= GRID_COUNT and 1 <= col <= GRID_COUNT:
            return (row, col)

    return None


def pixel_to_wall_gap(mx: int, my: int):
    """
    Returns (logical_row, logical_col, Orientation) if the cursor is over a
    wall gap, or None otherwise.

    Wall gap coordinates use the same anchor convention as Wall objects:
      - HORIZONTAL gap at (r, c) sits BELOW row r, between col c and c+1
      - VERTICAL   gap at (r, c) sits to the RIGHT of col c, between row r and r+1
    """
    bx = mx - BOARD_OFFSET_X
    by = my - BOARD_OFFSET_Y

    if bx < 0 or by < 0:
        return None

    step = CELL_SIZE + GAP_SIZE

    tile_col = bx // step
    tile_row = by // step
    ox = bx % step   # offset inside the tile
    oy = by % step

    in_col_cell = ox < CELL_SIZE
    in_row_cell = oy < CELL_SIZE
    in_col_gap  = CELL_SIZE <= ox < CELL_SIZE + GAP_SIZE
    in_row_gap  = CELL_SIZE <= oy < CELL_SIZE + GAP_SIZE

    row = tile_row + 1   # 1-based anchor
    col = tile_col + 1

    # --- VERTICAL gap: inside a cell row, inside a column gap ---
    if in_row_cell and in_col_gap:
        # Valid only if there is a next column (col goes up to GRID_COUNT-1)
        if 1 <= row <= GRID_COUNT and 1 <= col <= GRID_COUNT - 1:
            return (row, col, Orientation.VERTICAL)

    # --- HORIZONTAL gap: inside a row gap, inside a cell column ---
    if in_col_cell and in_row_gap:
        if 1 <= row <= GRID_COUNT - 1 and 1 <= col <= GRID_COUNT:
            return (row, col, Orientation.HORIZONTAL)

    return None


# ---------------------------------------------------------------------------
# Input handler class
# ---------------------------------------------------------------------------

class InputHandler:
    """
    Converts pygame events into structured action dicts that the GameScreen
    can understand.

    Action types returned:
        {"type": "move",  "pos": (row, col)}
        {"type": "wall",  "row": r, "col": c, "orientation": Orientation.X}
        {"type": "reset"}
        {"type": "quit"}
        {"type": "mode_pvp"}
        {"type": "mode_pve"}
        {"type": "hover_cell",  "pos": (row, col) | None}
        {"type": "hover_wall",  "data": (row, col, orient) | None}
        {"type": "btn_click",   "index": int}   -- used on the mode screen
    """

    def __init__(self):
        self.hover_cell = None     # (row, col) or None
        self.hover_wall = None     # (row, col, Orientation) or None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process(self, event: pygame.event.Event, mode_screen: bool,
                buttons: list) -> dict | None:
        """
        Processes one pygame event and returns an action dict or None.

        mode_screen -- True while the mode-selection overlay is visible
        buttons     -- list of button dicts from GameScreen (needed for click detection)
        """
        if event.type == pygame.QUIT:
            return {"type": "quit"}

        if event.type == pygame.KEYDOWN:
            return self._handle_key(event)

        if event.type == pygame.MOUSEMOTION:
            self._handle_motion(event.pos, mode_screen, buttons)
            return None     # motion never triggers a game action directly

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self._handle_click(event.pos, mode_screen, buttons)

        return None

    def get_hover_cell(self):
        return self.hover_cell

    def get_hover_wall(self):
        return self.hover_wall

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _handle_key(self, event) -> dict | None:
        if event.key == pygame.K_ESCAPE:
            return {"type": "quit"}
        if event.key == pygame.K_r:
            return {"type": "reset"}
        if event.key == pygame.K_h:
            return {"type": "mode_pvp"}
        if event.key == pygame.K_a:
            return {"type": "mode_pve"}
        return None

    def _handle_motion(self, pos, mode_screen: bool, buttons: list):
        mx, my = pos

        # Update button hover states
        for btn in buttons:
            btn["hovered"] = btn["rect"].collidepoint(mx, my)

        if mode_screen:
            self.hover_cell = None
            self.hover_wall = None
            return

        # Update board hover states
        cell = pixel_to_cell(mx, my)
        wall = pixel_to_wall_gap(mx, my)

        self.hover_cell = cell if cell else None
        self.hover_wall = wall if wall else None

    def _handle_click(self, pos, mode_screen: bool, buttons: list) -> dict | None:
        mx, my = pos

        # Button clicks (mode screen or always-visible buttons)
        for i, btn in enumerate(buttons):
            if btn["rect"].collidepoint(mx, my):
                return {"type": "btn_click", "index": i}

        if mode_screen:
            return None

        # Board clicks
        cell = pixel_to_cell(mx, my)
        if cell:
            return {"type": "move", "pos": cell}

        wall = pixel_to_wall_gap(mx, my)
        if wall:
            r, c, orient = wall
            return {"type": "wall", "row": r, "col": c, "orientation": orient}

        return None
