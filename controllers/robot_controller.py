import threading
import chess
from controllers.robot_manipulator import RobotManipulator

class RobotController:

    def __init__(self ,robot_white=None,robot_black=None,databus=None):

        self.lock=threading.Lock()
        self.databus=databus

        whiteBoardCoords={
            "boardStart": (380.4,-109.5),
            "boardOffset": 27.58,
            "whiteStorageStart": (170, 170),
            "blackStorageStart": (170, -180),
            "storageOffset": 0,
            "directionMultiplier": 1
        }
        blackBoardCoords={
            "boardStart": self.translate_position(whiteBoardCoords["boardStart"]),
            "boardOffset": whiteBoardCoords["boardOffset"],
            "whiteStorageStart": self.translate_position(whiteBoardCoords["whiteStorageStart"]),
            "blackStorageStart": self.translate_position(whiteBoardCoords["blackStorageStart"]),
            "storageOffset": whiteBoardCoords["storageOffset"],
            "directionMultiplier": whiteBoardCoords["directionMultiplier"]*-1
        }

        if robot_white is None and robot_black is not None:
            self.white_rm=None
            self.black_rm=RobotManipulator(robot_black,blackBoardCoords,self.databus.robot1)
        elif robot_white is not None and robot_black is None:
            self.white_rm=RobotManipulator(robot_white,whiteBoardCoords,self.databus.robot1)
            self.black_rm=None
        elif robot_white==robot_black:
            self.white_rm=RobotManipulator(robot_white,whiteBoardCoords,self.databus.robot1)
            self.black_rm=self.white_rm
        else:
            self.white_rm=RobotManipulator(robot_white,whiteBoardCoords,self.databus.robot1)
            self.black_rm=RobotManipulator(robot_black,whiteBoardCoords,self.databus.robot2)

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

    def execute_move_queue(self,moveQueue,board,isWhite):
        with (self.lock):
            if isWhite:
                if self.white_rm is None:
                    return
                rm=self.white_rm
                self.databus.execLog.append("White robot:")
            else:
                if self.black_rm is None:
                    return
                rm=self.black_rm
                self.databus.execLog.append("Black robot:")

            self.databus.execLog.append("Starting move queue:")
            for i,move in enumerate(moveQueue):
                self.databus.execLog.append(f"Executing move {i+1} of {len(moveQueue)} : {move[0]} to {move[1]}")
                #pickup
                if len(move[0])==1:
                    piece=move[0]
                    #find highest index occupied storage slot
                    for i in reversed(range(len(rm.storageOccupancy[piece]))):
                        if rm.storageOccupancy[piece][i]:
                            targetSlot = i
                            rm.storageOccupancy[piece][i] = False
                            break

                    #move to storageMap[piece][targetSlot]
                    self.databus.execLog.append(f"Moving to slot {piece}{targetSlot} ({rm.storageMap[piece][targetSlot]})...")
                    x,y= rm.storageMap[piece][targetSlot]

                else:
                    #move to boardMap[move[0]]
                    piece=board.piece_at(chess.parse_square(move[0])).symbol()
                    self.databus.execLog.append(f"Moving to square {move[0]} ({rm.boardMap[move[0]]})...")
                    x,y=rm.boardMap[move[0]]

                rm.move(x, y)
                self.databus.execLog.append("picking up piece")
                rm.pickup(piece)

                #drop
                if len(move[1])==1:
                    piece=move[1]
                    #find lowest index unoccupied storage slot
                    for i in range(len(rm.storageOccupancy[piece])):
                        if not rm.storageOccupancy[piece][i]:
                            targetSlot = i
                            rm.storageOccupancy[piece][i] = True
                            break
                    #move to storageMap[piece][targetSlot]
                    self.databus.execLog.append(f"Moving to slot {piece}{targetSlot} ({rm.storageMap[piece][targetSlot]})...")
                    x,y=rm.storageMap[piece][targetSlot]
                else:
                    #move to boardMap[move[1]]
                    self.databus.execLog.append(f"Moving to square {move[1]} ({rm.boardMap[move[1]]})...")
                    x,y=rm.boardMap[move[1]]
                #drop
                rm.move(x, y)
                self.databus.execLog.append("dropping piece")
                rm.place(piece)

            rm.return_home()
            self.databus.robotBusy = False

    def translate_position(self,position,x_translation=400):
        x=-position[0]+x_translation
        y=-position[1]
        return x,y