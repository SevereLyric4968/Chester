import chess
import subprocess

#make function calibrate runs process_b
#make funciton that runs process_p
#make function subprocess that takes variable of matlab file.

class VisionInterface:
    def __init__(self):
        self.take_image()
        self.calibrate()

    def get_move(self,board_manager):
        self.take_image()
        self.process_pieces()
        while True:
            if "button pressed":
                image=self.take_image()
                #print(image)
                newBoard=self.process_pieces(image)
                move = self.parse_move(board_manager.board,newBoard)

                if move in board_manager.get_legal_moves():
                    return move
                print("Invalid or illegal move, try again.")
         
    
    #runs matlabfilepath, insert variable(s) you want you spit back out
    # THIS REQUIRES THE VARIABLE YOU WANT TO READ TO BE PRINTED IN THE MATLAB CONSOLE FIRST
    # MAKE SURE YOU DISP(VARIABLE)
    def run_subprocess(filepath: str, *variables: str) -> list[str]:
        disp_calls = "; disp('---'); ".join(f"disp({v})" for v in variables)
        result = subprocess.run(
            ["matlab", "-batch", f"run('{filepath}'); {disp_calls}"],
            capture_output=True,
            text=True
        )
        parts = result.stdout.strip().split('---\n')
        return [p.strip() for p in parts]

    #all of this needs tested VVV
    def take_image(self):
        image = self.run_subprocess("D:\Chester-master\Chester\testbed\centering.m", "imgRGB")
        return image

    def process_pieces(self,image):
        white_occupancy_grid, black_occupancy_grid = self.run_subprocess("D:\Chester-master\Chester\testbed\centering.m", "black_occupancy_grid", "white_occupancy_grid")
        return white_occupancy_grid, black_occupancy_grid
    
    def calibrate(self):
        calibration_file = self.run_subprocess("D:\Chester-master\Chester\testbed\process_board.m", "board_calibration.mat")
        return calibration_file

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