from stockfish import Stockfish

class EngineInterface:
    def __init__(self, path, depth=15, threads=2, min_time=30,skill=10):
        """Initialize Stockfish engine with config."""
        self.engine = Stockfish(
            path=path,
            depth=depth,
            parameters={
                "Threads": threads,
                "Minimum Thinking Time": min_time,
                "Skill Level": skill
            }
        )

    def set_position(self, fen: str):
        """Set the board position using FEN."""
        self.engine.set_fen_position(fen)


    def get_best_move(self) -> str:
        """Ask Stockfish for the best move in UCI format."""
        return self.engine.get_best_move()