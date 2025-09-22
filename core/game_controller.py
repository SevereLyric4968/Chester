class GameController:
    def __init__(self, board_manager, white_player, black_player,gui=None):
        self.board_manager = board_manager
        self.white_player = white_player
        self.black_player = black_player
        self.gui=gui

    def play(self):
        """Run the game loop until it's over."""
        print("Starting game...")
        print(self.board_manager)
        if self.gui:
            self.gui.draw_board(self.board_manager.board)
            self.gui.window.update_idletasks()
            self.gui.window.update()

        while not self.board_manager.is_game_over():
            current_player = (
                self.white_player if self.board_manager.board.turn else self.black_player
            )

            print(f"\n{current_player.color.capitalize()}'s turn")

            move = current_player.get_move(self.board_manager)
            self.board_manager.apply_move(move)

            print(self.board_manager)

            # update GUI if present
            if self.gui:
                self.gui.draw_board(self.board_manager.board)
                self.gui.window.update_idletasks()
                self.gui.window.update()

        print("Game over:", self.board_manager.get_result())
