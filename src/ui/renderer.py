# =============================================================================
# renderer.py
# Responsible for ALL drawing.  It reads game state but NEVER changes it.
# The GameScreen passes a snapshot of what to draw; this file makes it appear.
# =============================================================================

import pygame
from src.ui.constants import *


# ---------------------------------------------------------------------------
# Font cache — loaded once, reused everywhere
# ---------------------------------------------------------------------------
_fonts = {}

def _font(size: int, bold: bool = False) -> pygame.font.Font:
    """Returns a cached pygame Font at the requested size."""
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont("segoeui", size, bold=bold)
    return _fonts[key]


# ---------------------------------------------------------------------------
# Coordinate helpers
# ---------------------------------------------------------------------------

def cell_to_pixel(row: int, col: int):
    """
    Converts a 1-based logical (row, col) to the top-left pixel
    of that cell on screen.
    """
    # Convert to 0-based
    r = row - 1
    c = col - 1
    x = BOARD_OFFSET_X + c * (CELL_SIZE + GAP_SIZE)
    y = BOARD_OFFSET_Y + r * (CELL_SIZE + GAP_SIZE)
    return x, y


def cell_center(row: int, col: int):
    """Returns the pixel centre of a cell."""
    x, y = cell_to_pixel(row, col)
    return x + CELL_SIZE // 2, y + CELL_SIZE // 2


def wall_gap_rect(logical_row: int, logical_col: int, orientation) -> pygame.Rect:
    """
    Returns the pygame.Rect for a wall gap.
    logical_row / logical_col are 1-based anchor coords.
    orientation is Orientation.HORIZONTAL or Orientation.VERTICAL.
    """
    from src.core.enums import Orientation
    x, y = cell_to_pixel(logical_row, logical_col)

    if orientation == Orientation.HORIZONTAL:
        # Gap sits BELOW row `logical_row`, spans two cells + gap
        gx = x
        gy = y + CELL_SIZE
        gw = 2 * CELL_SIZE + GAP_SIZE
        gh = GAP_SIZE
    else:  # VERTICAL
        # Gap sits to the RIGHT of col `logical_col`, spans two cells + gap
        gx = x + CELL_SIZE
        gy = y
        gw = GAP_SIZE
        gh = 2 * CELL_SIZE + GAP_SIZE

    return pygame.Rect(gx, gy, gw, gh)


# ---------------------------------------------------------------------------
# Board rendering
# ---------------------------------------------------------------------------

def draw_board(surface: pygame.Surface, valid_moves: list, selected_pos):
    """
    Draws the 9×9 board: background cells and valid-move highlights.

    Args:
        surface       -- pygame Surface to draw on
        valid_moves   -- list of (row, col) tuples that are currently reachable
        selected_pos  -- (row, col) of the currently selected cell, or None
    """
    valid_set = set(valid_moves)

    for r in range(1, GRID_COUNT + 1):
        for c in range(1, GRID_COUNT + 1):
            px, py = cell_to_pixel(r, c)
            rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)

            # Choose fill colour
            if selected_pos == (r, c):
                colour = C_SELECTED_CELL
            elif (r, c) in valid_set:
                colour = C_VALID_MOVE
            else:
                colour = C_BOARD_BG

            pygame.draw.rect(surface, colour, rect)
            pygame.draw.rect(surface, C_CELL_BORDER, rect, 1)


def draw_walls(surface: pygame.Surface, walls: list, player_id_map: dict,
               hover_wall=None):
    """
    Draws all placed walls, plus an optional hover preview.

    Args:
        surface       -- target surface
        walls         -- list of Wall objects
        player_id_map -- dict mapping Wall → player_id (so we can colour by owner)
                         (currently unused because the controller doesn't track this;
                          we fall back to a neutral brown colour)
        hover_wall    -- (logical_row, logical_col, Orientation) tuple while user
                         is hovering over a gap, or None
    """
    from src.core.enums import Orientation

    # Draw placed walls in yellow
    for wall in walls:
        rect = wall_gap_rect(wall.row, wall.col, wall.orientation)
        pygame.draw.rect(surface, C_WALL_PLACED, rect)
        pygame.draw.rect(surface, (80, 50, 20), rect, 2)       # dark border

    # Draw hover preview
    if hover_wall is not None:
        h_row, h_col, h_orient = hover_wall
        rect = wall_gap_rect(h_row, h_col, h_orient)
        # Draw translucent yellow preview
        preview = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        preview.fill((*C_WALL_HOVER, 160))
        surface.blit(preview, rect.topleft)
        pygame.draw.rect(surface, C_WALL_HOVER, rect, 2)


def draw_pawns(surface: pygame.Surface, positions: dict):
    """
    Draws both pawns.

    Args:
        positions -- {player_id: (row, col)}  (1-based coords)
    """
    colours   = {1: C_PAWN_P1, 2: C_PAWN_P2}
    radius    = int(CELL_SIZE * PAWN_RADIUS_RATIO)

    for pid, pos in positions.items():
        cx, cy = cell_center(pos[0], pos[1])
        colour = colours.get(pid, (200, 200, 200))

        # Shadow
        pygame.draw.circle(surface, (0, 0, 0, 80), (cx + 2, cy + 3), radius)
        # Outer ring
        pygame.draw.circle(surface, C_PAWN_BORDER, (cx, cy), radius + 2)
        # Main body
        pygame.draw.circle(surface, colour, (cx, cy), radius)
        # Highlight spot
        pygame.draw.circle(surface, tuple(min(255, v + 80) for v in colour),
                           (cx - radius // 3, cy - radius // 3), radius // 4)


# ---------------------------------------------------------------------------
# Sidebar rendering
# ---------------------------------------------------------------------------

def draw_sidebar(surface: pygame.Surface, state: dict):
    """
    Draws the entire right-side information panel.

    state keys expected:
        current_player  -- 1 or 2
        walls_left      -- {1: int, 2: int}
        message         -- str (status message to show)
        message_type    -- "ok" | "error" | "info"
        game_mode_label -- str ("Human vs Human" | "Human vs AI")
        winner          -- None | 1 | 2
        mode_selecting  -- bool (True while on mode screen)
    """
    sx = BOARD_PX + BOARD_OFFSET_X + 10
    sy = BOARD_OFFSET_Y

    # Background panel
    panel = pygame.Rect(sx - 5, sy, SIDEBAR_W, BOARD_PX)
    pygame.draw.rect(surface, C_SIDEBAR_BG, panel, border_radius=8)

    y = sy + 14
    cx = sx + SIDEBAR_W // 2 - 5  # horizontal centre of sidebar

    # --- Title ---
    _blit_centered(surface, "QUORIDOR", _font(FONT_TITLE_SIZE, bold=True),
                   C_SIDEBAR_TITLE, cx, y)
    y += 34

    # --- Mode label ---
    mode_lbl = state.get("game_mode_label", "")
    _blit_centered(surface, mode_lbl, _font(FONT_SMALL_SIZE), C_TEXT_DIM, cx, y)
    y += 28

    # Divider
    pygame.draw.line(surface, (60, 60, 80),
                     (sx, y), (sx + SIDEBAR_W - 10, y), 1)
    y += 12

    # --- Turn indicator ---
    cur = state.get("current_player", 1)
    winner = state.get("winner")

    if winner:
        turn_text = f"🏆  Player {winner} Wins!"
        turn_col  = C_PAWN_P1 if winner == 1 else C_PAWN_P2
    else:
        turn_text = f"Player {cur}'s Turn"
        turn_col  = C_P1_ACCENT if cur == 1 else C_P2_ACCENT

    _blit_centered(surface, turn_text, _font(FONT_BODY_SIZE, bold=True),
                   turn_col, cx, y)
    y += 32

    # Pawn colour legend dots
    for pid, col, lbl in [(1, C_PAWN_P1, "Player 1"), (2, C_PAWN_P2, "Player 2")]:
        dot_x = sx + 16
        pygame.draw.circle(surface, col, (dot_x, y + 8), 8)
        pygame.draw.circle(surface, C_PAWN_BORDER, (dot_x, y + 8), 8, 2)
        surf = _font(FONT_SMALL_SIZE).render(lbl, True, C_TEXT_LIGHT)
        surface.blit(surf, (dot_x + 16, y))
        y += 22

    y += 8
    # Divider
    pygame.draw.line(surface, (60, 60, 80),
                     (sx, y), (sx + SIDEBAR_W - 10, y), 1)
    y += 12

    # --- Wall counts ---
    _blit_left(surface, "Walls Remaining", _font(FONT_SMALL_SIZE),
               C_TEXT_DIM, sx + 8, y)
    y += 22

    walls_left = state.get("walls_left", {1: 10, 2: 10})
    for pid in [1, 2]:
        wl   = walls_left.get(pid, 0)
        col  = C_P1_ACCENT if pid == 1 else C_P2_ACCENT
        label = f"P{pid}: "
        lsurf = _font(FONT_BODY_SIZE, bold=True).render(label, True, col)
        surface.blit(lsurf, (sx + 8, y))

        # Draw mini wall bricks
        bx = sx + 8 + lsurf.get_width() + 4
        for i in range(10):
            brick = pygame.Rect(bx + i * 12, y + 3, 10, 12)
            if i < wl:
                pygame.draw.rect(surface, col, brick, border_radius=2)
            else:
                pygame.draw.rect(surface, (50, 50, 70), brick, border_radius=2)
        y += 26

    y += 6
    # Divider
    pygame.draw.line(surface, (60, 60, 80),
                     (sx, y), (sx + SIDEBAR_W - 10, y), 1)
    y += 12

    # --- Status / message ---
    msg      = state.get("message", "")
    msg_type = state.get("message_type", "info")
    msg_col  = {"ok": C_MSG_OK, "error": C_MSG_ERR, "info": C_MSG_INFO}.get(
                msg_type, C_TEXT_LIGHT)

    if msg:
        for line in _wrap_text(msg, _font(FONT_SMALL_SIZE), SIDEBAR_W - 20):
            lsurf = _font(FONT_SMALL_SIZE).render(line, True, msg_col)
            surface.blit(lsurf, (sx + 8, y))
            y += 18

    y += 6
    # Divider
    pygame.draw.line(surface, (60, 60, 80),
                     (sx, y), (sx + SIDEBAR_W - 10, y), 1)
    y += 14

    # --- Controls cheat-sheet ---
    controls = [
        ("LClick cell",   "Move pawn"),
        ("LClick gap",    "Place wall"),
        ("R key",         "Reset game"),
        ("H/A key",       "Switch mode"),
        ("ESC",           "Quit"),
    ]
    _blit_left(surface, "Controls", _font(FONT_SMALL_SIZE, bold=True),
               C_TEXT_DIM, sx + 8, y)
    y += 18
    for key, action in controls:
        k = _font(FONT_SMALL_SIZE, bold=True).render(key, True, C_SIDEBAR_TITLE)
        a = _font(FONT_SMALL_SIZE).render(f"  {action}", True, C_TEXT_DIM)
        surface.blit(k, (sx + 8, y))
        surface.blit(a, (sx + 8 + k.get_width(), y))
        y += 16


# ---------------------------------------------------------------------------
# Mode selection screen
# ---------------------------------------------------------------------------

def draw_mode_screen(surface: pygame.Surface, buttons: list, subtitle: str = "Select Game Mode"):
    """
    Draws the game-mode selection overlay.

    buttons -- list of dicts: {label, rect, hovered}
    """
    # Dark overlay
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((20, 20, 40, 230))
    surface.blit(overlay, (0, 0))

    cx = WINDOW_W // 2
    cy = WINDOW_H // 2

    # Title
    title = _font(36, bold=True).render("QUORIDOR", True, C_SIDEBAR_TITLE)
    surface.blit(title, title.get_rect(center=(cx, cy - 110)))

    sub = _font(FONT_BODY_SIZE).render(subtitle, True, C_TEXT_DIM)
    surface.blit(sub, sub.get_rect(center=(cx, cy - 68)))

    # Buttons
    for btn in buttons:
        col = C_BTN_HOVER if btn["hovered"] else C_BTN_NORMAL
        pygame.draw.rect(surface, col, btn["rect"], border_radius=8)
        pygame.draw.rect(surface, C_BTN_TEXT, btn["rect"], 2, border_radius=8)
        lbl = _font(FONT_BODY_SIZE, bold=True).render(btn["label"], True, C_BTN_TEXT)
        surface.blit(lbl, lbl.get_rect(center=btn["rect"].center))


# ---------------------------------------------------------------------------
# Winner overlay
# ---------------------------------------------------------------------------

def draw_winner_overlay(surface: pygame.Surface, winner: int):
    """Full-screen translucent winner celebration."""
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((20, 20, 40, 190))
    surface.blit(overlay, (0, 0))

    cx, cy = WINDOW_W // 2, WINDOW_H // 2
    col = C_PAWN_P1 if winner == 1 else C_PAWN_P2

    big   = _font(48, bold=True).render(f"Player {winner} Wins!", True, col)
    small = _font(FONT_BODY_SIZE).render("Press  R  to play again", True, C_TEXT_DIM)

    surface.blit(big,   big.get_rect(center=(cx, cy - 24)))
    surface.blit(small, small.get_rect(center=(cx, cy + 32)))


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _blit_centered(surface, text, font, colour, cx, y):
    surf = font.render(text, True, colour)
    surface.blit(surf, (cx - surf.get_width() // 2, y))


def _blit_left(surface, text, font, colour, x, y):
    surf = font.render(text, True, colour)
    surface.blit(surf, (x, y))


def _wrap_text(text: str, font, max_width: int) -> list:
    """Splits a string into lines that fit within max_width pixels."""
    words = text.split()
    lines, current = [], ""
    for w in words:
        test = (current + " " + w).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines
