
def init_board_map(self, startPos, offsetX, offsetY):
    boardMap = {}
    for rank in range(8):
        for file in range(8):
            square = chr(ord("a") + file) + str(rank + 1)
            boardMap[square] = (startPos[0] - offsetX * rank, startPos[1] + offsetY * file)

    return boardMap


def init_storage_map(self, whiteStartPos, blackStartPos, offset):
    storageMap = {}
    layout = {
        'p': [(2, i) for i in range(5)] + [(1,j) for j in range(3)],
        'r': [(4, 6), (4, 5), (3, 5), (3, 4)],
        'n': [(4, 4), (4, 3), (3, 3), (3, 2)],
        'b': [(4, 2), (4, 1), (3, 1), (3, 0)],
        'q': [(0, 0), (0, 1)],
        'k': [(4,0)]
    }

    for piece in layout:
        # iterate through piece positions
        # apply offset between grid squares
        # append to list in dictionary

        # white
        storageMap[piece.upper()] = []
        for pos in layout[piece]:
            yOffset = (0 if pos[1] == 4 else 0.5 if pos[1] == 3 else 1 if pos[1] == 2 else 2 if pos[1] == 1 else 2.5)

            x = pos[0] * offset + whiteStartPos[0]
            y = pos[1] * offset + whiteStartPos[1]
            storageMap[piece.upper()].append((x, y))

        # black
        # todo potentially need to flip black but thats a later problem
        storageMap[piece] = []
        for pos in layout[piece]:
            x = pos[0] * offset + blackStartPos[0]
            y = pos[1] * offset + blackStartPos[1]
            storageMap[piece].append((x, y))
    return storageMap


def init_storage_occupancy(self, storageMap, mode="standard"):
    # True = Occupied
    # False = Free
    standardCounts = {
        'P': 8, 'p': 8,
        'R': 2, 'r': 2,
        'N': 2, 'n': 2,
        'B': 2, 'b': 2,
        'Q': 1, 'q': 1,
        'K': 1, 'k': 1
    }
    # todo read board and manually count instead of hard code

    storageOccupancy = {}
    for pieceType in storageMap:
        storageOccupancy[pieceType] = []
        totalSlots = len(storageMap[pieceType])
        onBoard = standardCounts[pieceType]
        for i in range(totalSlots):
            if mode == "standard":
                storageOccupancy[pieceType].append(i > onBoard)
            else:
                storageOccupancy[pieceType].append(True)
    return storageOccupancy


def init_maps(self, boardCoords):
    board_map = self.init_board_map(boardCoords["boardStart"], boardCoords["xOffset"], boardCoords["yOffset"])
    storage_map = self.init_storage_map(boardCoords["whiteStorageStart"], boardCoords["blackStorageStart"],
                                        boardCoords["storageOffset"])
    storageOccupancy = self.init_storage_occupancy(storage_map)

    return board_map, storage_map, storageOccupancy