import tkinter as tk
from pyniryo import NiryoRobot, PinID, PoseObject

class ControlPanel:
    def __init__(self):
        robot_ip = ""
        self.robot=NiryoRobot(robot_ip)
        self.window = tk.Tk()
        self.window.title("Control Panel")

        # main panel
        self.panel = tk.Frame(self.window, padx=10, pady=10)
        self.panel.pack()

        # -----------------
        # regular buttons
        # -----------------

        tk.Button(self.panel, text="print Pose", command=self.print_pose).grid(row=0, column=0, pady=5, sticky="ew")
        tk.Button(self.panel, text="Action 2", command=self.action2).grid(row=1, column=0, pady=5, sticky="ew")

        # -----------------
        # inputs for go button
        # -----------------

        self.inputs = []

        for i in range(6):
            entry = tk.Entry(self.panel, width=10)
            entry.grid(row=2+i, column=0, pady=2)
            self.inputs.append(entry)

        tk.Button(self.panel, text="Go", command=self.processInputs).grid(row=8, column=0, pady=10, sticky="ew")

        self.window.mainloop()

    def print_pose(self):
        print("pose")

    def action2(self):
        print("action2 called")

    def processInputs(self):
        values = []

        for entry in self.inputs:
            values.append(entry.get())

        print("values:", values)


if __name__ == "__main__":
    ControlPanel()