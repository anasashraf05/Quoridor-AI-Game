import src.ui.main_window       # check this import, we just need square_grids
#amgad we will need to implement all valid moves for AI to see all the valid moves

class Rules:
    @staticmethod
    def is_valid_pawn_move(board, current_pos, target_pos):
        """
        Checks if the pawn move is valid:
        1. Is it exactly one step orthogonally?
        2. Is there a wall blocking the way?
        3. Is there an opponent blocking? (Handles jumping logic)
        """
        r1, c1 = current_pos
        r2, c2 = target_pos

        # 1. OUT OF BOUNDS: Target must be inside the 9x9 grid (0 to 8)
        if not (0 <= r2 < 9 and 0 <= c2 < 9): # amgad check be < 9 not <= 8
            return False

        # 2. FIND THE OPPONENT: Ask the board where the other guy is
        opponent_pos = None
        for pid, pos in board.pawn_positions.items():
            if pos != current_pos:
                opponent_pos = pos  # ask amgad can the opponent pos still be none

        # 3. OCCUPIED: You cannot land exactly on your opponent's head
        if target_pos == opponent_pos:
            return False

        row_diff = abs(r2 - r1)
        col_diff = abs(c2 - c1)
        distance = row_diff + col_diff

        # 4. STANDARD MOVE (1 step away up, down, left, or right)
        if distance == 1:
            # Check if a wall is blocking the path
            if board.has_wall_between(current_pos, target_pos):
                return False
            return True

        # 5. STRAIGHT JUMP (2 steps in a straight line)
        elif distance == 2 and (row_diff == 0 or col_diff == 0):
            # To jump, the opponent MUST be exactly in the middle square
            middle_r = (r1 + r2) // 2
            middle_c = (c1 + c2) // 2
            middle_pos = (middle_r, middle_c)

            if middle_pos != opponent_pos:
                return False

            # The jump is only valid if NO walls block the way up to the opponent, 
            # and NO walls block the way down behind the opponent.
            if board.has_wall_between(current_pos, middle_pos) or board.has_wall_between(middle_pos, target_pos):
                return False
                
            return True

        # 6. DIAGONAL JUMP (1 step row, 1 step col)
        elif row_diff == 1 and col_diff == 1:  
            # Diagonal jumps in Quoridor are complex! You can only do them if the 
            # straight jump is blocked by a wall. We will add this beast later

            opp_r, opp_c = opponent_pos

            if abs(opp_r - r1) + abs(opp_c - c1) != 1:
                # Opponent is not adjacent, so diagonal jump is not possible
                return False
            
            dr = opp_r - r1
            dc = opp_c - c1
            jump_r = opp_r + dr
            jump_c = opp_c + dc
            jump_pos = (jump_r, jump_c)

            # straight jump is possible, so diagonal jump is not allowed
            if (0 <= jump_r < 9 and 0 <= jump_c < 9 and not board.has_wall_between(opponent_pos,jump_pos)):
                return False 
            
            # check if diagonal path is blocked by a wall
            if board.is_diagonal_path_blocked(opponent_pos, target_pos):
                return False
                       
            return True

        # If it's none of the above (e.g., trying to teleport 3 spaces away), it's illegal
        return False

    @staticmethod
    def is_valid_wall_placement(board, new_wall):
        """
        Checks if a wall placement is valid:
        1. Is it within the board boundaries?
        2. Does it overlap or cross any existing walls?
        3. Does it leave at least one valid path for both players to reach their goals? (after we implement pathfinder)
        """
        wall_row = new_wall.row
        wall_col = new_wall.col
        orientation = new_wall.orientation
        if orientation not in ['horizontal', 'vertical']: # wrong orientation
            return False
        
        # 1. OUT OF BOUNDS: The anchor point of the wall must be within the 8x8 area (since it occupies 2 spaces)
        if not (0 <= wall_row < 8 and 0 <= wall_col< 8): 
            return False
        
        # 2. OVERLAP/CROSS: Check against all existing walls
        for existing_wall in board.get_all_walls():
            row_diff = abs(existing_wall.row - wall_row)
            col_diff = abs(existing_wall.col - wall_col)

            if orientation == existing_wall.orientation:
                # Same orientation: Check if they share the same anchor point
                if ( row_diff==0 or row_diff ==1) and wall_col == existing_wall.col:
                    return False
                if ( col_diff==0 or col_diff ==1) and wall_row == existing_wall.row:
                    return False
            else:
                # Check for crossing
                if orientation != existing_wall.orientation:
                    if wall_row == existing_wall.row and wall_col == existing_wall.col:
                        return False
                    
        return True

    @staticmethod
    def is_winner(player):
        """
        Checks if the player's current position matches their assigned goal_row.
        """
        r1, c1 = player.position
        return r1 == player.goal_row
    

    