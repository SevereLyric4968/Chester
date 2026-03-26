import subprocess
    
#runs matlabfilepath, insert variable(s) you want you spit back out
# THIS REQUIRES THE VARIABLE YOU WANT TO READ TO BE PRINTED IN THE MATLAB CONSOLE FIRST
# MAKE SURE YOU DISP(VARIABLE)
def run_subprocess(filepath: str, *variables: str) -> list[str]:
    disp_calls = "; disp('---'); ".join(f"disp({v})" for v in variables)
    result = subprocess.run(
        ["matlab", "-batch", f"run('{filepath}'); {disp_calls}"],
        capture_output=True,
        text=True
    )
    print("STDERR:", result.stderr)
    
    parts = result.stdout.strip().split('---\n')
    return [p.strip() for p in parts]

#all of this needs tested VVV
def take_image():
    image = run_subprocess("D:/Chester-master/Chester/testbed/centering.m", "test")
    print(image)

def process_pieces(image):
    white_occupancy_grid, black_occupancy_grid = run_subprocess("D:/Chester-master/Chester/testbed/centering.m", "black_occupancy_grid", "white_occupancy_grid")
    return white_occupancy_grid, black_occupancy_grid

def calibrate():
    calibration_file = run_subprocess("D:/Chester-master/Chester/testbed/process_board.m", "board_calibration.mat")
    print(calibration_file)

take_image()
calibrate()