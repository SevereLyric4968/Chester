from core.board_manager import BoardManager
from core.engine_interface import EngineInterface
from core.players import HumanPlayer, AIPlayer
from core.human_interface import HumanInterface
from core.game_controller import GameController
from core.robot_interface import RobotInterface
from core.chess_gui import ChessGui
from core.gui_interface import GuiInterface
import json

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    config = load_config()

    # 1. Create board
    bm = BoardManager()
    gui = ChessGui(bm.board)

    gui_interface = GuiInterface(gui, bm)

    # 2. Setup engine
    engine_cfg = config["engine"]
    engine = EngineInterface(
        path=engine_cfg["path"],
        depth=engine_cfg["depth"],
        threads=engine_cfg["threads"],
        min_time=engine_cfg["min_time"],
    )

    # 3. Create players based on config
    robotInterface = RobotInterface()

    robot1Type = config["robot_1_control_type"]  # white
    robot2Type = config["robot_2_control_type"]  # black

    if robot1Type == "rc":
        white = HumanPlayer("white", gui_interface)
    elif robot1Type == "ai":
        white = AIPlayer("white", engine)
    else:
        raise ValueError("Invalid robot_1_control_type")

    if robot2Type == "rc":
        black = HumanPlayer("black", gui_interface)
    elif robot2Type == "ai":
        black = AIPlayer("black", engine)
    else:
        raise ValueError("Invalid robot_2_control_type")

    # 4. Run game
    game = GameController(bm, white, black,gui,robotInterface=robotInterface)
    game.play()
