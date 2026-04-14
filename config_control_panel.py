import tkinter as tk
import json
import os

def run():

    def updatePlayer1(*args):
        if p1_type.get() == "ai":
            p1_strength_dropdown.grid()
            p1_strength_label.grid()
        else:
            p1_strength_dropdown.grid_remove()
            p1_strength_label.grid_remove()

    def updatePlayer2(*args):
        if p2_type.get() == "ai":
            p2_strength_dropdown.grid()
            p2_strength_label.grid()
        else:
            p2_strength_dropdown.grid_remove()
            p2_strength_label.grid_remove()

    def updateModeDesc(*args):
        modeDescLabel.config(text=modeDescriptions[control_mode.get()])

    def save_config():
        config={
            "control_type": control_mode.get(),

            "player_1_type": p1_type.get(),
            "player_1_skill": p1_strength.get(),

            "player_2_type": p2_type.get(),
            "player_2_skill": p2_strength.get(),

            "white_robot_ip": "192.168.42.1",
            "black_robot_ip": "192.168.42.2",

            "robot_side": robot_side.get(),

            "location_map": location_file_name.get(),

            "starting_board": board_name.get(),

            "robot_setup": robot_setup.get(),

            "engine": {
                "path": "stockfish-windows-x86-64-avx2/stockfish/stockfish-windows-x86-64-avx2.exe",
                "depth": 15,
                "threads": 2,
                "min_time": 30
            }
        }

        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

        root.destroy()

    root = tk.Tk()
    root.title("Config Builder")

    frame = tk.Frame(root)
    frame.grid(row=0, column=0, padx=10, pady=10)

#todo display descriptions for robot side and player types, only display robot side if control mode is drunk adam or human
#todo human player type and robot side is redundant. get rid of 1 or streamline

    # Control Mode
    tk.Label(frame, text="Control Mode").grid(row=0, column=0, sticky="w")

    controlModes = ["drunk adam", "robot wars", "man vs ned", "test"]
    control_mode = tk.StringVar(value=controlModes[0])

    tk.OptionMenu(frame, control_mode, *controlModes).grid(row=0, column=1)

    modeDescriptions = {
        "drunk adam": "Single robot controls both sides",
        "robot wars": "One robot plays each side",
        "man vs ned": "Human vs robot play mode",
        "test": "Debug mode, no robots"
    }

    modeDescLabel = tk.Label(frame, text="", justify="left")
    modeDescLabel.grid(row=0, column=2, columnspan=4, sticky="w")

    control_mode.trace_add("write", updateModeDesc)
    updateModeDesc()

    # Player 1 Type
    tk.Label(frame, text="Player 1 type").grid(row=1, column=0, sticky="w")

    p1_strength_label = tk.Label(frame, text="Player 1 strength")
    p1_strength_label.grid(row=1, column=2, sticky="w")

    playerTypes = ["rc", "ai", "human"]
    aiStrengths = [str(i) for i in range(21)] #only displays if ai is selected

    p1_type = tk.StringVar(value=playerTypes[0])
    tk.OptionMenu(frame, p1_type, *playerTypes).grid(row=1, column=1)

    p1_strength = tk.StringVar(value=aiStrengths[10])

    p1_strength_dropdown = tk.OptionMenu(frame, p1_strength, *aiStrengths)
    p1_strength_dropdown.grid(row=1, column=3)

    p1_type.trace_add("write", updatePlayer1)
    updatePlayer1()

    # Player 2 Type
    tk.Label(frame, text="Player 2 type").grid(row=2, column=0, sticky="w")

    p2_strength_label = tk.Label(frame, text="Player 2 strength")
    p2_strength_label.grid(row=2, column=2, sticky="w")

    p2_type = tk.StringVar(value=playerTypes[0])
    tk.OptionMenu(frame, p2_type, *playerTypes).grid(row=2, column=1)

    p2_strength = tk.StringVar(value=aiStrengths[10])

    p2_strength_dropdown=(tk.OptionMenu(frame, p2_strength, *aiStrengths))
    p2_strength_dropdown.grid(row=2, column=3)

    p2_type.trace_add("write", updatePlayer2)
    updatePlayer2()

    # Robot Side
    tk.Label(frame, text="Robot Side").grid(row=3, column=0, sticky="w")

    sides = ["white", "black"]
    robot_side = tk.StringVar(value=sides[0])

    tk.OptionMenu(frame, robot_side, *sides).grid(row=3, column=1)

    # Location File
    tk.Label(frame, text="Location File").grid(row=4, column=0, sticky="w")

    locationFiles = [
        f for f in os.listdir("./location_maps")
        if f.endswith(".json")
    ]
    location_file_name = tk.StringVar(value=locationFiles[0])

    tk.OptionMenu(frame, location_file_name, *locationFiles).grid(row=4, column=1)

    # Starting Board
    tk.Label(frame, text="Starting Board").grid(row=5, column=0, sticky="w")

    with open("boards.json", "r") as f:
        boards = json.load(f)
        boardList=list(boards.keys())

    board_name = tk.StringVar(value=boardList[0])

    tk.OptionMenu(frame, board_name, *boardList).grid(row=5, column=1)

    # Robot Setup check box
    robot_setup = tk.BooleanVar()

    tk.Checkbutton(
        frame,
        text="Robot setup board",
        variable=robot_setup
    ).grid(row=6, column=0, columnspan=2, sticky="w")

    # Buttons
    tk.Button(frame, text="Use Previous Config", command=lambda: root.destroy()).grid(row=7, column=1)
    tk.Button(frame, text="Save Config", command=save_config).grid(row=7, column=0)

    root.mainloop()