from pyniryo import *
import pyniryo

robotIpAddress = "192.168.42.1"

robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()

robot.set_volume(50)
print(robot.get_sounds())
#robot.play_sound("error.wav")
#delay(1000)
#robot.stop_sound()

