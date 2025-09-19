class HumanInterface:
    def get_move(self, board_manager):
        while True:
            move = input("Enter your move (e.g., e2e4): ")
            if move in board_manager.get_legal_moves():
                return move
            print("Invalid or illegal move, try again.")