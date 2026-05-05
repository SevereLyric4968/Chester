import matlab.engine
    
_eng = None

def get_engine():
    global _eng
    if _eng is None:
        _eng = matlab.engine.start_matlab()
    return _eng

def run_m_file(filepath):
    eng = matlab.engine.start_matlab()
    
    # Run the script
    eng.run(filepath, nargout=0)
    
    eng.quit()
    
    return

run_m_file("C:\\Users\\elisa\\Python Stoof\\Chester\\testbed\\centering.m")