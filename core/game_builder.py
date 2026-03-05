from operator import truediv

from core.board_manager import BoardManager
from core.game_controller import GameController
from core.engine_interface import EngineInterface
from core.players import AIPlayer, rcPlayer, HumanPlayer
from core.robot_interface import RobotInterface
from core.chess_gui import ChessGui
from core.vision_interface import VisionInterface
from core.gui_interface import GuiInterface

import json

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

class GameBuilder():

    def build(mode):

        board = BoardManager()
        config = load_config()

        # 1. create board
        bm = BoardManager()
        gui = ChessGui(bm.board)

        gui_interface = GuiInterface(gui, bm)

        # 2. setup engine
        engine_cfg = config["engine"]
        engine = EngineInterface(
            path=engine_cfg["path"],
            depth=engine_cfg["depth"],
            threads=engine_cfg["threads"],
            min_time=engine_cfg["min_time"],
        )

        # 3. setup player types
        white_player_type=config["player_1_type"]
        black_player_type=config["player_2_type"]

        if white_player_type=="human":
            white = HumanPlayer("white",VisionInterface)
        elif white_player_type=="ai":
            white = AIPlayer("white", engine)
            white_robot=config["white_robot_ip"]
        elif white_player_type=="rc":
            white = rcPlayer("white", gui_interface)
            white_robot = config["white_robot_ip"]
        else:
            raise ValueError("Invalid player_1_type")
        if black_player_type=="human":
            black = HumanPlayer("black",VisionInterface)
        elif black_player_type=="ai":
            black = AIPlayer("black", engine)
            black_robot = config["black_robot_ip"]
        elif black_player_type=="rc":
            black = rcPlayer("black", gui_interface)
            black_robot = config["black_robot_ip"]
        else:
            raise ValueError("Invalid player_2_type")

        # 4. setup control mode
        if config["control_type"]=="robot wars":
            white_robot=config["white_robot_ip"]
            black_robot=config["black_robot_ip"]
        elif config["control_type"]=="drunk adam":
            if config["robot_side"]=="white":
                white_robot=config["white_robot_ip"]
                black_robot=config["white_robot_ip"]
            else:
                white_robot=config["black_robot_ip"]
                black_robot=config["black_robot_ip"]
        elif config["control_type"]=="man vs ned":
            if config["robot_side"] == "white":
                white_robot = config["white_robot_ip"]
                black_robot = None
            else:
                white_robot = None
                black_robot = config["black_robot_ip"]
        elif config["control_type"]=="test":
            white_robot = None
            black_robot = None
        else:
            raise ValueError("Invalid control_type")

        controller = GameController(
            board_manager=bm,
            white_player=white,
            black_player=black,
            gui=gui,
            robotInterface=RobotInterface(white_robot, black_robot)
        )

        return controller