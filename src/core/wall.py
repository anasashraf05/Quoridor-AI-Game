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
        pass