import threading

class GameController:
    def __init__(self, board_manager, white_player, black_player,gui,robot_controller,databus):
        self.bm = board_manager
        self.white_player = white_player
        self.black_player = black_player
        self.gui=gui
        self.rc=robot_controller
        self.databus=databus

    def play(self):
        #Run the game loop until it's over.
        print("Starting game...")
        print(self.bm)

        self.gui.draw_board(self.bm.board)
        self.gui.window.update_idletasks()
        self.gui.window.update()

        while not self.bm.is_game_over():
            current_player = (
                self.white_player if self.bm.board.turn else self.black_player
            )

            self.databus.game.turn=current_player.color.capitalize()
            self.databus.game.status= self.bm.get_status()

            boardBefore = self.bm.board.copy()

            move = current_player.get_move(self.bm)
            self.databus.gameLog.append(move.uci())

            #robot execution
            #threading.Thread()
            moveQueue = self.rc.translate(move, boardBefore)
            self.rc.executeMoveQueue(moveQueue, boardBefore)

            self.bm.apply_move(move)

            #print(self.bm)

            # update gui
            if self.gui:
                self.gui.draw_board(self.bm.board)
                self.gui.window.update_idletasks()
                self.gui.window.update()

        print("Game over:", self.bm.get_result())