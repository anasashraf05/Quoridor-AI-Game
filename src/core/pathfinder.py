from collections import deque


class Pathfinder:

    @staticmethod
    def get_neighbors(board, pos):
        """Returns all valid positions reachable in one step (no walls blocking)."""
        r, c = pos
        neighbors = []

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc

            if not (0 < nr <= 9 and 0 < nc <= 9):
                continue

            next_pos = (nr, nc)

            if board.has_wall_between(pos, next_pos):
                continue

            neighbors.append(next_pos)

        return neighbors

    @staticmethod
    def path_exists(board, start_pos, goal_rows):
        """
        BFS to check whether at least one path exists from start_pos to any
        row in goal_rows. Returns True if reachable, False if trapped.
        """
        visited        = set()
        will_be_checked = deque()

        visited.add(start_pos)
        will_be_checked.append(start_pos)

        if start_pos[0] in goal_rows:
            return True

        while will_be_checked:
            current_pos = will_be_checked.popleft()

            for neighbor in Pathfinder.get_neighbors(board, current_pos):
                if neighbor in visited:
                    continue
                if neighbor[0] in goal_rows:
                    return True
                visited.add(neighbor)
                will_be_checked.append(neighbor)

        return False

    @staticmethod
    def get_shortest_path_length(board, start_pos, goal_row):
        """
        BFS to find the minimum number of steps from start_pos to goal_row.
        Returns float('inf') if no path exists.
        """
        if start_pos[0] == goal_row:
            return 0

        if not Pathfinder.path_exists(board, start_pos, {goal_row}):
            return float('inf')

        visited        = set()
        will_be_checked = deque()

        visited.add(start_pos)
        will_be_checked.append((start_pos, 0))

        while will_be_checked:
            current_pos, distance = will_be_checked.popleft()

            if current_pos[0] == goal_row:
                return distance

            for neighbor in Pathfinder.get_neighbors(board, current_pos):
                if neighbor not in visited:
                    visited.add(neighbor)
                    will_be_checked.append((neighbor, distance + 1))

        return float('inf')