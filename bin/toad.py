# Add to the start of your script in toad/bin
import sys
import os

# Add the parent directory of 'bin' to sys.path to make 'toad' package importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from toad.lib import Toad

if __name__ == "__main__":
    currentInstance = Toad(run_mode="cli", qparams=None, mode='debug', user_id=None)
