import os
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

class ChessGui:
    def __init__(self, board=None,databus=None):
        self.window = tk.Tk()
        self.window.title("Chester - Chess GUI")
        self.window.state("zoomed")

        self.databus = databus

        # ----------------------------
        # DARK MODE COLORS
        # ----------------------------
        dark_bg = "#1e1e1e"
        panel_bg = "#252526"
        accent_bg = "#2d2d30"
        text_color = "#d4d4d4"

        self.window.configure(bg=dark_bg)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=dark_bg, borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=accent_bg,
                        foreground=text_color,
                        padding=6)
        style.map("TNotebook.Tab",
                  background=[("selected", panel_bg)])

        self.square_size = 60
        self.highlighted_squares = None

        # ----------------------------
        # MAIN GRID LAYOUT
        # ----------------------------
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_rowconfigure(2, weight=0)
        self.window.grid_rowconfigure(3, weight=0)


        self.window.grid_columnconfigure(0, weight=3)
        self.window.grid_columnconfigure(1, weight=1)

        # ----------------------------
        # TOP STATUS BAR
        # ----------------------------
        self.status_frame = tk.Frame(self.window, bg=panel_bg)
        self.status_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.turn_label = tk.Label(self.status_frame, text="Turn: White",
                                   bg=panel_bg, fg=text_color)
        self.turn_label.pack(side="left", padx=10, pady=5)

        self.game_status_label = tk.Label(self.status_frame, text="Status: Normal",
                                          bg=panel_bg, fg=text_color)
        self.game_status_label.pack(side="left", padx=10)

        self.robot_status_label = tk.Label(self.status_frame,
                                           text="Robot1: Idle | Robot2: Idle",
                                           bg=panel_bg, fg=text_color)
        self.robot_status_label.pack(side="left", padx=10)

        # ----------------------------
        # BOARD FRAME
        # ----------------------------
        self.board_frame = tk.Frame(self.window, bg=dark_bg)
        self.board_frame.grid(row=1, column=0, sticky="nsew")

        self.canvas = tk.Canvas(
            self.board_frame,
            width=self.square_size * 8,
            height=self.square_size * 8,
            bg=dark_bg,
            highlightthickness=0
        )
        self.canvas.pack(padx=20, pady=20, expand=True)

        # ----------------------------
        # GAME LOG PANEL
        # ----------------------------
        self.log_frame = tk.Frame(self.window, bg=panel_bg)
        self.log_frame.grid(row=1, column=1, sticky="nsew")

        self.log_frame.grid_rowconfigure(1, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        tk.Label(self.log_frame,
                 text="Game Log",
                 bg=panel_bg,
                 fg=text_color).grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.game_log = tk.Text(self.log_frame,
                                bg=dark_bg,
                                fg=text_color,
                                insertbackground=text_color,
                                relief="flat")
        self.game_log.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # ----------------------------
        # ROBOT PANEL (TABBED)
        # ----------------------------
        self.robot_frame = tk.Frame(self.window, bg=dark_bg)
        self.robot_frame.grid(row=2, column=0, columnspan=2, sticky="new")

        self.notebook = ttk.Notebook(self.robot_frame)
        self.notebook.pack(fill="both",expand=True)

        # Robots Tab
        self.robot_tab = tk.Frame(self.notebook, bg=panel_bg)
        self.notebook.add(self.robot_tab, text="Robots")

        self.robot_tab.grid_columnconfigure(0, weight=1)
        self.robot_tab.grid_columnconfigure(1, weight=1)

        self.robot1_box = tk.LabelFrame(
            self.robot_tab,
            text="Robot 1",
            bg=panel_bg,
            fg=text_color,
            bd=1,
            relief="solid"
        )
        self.robot1_box.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.robot1_connected_label = tk.Label(self.robot1_box, bg=panel_bg, fg=text_color)
        self.robot1_connected_label.pack(anchor="w", padx=5, pady=2)

        self.robot1_status_label = tk.Label(self.robot1_box, bg=panel_bg, fg=text_color)
        self.robot1_status_label.pack(anchor="w", padx=5, pady=2)

        self.robot1_homed_label = tk.Label(self.robot1_box, bg=panel_bg, fg=text_color)
        self.robot1_homed_label.pack(anchor="w", padx=5, pady=2)

        self.robot1_magnet_label = tk.Label(self.robot1_box, bg=panel_bg, fg=text_color)
        self.robot1_magnet_label.pack(anchor="w", padx=5, pady=2)

        self.robot2_box = tk.LabelFrame(
            self.robot_tab,
            text="Robot 2",
            bg=panel_bg,
            fg=text_color,
            bd=1,
            relief="solid"
        )
        self.robot2_box.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.robot2_connected_label = tk.Label(self.robot2_box, bg=panel_bg, fg=text_color)
        self.robot2_connected_label.pack(anchor="w", padx=5, pady=2)

        self.robot2_status_label = tk.Label(self.robot2_box, bg=panel_bg, fg=text_color)
        self.robot2_status_label.pack(anchor="w", padx=5, pady=2)

        self.robot2_homed_label = tk.Label(self.robot2_box, bg=panel_bg, fg=text_color)
        self.robot2_homed_label.pack(anchor="w", padx=5, pady=2)

        self.robot2_magnet_label = tk.Label(self.robot2_box, bg=panel_bg, fg=text_color)
        self.robot2_magnet_label.pack(anchor="w", padx=5, pady=2)

        # Execution Log Tab
        self.exec_tab = tk.Frame(self.notebook, bg=panel_bg)
        self.notebook.add(self.exec_tab, text="Execution Log")

        self.exec_log = tk.Text(self.exec_tab,
                                height=15,
                                bg=dark_bg,
                                fg=text_color,
                                insertbackground=text_color,
                                relief="flat")
        self.exec_log.pack(fill="both", expand=True, padx=5, pady=5)

        # Error Tab
        self.error_tab = tk.Frame(self.notebook, bg=panel_bg)
        self.notebook.add(self.error_tab, text="Errors")

        self.error_log = tk.Text(self.error_tab,
                                 height=15,
                                 bg=dark_bg,
                                 fg=text_color,
                                 insertbackground=text_color,
                                 relief="flat")
        self.error_log.pack(fill="both", expand=True, padx=5, pady=5)

        tk.Button(self.error_tab,
                  text="Clear Errors",
                  bg=accent_bg,
                  fg=text_color,
                  command=databus.errorLog.clear,
                  relief="flat").pack(pady=5)

        # ----------------------------
        # IMAGE LOADING
        # ----------------------------
        self.images = {}
        self._load_images()

        if board is not None:
            self.draw_board(board)

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
        self.board = board
        self.canvas.delete("all")

        for row in range(8):
            for col in range(8):
                color = "#EEEED2" if (row + col) % 2 == 0 else "#769656"
                x1, y1 = col * self.square_size, row * self.square_size
                x2, y2 = x1 + self.square_size, y1 + self.square_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

        if self.highlighted_squares:
            self.highlight_legal_moves(self.highlighted_squares)

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
        col = event.x // self.square_size
        row = 7 - (event.y // self.square_size)
        square = row * 8 + col
        if self.click_handler:
            self.click_handler(square)

    def highlight_legal_moves(self, square):
        self.canvas.delete("highlight")
        legal_moves = [
            move.to_square
            for move in self.board.legal_moves
            if move.from_square == square
        ]
        self.highlighted_squares = legal_moves

        for moves in legal_moves:
            row = 7 - (moves // 8)
            col = moves % 8
            x1 = col * self.square_size
            y1 = row * self.square_size
            x2 = x1 + self.square_size
            y2 = y1 + self.square_size
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="#FFFF00",
                outline="",
                tags="highlight",
                stipple="gray75"
            )

    def start_update_loop(self):
        self.update_loop()

    def update_loop(self):
        if hasattr(self, "controller"):
            self.controller.step()

        self.turn_label.config(text=f"Turn: {self.databus.game.turn}")
        self.game_status_label.config(text=f"Status: {self.databus.game.status}")

        self.robot_status_label.config(
            text=f"Robot1: {self.databus.robot1.movementStatus} | Robot2: {self.databus.robot2.movementStatus}"
        )

        # robot 1 tab
        self.robot1_status_label.config(
            text=f"Status: {self.databus.robot1.movementStatus}"
        )
        self.robot1_connected_label.config(
            text=f"Connected: {self.databus.robot1.connectionStatus}"
        )
        self.robot1_homed_label.config(
            text=f"Homed: {self.databus.robot1.homedStatus}"
        )
        self.robot1_magnet_label.config(
            text=f"Magnet: {self.databus.robot1.magnetStatus}"
        )

        # robot 2 tab
        self.robot2_status_label.config(
            text=f"Status: {self.databus.robot2.movementStatus}"
        )
        self.robot2_connected_label.config(
            text=f"Connected: {self.databus.robot2.connectionStatus}"
        )
        self.robot2_homed_label.config(
            text=f"Homed: {self.databus.robot2.homedStatus}"
        )
        self.robot2_magnet_label.config(
            text=f"Magnet: {self.databus.robot2.magnetStatus}"
        )
        self.update_logs()


        self.window.after(100, self.update_loop)

    def update_logs(self):

        self.game_log.delete("1.0", tk.END)
        for line in self.databus.gameLog:
            self.game_log.insert(tk.END, line + "\n")
        self.game_log.see(tk.END)

        self.exec_log.delete("1.0", tk.END)
        for line in self.databus.execLog:
            self.exec_log.insert(tk.END, line + "\n")
        self.exec_log.see(tk.END)

        self.error_log.delete("1.0", tk.END)
        for line in self.databus.errorLog:
            self.error_log.insert(tk.END, line + "\n")
        self.error_log.see(tk.END)