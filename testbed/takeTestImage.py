import cv2
from pyniryo import NiryoRobot
from pyniryo.vision.image_functions import uncompress_image

robot = NiryoRobot("192.168.42.1")

try:
    img = uncompress_image(robot.get_img_compressed())
    img = cv2.flip(img, 0)  
    cv2.imwrite("getColour.png", img)
    print("Saved image as getColour.png")
finally:
    robot.close_connection()