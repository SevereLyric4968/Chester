from abc import ABC, abstractmethod

class Player(ABC):
    """Abstract base class for all player types."""

    def __init__(self, color: str):
        self.color = color  # "white" or "black"

    @abstractmethod
    def get_move(self, board_manager):
        """Return a move in UCI format (e.g., 'e2e4')."""
        pass

class HumanPlayer(Player):
    def __init__(self, color, interface):
        super().__init__(color)
        self.interface = interface  # An instance of HumanInterface

    def get_move(self, board_manager):
        # Ask human for a move
        return self.interface.get_move(board_manager)

class AIPlayer(Player):
    def __init__(self, color, engine):
        super().__init__(color)
        self.engine = engine  # An instance of EngineInterface

    def get_move(self, board_manager):
        # Ask engine for best move
        self.engine.set_position(board_manager.get_fen())
        return self.engine.get_best_move()
