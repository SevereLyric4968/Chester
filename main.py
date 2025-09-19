from core.board_manager import BoardManager
from core.engine_interface import EngineInterface
from core.players import HumanPlayer, AIPlayer
from core.human_interface import HumanInterface
from core.game_controller import GameController
import json

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    config = load_config()

    # 1. Create board
    bm = BoardManager()

    # 2. Setup engine
    engine_cfg = config["engine"]
    engine = EngineInterface(
        path=engine_cfg["path"],
        depth=engine_cfg["depth"],
        threads=engine_cfg["threads"],
        min_time=engine_cfg["min_time"],
    )

    # 3. Create players based on config
    mode = config["mode"]
    human_side = config["human_side"]

    if mode == "human_vs_ai":
        if human_side == "white":
            white = HumanPlayer("white", HumanInterface())
            black = AIPlayer("black", engine)
        else:
            white = AIPlayer("white", engine)
            black = HumanPlayer("black", HumanInterface())

    elif mode == "ai_vs_ai":
        white = AIPlayer("white", engine)
        black = AIPlayer("black", engine)

    elif mode == "human_vs_human":
        white = HumanPlayer("white", HumanInterface())
        black = HumanPlayer("black", HumanInterface())

    else:
        raise ValueError(f"Unknown mode: {mode}")

    # 4. Run game
    game = GameController(bm, white, black)
    game.play()
