from pyniryo import *

robotIpAddress = "192.168.42.1"

robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()

robot.set_volume(50)
print(robot.get_sounds())
robot.play_sound("Pink Pony Club-Chappell Roan ).mp3")
delay(1000)
robot.stop_sound()