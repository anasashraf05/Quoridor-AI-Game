from operator import pos

from src.core import board

from collections import deque


class Pathfinder:

    @staticmethod
    def get_neighbors(board, pos):
        """Returns all valid positions reachable in one move (no walls blocking)."""
        r, c = pos
        directions = [(-1,0), (1,0), (0,-1), (0,1)]
    
        neighbors = []
    
        for dr, dc in directions:
            nr, nc = r + dr, c + dc

            if 0 <= nr < 9 and 0 <= nc < 9: # boundary check
                continue

            next_pos = (nr, nc) #

            if board.has_wall_between(pos, next_pos): # wall check
                continue

            neighbors.append((nr, nc)) 
                
        return neighbors
    
    @staticmethod
    def path_exists(board, start_pos, goal_rows):
        """
        Runs Breadth-First Search (BFS) to ensure there is at least one valid path from start_pos to goal_row.
        Returns True if a path exists, False if the player is trapped.
        """
        visited = set() # set of positions we have visited and set to store unique positions
        will_be_checked = deque() # positions that may that we will see their neighbors later

        visited.add(start_pos)
        will_be_checked.append(start_pos)

        if start_pos[0] in goal_rows: # if we start on the goal row, we are already there!
            return True

        while will_be_checked:
            current_pos = will_be_checked.popleft() 

            for neighbor in Pathfinder.get_neighbors(board, current_pos):
                if neighbor in visited:
                    continue

                if neighbor[0] in goal_rows: # if we reach the goal row, we are done!
                    return True

                visited.add(neighbor)
                will_be_checked.append(neighbor)
        
        return False # if we exhaust all reachable positions without finding the goal row, there is no path!    

    @staticmethod
    def get_shortest_path_length(board, start_pos, goal_row):
        """
        Calculates the exact number of steps to reach the goal.
        (You will need this function heavily when writing the AI evaluation!).
        """

        if start_pos[0] == goal_row:
            return 0 # if we start on the goal row, we are already there!
        if not Pathfinder.path_exists(board, start_pos, {goal_row}):
            return float('inf') # if there is no path, return infinity 
        
        visited = set()
        will_be_checked = deque()

        visited.add(start_pos)
        will_be_checked.append((start_pos, 0)) # we will store tuples of (position, distance_from_start)

        while will_be_checked:
            current_pos, distance = will_be_checked.popleft()

            if current_pos[0] == goal_row:
                return distance

            for neighbor in Pathfinder.get_neighbors(board, current_pos):
                if neighbor not in visited:
                    visited.add(neighbor)
                    will_be_checked.append((neighbor, distance + 1))

        return float('inf') # this line should never be reached because we already check for path existence at the start