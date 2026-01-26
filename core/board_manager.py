import chess

class BoardManager:
    def __init__(self):
        self.board = chess.Board()

    def reset(self):
        self.board.reset()

    def apply_move(self, move_uci: str):
        move = chess.Move.from_uci(move_uci)
        if move in self.board.legal_moves:
            self.board.push(move)
        else:
            raise ValueError(f"Illegal move: {move_uci}")

    def is_game_over(self):
        return self.board.is_game_over()

    def get_result(self):
        return self.board.result()

    def get_legal_moves(self):
        return [move.uci() for move in self.board.legal_moves]

    def get_fen(self):
        return self.board.fen()

    def __str__(self):
        return str(self.board)