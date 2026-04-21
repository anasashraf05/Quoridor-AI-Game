from enum import Enum, auto

class GameMode(Enum):
    PVP = auto()
    PVE = auto()

class ItemType(Enum):
    PAWN_SQUARE = auto()
    WALL_GAP_HORIZONTAL = auto()
    WALL_GAP_VERTICAL = auto()

class Orientation(Enum):
    VERTICAL = auto()
    HORIZONTAL = auto()