import os
from interface1 import run         

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))   
    run()
