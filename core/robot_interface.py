import chess


class RobotInterface:
    moveMap={}
    def translate(self,move,board):
        pass
        fromSq=move[:2]
        toSq=move[2:4]
        piece=board.piece_at(fromSq)
        isCapture=board.piece_at(toSq)!=None
        isEnPassant=piece==chess.PAWN and board.piece_at(toSq)==None and fromSq[0]!=toSq[0]
        isCastling = piece==chess.KING and fromSq[0]=="e" and toSq[0] in {"g","c"}
        isPromotion=len(move)==5
        #take move
        #select case
        #complete appropriate moves

        #cases

        #normal move

        #capture
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


    def send_move(self,target,destination):
        pass

    def sendToStorage(self):
        pass

    def getFromStorage(self):
        pass

    def capture(self,fromSquare,piece):
        pass
    def move(self,fromSquare,toSquare):
        pass