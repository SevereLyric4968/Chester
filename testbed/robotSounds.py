from pyniryo import *

robotIpAddress = "10.10.10.10"

robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()

robot.set_volume(50)
print(robot.get_sounds())
robot.play_sound("Pink Pony Club-Chappell Roan ).mp3")