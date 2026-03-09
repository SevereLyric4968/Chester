beforeMoveMap=[
                [-1,-1,-1,-1,-1,-1,-1,-1],
                [-1,-1,-1,-1,-1,-1,-1,-1],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [1,1,1,1,1,1,1,1],
                [1,0,0,0,1,1,1,1]
]
whiteOccupancyMap=[
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [1,1,1,1,1,1,1,1],
                [0,1,1,0,0,1,1,1]
                ]
blackOccupancyMap=[
                [1,1,1,1,1,1,1,1],
                [1,1,1,1,1,1,1,1],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0],
                [0,0,0,0,0,0,0,0]
]


def parse_move(beforeMoveMap, whiteOccupancyMap, blackOccupancyMap):

    if not(beforeMoveMap): beforeMoveMap = [[0 for _ in range(8)] for _ in range(8)]
    afterMoveMap = [[0 for _ in range(8)] for _ in range(8)]

    for i in range(8):
        for j in range(8):
            afterMoveMap[i][j] = whiteOccupancyMap[i][j]+blackOccupancyMap[i][j]

    posDiffs=[]
    negDiffs=[]
    posStorageDiffs=[]
    negStorageDiffs=[]

    for i in range(8):
        for j in range(8):
            if beforeMoveMap[i][j] == 0 and afterMoveMap[i][j] == 1:
                posDiffs.append((i,j))
            elif beforeMoveMap[i][j] != 0 and afterMoveMap[i][j] == 0:
                negDiffs.append((i,j))

    changeCount = len(posDiffs)+len(negDiffs)
    storageChangeCount = len(posStorageDiffs)+len(negStorageDiffs)

    isCastling = changeCount == 4
    isPromotion = changeCount == 2 and storageChangeCount >= 2
    isCapture = changeCount == 1 and storageChangeCount == 1
    isEnPassant = changeCount == 3

    print(changeCount)

    piece = None

    if isCastling:
        for i in range(2):
            if negDiffs[i][1] == 4:
                fromSq = negDiffs[i]
        toSq = (fromSq[0],1 if posDiffs[0][1]==1 else 6)


    elif isPromotion:
        fromSq = negDiffs[0]
        if storageChangeCount == 3:
            for i in range(8):
                for j in range(8):
                    if (beforeMoveMap[i][j] != 1 and whiteOccupancyMap[i][j] == 1) or (
                            beforeMoveMap[i][j] != -1 and blackOccupancyMap[i][j] == 1):
                        toSq = (i, j)

        else:
            toSq = posDiffs[0]
        piece = negStorageDiffs[0]

    elif isEnPassant:
        toSq = posDiffs[0]
        fromSq = negStorageDiffs[0] if negDiffs[0][0]!=toSq[0] else negStorageDiffs[1]

    elif isCapture:
        fromSq = negDiffs[0]

        for i in range(8):
            for j in range(8):
                if (beforeMoveMap[i][j] != 1 and whiteOccupancyMap[i][j] == 1) or (beforeMoveMap[i][j] != -1 and blackOccupancyMap[i][j] == 1):
                    toSq = (i, j)

    else:
        fromSq = negDiffs[0]
        toSq = posDiffs[0]

    # convert from index to board ref
    move = (fromSq, toSq)
    move = (convert_to_uci(move[0]),convert_to_uci(move[1]))
    return move

def convert_to_uci(move):
    square = chr(ord("a") + move[1]) + str(8-move[0])
    return square


print(parse_move(beforeMoveMap,whiteOccupancyMap,blackOccupancyMap))
