import matlab.engine
class VisionInterface:
    def __init__(self):
        print("init")
        self.eng = matlab.engine.start_matlab()
        self.script_path = "C:\\Users\\kirst\\Chester\\testbed"
        self.eng.addpath(self.script_path, nargout=0)

        #self.calibrate()
        #self.take_image()

    def take_image(self):
        print("take_image")
        self.eng.centering(nargout=0)
        image = self.eng.workspace['imgRGB']
        return image

    def process_pieces(self):
        print("process_pieces")
        self.eng.process_pieces(nargout=0)
        blackOccupancyMap = self.eng.workspace['black_occupancy_grid']
        whiteOccupancyMap = self.eng.workspace['white_occupancy_grid']
        return blackOccupancyMap, whiteOccupancyMap
    
    def calibrate(self):
        print("calibrate")
        self.eng.process_board(nargout=0)

if __name__ == "__main__":
    vision = VisionInterface()
    vision.calibrate()
    vision.process_pieces()