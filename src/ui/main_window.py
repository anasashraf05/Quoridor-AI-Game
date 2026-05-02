import sys
import os
from pathlib import Path

from matplotlib.pylab import dot, size

# Add project root to sys.path so 'src' package is discoverable
project_root = Path(__file__).resolve().parents[2]  # Goes up 2 levels: ui -> src -> project_root
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now imports will work
from PyQt6 import QtWidgets, QtGui, QtCore, uic
import src.core.enums
from src.core.enums import ItemType, Orientation  # Optional: cleaner imports

class MainWindow(QtWidgets.QMainWindow):
    SQUARE_SIZE = 50  # Pixels for the pawn squares
    GAP_SIZE = 15    # Pixels for the wall gaps
    square_grids = 9  # Visual Square grids  
    total_grids = 2 * square_grids - 1 # Total grids including wall grids

    def __init__(self, controller):
        super().__init__()
        uic.loadUi('src/ui/main_window.ui', self)
        self.controller = controller

        # 1. Create the Stage (Scene)
        self.scene = QtWidgets.QGraphicsScene()
        
        # 2. Attach the stage to the Graphics View you made in Qt Designer
        # (Assuming you named it 'graphicsView' in Qt Designer)
        self.graphicsView.setScene(self.scene) 

        # 3. Draw the board
        self.draw_board()
        self.draw_init_position()

        # 4. This will keep track of any highlighted squares 
        self.highlight_items = []

    def draw_init_position(self):
        # 1. Define the size of your pawn (e.g., 30% of the square size so it fits nicely)
        radius = self.SQUARE_SIZE * 0.3  
        diameter = radius * 2

        # 2. Your math for the center X coordinate (Middle column)
        # Note: I am assuming self.square_grids is 9
        centerX = (self.SQUARE_SIZE + self.GAP_SIZE) * (self.square_grids // 2) + (self.SQUARE_SIZE / 2)

        # 3. Calculate the center Y coordinate
        # Player 1 usually starts at the very top row (row 0)
        centerY_player1 = 0 * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)
        
        # Player 2 usually starts at the very bottom row (row 8)
        centerY_player2 = (self.square_grids - 1) * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)

        # 4. Calculate the top-left corners for PyQt
        p1_x = centerX - radius
        p1_y = centerY_player1 - radius
        
        p2_x = centerX - radius
        p2_y = centerY_player2 - radius

        # 5. Draw Player 1's Pawn (Let's make it Blue)
        self.p1_pawn = self.draw_pawn(p1_x, p1_y, diameter, "blue")
        self.scene.addItem(self.p1_pawn)

        # 6. Draw Player 2's Pawn (Let's make it Red)
        self.p2_pawn = self.draw_pawn(p2_x, p2_y, diameter, "red")
        self.scene.addItem(self.p2_pawn)
    
    def draw_board(self):
        # Loop to create the 17x17 grid layout
        for row in range(self.total_grids):
            for col in range(self.total_grids):
                
                # Calculate X and Y pixel positions
                x_pos = (col // 2) * (self.SQUARE_SIZE + self.GAP_SIZE) + (col % 2) * self.SQUARE_SIZE
                y_pos = (row // 2) * (self.SQUARE_SIZE + self.GAP_SIZE) + (row % 2) * self.SQUARE_SIZE
                rect = None

                # EVEN rows/cols are Pawn Squares
                if row % 2 == 0 and col % 2 == 0:
                    rect = self.draw_square(x_pos, y_pos, row, col, "tan")  # Wooden color

                # ODD rows/cols are Wall Gaps (we leave them blank or draw tiny invisible rects for clicking)
                else:
                    if col % 2 == 1 and row % 2 == 0:
                        # For outer edges bug
                        if row < self.total_grids - 1:
                            rect = self.draw_wall(x_pos, y_pos, row, col, ItemType.WALL_GAP_VERTICAL, "white")

                    if col % 2 == 0 and row % 2 == 1:
                        # For outer edges bug
                        if col < self.total_grids - 1:
                            rect = self.draw_wall(x_pos, y_pos, row, col, ItemType.WALL_GAP_HORIZONTAL, "white")
                        
                if rect is not None:
                    self.scene.addItem(rect)

    def draw_pawn(self, x_pos, y_pos, diameter, color):
        pawn = QtWidgets.QGraphicsEllipseItem(0, 0, diameter, diameter)
        pawn.setBrush(QtGui.QBrush(QtGui.QColor(color)))
        pawn.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black, 2)) # 2px black border

        # We use setPos to handle the coordinates instead
        pawn.setPos(x_pos, y_pos)
        return pawn
    
    def draw_square(self, x_pos, y_pos, row, col, color):
        rect = QtWidgets.QGraphicsRectItem(x_pos, y_pos, self.SQUARE_SIZE, self.SQUARE_SIZE)
        rect.setBrush(QtGui.QBrush(QtGui.QColor(color)))       
        # You can attach data to this rectangle so when it's clicked, 
        # you know exactly which logical board square it is!
        rect.setData(0, src.core.enums.ItemType.PAWN_SQUARE)
        rect.setData(1, (row//2 + 1, col//2 + 1))       # One index based

        return rect

    def draw_wall(self, x_pos, y_pos, row, col, itemType, color):
        width = self.GAP_SIZE if itemType == ItemType.WALL_GAP_VERTICAL else 2 * self.SQUARE_SIZE + self.GAP_SIZE
        height = 2 * self.SQUARE_SIZE + self.GAP_SIZE if itemType == ItemType.WALL_GAP_VERTICAL else self.GAP_SIZE

        rect = QtWidgets.QGraphicsRectItem(x_pos, y_pos, width, height)
        if color == "transparent":
            # Set brush to invisible
            rect.setBrush(QtCore.Qt.GlobalColor.transparent)
            # Set border (pen) to invisible
            rect.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))
        else:
            # Normal colors for when a wall is ACTUALLY placed later!
            rect.setBrush(QtGui.QBrush(QtGui.QColor(color)))
            rect.setPen(QtGui.QPen(QtCore.Qt.GlobalColor.black))

        rect.setData(0, itemType)
        rect.setData(1, (row//2 + 1, col//2 + 1))       # One index based

        return rect
    #TODO: CLEAN THIS SHIT
    def place_wall_visually(self, logical_row, logical_col, orientation):
        # 1. Convert 1-based logical coordinates back to 0-based for pixel math
        r = logical_row - 1
        c = logical_col - 1

        # 2. Find the top-left corner of the adjacent pawn square
        x_offset = c * (self.SQUARE_SIZE + self.GAP_SIZE)
        y_offset = r * (self.SQUARE_SIZE + self.GAP_SIZE)

        # 3. Shift the coordinates into the gap based on orientation
        # (This safely handles both string "horizontal" and Enum Orientation.HORIZONTAL)
        if str(orientation).endswith("HORIZONTAL") or orientation == "horizontal":
            # Horizontal walls sit directly BELOW the row's square
            x_pos = x_offset
            y_pos = y_offset + self.SQUARE_SIZE
            item_type = ItemType.WALL_GAP_HORIZONTAL
            
        else:
            # Vertical walls sit directly to the RIGHT of the column's square
            x_pos = x_offset + self.SQUARE_SIZE
            y_pos = y_offset
            item_type = ItemType.WALL_GAP_VERTICAL

        # 4. Use your existing draw method, but make it a solid color (e.g., saddlebrown)
        # Note: We pass 0, 0 for row/col here because this visual overlay doesn't need to be clicked again
        solid_wall = self.draw_wall(x_pos, y_pos, 0, 0, item_type, "saddlebrown")

        # 5. Add it to the stage!
        self.scene.addItem(solid_wall)

    def move_pawn(self, player_id, logical_coords):
        row, col = logical_coords
        visual_row = row - 1    # Convert back into 0 based index      
        visual_col = col - 1

        # Your math to convert logical grid to pixel coordinates
        radius = self.SQUARE_SIZE * 0.3
        
        # Calculate the center of the clicked square
        cx = visual_col * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)
        cy = visual_row * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2)
        
        # Calculate top-left corner for the circle
        new_x = cx - radius
        new_y = cy - radius
        
        # Move the correct pawn!
        if player_id == 1:
            self.p1_pawn.setPos(new_x, new_y)
        elif player_id == 2:
            self.p2_pawn.setPos(new_x, new_y)        
    
    def clear_highlights(self):
        """ Removes all green dots from the board """
        for item in self.highlight_items:
            self.scene.removeItem(item)
        self.highlight_items = []
    
    def highlight_square(self, logical_row, logical_col): # amgad when u try don't click on the highlight point it self click any place on the square to move
        r, c = logical_row - 1, logical_col - 1
        size = 15
        cx = c * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2) - (size / 2)
        cy = r * (self.SQUARE_SIZE + self.GAP_SIZE) + (self.SQUARE_SIZE / 2) - (size / 2)
    
        dot = QtWidgets.QGraphicsEllipseItem(cx, cy, size, size)
        dot.setBrush(QtGui.QColor(0, 255, 0, 100))  # Transparent Green
        dot.setPen(QtGui.QPen(QtCore.Qt.PenStyle.NoPen))

        dot.setAcceptedMouseButtons(QtCore.Qt.MouseButton.NoButton)
    
        dot.setZValue(1)  # Keep it visually on top
        self.scene.addItem(dot)
        self.highlight_items.append(dot)

    def show_winner(self, player_id):
        """ Displays win message and disables further interaction via controller flag """
        color = "Blue" if player_id == 1 else "Red"
        self.turnLabel.setText(f"GAME OVER: {color} Wins!")
        QtWidgets.QMessageBox.information(self, "Victory!", f"Player {player_id} has reached the goal!")

    def mousePressEvent(self, event):
        # 1. Get the exact (X, Y) pixel coordinates of the click relative to the scene
        # We map the global window click down into the graphics view stage
        view_point = self.graphicsView.mapFromGlobal(event.globalPosition().toPoint())
        scene_point = self.graphicsView.mapToScene(view_point)

        # 2. Ask PyQt: "Is there an item exactly at this point?"
        clicked_item = self.scene.itemAt(scene_point, self.graphicsView.transform())

        # 3. If they actually clicked a shape
        if clicked_item is not None:
            item_type = clicked_item.data(0)
            logical_coords = clicked_item.data(1) 

            if item_type == ItemType.PAWN_SQUARE:
                self.controller.handle_pawn_move_attempt((logical_coords[0], logical_coords[1]))
                
            elif item_type == ItemType.WALL_GAP_HORIZONTAL:
                self.controller.handle_wall_placement_attempt(logical_coords[0], logical_coords[1], Orientation.HORIZONTAL)

            elif item_type == ItemType.WALL_GAP_VERTICAL:
                self.controller.handle_wall_placement_attempt(logical_coords[0], logical_coords[1], Orientation.VERTICAL)