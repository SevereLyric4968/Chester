import subprocess

matlab_program_path = r"C:\Program Files\MATLAB\R2025b\bin\matlab.exe"

matlab_script_path = r"D:\Chester-master\Chester\testbed\centering.m"

cmd = f'"{matlab_program_path}" -batch "run(\'{matlab_script_path}\')"'

subprocess.run(cmd, shell=True)