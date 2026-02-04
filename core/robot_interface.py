import chess
from core.robot_manipulator import RobotManipulator

class RobotInterface:

    def __init__(self, boardStart=(360, -100), boardOffset=31,whiteStorageStart=(0, 0), blackStorageStart=(10, 0),storageOffset=1):
        self.boardMap = self.init_board_map(boardStart, boardOffset)
        self.storageMap, self.storageOccupancy = self.init_storage(whiteStorageStart,blackStorageStart,storageOffset)
        self.rm=RobotManipulator()

    def translate(self,move,board):
        moveQueue=[] #list of target destination tuples

        fromSq=move[:2]
        toSq=move[2:4]
        piece=board.piece_at(chess.parse_square(fromSq)
)
        isCapture=board.piece_at(chess.parse_square(toSq))!=None
        isEnPassant=piece.piece_type==chess.PAWN and board.piece_at(chess.parse_square(toSq))==None and fromSq[0]!=toSq[0]
        isCastling = piece.piece_type==chess.KING and fromSq[0]=="e" and toSq[0] in {"g","c"}
        isPromotion=len(move)==5

        isWhite=piece.color==chess.WHITE
        homeRank=1 if isWhite else 8
        pawnDir=1 if isWhite else -1

        #find case and queue correct move(s)
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

        return moveQueue

    def executeMoveQueue(self,moveQueue):
        print("Starting move queue:")
        for i,move in enumerate(moveQueue):
            print(f"Executing move {i+1} of {len(moveQueue)} : {move}")
            #pickup
            if len(move[0])==1:
                piece=move[0]
                #find highest index occupied storage slot
                for i in reversed(range(len(self.storageOccupancy[piece]))):
                    if self.storageOccupancy[piece][i]:
                        targetSlot = i
                        self.storageOccupancy[piece][i] = False
                        break

                #move to storageMap[piece][targetSlot]
                print(f"Moving to slot {piece}{targetSlot} ({self.storageMap[piece][targetSlot]})...")

            else:
                #move to boardMap[move[0]]
                print(f"Moving to square {move[0]} ({self.boardMap[move[0]]})...")

            print("pickup")

            #drop
            if len(move[1])==1:
                piece=move[1]
                #find lowest index unoccupied storage slot
                for i in range(len(self.storageOccupancy[piece])):
                    if not self.storageOccupancy[piece][i]:
                        targetSlot = i
                        self.storageOccupancy[piece][i] = True
                        break
                #move to storageMap[piece][targetSlot]
                print(f"Moving to slot {piece}{targetSlot} ({self.storageMap[piece][targetSlot]})...")
            else:
                #move to boardMap[move[1]]
                print(f"Moving to square {move[1]} ({self.boardMap[move[1]]})...")
            #drop
            print("drop")

    def init_board_map(self,startPos,offset):
        boardMap={}
        for rank in range(8):
            for file in range(8):
                square=chr(ord("a")+file)+str(rank+1)
                boardMap[square]=(startPos[0]-offset*file,startPos[1]+offset*rank)

        return boardMap

    def init_storage_map(self,whiteStartPos,blackStartPos,offset):
        storageMap={}
        layout={
            'p' : [(0,i) for i in range(8)],
            'r' : [(1,0),(1,1),(2,0),(2,1)],
            'n' : [(1,2),(1,3),(2,2),(2,3)],
            'b' : [(1,4),(1,5),(2,4),(2,5)],
            'q' : [(1,7),(2,6),(2,7)],
            'k' : [(1,6)]
        }
        for piece in layout:
            # iterate through piece positions
            # apply offset between grid squares
            # append to list in dictionary

            #white
            storageMap[piece.upper()]=[]
            for pos in layout[piece]:
                x=pos[0]*offset+whiteStartPos[0]
                y=pos[1]*offset+whiteStartPos[1]
                storageMap[piece.upper()].append((x,y))

            #black
            #todo potentially need to flip black but thats a later problem
            storageMap[piece]=[]
            for pos in layout[piece]:
                x=pos[0]*offset+blackStartPos[0]
                y=pos[1]*offset+blackStartPos[1]
                storageMap[piece].append((x,y))
        return storageMap

    def init_storage_occupancy(self,storageMap,mode="standard"):
        # True = Occupied
        # False = Free
        standardCounts={
            'P': 8, 'p' : 8,
            'R': 2, 'r' : 2,
            'N': 2, 'n' : 2,
            'B': 2, 'b' : 2,
            'Q': 1, 'q' : 1,
            'K': 1, 'k' : 1
        }
        #todo read board and manually count instead of hard code

        storageOccupancy={}
        for pieceType in storageMap:
            storageOccupancy[pieceType]=[]
            totalSlots = len(storageMap[pieceType])
            onBoard=standardCounts[pieceType]
            for i in range(totalSlots):
                if mode=="standard":
                    storageOccupancy[pieceType].append(i>onBoard)
                else:
                    storageOccupancy[pieceType].append(True)
        return storageOccupancy

    def init_storage(self,whiteStartPos,blackStartPos,offset):
        storageMap=self.init_storage_map(whiteStartPos,blackStartPos,offset)
        storageOccupancy=self.init_storage_occupancy(storageMap)

        return storageMap,storageOccupancy