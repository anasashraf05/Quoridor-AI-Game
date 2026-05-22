import sys
import os
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from PyQt6 import QtWidgets, QtGui, QtCore, uic
import src.core.enums
from src.core.enums import ItemType, Orientation


class MainWindow(QtWidgets.QMainWindow):
    SQUARE_SIZE = 50
    GAP_SIZE    = 15
    square_grids = 9
    total_grids  = 2 * square_grids - 1

    # How long (ms) the red-flash on an invalid wall lasts
    INVALID_WALL_FLASH_MS = 600

    def __init__(self, controller):
        super().__init__()
        uic.loadUi('src/ui/main_window.ui', self)
        self.controller = controller

        self.scene = QtWidgets.QGraphicsScene()
        self.graphicsView.setScene(self.scene)

        self.draw_board()
        self.draw_init_position()

        self.highlight_items  = []
        self.wall_preview_item = None

        self.graphicsView.setMouseTracking(True)
        self.graphicsView.installEventFilter(self)

        # Invalid-wall flash state
        self.invalid_wall_item      = None
        self.original_wall_brush    = None
        self.revert_timer = QtCore.QTimer(self)
        self.revert_timer.setSingleShot(True)
        self.revert_timer.timeout.connect(self._revert_invalid_wall)

        self.setMouseTracking(True)

        # Wire up buttons that are expected to exist in the .ui file
        self._connect_buttons()

    # ------------------------------------------------------------------ #
    #  Button wiring
    # ------------------------------------------------------------------ #

    def _connect_buttons(self):
        """Connect buttons defined in Qt Designer. Uses getattr so missing
        buttons don't crash the app."""
        reset_btn = getattr(self, "resetButton", None)
        if reset_btn:
            reset_btn.clicked.connect(self.controller.reset_game)

        undo_btn = getattr(self, "undoButton", None)
        if undo_btn:
            undo_btn.clicked.connect(self.controller.undo)

        redo_btn = getattr(self, "redoButton", None)
        if redo_btn:
            redo_btn.clicked.connect(self.controller.redo)

        save_btn = getattr(self, "saveButton", None)
        if save_btn:
            save_btn.clicked.connect(self.controller.save_game)

        load_btn = getattr(self, "loadButton", None)
        if load_btn:
            load_btn.clicked.connect(self.controller.load_game)

    # ------------------------------------------------------------------ #
    #  Board drawing
    # ------------------------------------------------------------------ #

    def draw_init_position(self):
        radius   = self.SQUARE_SIZE * 0.3
        diameter = radius * 2
        centerX  = (self.SQUARE_SIZE + self.GAP_SIZE) * (self.square_grids // 2) + (self.SQUARE_SIZE / 2)

        centerY_p1 = 0 * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)
        centerY_p2 = (self.square_grids - 1) * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)

        self.p1_pawn = self.draw_pawn(centerX - radius, centerY_p1 - radius, diameter, "blue")
        self.scene.addItem(self.p1_pawn)

        self.p2_pawn = self.draw_pawn(centerX - radius, centerY_p2 - radius, diameter, "red")
        self.scene.addItem(self.p2_pawn)

    def draw_board(self):
        for row in range(self.total_grids):
            for col in range(self.total_grids):
                x_pos = (col // 2) * (self.SQUARE_SIZE + self.GAP_SIZE) + (col % 2) * self.SQUARE_SIZE
                y_pos = (row // 2) * (self.SQUARE_SIZE + self.GAP_SIZE) + (row % 2) * self.SQUARE_SIZE
                rect = None

                if row % 2 == 0 and col % 2 == 0:
                    rect = self.draw_square(x_pos, y_pos, row, col, "tan")
                elif col % 2 == 1 and row % 2 == 0:
                    if row < self.total_grids - 1:
                        rect = self.draw_wall(x_pos, y_pos, row, col, ItemType.WALL_GAP_VERTICAL, "white")
                elif col % 2 == 0 and row % 2 == 1:
                    if col < self.total_grids - 1:
                        rect = self.draw_wall(x_pos, y_pos, row, col, ItemType.WALL_GAP_HORIZONTAL, "white")

                if rect is not None:
                    self.scene.addItem(rect)

    def draw_pawn(self, x_pos, y_pos, diameter, color):
        pawn = QtWidgets.QGraphicsEllipseItem(0, 0, diameter, diameter)
        pawn.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        pawn.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black, 2))
        pawn.setPos(x_pos, y_pos)
        pawn.setZValue(2)  # Always on top of highlights
        return pawn

    def draw_square(self, x_pos, y_pos, row, col, color):
        rect = QtWidgets.QGraphicsRectItem(x_pos, y_pos, self.SQUARE_SIZE, self.SQUARE_SIZE)
        rect.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        rect.setData(0, src.core.enums.ItemType.PAWN_SQUARE)
        rect.setData(1, (row // 2 + 1, col // 2 + 1))
        rect.setData(2, "BASE")
        rect.setZValue(0)
        return rect

    def draw_wall(self, x_pos, y_pos, row, col, itemType, color):
        width  = self.GAP_SIZE if itemType == ItemType.WALL_GAP_VERTICAL else 2 * self.SQUARE_SIZE + self.GAP_SIZE
        height = 2 * self.SQUARE_SIZE + self.GAP_SIZE if itemType == ItemType.WALL_GAP_VERTICAL else self.GAP_SIZE

        rect = QtWidgets.QGraphicsRectItem(x_pos, y_pos, width, height)
        if color == "transparent":
            rect.setBrush(QtCore.Qt.GlobalColor.transparent)
            rect.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
        else:
            rect.setBrush(QtGui.QBrush(QtGui.QColor(color)))
            rect.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black))

        rect.setData(0, itemType)
        rect.setData(1, (row // 2 + 1, col // 2 + 1))
        rect.setData(2, "BASE")
        rect.setAcceptHoverEvents(True)
        rect.setZValue(1)
        return rect

    # ------------------------------------------------------------------ #
    #  Visual state updates
    # ------------------------------------------------------------------ #

    def place_wall_visually(self, logical_row, logical_col, orientation):
        r = logical_row - 1
        c = logical_col - 1

        x_offset = c * (self.SQUARE_SIZE + self.GAP_SIZE)
        y_offset = r * (self.SQUARE_SIZE + self.GAP_SIZE)

        if str(orientation).endswith("HORIZONTAL") or orientation == "horizontal":
            x_pos    = x_offset
            y_pos    = y_offset + self.SQUARE_SIZE
            item_type = ItemType.WALL_GAP_HORIZONTAL
        else:
            x_pos    = x_offset + self.SQUARE_SIZE
            y_pos    = y_offset
            item_type = ItemType.WALL_GAP_VERTICAL

        solid_wall = self.draw_wall(x_pos, y_pos, 0, 0, item_type, "saddlebrown")
        solid_wall.setData(2, "PLACED_WALL")
        solid_wall.setZValue(3)
        self.scene.addItem(solid_wall)

    def move_pawn(self, player_id, logical_coords):
        row, col   = logical_coords
        visual_row = row - 1
        visual_col = col - 1
        radius     = self.SQUARE_SIZE * 0.3

        cx = visual_col * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)
        cy = visual_row * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)

        if player_id == 1:
            self.p1_pawn.setPos(cx - radius, cy - radius)
        elif player_id == 2:
            self.p2_pawn.setPos(cx - radius, cy - radius)

    def reset_board_visuals(self):
        """Remove everything except BASE squares/walls and the two pawns, then
        re-seat the pawns at their logical positions."""
        for item in list(self.scene.items()):
            tag = item.data(2) if hasattr(item, 'data') else None
            if tag == "PLACED_WALL":
                self.scene.removeItem(item)

        self.clear_highlights()

        # Reset wall-gap colours back to white
        for item in self.scene.items():
            if not hasattr(item, 'data'):
                continue
            itype = item.data(0)
            tag   = item.data(2)
            if tag == "BASE" and itype in (ItemType.WALL_GAP_HORIZONTAL, ItemType.WALL_GAP_VERTICAL):
                item.setBrush(QtGui.QBrush(QtGui.QColor("white")))

        # Reset pawn positions to start
        start_positions = {1: (1, 5), 2: (9, 5)}
        for pid, pos in start_positions.items():
            self.move_pawn(pid, pos)

    # ------------------------------------------------------------------ #
    #  Highlights
    # ------------------------------------------------------------------ #

    def clear_highlights(self):
        for item in self.highlight_items:
            self.scene.removeItem(item)
        self.highlight_items = []

    def highlight_square(self, logical_row, logical_col):
        r, c   = logical_row - 1, logical_col - 1
        size   = 20  # Slightly larger so it's easier to hit
        cx     = c * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2) - (size / 2)
        cy     = r * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2) - (size / 2)

        dot = QtWidgets.QGraphicsEllipseItem(cx, cy, size, size)
        dot.setBrush(QtGui.QColor(0, 200, 0, 130))
        dot.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))

        # KEY FIX: Accept mouse buttons so clicks land on the dot reach it,
        # but we tag it as a highlight so the click handler resolves to the
        # underlying square.
        dot.setAcceptedMouseButtons(QtCore.Qt.MouseButton.LeftButton)
        dot.setData(0, ItemType.HIGHLIGHT_DOT)         # new tag — handled in mousePressEvent
        dot.setData(3, (logical_row, logical_col))     # store target in slot 3

        dot.setZValue(1)
        self.scene.addItem(dot)
        self.highlight_items.append(dot)

    # ------------------------------------------------------------------ #
    #  Invalid wall feedback
    # ------------------------------------------------------------------ #

    def show_invalid_wall_feedback(self, row, col, orientation):
        """Flash the clicked wall gap red briefly."""
        for item in self.scene.items():
            if not hasattr(item, 'data'):
                continue
            coords    = item.data(1)
            item_type = item.data(0)
            tag       = item.data(2)

            if tag == "BASE" and coords == (row, col):
                if (
                    (orientation == Orientation.HORIZONTAL and item_type == ItemType.WALL_GAP_HORIZONTAL) or
                    (orientation == Orientation.VERTICAL   and item_type == ItemType.WALL_GAP_VERTICAL)
                ):
                    self._flash_wall_red(item)
                    break

    def _flash_wall_red(self, item):
        """Paint item red and schedule a revert."""
        # Cancel any pending revert for the previous item
        self.revert_timer.stop()
        if self.invalid_wall_item and self.invalid_wall_item is not item:
            self._revert_invalid_wall()

        self.original_wall_brush = item.brush()
        item.setBrush(QtGui.QBrush(QtGui.QColor(220, 40, 40, 200)))
        self.invalid_wall_item = item
        self.revert_timer.start(self.INVALID_WALL_FLASH_MS)

    def _revert_invalid_wall(self):
        if self.invalid_wall_item:
            self.invalid_wall_item.setBrush(QtGui.QBrush(QtGui.QColor("white")))
            self.invalid_wall_item   = None
            self.original_wall_brush = None

    # ------------------------------------------------------------------ #
    #  Walls-left label
    # ------------------------------------------------------------------ #

    def update_walls_left_display(self):
        if len(self.controller.players) >= 2:
            p1_walls = self.controller.players[0].walls_left
            p2_walls = self.controller.players[1].walls_left
            self.p1WallLabel.setText(f"Player 1 Walls: {p1_walls}")
            self.p2WallLabel.setText(f"Player 2 Walls: {p2_walls}")

    # ------------------------------------------------------------------ #
    #  Win screen
    # ------------------------------------------------------------------ #

    def show_winner(self, player_id):
        color = "Blue" if player_id == 1 else "Red"
        self.turnLabel.setText(f"GAME OVER: {color} Wins!")
        QtWidgets.QMessageBox.information(self, "Victory!", f"Player {player_id} has reached the goal!")

    # ------------------------------------------------------------------ #
    #  Mouse events
    # ------------------------------------------------------------------ #

    def _scene_point_from_event(self, event):
        view_point  = self.graphicsView.mapFromGlobal(event.globalPosition().toPoint())
        return self.graphicsView.mapToScene(view_point)

    def mousePressEvent(self, event):
        scene_point  = self._scene_point_from_event(event)
        clicked_item = self.scene.itemAt(scene_point, self.graphicsView.transform())

        if not clicked_item:
            return

        item_type     = clicked_item.data(0)
        logical_coords = clicked_item.data(1)

        # ---- Highlight dot: resolve to the square it sits on ----
        if item_type == ItemType.HIGHLIGHT_DOT:
            target = clicked_item.data(3)
            self.controller.handle_pawn_move_attempt(target)
            return

        if item_type is None or logical_coords is None:
            return

        if item_type == ItemType.PAWN_SQUARE:
            self.controller.handle_pawn_move_attempt((logical_coords[0], logical_coords[1]))

        elif item_type == ItemType.WALL_GAP_HORIZONTAL:
            self.controller.handle_wall_placement_attempt(
                logical_coords[0], logical_coords[1], Orientation.HORIZONTAL
            )

        elif item_type == ItemType.WALL_GAP_VERTICAL:
            self.controller.handle_wall_placement_attempt(
                logical_coords[0], logical_coords[1], Orientation.VERTICAL
            )

    def mouseMoveEvent(self, event):
        scene_point = self._scene_point_from_event(event)
        item        = self.scene.itemAt(scene_point, self.graphicsView.transform())

        if not item:
            return

        item_type = item.data(0)
        if item_type not in (ItemType.WALL_GAP_HORIZONTAL, ItemType.WALL_GAP_VERTICAL):
            return

        coords = item.data(1)
        if coords is None:
            return

        orient = (
            Orientation.HORIZONTAL
            if item_type == ItemType.WALL_GAP_HORIZONTAL
            else Orientation.VERTICAL
        )

        is_valid = self.controller.is_valid_wall_placement_preview(coords[0], coords[1], orient)

        if not is_valid:
            # Only flash if this is a new invalid item (avoid spamming)
            if item is not self.invalid_wall_item:
                self._flash_wall_red(item)