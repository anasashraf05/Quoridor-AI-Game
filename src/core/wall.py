from src.core.enums import Orientation

class Wall:
    def __init__(self, row, col, orientation):
        """
        row, column: the coordinates of the wall's anchor point
        orientation: 'horizontal' or 'vertical'
        """
        self.row = row
        self.col = col
        self.orientation = orientation
    
    def get_blocked_edges(self):
        """
        Calculates exactly which cell-to-cell movements are blocked by this specific wall.
        Returns a list of coordinate pairs that can no longer be traversed.
        """
        row = self.row
        col = self.col

        blocked_edges = []

        if self.orientation == Orientation.HORIZONTAL:
            blocked_edges.append(((row, col), (row + 1, col)))
            blocked_edges.append(((row, col + 1), (row + 1, col + 1)))
        
        if self.orientation == Orientation.VERTICAL:
            blocked_edges.append(((row, col), (row, col + 1)))
            blocked_edges.append(((row + 1, col), (row + 1, col + 1)))
        
        return blocked_edges