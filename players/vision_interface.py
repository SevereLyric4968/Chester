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
        #pseudo code
        #run camera.m
        #returns image file path into VVV
        image="file path.png"
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
