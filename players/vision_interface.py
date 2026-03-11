import chess
import subprocess

class VisionInterface:
    def __init__(self):
        #connect camera
        pass

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
        # Here's my proposed solution to Matlab Integration and passing variables to Python
        # result() launches the matlab script for taking pictures
        # (for now i am not changing it to a python script unless serious delays occur from this process).
        # stdout.strip() is a function that reads whatever prints into the console and cleans it up.
        # within camera.m there is a method that prints the filepath of the taken image
        # into the console for stdout.strip() to read and write to image.
        # feel free to copy this method for process_image.
        #if i have time i'll look into how to pass this filepath back to matlab to speed up kirsty's bit
        result = subprocess.run(
        [
            "matlab",
            "-batch",
            "run('D:/Chester-master/Chester/testbed/camera.m')"
        ],
        capture_output=True,
        text=True
        )
        image = result.stdout.strip()   
        return image  

    def process_image(self,image):
        occupiedSpaces="kirsty shit HSV"
        return occupiedSpaces

    """def parse_move(self, board, afterMoveMap):

        beforeMoveMap=[[0 for _ in range(8)] for _ in range(8)]

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                row = 7 - chess.square_rank(square)  # flip so white is at bottom
                col = chess.square_file(square)
                if piece.color == chess.WHITE:
                    beforeMoveMap[row][col] = 1
                else:
                    beforeMoveMap[row][col] = -1

        changeMap=[[0 for _ in range(8)] for _ in range(8)]

        for i in range(8):
            for j in range(8):
                changeLocationMap = not(beforeMoveMap[i][j] and afterMoveMap[i][j])

        changeCount=sum(sum(row) for row in changeMap)

        isCastling = changeCount == 4
        #isPromotion = some bullshit
        isCapture = changeCount == 1

        if isCastling:
            # fromSq=king
            # toSq=g or c
            #kingside
            if toSq[0]=="g":

            #queenside
            if toSq[0]=="c":

        elif isPromotion:
            if isCapture:

        elif isEnPassant:

        elif isCapture:

        else:
            fromSq=moveMatrix.index(-1)
            toSq=moveMatrix.index(1)

        #convert from index to board ref
        move=(fromSq,toSq)
        return move"""
