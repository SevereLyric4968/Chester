import inverse_kinematics as ik
from pyniryo import *
import json
import keyboard

locationMap = json.load(open("location_maps/custom_ik_locations.json"))
robotIpAddress = "192.168.42.1"
robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()
pin_electromagnet = PinID.DO4
robot.activate_electromagnet(pin_electromagnet)

robot.setup_electromagnet(pin_electromagnet)

flip = False

def makeAdjustment(square):
    newX, newY = locationMap["white"][square]["x"], locationMap["white"][square]["y"]
    print("Use WASD to adjust position, Enter to confirm")
    while not keyboard.is_pressed('enter'):
        if keyboard.is_pressed('w'):
            ik.calculateIK(robot, newX+0.001, newY, locationMap["white"][square]["z"]+0.001)
            newX += 0.001
        elif keyboard.is_pressed('s'):
            ik.calculateIK(robot, newX-0.001, newY, locationMap["white"][square]["z"]+0.001)
            newX -= 0.001
        elif keyboard.is_pressed('a'):
            ik.calculateIK(robot, newX, newY+0.001, locationMap["white"][square]["z"]+0.001)
            newY += 0.001
        elif keyboard.is_pressed('d'):
            ik.calculateIK(robot, newX, newY-0.001, locationMap["white"][square]["z"]+0.001)
            newY -= 0.001
    locationMap["white"][square]["x"] = newX
    locationMap["white"][square]["y"] = newY
    
    json.dump(locationMap, open("location_maps/custom_ik_locations.json", "w"), indent=2)


for i in "abcdefgh":
    column = "12345678"
    if flip:
        column = column[::-1]
    for j in column:
        ik.calculateIK(robot, locationMap["white"][i+j]["x"], locationMap["white"][i+j]["y"], locationMap["white"][i+j]["z"]+0.01)
        ik.calculateIK(robot, locationMap["white"][i+j]["x"], locationMap["white"][i+j]["y"], locationMap["white"][i+j]["z"])
        ik.calculateIK(robot, locationMap["white"][i+j]["x"], locationMap["white"][i+j]["y"], locationMap["white"][i+j]["z"]+0.01)

        makeAdjustment(i+j)
    flip = not flip

robot.deactivate_electromagnet(pin_electromagnet)

