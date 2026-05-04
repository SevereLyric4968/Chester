import inverse_kinematics as ik
from pyniryo import *
import json

locationMap = json.load(open("location_maps/custom_ik_locations.json"))
robotIpAddress = "192.168.42.1"
robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()
pin_electromagnet = PinID.DO4
robot.activate_electromagnet(pin_electromagnet)

robot.setup_electromagnet(pin_electromagnet)

flip = False

for i in "abcdefgh":
    column = "12345678"
    if flip:
        column = column[::-1]
    for j in column:
        ik.calculateIK(robot, locationMap["white"][i+j]["x"], locationMap["white"][i+j]["y"], locationMap["white"][i+j]["z"]+0.01)
        ik.calculateIK(robot, locationMap["white"][i+j]["x"], locationMap["white"][i+j]["y"], locationMap["white"][i+j]["z"])
        ik.calculateIK(robot, locationMap["white"][i+j]["x"], locationMap["white"][i+j]["y"], locationMap["white"][i+j]["z"]+0.01)

    flip = not flip

robot.deactivate_electromagnet(pin_electromagnet)

