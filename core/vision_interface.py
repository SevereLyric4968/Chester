class VisionInterface:
    def __init__(self):
        #connect camera

    def get_move(self,board_manager):
        while True:
            if "button pressed":
                image=self.take_image()
                newBoard=self.process_image(image)
                move = self.parse_move(board_manager.board,newBoard)

                if move in board_manager.get_legal_moves():
                    return move
                print("Invalid or illegal move, try again.")

    def take_image(self):
        image="camera"
        return image

    def process_image(self,image):
        occupiedSpaces="kirsty shit HSV"
        return occupiedSpaces

    def parse_move(self,boardBefore,occupiedSpaces):
        move="compare occupied spaces to board now and find what move happened"
        return move
