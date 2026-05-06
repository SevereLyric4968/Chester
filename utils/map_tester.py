import inverse_kinematics as ik
from pyniryo import *
import json
import keyboard

locationMap = json.load(open("location_maps/custom_ik_locations.json"))
robotIpAddress = "192.168.42.2"
robot = NiryoRobot(robotIpAddress)
robot.calibrate_auto()
pin_electromagnet = PinID.DO4
robot.activate_electromagnet(pin_electromagnet)
colour = "black" #black or white

robot.setup_electromagnet(pin_electromagnet)

checkingMainBoard = False
checkingStorage = True
makingAdjustments = False

flip = False

def makeAdjustment(square):
    newX, newY = locationMap[colour][square]["x"], locationMap[colour][square]["y"]
    print("Use WASD to adjust position, Enter to confirm")
    print("Checking Square:", square)
    while not keyboard.is_pressed('enter'):
        if keyboard.is_pressed('w'):
            ik.calculateIK(robot, newX+0.0005, newY, locationMap[colour][square]["z"]+0.001)
            newX += 0.0005
        elif keyboard.is_pressed('s'):
            ik.calculateIK(robot, newX-0.0005, newY, locationMap[colour][square]["z"]+0.001)
            newX -= 0.0005
        elif keyboard.is_pressed('a'):
            ik.calculateIK(robot, newX, newY+0.0005, locationMap[colour][square]["z"]+0.001)
            newY += 0.0005
        elif keyboard.is_pressed('d'):
            ik.calculateIK(robot, newX, newY-0.0005, locationMap[colour][square]["z"]+0.001)
            newY -= 0.0005
        elif keyboard.is_pressed('j'):
            ik.calculateIK(robot, newX+0.002, newY, locationMap[colour][square]["z"]+0.001)
            newX += 0.002
        elif keyboard.is_pressed('k'):
            ik.calculateIK(robot, newX-0.002, newY, locationMap[colour][square]["z"]+0.001)
            newX -= 0.002
        elif keyboard.is_pressed('l'):
            ik.calculateIK(robot, newX, newY+0.002, locationMap[colour][square]["z"]+0.001)
            newY += 0.002
        elif keyboard.is_pressed('i'):
            ik.calculateIK(robot, newX, newY-0.002, locationMap[colour][square]["z"]+0.001)
            newY -= 0.002
    locationMap[colour][square]["x"] = newX
    locationMap[colour][square]["y"] = newY
    
    json.dump(locationMap, open("location_maps/custom_ik_locations.json", "w"), indent=2)

def makeStorageAdjustment(square, number):
    newX, newY = locationMap[colour][square][number]["x"], locationMap[colour][square][number]["y"]
    print("Use WASD to adjust position, Enter to confirm")
    print("Checking Piece:", square, "Number:", number)
    while not keyboard.is_pressed('enter'):
        if keyboard.is_pressed('w'):
            ik.calculateIK(robot, newX+0.0005, newY, locationMap[colour][square][number]["z"]+0.001)
            newX += 0.0005
        elif keyboard.is_pressed('s'):
            ik.calculateIK(robot, newX-0.0005, newY, locationMap[colour][square][number]["z"]+0.001)
            newX -= 0.0005
        elif keyboard.is_pressed('a'):
            ik.calculateIK(robot, newX, newY+0.0005, locationMap[colour][square][number]["z"]+0.001)
            newY += 0.0005
        elif keyboard.is_pressed('d'):
            ik.calculateIK(robot, newX, newY-0.0005, locationMap[colour][square][number]["z"]+0.001)
            newY -= 0.0005
        elif keyboard.is_pressed('j'):
            ik.calculateIK(robot, newX+0.002, newY, locationMap[colour][square][number]["z"]+0.001)
            newX += 0.002
        elif keyboard.is_pressed('k'):
            ik.calculateIK(robot, newX-0.002, newY, locationMap[colour][square][number]["z"]+0.001)
            newX -= 0.002
        elif keyboard.is_pressed('l'):
            ik.calculateIK(robot, newX, newY+0.002, locationMap[colour][square][number]["z"]+0.001)
            newY += 0.002
        elif keyboard.is_pressed('i'):
            ik.calculateIK(robot, newX, newY-0.002, locationMap[colour][square][number]["z"]+0.001)
            newY -= 0.002
    locationMap[colour][square][number]["x"] = newX
    locationMap[colour][square][number]["y"] = newY

    json.dump(locationMap, open("location_maps/custom_ik_locations.json", "w"), indent=2)

#main board
if checkingMainBoard:
    for i in "abcdefgh":
        column = "12345678"
        if flip:
            column = column[::-1]
        for j in column:
            ik.calculateIK(robot, locationMap[colour][i+j]["x"], locationMap[colour][i+j]["y"], locationMap[colour][i+j]["z"]+0.01)
            ik.calculateIK(robot, locationMap[colour][i+j]["x"], locationMap[colour][i+j]["y"], locationMap[colour][i+j]["z"])
            if makingAdjustments:
                makeAdjustment(i+j)
            ik.calculateIK(robot, locationMap[colour][i+j]["x"], locationMap[colour][i+j]["y"], locationMap[colour][i+j]["z"]+0.01)
        flip = not flip

#storage
if checkingStorage:
    for a in "KQBNRPkqbnrp":
        i = 0
        print(a+str(i))
        try:
            while locationMap[colour][a][i]["x"] != 0:
                ik.calculateIK(robot, locationMap[colour][a][i]["x"], locationMap[colour][a][i]["y"], locationMap[colour][a][i]["z"]+0.01)
                ik.calculateIK(robot, locationMap[colour][a][i]["x"], locationMap[colour][a][i]["y"], locationMap[colour][a][i]["z"])
                if makingAdjustments:
                    makeStorageAdjustment(a,i)
                ik.calculateIK(robot, locationMap[colour][a][i]["x"], locationMap[colour][a][i]["y"], locationMap[colour][a][i]["z"]+0.01)
                if ((a+str(i))=="P7"):
                    ik.calculateIK(robot, locationMap[colour][a][i]["x"], locationMap[colour][a][i]["y"], locationMap[colour][a][i]["z"]+0.1)
                i += 1
        except:
            pass


robot.deactivate_electromagnet(pin_electromagnet)

