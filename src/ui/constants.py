# =============================================================================
# constants.py
# All visual constants for the Quoridor UI.
# Change values here to restyle the entire game.
# =============================================================================

# --- Board Sizes ---
CELL_SIZE   = 60    # Pixels: size of one playable square
GAP_SIZE    = 14    # Pixels: width/height of the wall gap between squares
GRID_COUNT  = 9     # Number of playable rows/columns

# --- Sidebar ---
SIDEBAR_W   = 220   # Pixels: width of the right-side info panel

# --- Computed sizes (don't edit these) ---
# Total pixel width of the board area (cells + gaps)
BOARD_PX = GRID_COUNT * CELL_SIZE + (GRID_COUNT - 1) * GAP_SIZE
WINDOW_W = BOARD_PX + SIDEBAR_W + 20   # 20px right margin
WINDOW_H = BOARD_PX + 60               # 60px top margin for title

# Board top-left offset so it sits centred vertically with a small top margin
BOARD_OFFSET_X = 10
BOARD_OFFSET_Y = 10

# --- Colours (R, G, B) ---
C_BG            = (30,  30,  45)   # Dark navy background
C_BOARD_BG      = (240, 217, 181)  # Warm wood colour for cells
C_CELL_BORDER   = (180, 140, 100)  # Cell border
C_GAP_EMPTY     = (200, 180, 155)  # Empty wall gap

C_WALL_P1       = (220,  60,  60)  # Red walls (Player 1)
C_WALL_P2       = (60,  100, 220)  # Blue walls (Player 2)
C_WALL_HOVER    = (255, 200,  50)  # Yellow hover preview

C_PAWN_P1       = (220,  60,  60)  # Player 1 pawn colour
C_PAWN_P2       = (60,  100, 220)  # Player 2 pawn colour
C_PAWN_BORDER   = (255, 255, 255)  # White pawn ring

C_VALID_MOVE    = (100, 220, 100)  # Green highlight for valid moves
C_SELECTED_CELL = (255, 240,  80)  # Yellow: currently selected cell

C_SIDEBAR_BG    = (20,  20,  35)   # Dark sidebar background
C_SIDEBAR_TITLE = (255, 200,  50)  # Gold title text
C_TEXT_LIGHT    = (230, 230, 230)  # Normal text
C_TEXT_DIM      = (140, 140, 160)  # Dimmed/inactive text
C_P1_ACCENT     = (220,  60,  60)  # Player 1 accent
C_P2_ACCENT     = (60,  100, 220)  # Player 2 accent
C_BTN_NORMAL    = (50,  55,  80)   # Button idle
C_BTN_HOVER     = (70,  80, 120)   # Button hovered
C_BTN_ACTIVE    = (90, 110, 160)   # Button pressed
C_BTN_TEXT      = (220, 220, 255)  # Button label
C_MSG_OK        = (100, 220, 100)  # Green status message
C_MSG_ERR       = (220,  80,  80)  # Red error message
C_MSG_INFO      = (200, 200,  80)  # Yellow info message
C_WINNER_BG     = (30,  30,  45, 180)   # Semi-transparent winner overlay

# --- Fonts (loaded at runtime in renderer.py) ---
FONT_TITLE_SIZE = 22
FONT_BODY_SIZE  = 16
FONT_SMALL_SIZE = 13

# --- Pawn ---
PAWN_RADIUS_RATIO = 0.35   # Fraction of CELL_SIZE used as pawn radius

# --- Wall hover tolerance ---
# How many pixels from the centre of a gap the mouse must be to trigger a hover
GAP_HIT_MARGIN = 8

# --- AI think delay (milliseconds) ---
AI_THINK_MS = 400
