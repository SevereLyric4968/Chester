import json
import threading
import chess
from controllers.robot_manipulator import RobotManipulator

class RobotController:

    def __init__(self ,robot_white=None,robot_black=None,databus=None):

        self.lock=threading.Lock()
        self.databus=databus

        self.locationMap=self.load_json(r"C:\Users\Jayda\PycharmProjects\Chester\testbed\testLocations.json")
        self.storageOccupancy={
            "K":[False],
            "Q":[False,True],
            "B":[False,False,True],
            "N":[False,False,True],
            "R":[False,False,True],
            "P":[False,False,False,False,False,False,False,False],

            "k": [False],
            "q": [False, True],
            "b": [False, False, True],
            "n": [False, False, True],
            "r": [False, False, True],
            "p": [False, False, False, False, False, False, False, False]
        }

        if robot_white is None and robot_black is not None:
            self.white_rm=None
            self.black_rm=RobotManipulator(robot_black, self.databus.robot1)
        elif robot_white is not None and robot_black is None:
            self.white_rm=RobotManipulator(robot_white, self.databus.robot1)
            self.black_rm=None
        elif robot_white==robot_black:
            self.white_rm=RobotManipulator(robot_white, self.databus.robot1)
            self.black_rm=self.white_rm
        else:
            self.white_rm=RobotManipulator(robot_white, self.databus.robot1)
            self.black_rm=RobotManipulator(robot_black, self.databus.robot2)

    def uci_to_move_queue(self,move,board):

        moveQueue=[] #list of target destination tuples
        fromSq=move[:2]
        toSq=move[2:4]
        piece=board.piece_at(chess.parse_square(fromSq))

        isCapture=board.piece_at(chess.parse_square(toSq))!=None
        isEnPassant=piece.piece_type==chess.PAWN and board.piece_at(chess.parse_square(toSq))==None and fromSq[0]!=toSq[0]
        isCastling = piece.piece_type==chess.KING and fromSq[0]=="e" and toSq[0] in {"g","c"}
        isPromotion=len(move)==5

        isWhite=piece.color==chess.WHITE

        homeRank=1 if isWhite else 8
        pawnDir=1 if isWhite else -1

        #find case and queue correct moves
        if isCastling:
            #kingside
            if toSq[0]=="g":
                # move king to square
                moveQueue.append((fromSq,toSq))

                # move rook to square
                moveQueue.append(("h"+str(homeRank),"f"+str(homeRank)))
            #queenside
            if toSq[0]=="c":
                # move king to square
                moveQueue.append((fromSq,toSq))

                # move rook to square
                moveQueue.append(("a"+str(homeRank),"d"+str(homeRank)))

        elif isPromotion:
            if isCapture:
                #move dead piece to storage slot
                moveQueue.append((toSq,board.piece_at(chess.parse_square(toSq)).symbol()))

            #move pawn to square
            moveQueue.append((fromSq,toSq))

            #move pawn to storage slot
            pawnSymbol = 'P' if isWhite else 'p'
            moveQueue.append((toSq, pawnSymbol))

            #move piece from storage slot to square
            moveQueue.append((move[4],toSq))


        elif isEnPassant:
            #move pawn to square
            moveQueue.append((fromSq,toSq))

            #move dead piece to storage slot
            moveQueue.append((toSq[0]+str(int(toSq[1])-pawnDir),board.piece_at(chess.parse_square(toSq[0]+str(int(toSq[1])-pawnDir))).symbol()))


        elif isCapture:
            #move dead piece to graveyard
            moveQueue.append((toSq,board.piece_at(chess.parse_square(toSq)).symbol()))

            #move piece to square
            moveQueue.append((fromSq,toSq))

        else:
            #move piece to square
            moveQueue.append((fromSq,toSq))

        return (moveQueue,isWhite)

    def move_to_target(self,rm,target,color):
        if len(target) == 1:
            # find highest index occupied storage slot
            for i in reversed(range(len(self.storageOccupancy[target]))):
                if self.storageOccupancy[target][i]:
                    targetSlot = i
                    self.storageOccupancy[target][i] = False
                    break
            target += targetSlot
            targetLocation = self.locationMap[color][target]
            self.databus.execLog.append(f"Moving to {target} ({targetLocation})...")
            x, y, z = targetLocation["x"], targetLocation["y"], targetLocation["z"]

        rm.move(x, y, z)

    def execute_move_queue(self,moveQueue,board,isWhite):
        with (self.lock):
            if isWhite:
                if self.white_rm is None:
                    return
                rm=self.white_rm
                self.databus.execLog.append("White robot:")
                color="white"
            else:
                if self.black_rm is None:
                    return
                rm=self.black_rm
                self.databus.execLog.append("Black robot:")
                color="black"

            self.databus.execLog.append("Starting move queue:")
            for i,move in enumerate(moveQueue):
                self.databus.execLog.append(f"Executing move {i+1} of {len(moveQueue)} : {move[0]} to {move[1]}")
                if len(move[0])==1:
                    piece = move[0]
                else:
                    board.piece_at(chess.parse_square(move[0])).symbol()
                #pickup
                self.move_to_target(rm,move[0],color)
                self.databus.execLog.append("picking up piece")
                rm.pickup(piece)

                # place
                self.move_to_target(rm,move[0],color)
                self.databus.execLog.append("picking up piece")
                rm.place(piece)
                #drop

            self.databus.robotBusy = False

    def translate_position(self,position,x_translation=400):
        x=-position[0]+x_translation
        y=-position[1]
        return x,y

    def load_config(path):
        with open(path, "r") as f:
            return json.load(f)
