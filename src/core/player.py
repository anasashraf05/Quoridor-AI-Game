class Player:
    def __init__(self, player_id, start_pos, goal_row):
        """
        Sets up the player.
        player_id: 1 or 2
        start_position: (x, y) tuple of their starting square
        goal_row: the row number (0 or 8) they need to reach to win
        """
        self.player_id = player_id
        self.position = start_pos
        self.goal_row = goal_row
        self.walls_left = 10

    def use_wall(self):
        """Decrements the player's wall count by 1."""
        if self.has_walls_left():
            self.walls_left -= 1 #amgad it was self.walls_left -=  self.walls_left, which is wrong because it will set walls_left to 0 after the first use
        
    def has_walls_left(self):
        """Returns True if walls_left > 0, otherwise False."""
        return  self.walls_left > 0