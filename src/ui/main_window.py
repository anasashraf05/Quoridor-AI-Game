from PyQt6 import QtWidgets, QtGui, QtCore, uic
from src.core.enums import GameMode, ItemType, Orientation


class MainWindow(QtWidgets.QMainWindow):
    SQUARE_SIZE = 50
    GAP_SIZE    = 15
    square_grids = 9
    total_grids  = 2 * square_grids - 1

    # How long (ms) the red invalid-wall flash stays visible
    INVALID_WALL_FLASH_MS = 600

    def __init__(self, controller):
        super().__init__()
        uic.loadUi('src/ui/main_window.ui', self)
        self.controller = controller

        # Scene
        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        # Timer used to revert the invalid-wall red flash
        self.revert_timer = QtCore.QTimer(self)
        self.revert_timer.setSingleShot(True)
        self.revert_timer.timeout.connect(self._revert_invalid_wall)
        self._invalid_wall_item = None   # QGraphicsRectItem shown during flash

        # Track highlight dots so we can remove them later
        self._highlight_items = []

        # Wire the Restart button
        self.restartButton.clicked.connect(self.controller.reset_game)

        # Forward clicks on the graphics view to this window for game input
        self.graphicsView.viewport().installEventFilter(self)

        # Draw initial board and pawns
        self.draw_board()
        self.draw_init_position()

    # ------------------------------------------------------------------ #
    #  Board drawing
    # ------------------------------------------------------------------ #

    def draw_board(self):
        for row in range(self.total_grids):
            for col in range(self.total_grids):
                x_pos = (col // 2) * (self.SQUARE_SIZE + self.GAP_SIZE) + (col % 2) * self.SQUARE_SIZE
                y_pos = (row // 2) * (self.SQUARE_SIZE + self.GAP_SIZE) + (row % 2) * self.SQUARE_SIZE
                rect = None

                if row % 2 == 0 and col % 2 == 0:
                    rect = self.draw_square(x_pos, y_pos, row, col, "tan")
                else:
                    if col % 2 == 1 and row % 2 == 0:
                        if row < self.total_grids - 1:
                            rect = self.draw_wall(x_pos, y_pos, row, col,
                                                  ItemType.WALL_GAP_VERTICAL, "white")
                    if col % 2 == 0 and row % 2 == 1:
                        if col < self.total_grids - 1:
                            rect = self.draw_wall(x_pos, y_pos, row, col,
                                                  ItemType.WALL_GAP_HORIZONTAL, "white")

                if rect is not None:
                    self.scene.addItem(rect)

    def draw_init_position(self):
        radius   = self.SQUARE_SIZE * 0.3
        diameter = radius * 2

        centerX = (self.SQUARE_SIZE + self.GAP_SIZE) * (self.square_grids // 2) + (self.SQUARE_SIZE / 2)

        centerY_p1 = 0 * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)
        centerY_p2 = (self.square_grids - 1) * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)

        self.p1_pawn = self.draw_pawn(centerX - radius, centerY_p1 - radius, diameter, "blue")
        self.scene.addItem(self.p1_pawn)

        self.p2_pawn = self.draw_pawn(centerX - radius, centerY_p2 - radius, diameter, "red")
        self.scene.addItem(self.p2_pawn)

    # ------------------------------------------------------------------ #
    #  Primitive drawing helpers
    # ------------------------------------------------------------------ #

    def draw_pawn(self, x_pos, y_pos, diameter, color):
        pawn = QtWidgets.QGraphicsEllipseItem(0, 0, diameter, diameter)
        pawn.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        pawn.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black, 2))
        pawn.setPos(x_pos, y_pos)
        return pawn

    def draw_square(self, x_pos, y_pos, row, col, color):
        rect = QtWidgets.QGraphicsRectItem(x_pos, y_pos, self.SQUARE_SIZE, self.SQUARE_SIZE)
        rect.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        rect.setData(0, ItemType.PAWN_SQUARE)
        rect.setData(1, (row // 2 + 1, col // 2 + 1))
        return rect

    def draw_wall(self, x_pos, y_pos, row, col, itemType, color):
        width  = self.GAP_SIZE if itemType == ItemType.WALL_GAP_VERTICAL \
                 else 2 * self.SQUARE_SIZE + self.GAP_SIZE
        height = 2 * self.SQUARE_SIZE + self.GAP_SIZE if itemType == ItemType.WALL_GAP_VERTICAL \
                 else self.GAP_SIZE

        rect = QtWidgets.QGraphicsRectItem(x_pos, y_pos, width, height)
        if color == "transparent":
            rect.setBrush(QtCore.Qt.GlobalColor.transparent)
            rect.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
        else:
            rect.setBrush(QtGui.QBrush(QtGui.QColor(color)))
            rect.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black))

        rect.setData(0, itemType)
        rect.setData(1, (row // 2 + 1, col // 2 + 1))
        return rect

    # ------------------------------------------------------------------ #
    #  Public interface called by GameController
    # ------------------------------------------------------------------ #

    def move_pawn(self, player_id, logical_coords):
        row, col = logical_coords
        radius = self.SQUARE_SIZE * 0.3
        cx = (col - 1) * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)
        cy = (row - 1) * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)
        if player_id == 1:
            self.p1_pawn.setPos(cx - radius, cy - radius)
        elif player_id == 2:
            self.p2_pawn.setPos(cx - radius, cy - radius)

    def place_wall_visually(self, logical_row, logical_col, orientation, color="saddlebrown"):
        r = logical_row - 1
        c = logical_col - 1
        x_offset = c * (self.SQUARE_SIZE + self.GAP_SIZE)
        y_offset = r * (self.SQUARE_SIZE + self.GAP_SIZE)

        if str(orientation).endswith("HORIZONTAL") or orientation == "horizontal":
            x_pos     = x_offset
            y_pos     = y_offset + self.SQUARE_SIZE
            item_type = ItemType.WALL_GAP_HORIZONTAL
        else:
            x_pos     = x_offset + self.SQUARE_SIZE
            y_pos     = y_offset
            item_type = ItemType.WALL_GAP_VERTICAL

        wall_item = self.draw_wall(x_pos, y_pos, 0, 0, item_type, color)
        self.scene.addItem(wall_item)
        return wall_item

    def update_walls_left_display(self):
        """Refresh the two wall-count labels from the controller's player list."""
        try:
            players = self.controller.players
            self.p1WallLabel.setText(f"Player 1 Walls: {players[0].walls_left}")
            self.p2WallLabel.setText(f"Player 2 Walls: {players[1].walls_left}")
        except Exception:
            pass

    def update_turn_label(self, player_id: int):
        try:
            self.turnLabel.setText(f"Player {player_id}'s Turn")
        except Exception:
            pass

    # Keep old name working too (teammate's controller uses this)
    def update_wall_counts(self, players):
        try:
            self.p1WallLabel.setText(f"Player 1 Walls: {players[0].walls_left}")
            self.p2WallLabel.setText(f"Player 2 Walls: {players[1].walls_left}")
        except Exception:
            pass

    def schedule_ai(self):
        if self.controller and self.controller.game_mode == GameMode.PVE:
            QtCore.QTimer.singleShot(500, self.controller.execute_ai_turn)

    # ------------------------------------------------------------------ #
    #  Move highlights
    # ------------------------------------------------------------------ #

    def highlight_square(self, row, col):
        """Draw a semi-transparent green dot on a reachable square."""
        r = row - 1
        c = col - 1
        cx = c * (self.SQUARE_SIZE + self.GAP_SIZE) + self.SQUARE_SIZE / 2
        cy = r * (self.SQUARE_SIZE + self.GAP_SIZE) + self.SQUARE_SIZE / 2
        dot_r = self.SQUARE_SIZE * 0.18
        dot = QtWidgets.QGraphicsEllipseItem(cx - dot_r, cy - dot_r, dot_r * 2, dot_r * 2)
        dot.setBrush(QtGui.QBrush(QtGui.QColor(0, 200, 0, 160)))
        dot.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
        dot.setData(0, ItemType.HIGHLIGHT_DOT)
        self.scene.addItem(dot)
        self._highlight_items.append(dot)

    def clear_highlights(self):
        """Remove all move-highlight dots."""
        for item in self._highlight_items:
            self.scene.removeItem(item)
        self._highlight_items.clear()

    # ------------------------------------------------------------------ #
    #  Invalid wall feedback (red flash)
    # ------------------------------------------------------------------ #

    def show_invalid_wall_feedback(self, logical_row, logical_col, orientation):
        """Flash the attempted wall position in red for INVALID_WALL_FLASH_MS ms."""
        self.revert_timer.stop()
        self._revert_invalid_wall()   # clear any previous flash

        wall_item = self.place_wall_visually(logical_row, logical_col, orientation, color="red")
        self._invalid_wall_item = wall_item
        self.revert_timer.start(self.INVALID_WALL_FLASH_MS)

    def _revert_invalid_wall(self):
        """Remove the red flash item."""
        if self._invalid_wall_item is not None:
            self.scene.removeItem(self._invalid_wall_item)
            self._invalid_wall_item = None

    # ------------------------------------------------------------------ #
    #  Reset helpers (called by GameController.reset_game)
    # ------------------------------------------------------------------ #

    def reset_board_visuals(self):
        """
        Clear everything from the scene and redraw the empty board + pawns.
        Called by GameController._refresh_ui_after_state_change (undo/redo/load).
        """
        self.revert_timer.stop()
        self._invalid_wall_item = None
        self._highlight_items.clear()
        self.scene.clear()
        self.draw_board()
        self.draw_init_position()

    # ------------------------------------------------------------------ #
    #  Win dialog
    # ------------------------------------------------------------------ #

    def show_winner(self, player_id):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Game Over")
        msg.setText(f"Player {player_id} wins! 🎉")
        msg.exec()

    # ------------------------------------------------------------------ #
    #  Mouse input
    # ------------------------------------------------------------------ #

    def eventFilter(self, watched, event):
        if watched is self.graphicsView.viewport() and \
           event.type() == QtCore.QEvent.Type.MouseButtonPress and \
           event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._handle_graphics_view_click(event.pos())
            return True
        return super().eventFilter(watched, event)

    def mousePressEvent(self, event):
        self._handle_graphics_view_click(event.globalPosition().toPoint())

    def _handle_graphics_view_click(self, point):
        view_point  = self.graphicsView.mapFromGlobal(point)
        scene_point = self.graphicsView.mapToScene(view_point)
        clicked_item = self.scene.itemAt(scene_point, self.graphicsView.transform())

        if clicked_item is None:
            return

        item_type      = clicked_item.data(0)
        logical_coords = clicked_item.data(1)

        # Ignore highlight dots — treat the underlying square as the click target
        if item_type == ItemType.HIGHLIGHT_DOT:
            # Find the square underneath
            items = self.scene.items(scene_point)
            for it in items:
                if it.data(0) == ItemType.PAWN_SQUARE:
                    logical_coords = it.data(1)
                    item_type      = ItemType.PAWN_SQUARE
                    break
            else:
                return

        if item_type == ItemType.PAWN_SQUARE:
            self.controller.handle_pawn_move_attempt(
                (logical_coords[0], logical_coords[1]))

        elif item_type == ItemType.WALL_GAP_HORIZONTAL:
            self.controller.handle_wall_placement_attempt(
                logical_coords[0], logical_coords[1], Orientation.HORIZONTAL)

        elif item_type == ItemType.WALL_GAP_VERTICAL:
            self.controller.handle_wall_placement_attempt(
                logical_coords[0], logical_coords[1], Orientation.VERTICAL)