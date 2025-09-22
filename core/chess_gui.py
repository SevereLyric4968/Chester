import os
import tkinter as tk
from PIL import Image, ImageTk
import chess

class ChessGui:
    def __init__(self, board=None):
        self.window = tk.Tk()
        self.window.title("Chester - Chess GUI")
        self.square_size = 60
        self.canvas = tk.Canvas(
            self.window,
            width=self.square_size * 8,
            height=self.square_size * 8
        )
        self.canvas.pack()

        self.highlighted_squares=None

        # preload piece images
        self.images = {}
        self._load_images()

        # draw starting board if provided
        if board is not None:
            self.draw_board(board)

        # just a placeholder for whoever handles clicks
        self.click_handler = None
        self.canvas.bind("<Button-1>", self.on_click)

    def _load_images(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        photos_dir = os.path.abspath(os.path.join(script_dir, "..", "photos"))

        piece_map = {
            "P": "wp.png", "p": "bp.png",
            "N": "wn.png", "n": "bn.png",
            "B": "wb.png", "b": "bb.png",
            "R": "wr.png", "r": "br.png",
            "Q": "wq.png", "q": "bq.png",
            "K": "wk.png", "k": "bk.png",
        }

        for symbol, filename in piece_map.items():
            path = os.path.join(photos_dir, filename)
            pil_img = Image.open(path).convert("RGBA").resize(
                (self.square_size, self.square_size)
            )
            self.images[symbol] = ImageTk.PhotoImage(pil_img)

    def draw_board(self, board):
        """Redraw board + pieces based on python-chess board."""
        self.board = board
        self.canvas.delete("all")

        # draw squares
        for row in range(8):
            for col in range(8):
                color = "#EEEED2" if (row + col) % 2 == 0 else "#769656"
                x1, y1 = col * self.square_size, row * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        if self.highlighted_squares:
            self.highlight_legal_moves(self.highlighted_squares)

        # draw pieces
        for square, piece in board.piece_map().items():
            row = 7 - (square // 8)
            col = square % 8
            symbol = piece.symbol()
            img = self.images[symbol]
            self.canvas.create_image(
                col * self.square_size,
                row * self.square_size,
                anchor="nw",
                image=img
            )

    def on_click(self, event):
        """Forward click event to external handler if set."""
        col = event.x // self.square_size
        row = 7 - (event.y // self.square_size)
        square = row * 8 + col
        if self.click_handler:
            self.click_handler(square)

    def highlight_legal_moves(self, square):
        self.canvas.delete("highlight")
        legal_moves = [move.to_square for move in self.board.legal_moves if move.from_square == square]
        self.highlighted_squares = legal_moves
        for moves in legal_moves:
            row = 7 - (moves // 8)
            col = moves % 8
            x1 = col * self.square_size
            y1 = row * self.square_size
            x2 = x1 + self.square_size
            y2 = y1 + self.square_size
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#FFFF00", outline="",tags="highlight",stipple="gray75")