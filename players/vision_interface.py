#import chess
import subprocess

import matlab.engine
#eng = matlab.engine.start_matlab()

class VisionInterface:
    def __init__(self):
        print("init")
        self.eng = matlab.engine.start_matlab()
        self.script_path = "D:\\Chester-master\\Chester\\testbed"
        self.eng.addpath(self.script_path, nargout=0)

    def get_move(self,board_manager):
        
        while True:
            if "button pressed":
                image=self.take_image()
                #print(image)
                newBoard=self.process_pieces(image)
                move = self.parse_move(board_manager.board,newBoard)

                if move in board_manager.get_legal_moves():
                    return move
                print("Invalid or illegal move, try again.")

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

    def parse_move(self, board, whiteOccupancyMap,blackOccupancyMap):
        beforeMoveMap=[[0 for _ in range(8)] for _ in range(8)]
        afterMoveMap=whiteOccupancyMap+2*blackOccupancyMap
        storageMap=0

        changeMap = [[0 for _ in range(8)] for _ in range(8)]
        signedChangeMap = [[0 for _ in range(8)] for _ in range(8)]

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                row = 7 - chess.square_rank(square)
                col = chess.square_file(square)
                if piece.color == chess.WHITE:
                    beforeMoveMap[row][col] = 1
                else:
                    beforeMoveMap[row][col] = -1

        for i in range(8):
            for j in range(8):
                changeMap[i][j] = 0 if beforeMoveMap[i][j]==afterMoveMap[i][j] else 1

                if beforeMoveMap[i][j]==0 and afterMoveMap[i][j]==0:
                    signedChangeMap[i][j]=0
                elif beforeMoveMap[i][j]==0 and afterMoveMap[i][j]!=0:
                    signedChangeMap[i][j]=1
                else:
                    signedChangeMap[i][j]=-1
                    yield

        changeCount=sum(sum(row) for row in changeMap)
        storageChangeCount=0

        isCastling = changeCount == 4
        isPromotion= changeCount==2 and storageChangeCount>=2
        isCapture= changeCount==2 and storageChangeCount==1
        isEnPassant= changeCount == 3

        piece=None

        if isCastling:
            negativeChanges=findGridSquare(signedChangeMap,-1)
            for i in range(2):
                if negativeChanges[i][1]==4:
                    fromSq=negativeChanges[i]
            positiveChanges=findGridSquare(signedChangeMap,1)
            toSq=(2 if positiveChanges[2][fromSq[1]] else 6 ,fromSq[1])


        elif isPromotion:
            fromSq=findGridSquare(signedChangeMap,-1)
            if storageChangeCount==3:
                for i in range(8):
                    for j in range(8):
                        if whiteOccupancyMap[i][j] and blackOccupancyMap[i][j]:
                            toSq = (i, j)

            else:
                toSq=findGridSquare(signedChangeMap,1)
            piece=findGridSquare(storageMap,-1)

        elif isEnPassant:
            toSq=findGridSquare(signedChangeMap,1)
            for i in range(2):
                for j in range(2):
                    try:
                        if signedChangeMap[toSq[0]+pow(-1,i)][toSq[1]+pow(-1,j)]==-1:
                            fromSq=signedChangeMap[toSq[0]+pow(-1,i)][toSq[1]+pow(-1,j)]
                    except:
                        continue

        elif isCapture:
            fromSq=findGridSquare(signedChangeMap,-1)
            for i in range(8):
                for j in range(8):
                    if whiteOccupancyMap[i][j] and blackOccupancyMap[i][j]:
                        toSq=(i,j)

        else:
            fromSq=findGridSquare(signedChangeMap,-1)
            toSq=findGridSquare(signedChangeMap,1)

        #convert from index to board ref
        move=(fromSq,toSq)
        move=convert_to_uci(move)
        return move

def findGridSquare(grid,value):
    gridSquares=[]
    for row in range(8):
        for col in range(8):
            if grid[row][col] == value:
                gridSquares.append((row,col))

def convert_to_uci(move):
    square = chr(ord("a") + move[0]) + str(move[1])
    return square


if __name__ == "__main__":
    vision = VisionInterface()
    image = vision.take_image()
    whiteOccupancyMap, blackOccupancyMap = vision.process_pieces()
    vision.parse_move(bm.board, whiteOccupancyMap, blackOccupancyMap) #bm.board pass from someone else