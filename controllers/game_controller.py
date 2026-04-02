import threading

class GameController:
    def __init__(self, board_manager, white_player, black_player,gui,robot_controller,databus):
        self.bm = board_manager
        self.white_player = white_player
        self.black_player = black_player
        self.gui=gui
        self.rc=robot_controller
        self.databus=databus

        self.robotBusy=False

    def step(self):

        if self.databus.robotBusy:
            return

        currentPlayer = (
            self.white_player if self.bm.board.turn else self.black_player
        )
        self.databus.game.turn = currentPlayer.color.capitalize()
        self.databus.game.status = self.bm.get_status()

        move = currentPlayer.get_move(self.bm)

        self.databus.gameLog.append(f"{currentPlayer.color.capitalize()}: {move}")

        beforeBoard=self.bm.board.copy()

        # robot execution
        self.databus.robotBusy = True
        moveQueue,isWhite = self.rc.uci_to_move_queue(move, beforeBoard)
        threading.Thread(
            target=self.rc.execute_move_queue,
            args=(moveQueue, beforeBoard , isWhite, currentPlayer.color),
            daemon=True
        ).start()

        self.bm.apply_move(move)
        self.gui.draw_board(self.bm.board)