class Minimax:
    @staticmethod
    def get_best_action(board, ai_player_id, depth):
        """
        The public function that kicks off the Minimax search.
        It loops through all currently legal moves, scores them using _minimax, 
        and returns the absolute best one.
        """
        pass

    @staticmethod
    def _minimax(board, depth, alpha, beta, is_maximizing_player, current_player_id):
        """
        The recursive function that actually does the simulation.
        depth: How many turns into the future to look.
        alpha/beta: Used for pruning (skipping bad branches to save time).
        is_maximizing_player: True if the AI is playing, False if simulating the Human.
        """
        pass

    @staticmethod
    def _get_all_legal_actions(board, player_id):
        """
        A helper method that looks at the current board and generates a list of 
        EVERY possible valid pawn move and EVERY possible valid wall placement 
        for the given player.
        """
        pass