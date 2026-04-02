import json
import os
from pyniryo import NiryoRobot
import utils.inverse_kinematics as ik

usingIK=True

def generateSquares():
    files = "abcdefgh"
    ranks = "12345678"

    squares = []
    for i, f in enumerate(files):
        row = [f + r for r in ranks]
        if i % 2 == 1:
            row.reverse()  # snake pattern
        squares.extend(row)

    return squares


def initSideTemplate(pieceCounts):
    sideData = {}

    # board squares
    for f in "abcdefgh":
        for r in "12345678":
            sideData[f + r] = {"x": 0, "y": 0, "z": 0}

    # storage (lists)
    for piece, count in pieceCounts.items():
        sideData[piece] = [{"x": 0, "y": 0, "z": 0} for _ in range(count)]
        sideData[piece.upper()] = [{"x": 0, "y": 0, "z": 0} for _ in range(count)]

    return sideData


def initData(pieceCounts):
    return {
        "white": initSideTemplate(pieceCounts),
        "black": initSideTemplate(pieceCounts)
    }


def calibrateBoard(robot, outputPath, pieceCounts, side):
    # load or init
    if os.path.exists(outputPath):
        try:
            with open(outputPath, "r") as f:
                content = f.read().strip()
                data = json.loads(content) if content else initData(pieceCounts)
        except:
            print("Invalid JSON, starting fresh.")
            data = initData(pieceCounts)
    else:
        data = initData(pieceCounts)

    squares = generateSquares()

    print(f"\n--- Calibrating {side} board ---")

    # --- BOARD ---
    for square in squares:
        if data[side][square]["x"] != 0:
            continue

        while True:
            cmd = input(f"{side} {square} → Enter=save | r=redo | s=skip | q=quit: ").lower()

            if cmd == "q":
                return
            if cmd == "s":
                break
            
            x, y, z = None, None, None
            if usingIK:
                pose = ik.getFK(robot)
                x, y, z = pose[0], pose[1], pose[2]
            else:
                pose = robot.get_pose()
                x, y, z = pose.x, pose.y, pose.z

            print(f"Captured: {x:.4f}, {y:.4f}, {z:.4f}")
            confirm = input("Accept? (y/n): ").lower()

            if confirm == "y":
                data[side][square] = {"x": x, "y": y, "z": z}

                with open(outputPath, "w") as f:
                    json.dump(data, f, indent=2)

                break

    # --- STORAGE ---
    print(f"\n--- Calibrating {side} storage ---")

    for piece, count in pieceCounts.items():
        for casePiece in [piece.upper(), piece]:  # white + black storage

            for i in range(count):
                if data[side][casePiece][i]["x"] != 0:
                    continue

                while True:
                    cmd = input(f"{side} storage {casePiece}[{i}] → Enter=save | r=redo | s=skip | q=quit: ").lower()

                    if cmd == "q":
                        return
                    if cmd == "s":
                        break

                    x, y, z = None, None, None
                    if usingIK:
                        pose = ik.getFK(robot)
                        x, y, z = pose[0], pose[1], pose[2]
                    else:
                        pose = robot.get_pose()
                        x, y, z = pose.x, pose.y, pose.z

                    print(f"Captured: {x:.4f}, {y:.4f}, {z:.4f}")
                    confirm = input("Accept? (y/n): ").lower()

                    if confirm == "y":
                        data[side][casePiece][i] = {"x": x, "y": y, "z": z}

                        with open(outputPath, "w") as f:
                            json.dump(data, f, indent=2)

                        break

    print(f"\n{side} calibration complete.")

robot = NiryoRobot("192.168.42.1")
robot.calibrate_auto()

pieceCounts = {
        "k": 1,
        "q": 2,
        "b": 3,
        "n": 3,
        "r": 3,
        "p": 8
    }

calibrateBoard(robot, r"C:\Users\Jayda\PycharmProjects\Chester\testbed\IKLocations.json", pieceCounts,"white")