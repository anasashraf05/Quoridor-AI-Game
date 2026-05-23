import random
from src.core.enums import DIFFICULTY
from src.ai.minimax import Minimax


class AIPlayer:
    """
    Wraps the Minimax engine and exposes difficulty-based search depths.

    Easy   → random pawn move
    Medium → depth 1 with limited wall consideration
    Hard   → depth 2 with deeper search
    """

    DEPTH_MAP = {
        DIFFICULTY.EASY:   1,
        DIFFICULTY.MEDIUM: 1,
        DIFFICULTY.HARD:   2,
    }

    WALL_ACTIONS_MAP = {
        DIFFICULTY.EASY:   0,      # No wall placement for Easy (focuses on pawn moves)
        DIFFICULTY.MEDIUM: 4,      # Consider 4 best wall placements
        DIFFICULTY.HARD:   10,     # Consider 10 best wall placements
    }

    def __init__(self, player_id, start_position, goal_row, difficulty=DIFFICULTY.MEDIUM):
        self.player_id         = player_id
        self.position          = start_position
        self.recent_positions  = []      # Track last 8 positions for better loop detection
        self.walls_left        = 10
        self.goal_row          = goal_row
        self.difficulty        = difficulty

    # ------------------------------------------------------------------ #
    #  Loop Detection & Breaking
    # ------------------------------------------------------------------ #
    def _detect_loop_pattern(self):
        """
        Detects if AI is stuck in a repeating loop.
        Returns set of positions to break free from, or empty set if no loop detected.
        """
        if len(self.recent_positions) < 4:
            return set()
        
        # Check for 2-position loop: A -> B -> A -> B
        if len(self.recent_positions) >= 4:
            last_4 = self.recent_positions[-4:]
            if last_4[0] == last_4[2] and last_4[1] == last_4[3]:
                # Loop detected: positions alternate between 2 spots
                return {last_4[0], last_4[1]}
        
        # Check for 3-position loop: A -> B -> C -> A -> B -> C
        if len(self.recent_positions) >= 6:
            last_6 = self.recent_positions[-6:]
            if (last_6[0] == last_6[3] and last_6[1] == last_6[4] and last_6[2] == last_6[5]):
                # 3-position cycle detected
                return {last_6[0], last_6[1], last_6[2]}
        
        return set()


    # ------------------------------------------------------------------ #
    #  Required by Player protocol
    # ------------------------------------------------------------------ #
    def has_walls_left(self):
        return self.walls_left > 0

    def use_wall(self):
        self.walls_left -= 1

    # ------------------------------------------------------------------ #
    #  Main interface called by GameController
    # ------------------------------------------------------------------ #
    def get_action(self, board, players):
        """
        Returns the best action for the current board state.
        Action format:
            {"type": "move", "pos": (row, col)}
            {"type": "wall", "wall": Wall}
        
        Includes loop detection to prevent oscillation between same positions.
        """
        depth = self.DEPTH_MAP.get(self.difficulty, 2)
        max_walls = self.WALL_ACTIONS_MAP.get(self.difficulty, Minimax.MAX_WALLS_PER_NODE)

        actions = Minimax.get_all_legal_actions(
            board,
            players,
            self.player_id,
            max_wall_actions=max_walls,
        )
        if not actions:
            return None

        # Detect if stuck in a loop and get positions to break free from
        loop_positions = self._detect_loop_pattern()
        
        if self.difficulty == DIFFICULTY.EASY:
            # Easy mode: prefer pawn moves that move toward goal, but stay random-ish.
            pawn_moves = [a for a in actions if a["type"] == "move"]
            if not pawn_moves:
                return random.choice(actions or [None])
            
            # Filter out loop positions if detected
            if loop_positions:
                non_loop_moves = [a for a in pawn_moves if a["pos"] not in loop_positions]
                if non_loop_moves:
                    pawn_moves = non_loop_moves
            
            # Prioritize moves closer to goal
            def move_score(action):
                target_row = action["pos"][0]
                dist_to_goal = abs(target_row - self.goal_row)
                return dist_to_goal
            
            best_dist = min(move_score(a) for a in pawn_moves)
            best_moves = [a for a in pawn_moves if move_score(a) == best_dist]
            return random.choice(best_moves)

        human_player_id = next(p.player_id for p in players if p.player_id != self.player_id)
        
        # For Medium/Hard: use avoid_positions to help minimax break loops
        avoid_positions = loop_positions if loop_positions else set()

        action = Minimax.get_best_action(
            board,
            players,
            self.player_id,
            human_player_id,
            depth,
            avoid_positions=avoid_positions,
            max_wall_actions=max_walls,
        )

        self.recent_positions.append(self.position)
        # Keep last 8 positions for better loop detection
        self.recent_positions = self.recent_positions[-8:]
        return action

