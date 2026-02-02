import chess


class RobotInterface:
    def translate(self,move,board):
        pass
        moveQueue=[] #list of target destination tuples

        fromSq=move[:2]
        toSq=move[2:4]
        piece=board.piece_at(fromSq)

        isCapture=board.piece_at(toSq)!=None
        isEnPassant=piece==chess.PAWN and board.piece_at(toSq)==None and fromSq[0]!=toSq[0]
        isCastling = piece==chess.KING and fromSq[0]=="e" and toSq[0] in {"g","c"}
        isPromotion=len(move)==5

        #find case and queue correct move(s)
        #todo replace print with correct move sequence
        if isCastling:
            print("move king to square")
            print("move rook to square")

        elif isPromotion:
            if isCapture:
                print("move dead piece to storage slot")
                print("move pawn to square")
                print("move pawn to storage slot")
                print("move piece from storage slot to square")

        elif isEnPassant:
            print("move pawn to square")
            print("move dead piece to storage slot")

        elif isCapture:
            print("move dead piece to graveyard")
            print("move piece to square")

        else:
            print("move piece to square")

        return moveQueue

    def executeMoveQueue(self,moveQueue,storageMap,boardMap,storageOccupancy):
        for move in moveQueue:
            #pickup
            if len.move[0]==1:
                #find lowest index unoccupied storage slot
                #move to storageMap[piece][slot]
                #pickup
            else:
                #move to boardMap[move[0]]
                #pickup

            #drop
            if len.move[1]==1:
                #find highest index occupied storage slot
                #move to storageMap[piece][slot]
                #drop
            else:
                #move to boardMap[move[1]]
                #drop

    def init_board_map(self,startPos,offset):
        boardMap={}
        for rank in range(8):
            for file in range(8):
                square=chr(ord("a")+file)+str(rank+1)
                boardMap[square]=(startPos[0]+offset*file,startPos[1]+offset*rank)

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