import cv2
from pyniryo import *
from pyniryo import NiryoRobot
from pyniryo.vision.image_functions import uncompress_image

robot = NiryoRobot("192.168.42.1")
robot.calibrate_auto()

photoLocation = PoseObject(0.1534,  -0.0029, 0.2420, 0, 1.5, 0)
robot.move_pose(photoLocation)

"""
try:
    img = uncompress_image(robot.get_img_compressed())
    img = cv2.flip(img, 0)  
    cv2.imwrite("testbed/getColour.png", img)
    print("Saved image as getColour.png")
finally:
    robot.close_connection()
    """