class Rules:
    @staticmethod
    def is_valid_pawn_move(board, current_pos, target_pos):
        """
        Checks if the pawn move is valid:
        1. Is it exactly one step orthogonally?
        2. Is there a wall blocking the way?
        3. Is there an opponent blocking? (Handles jumping logic)
        """
        pass

    @staticmethod
    def is_valid_wall_placement(board, new_wall):
        """
        Checks if a wall placement is valid:
        1. Is it within the board boundaries?
        2. Does it overlap or cross any existing walls?
        """
        pass

    @staticmethod
    def is_winner(player):
        """
        Checks if the player's current position matches their assigned goal_row.
        """
        pass