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
    
    # Get variables from workspace
    A = eng.workspace['Test']
    
    eng.quit()
    
    return {"Test": A}

run_m_file("D:/Chester-master/Chester/testbed/centering.m")