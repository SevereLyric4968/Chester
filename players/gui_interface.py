import chess

class GuiInterface:
    def __init__(self, gui, board_manager):
        self.gui = gui
        self.board_manager = board_manager
        self.board = board_manager.board
        self.pending_move = None
        self.selected_square = None

        # tell ChessGui to forward clicks here
        self.gui.click_handler = self.handle_click

    def handle_click(self, square):
        piece = self.board.piece_at(square)
        if piece:
            self.gui.highlight_legal_moves(square)
            if piece.color == self.board.turn:
                self.selected_square = square

        if self.selected_square is not None and square != self.selected_square:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.pending_move = move.uci()
                self.selected_square = None
                self.gui.draw_board(self.board)

    def get_move(self, board_manager):
        self.pending_move = None
        self.selected_square = None
        self.board_manager = board_manager  # store the manager
        self.board = board_manager.board  # store the chess.Board

        while self.pending_move is None:
            self.gui.window.update_idletasks()
            self.gui.window.update()

        return self.pending_move

