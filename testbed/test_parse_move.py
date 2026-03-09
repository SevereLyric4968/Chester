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
    if not(beforeMoveMap):beforeMoveMap = [[0 for _ in range(8)] for _ in range(8)]
    afterMoveMap = [[0 for _ in range(8)] for _ in range(8)]
    for i in range(8):
        for j in range(8):
            afterMoveMap[i][j] = whiteOccupancyMap[i][j]+blackOccupancyMap[i][j]
    storageMap = 0

    changeMap = [[0 for _ in range(8)] for _ in range(8)]
    signedChangeMap = [[0 for _ in range(8)] for _ in range(8)]

    for i in range(8):
        for j in range(8):
            if abs(beforeMoveMap[i][j]) == afterMoveMap[i][j]:
                signedChangeMap[i][j] = 0
                changeMap[i][j] = 0
            elif beforeMoveMap[i][j] == 0 and afterMoveMap[i][j] == 1:
                signedChangeMap[i][j] = 1
                changeMap[i][j] = 1
            elif beforeMoveMap[i][j] != 0 and afterMoveMap[i][j] == 0:
                signedChangeMap[i][j] = -1
                changeMap[i][j] = 1

    changeCount = sum(sum(row) for row in changeMap)
    storageChangeCount = 1

    isCastling = changeCount == 4
    isPromotion = changeCount == 2 and storageChangeCount >= 2
    isCapture = changeCount == 1 and storageChangeCount == 1
    isEnPassant = changeCount == 3

    print(changeCount)

    piece = None

    if isCastling:
        negativeChanges = findGridSquare(signedChangeMap, -1)
        for i in range(2):
            if negativeChanges[i][1] == 4:
                fromSq = negativeChanges[i]
        positiveChanges = findGridSquare(signedChangeMap, 1)
        toSq = (fromSq[0],1 if positiveChanges[0][1]==1 else 6)


    elif isPromotion:
        fromSq = findGridSquare(signedChangeMap, -1)
        if storageChangeCount == 3:
            for i in range(8):
                for j in range(8):
                    if (beforeMoveMap[i][j] != 1 and whiteOccupancyMap[i][j] == 1) or (
                            beforeMoveMap[i][j] != -1 and blackOccupancyMap[i][j] == 1):
                        toSq = (i, j)

        else:
            toSq = findGridSquare(signedChangeMap, 1)
        piece = findGridSquare(storageMap, -1)

    elif isEnPassant:
        toSq = findGridSquare(signedChangeMap, 1)[0]
        for i in range(2):
            for j in range(2):
                try:
                    if signedChangeMap[toSq[0] + pow(-1, i)][toSq[1] + pow(-1, j)] == -1:
                        fromSq = (toSq[0] + pow(-1, i),toSq[1] + pow(-1, j))
                except:
                    continue

    elif isCapture:
        fromSq = findGridSquare(signedChangeMap, -1)[0]

        for i in range(8):
            for j in range(8):
                if (beforeMoveMap[i][j] != 1 and whiteOccupancyMap[i][j] == 1) or (beforeMoveMap[i][j] != -1 and blackOccupancyMap[i][j] == 1):
                    toSq = (i, j)

    else:
        fromSq = findGridSquare(signedChangeMap, -1)[0]
        toSq = findGridSquare(signedChangeMap, 1)[0]

    # convert from index to board ref
    move = (fromSq, toSq)
    print(move)
    move = (convert_to_uci(move[0]),convert_to_uci(move[1]))
    return move


def findGridSquare(grid, value):
    gridSquares = []
    for row in range(8):
        for col in range(8):
            if grid[row][col] == value:
                gridSquares.append((row, col))
    return(gridSquares)

def convert_to_uci(move):
    square = chr(ord("a") + move[1]) + str(8-move[0])
    return square


print(parse_move(beforeMoveMap,whiteOccupancyMap,blackOccupancyMap))
