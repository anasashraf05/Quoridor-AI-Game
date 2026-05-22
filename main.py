import sys
from PyQt6.QtWidgets import QApplication

# Import your Controller and UI
from src.controller import GameController
from src.ui import MainWindow
from src.core.enums import GameMode

from PyQt6.QtWidgets import QInputDialog

def choose_settings():
    mode, ok = QInputDialog.getItem(
        None,
        "Game Mode",
        "Choose Mode:",
        ["Player vs Player", "Player vs AI"],
        0,
        False
    )

    if not ok:
        sys.exit()

    if mode == "Player vs Player":
        return GameMode.PVP, None

    difficulty, ok = QInputDialog.getItem(
        None,
        "Difficulty",
        "Choose AI Difficulty:",
        ["Easy", "Medium", "Hard"],
        1,
        False
    )

    if not ok:
        sys.exit()

    from src.core.enums import DIFFICULTY

    diff_map = {
        "Easy": DIFFICULTY.EASY,
        "Medium": DIFFICULTY.MEDIUM,
        "Hard": DIFFICULTY.HARD
    }

    return GameMode.PVE, diff_map[difficulty]


def main():
    app = QApplication(sys.argv)

    mode, difficulty = choose_settings()

    controller = GameController(mode=mode, ai_difficulty=difficulty)

    window = MainWindow(controller)
    controller.ui = window

    controller.start_game()

    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()