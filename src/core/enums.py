from enum import Enum, auto

class GameMode(Enum):
    PVP = auto()
    PVE = auto()

class ItemType(Enum):
    PAWN_SQUARE = auto()
    WALL_GAP_HORIZONTAL = auto()
    WALL_GAP_VERTICAL = auto()
    HIGHLIGHT_DOT       = auto()

class Orientation(Enum):
    VERTICAL = auto()
    HORIZONTAL = auto()

class DIFFICULTY(Enum):
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()