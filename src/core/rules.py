from src.core.pathfinder import Pathfinder
from src.core.enums import Orientation


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

        # 1. OUT OF BOUNDS: Target must be inside the 9x9 grid (rows/cols 1 to 9)
        if not (0 < r2 <= 9 and 0 < c2 <= 9):
            return False

        # 2. FIND THE OPPONENT
        opponent_pos = None
        for pid, pos in board.pawn_positions.items():
            if pos != current_pos:
                opponent_pos = pos

        # 3. OCCUPIED: Cannot land on the opponent's square
        if target_pos == opponent_pos:
            return False

        row_diff = abs(r2 - r1)
        col_diff = abs(c2 - c1)
        distance = row_diff + col_diff

        # 4. STANDARD MOVE (1 step orthogonally)
        if distance == 1:
            if board.has_wall_between(current_pos, target_pos):
                return False
            return True

        # 5. STRAIGHT JUMP (2 steps in a straight line over the opponent)
        elif distance == 2 and (row_diff == 0 or col_diff == 0):
            middle_r = (r1 + r2) // 2
            middle_c = (c1 + c2) // 2
            middle_pos = (middle_r, middle_c)

            # Opponent must be in the middle square
            if middle_pos != opponent_pos:
                return False

            # No walls may block either leg of the jump
            if (board.has_wall_between(current_pos, middle_pos) or
                    board.has_wall_between(middle_pos, target_pos)):
                return False

            return True

        # 6. DIAGONAL JUMP (1 step row + 1 step col — only when straight jump is blocked)
        elif row_diff == 1 and col_diff == 1:
            if opponent_pos is None:
                return False

            opp_r, opp_c = opponent_pos

            # Opponent must be adjacent to the current player
            if abs(opp_r - r1) + abs(opp_c - c1) != 1:
                return False

            # No wall between us and the opponent
            if board.has_wall_between(current_pos, opponent_pos):
                return False

            dr = opp_r - r1
            dc = opp_c - c1
            jump_r = opp_r + dr
            jump_c = opp_c + dc
            jump_pos = (jump_r, jump_c)

            # Diagonal is only allowed if the straight jump is impossible
            if (0 < jump_r <= 9 and 0 < jump_c <= 9 and
                    not board.has_wall_between(opponent_pos, jump_pos)):
                return False

            # The diagonal path itself must not be walled off
            if board.is_diagonal_path_blocked(opponent_pos, target_pos):
                return False

            if board.has_wall_between(opponent_pos, target_pos):
                return False

            return True

        return False

    @staticmethod
    def is_valid_wall_placement(board, new_wall):
        """
        Checks if a wall placement is valid:
        1. Within board boundaries.
        2. Does not overlap or cross existing walls.
        3. Does not completely block either player's path to their goal.
        """
        wall_row = new_wall.row
        wall_col = new_wall.col
        orientation = new_wall.orientation

        # 1. OUT OF BOUNDS (anchor must be in 1–8 so the 2-cell wall fits)
        if not (0 < wall_row < 9 and 0 < wall_col < 9):
            return False

        # 2. OVERLAP / CROSS check against all existing walls
        for existing_wall in board.get_all_walls():
            row_diff = abs(existing_wall.row - wall_row)
            col_diff = abs(existing_wall.col - wall_col)

            if orientation == existing_wall.orientation:
                if orientation == Orientation.HORIZONTAL:
                    # Same-orientation walls in the same row within 1 column overlap
                    if row_diff == 0 and col_diff <= 1:
                        return False
                elif orientation == Orientation.VERTICAL:
                    # Same-orientation walls in the same column within 1 row overlap
                    if col_diff == 0 and row_diff <= 1:
                        return False
            else:
                # Cross check: a horizontal and vertical wall cross if same anchor
                if wall_row == existing_wall.row and wall_col == existing_wall.col:
                    return False

        # 3. PATH CHECK — temporarily place the wall and run BFS for both players
        board.walls.append(new_wall)
        p1_ok = Pathfinder.path_exists(board, board.get_pawn_position(1), [9])
        p2_ok = Pathfinder.path_exists(board, board.get_pawn_position(2), [1])
        board.walls.pop()

        if not (p1_ok and p2_ok):
            return False

        return True

    @staticmethod
    def is_winner(player):
        """
        Checks if the player's current position matches their assigned goal_row.
        """
        r, c = player.position
        return r == player.goal_row