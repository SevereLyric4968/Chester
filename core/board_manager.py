import chess
import json

class BoardManager:
    def __init__(self,boardFen=None):
        self.board = chess.Board(boardFen)

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

    def get_status(self):

        if self.board.is_checkmate():
            return "checkmate"

        if self.board.is_stalemate():
            return "stalemate"

        if self.board.is_insufficient_material():
            return "draw_insufficient_material"

        if self.board.can_claim_threefold_repetition():
            return "threefold_repetition"

        if self.board.can_claim_fifty_moves():
            return "fifty_move_rule"

        if self.board.is_check():
            return "check"
        print("im incompetant")
        return "normal"

    def __str__(self):
        return str(self.board)

    def save_board(self):
        board=self.get_fen()
        with open("boards.json", "r") as f:
            data = json.load(f)
        data["last board"] = board
        with open("boards.json", "w") as f:
            json.dump(data, f, indent=4)