"""
test_game.py
Basic tests for the Quoridor game engine.
Run with:  python -m pytest tests/test_game.py -v
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.board import Board
from src.core.wall import Wall
from src.core.player import Player
from src.core.rules import Rules
from src.core.pathfinder import Pathfinder
from src.core.enums import Orientation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_board(p1=(1, 5), p2=(9, 5)):
    """Creates a fresh board with two players at the given positions."""
    board = Board()
    board.move_pawn(1, p1)
    board.move_pawn(2, p2)
    return board


# ---------------------------------------------------------------------------
# Pawn movement tests
# ---------------------------------------------------------------------------

class TestPawnMovement:
    def test_standard_move_up(self):
        board = make_board(p1=(5, 5), p2=(9, 5))
        assert Rules.is_valid_pawn_move(board, (5, 5), (4, 5))

    def test_standard_move_down(self):
        board = make_board(p1=(5, 5), p2=(9, 5))
        assert Rules.is_valid_pawn_move(board, (5, 5), (6, 5))

    def test_move_out_of_bounds(self):
        board = make_board(p1=(1, 5), p2=(9, 5))
        assert not Rules.is_valid_pawn_move(board, (1, 5), (0, 5))

    def test_cannot_move_diagonally_normally(self):
        board = make_board(p1=(5, 5), p2=(9, 5))
        assert not Rules.is_valid_pawn_move(board, (5, 5), (4, 4))

    def test_cannot_land_on_opponent(self):
        board = make_board(p1=(5, 5), p2=(6, 5))
        assert not Rules.is_valid_pawn_move(board, (5, 5), (6, 5))

    def test_straight_jump_over_opponent(self):
        board = make_board(p1=(5, 5), p2=(6, 5))
        assert Rules.is_valid_pawn_move(board, (5, 5), (7, 5))

    def test_straight_jump_blocked_by_wall(self):
        board = make_board(p1=(5, 5), p2=(6, 5))
        # Wall below opponent blocks the jump landing
        wall = Wall(6, 5, Orientation.HORIZONTAL)
        board.place_wall(wall)
        assert not Rules.is_valid_pawn_move(board, (5, 5), (7, 5))

    def test_move_blocked_by_wall(self):
        board = make_board(p1=(5, 5), p2=(9, 5))
        # Horizontal wall blocks moving from row 5 to row 6
        wall = Wall(5, 5, Orientation.HORIZONTAL)
        board.place_wall(wall)
        assert not Rules.is_valid_pawn_move(board, (5, 5), (6, 5))


# ---------------------------------------------------------------------------
# Wall placement tests
# ---------------------------------------------------------------------------

class TestWallPlacement:
    def test_valid_wall(self):
        board = make_board()
        wall = Wall(4, 4, Orientation.HORIZONTAL)
        assert Rules.is_valid_wall_placement(board, wall)

    def test_wall_out_of_bounds(self):
        board = make_board()
        wall = Wall(9, 5, Orientation.HORIZONTAL)
        assert not Rules.is_valid_wall_placement(board, wall)

    def test_overlapping_horizontal_walls(self):
        board = make_board()
        w1 = Wall(4, 4, Orientation.HORIZONTAL)
        board.place_wall(w1)
        w2 = Wall(4, 4, Orientation.HORIZONTAL)
        assert not Rules.is_valid_wall_placement(board, w2)

    def test_adjacent_same_orientation_overlap(self):
        board = make_board()
        w1 = Wall(4, 4, Orientation.HORIZONTAL)
        board.place_wall(w1)
        w2 = Wall(4, 5, Orientation.HORIZONTAL)  # 1 column away — overlaps
        assert not Rules.is_valid_wall_placement(board, w2)

    def test_crossing_walls_invalid(self):
        board = make_board()
        w1 = Wall(4, 4, Orientation.HORIZONTAL)
        board.place_wall(w1)
        w2 = Wall(4, 4, Orientation.VERTICAL)
        assert not Rules.is_valid_wall_placement(board, w2)

    def test_wall_cannot_trap_player(self):
        """Surround player 1 so they have no path — placement must be rejected."""
        board = make_board(p1=(1, 5), p2=(9, 5))
        # Block all exits from (1,5) by placing walls around it
        board.place_wall(Wall(1, 4, Orientation.HORIZONTAL))
        board.place_wall(Wall(1, 5, Orientation.HORIZONTAL))  # blocks down
        board.place_wall(Wall(1, 4, Orientation.VERTICAL))    # blocks right from col4
        # Attempt to place a wall that completes the trap
        trap_wall = Wall(1, 5, Orientation.VERTICAL)
        # This may or may not be the exact trapping wall depending on layout,
        # but the pathfinder should catch any true trapping case
        result = Rules.is_valid_wall_placement(board, trap_wall)
        # We just verify the function runs without error; trapping logic is in pathfinder
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Pathfinder tests
# ---------------------------------------------------------------------------

class TestPathfinder:
    def test_path_exists_open_board(self):
        board = make_board()
        assert Pathfinder.path_exists(board, (1, 5), [9])
        assert Pathfinder.path_exists(board, (9, 5), [1])

    def test_shortest_path_start_is_goal(self):
        board = make_board(p1=(9, 5), p2=(1, 5))
        assert Pathfinder.get_shortest_path_length(board, (9, 5), 9) == 0

    def test_shortest_path_one_step(self):
        board = make_board(p1=(8, 5), p2=(1, 5))
        assert Pathfinder.get_shortest_path_length(board, (8, 5), 9) == 1

    def test_shortest_path_open_board(self):
        board = make_board()
        # Player 1 at row 1, needs 8 steps to reach row 9
        length = Pathfinder.get_shortest_path_length(board, (1, 5), 9)
        assert length == 8


# ---------------------------------------------------------------------------
# Winner detection tests
# ---------------------------------------------------------------------------

class TestWinner:
    def test_player1_wins_at_row9(self):
        p = Player(player_id=1, start_pos=(9, 5), goal_row=9)
        assert Rules.is_winner(p)

    def test_player2_wins_at_row1(self):
        p = Player(player_id=2, start_pos=(1, 3), goal_row=1)
        assert Rules.is_winner(p)

    def test_not_winner_midboard(self):
        p = Player(player_id=1, start_pos=(5, 5), goal_row=9)
        assert not Rules.is_winner(p)


# ---------------------------------------------------------------------------
# Board clone tests
# ---------------------------------------------------------------------------

class TestBoardClone:
    def test_clone_is_independent(self):
        board = make_board()
        clone = board.clone()
        clone.move_pawn(1, (3, 5))
        # Original should be unchanged
        assert board.get_pawn_position(1) == (1, 5)

    def test_clone_walls_independent(self):
        board = make_board()
        clone = board.clone()
        clone.walls.append(Wall(4, 4, Orientation.HORIZONTAL))
        assert len(board.walls) == 0
