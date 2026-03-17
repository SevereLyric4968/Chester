from core.board_manager import BoardManager
from controllers.game_controller import GameController
from players.engine_interface import EngineInterface
from players.players import AIPlayer, rcPlayer, HumanPlayer
from controllers.robot_controller import RobotController
from core.chess_gui import ChessGui
from players.vision_interface import VisionInterface
from players.gui_interface import GuiInterface
from core.data_bus import DataBus

import json

def load_config(path="config.json"):
    with open(path, "r") as f:
        return json.load(f)

class GameBuilder():

    def build(mode):

        config = load_config()

        # 1. create board
        bm = BoardManager()
        databus = DataBus()
        gui = ChessGui(bm.board,databus)

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
            #white_robot=config["white_robot_ip"]
        elif white_player_type=="rc":
            white = rcPlayer("white", gui_interface)
            #white_robot = config["white_robot_ip"]
        else:
            raise ValueError("Invalid player_1_type")
        if black_player_type=="human":
            black = HumanPlayer("black",VisionInterface)
        elif black_player_type=="ai":
            black = AIPlayer("black", engine)
            #black_robot = config["black_robot_ip"]
        elif black_player_type=="rc":
            black = rcPlayer("black", gui_interface)
            #black_robot = config["black_robot_ip"]
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
            robot_controller=RobotController(white_robot, black_robot,databus),
            gui=gui,
            databus=databus
        )

        return controller,gui