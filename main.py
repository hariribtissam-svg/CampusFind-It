import os
from interface1 import run          # nom du fichier d'interface, sans le .py

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))   # pour que le fichier .db soit toujours trouvé
    run()