class RobotState:
    def __init__(self):
        self.movementStatus = "N/a"
        self.connectionStatus = "not connected"
        self.homedStatus = "N/a"
        self.magnetStatus="N/a"
        self.pose="N/a"

class GameState:
    def __init__(self):
        self.turn = "white"
        self.status = "normal"


class DataBus:
    def __init__(self):
        self.game = GameState()
        self.robot1 = RobotState()
        self.robot2 = RobotState()

        self.gameLog = []
        self.execLog = []
        self.errorLog = []

        self.robotBusy = False
        self.robotColor=None

    def logGame(self, msg):
        self.gameLog.append(msg)

    def logExec(self, msg):
        self.execLog.append(msg)

    def logError(self, msg):
        self.errorLog.append(msg)