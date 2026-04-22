import sys
from PyQt6.QtWidgets import QApplication

# Import your Controller and UI
from src.controller import GameController
from src.ui import MainWindow
from src.core.enums import GameMode

def main():
    # 1. Initialize the Qt Application (Required for any Qt program)
    app = QApplication(sys.argv)
    
    # 2. Create the Game Controller (The middleman)
    # Defaulting to Player vs Player for now!
    controller = GameController(mode= GameMode.PVP)
    
    # 3. Create the UI Window, passing it the controller so the UI can send click events
    window = MainWindow(controller)
    
    # 4. Give the controller a reference to the UI so it can update the screen
    controller.ui = window
    controller.start_game()
    
    # 5. Show the window!
    window.show()
    
    # 6. Start the Qt event loop (this keeps the window open and listening for clicks)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()