import tkinter as tk
from pyniryo import NiryoRobot, PinID, PoseObject
import inverse_kinematics as ik

class ControlPanel:
    def __init__(self):
        robot_ip = "192.168.42.2"
        self.robot = NiryoRobot(robot_ip)
        self.robot.calibrate_auto()

        self.homePose = PoseObject(0.1343, 0, 0.1652, 0, 1, 0)

        self.window = tk.Tk()
        self.window.title("Control Panel")

        self.panel = tk.Frame(self.window, padx=10, pady=10)
        self.panel.pack()

        # -----------------
        # basic buttons
        # -----------------

        tk.Button(self.panel, text="Print Pose", command=self.printPose).grid(row=0, column=0, columnspan=2, sticky="ew")
        tk.Button(self.panel, text="Home", command=self.home).grid(row=1, column=0, columnspan=2, sticky="ew")

        # -----------------
        # nudge controls
        # -----------------

        tk.Button(self.panel, text="X +1mm", command=lambda: self.nudge(0.001,0,0)).grid(row=2, column=0, sticky="ew")
        tk.Button(self.panel, text="X -1mm", command=lambda: self.nudge(-0.001,0,0)).grid(row=2, column=1, sticky="ew")

        tk.Button(self.panel, text="Y +1mm", command=lambda: self.nudge(0,0.001,0)).grid(row=3, column=0, sticky="ew")
        tk.Button(self.panel, text="Y -1mm", command=lambda: self.nudge(0,-0.001,0)).grid(row=3, column=1, sticky="ew")

        tk.Button(self.panel, text="Z +1mm", command=lambda: self.nudge(0,0,0.001)).grid(row=4, column=0, sticky="ew")
        tk.Button(self.panel, text="Z -1mm", command=lambda: self.nudge(0,0,-0.001)).grid(row=4, column=1, sticky="ew")

        # -----------------
        # pose inputs
        # -----------------

        labels = ["X","Y","Z","Yaw","Pitch","Roll"]
        self.inputs = {}

        for i, name in enumerate(labels):
            tk.Label(self.panel, text=name).grid(row=5+i, column=0)
            entry = tk.Entry(self.panel, width=10)
            entry.grid(row=5+i, column=1)
            self.inputs[name] = entry

        tk.Button(self.panel, text="Go To Pose", command=self.gotoPose).grid(row=11, column=0, columnspan=2, pady=10, sticky="ew")

        self.window.mainloop()

    def printPose(self):
        print(self.robot.get_pose())

    def home(self):
        self.robot.move_pose(self.homePose)

    def nudge(self, dx, dy, dz):
        pose = self.robot.get_pose()

        newPose = PoseObject(
            pose.x + dx,
            pose.y + dy,
            pose.z + dz,
            pose.roll,
            pose.pitch,
            pose.yaw
        )

        self.robot.move_pose(newPose)

    def gotoPose(self):
        currentPose = self.robot.get_pose()
        try:
            x = float(self.inputs["X"].get())
        except:
            x=currentPose.x
        try:
            y = float(self.inputs["Y"].get())
        except:
            y=currentPose.y
        try:
            z = float(self.inputs["Z"].get())
        except:
            z=currentPose.z
        try:
            yaw = float(self.inputs["Yaw"].get())
        except:
            yaw=currentPose.yaw
        try:
            pitch = float(self.inputs["Pitch"].get())
        except:
            pitch=1.5708
        try:
            roll = float(self.inputs["Roll"].get())
        except:
            roll=currentPose.roll

        pose = PoseObject(x, y, z, roll, pitch, yaw)
        ik.calculateIK(self.robot,*pose)
        #self.robot.move_pose(pose)


if __name__ == "__main__":
    ControlPanel()